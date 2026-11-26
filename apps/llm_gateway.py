"""
LLM gateway contract (PS1.6, PS5.1, RD1.3).

Single entry point for agent/eval LLM calls; backends live in apps.llm_backends.
"""

from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import Any

from prometheus_client import Counter

from config import settings
from apps.llm_backends._settings import chat_completions_path
from apps.llm_backends.http_common import normalize_chat_url
from apps.llm_backends.resilience import (
    can_use_gpu_backend,
    mark_gpu_backend_failure,
    mark_gpu_backend_success,
)
from apps.llm_cost import enforce_budget_before_generate, record_llm_usage
from apps.llm_backends.registry import get_backend_generator, resolve_llm_backend
from apps.llm_gateway_errors import (
    LLMBudgetExceededError,
    LLMEgressDeniedError,
    LLMGatewayProviderError,
    LLMGatewayTimeoutError,
)
from apps.llm_provenance import record_gateway_provenance
from apps.llm_burst_routing import (
    BurstRoutingSignals,
    decide_burst_route,
    explain_gateway_routing_reason,
)
from apps.mission_data.egress import (
    EgressContext,
    EgressDecision,
    evaluate_egress,
    gateway_verified_scope,
    get_active_protected_context,
    inherit_egress_classification,
    load_egress_approvals,
)
from apps.model_selection import get_current_model_id

_logger = logging.getLogger(__name__)

LLM_BACKEND_FALLBACK_TOTAL = Counter(
    "llm_backend_fallback_total",
    "LLM backend fallbacks by backend pair and reason (PS5.4).",
    ["from_backend", "to_backend", "reason"],
)

__all__ = [
    "LLMBudgetExceededError",
    "LLMEgressDeniedError",
    "LLMGatewayProviderError",
    "LLMGatewayTimeoutError",
    "generate",
]


def _resolve_backend_target(backend: str, model_id: str) -> tuple[str, str]:
    """Resolve effective (endpoint_url, model_id) for the requested backend before egress check."""
    chat_path = chat_completions_path()
    if backend == "openai":
        base = (
            getattr(settings, "openai_base_url", "") or ""
        ).strip() or "https://api.openai.com"
        endpoint = normalize_chat_url(base, chat_path)
        return endpoint, model_id
    if backend == "cursor_sh":
        base = (
            getattr(settings, "cursor_sh_base_url", "") or ""
        ).strip() or "https://api.cursor.sh"
        endpoint = normalize_chat_url(base, chat_path)
        return endpoint, model_id
    if backend == "gpu":
        base = (getattr(settings, "gpu_llm_base_url", "") or "").strip()
        endpoint = normalize_chat_url(base, chat_path) if base else ""
        effective_model = (
            getattr(settings, "gpu_llm_model_id", "") or ""
        ).strip() or model_id
        return endpoint, effective_model
    return "", model_id


def _resolve_effective_egress_context(
    egress_context: EgressContext | None,
) -> EgressContext | None:
    """Combine any active protected scope with an explicit context without downgrading restrictions."""
    active_ctx = get_active_protected_context()
    if active_ctx is None:
        return egress_context
    if egress_context is None:
        return active_ctx
    return inherit_egress_classification([active_ctx, egress_context])


def _enforce_gateway_egress(
    *,
    backend: str,
    model_id: str,
    prompt: str,
    egress_context: EgressContext | None,
) -> tuple[str, EgressDecision | None]:
    """Evaluate RD1.3 egress policy when egress_context, protected scope, or local-only mode is active."""
    local_only_setting = bool(getattr(settings, "llm_local_only_mode", False))
    effective_ctx = _resolve_effective_egress_context(egress_context)
    if effective_ctx is None and not local_only_setting:
        return prompt, None

    ctx = effective_ctx or EgressContext(
        data_class="synthetic_ci",
        local_only=True,
    )
    endpoint_url, effective_model = _resolve_backend_target(backend, model_id)
    approvals_path_raw = (
        ctx.approvals_path
        or (getattr(settings, "llm_egress_approvals_path", "") or "").strip()
    )
    registry = load_egress_approvals(
        Path(approvals_path_raw) if approvals_path_raw else None
    )
    request = ctx.to_request(
        provider=backend,
        model_id=effective_model,
        endpoint_url=endpoint_url,
        outbound_text=prompt,
        local_only_override=local_only_setting,
    )
    evaluation = evaluate_egress(request, registry)
    decision = evaluation.decision
    _logger.info(
        "llm_egress_decision allowed=%s reason_code=%s data_class=%s dataset_ids=%s "
        "policy_revision=%s approval_id=%s provider=%s model_id=%s processing_kind=%s "
        "redaction_applied=%s",
        decision.allowed,
        decision.reason_code,
        decision.data_class,
        ",".join(decision.dataset_ids),
        decision.policy_revision,
        decision.approval_id or "none",
        decision.provider,
        decision.model_id,
        decision.processing_kind,
        decision.redaction_applied,
    )
    if not decision.allowed:
        raise LLMEgressDeniedError(
            f"LLM egress denied ({decision.reason_code}) for provider={decision.provider} "
            f"data_class={decision.data_class}",
            decision=decision,
        )
    return evaluation.sanitized_text, decision


def generate(
    *,
    prompt: str,
    node: str,
    model_id: str | None = None,
    temperature: float = 0,
    trace_context: dict[str, Any] | None = None,
    egress_context: EgressContext | None = None,
) -> dict[str, Any]:
    """
    Execute a chat completion via the configured backend and return normalized output.

    Returns:
      content, model_id, provider (alias of backend_actual), latency_ms, usage,
      backend_requested, backend_actual, fallback_used, fallback_reason
      backend_routing_reason (PS7.7)
    """
    resolved_model = (model_id or "").strip() or get_current_model_id()
    started = time.perf_counter()
    backend_requested = "unresolved"
    fallback_used = False
    fallback_reason = ""
    egress_decision: EgressDecision | None = None
    try:
        enforce_budget_before_generate(node=node)
        backend_requested = resolve_llm_backend()
        outbound_prompt, egress_decision = _enforce_gateway_egress(
            backend=backend_requested,
            model_id=resolved_model,
            prompt=prompt,
            egress_context=egress_context,
        )
        raw: dict[str, Any]
        if backend_requested != "gpu":
            backend_fn = get_backend_generator(backend_requested)
            with gateway_verified_scope():
                raw = backend_fn(
                    prompt=outbound_prompt,
                    model_id=resolved_model,
                    temperature=temperature,
                )
        else:
            with gateway_verified_scope():
                can_use, preflight_reason = can_use_gpu_backend()
            if not can_use:
                fallback_used = True
                fallback_reason = preflight_reason
                raw, fallback_decision = _fallback_to_openai_or_raise(
                    prompt=outbound_prompt,
                    model_id=resolved_model,
                    temperature=temperature,
                    fallback_reason=preflight_reason,
                    egress_context=egress_context,
                )
                if fallback_decision is not None:
                    egress_decision = fallback_decision
            else:
                backend_fn = get_backend_generator("gpu")
                try:
                    with gateway_verified_scope():
                        raw = backend_fn(
                            prompt=outbound_prompt,
                            model_id=resolved_model,
                            temperature=temperature,
                        )
                    mark_gpu_backend_success()
                except (LLMBudgetExceededError, LLMEgressDeniedError):
                    raise
                except LLMGatewayTimeoutError:
                    mark_gpu_backend_failure()
                    fallback_used = True
                    fallback_reason = "gpu_timeout"
                    raw, fallback_decision = _fallback_to_openai_or_raise(
                        prompt=outbound_prompt,
                        model_id=resolved_model,
                        temperature=temperature,
                        fallback_reason=fallback_reason,
                        egress_context=egress_context,
                    )
                    if fallback_decision is not None:
                        egress_decision = fallback_decision
                except LLMGatewayProviderError:
                    mark_gpu_backend_failure()
                    fallback_used = True
                    fallback_reason = "gpu_error"
                    raw, fallback_decision = _fallback_to_openai_or_raise(
                        prompt=outbound_prompt,
                        model_id=resolved_model,
                        temperature=temperature,
                        fallback_reason=fallback_reason,
                        egress_context=egress_context,
                    )
                    if fallback_decision is not None:
                        egress_decision = fallback_decision
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        _logger.warning(
            "llm_gateway_call node=%s provider=%s backend_requested=%s "
            "backend_actual=unserved outcome=error error_type=%s model_id=%s "
            "latency_ms=%d total_tokens=0 estimated_cost_usd=0.000000",
            node,
            backend_requested,
            backend_requested,
            type(exc).__name__,
            resolved_model,
            latency_ms,
        )
        raise
    backend_actual = str(raw.get("backend_actual") or backend_requested)
    out_model = str(raw.get("model_id") or resolved_model)
    usage = raw.get("usage") or {}
    latency_ms = int(raw.get("latency_ms") or 0)

    if trace_context:
        _logger.debug(
            "llm_gateway trace_context keys=%s",
            sorted(trace_context.keys()),
        )

    estimated_cost = float(raw.get("estimated_cost_usd") or 0)
    backend_routing_reason = _resolve_backend_routing_reason(
        backend_requested=backend_requested,
        backend_actual=backend_actual,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
    )
    record_llm_usage(
        node=node,
        backend_actual=backend_actual,
        model_id=out_model,
        total_tokens=int(usage.get("total_tokens") or 0),
        estimated_cost_usd=estimated_cost,
    )
    _logger.info(
        "llm_gateway_call node=%s provider=%s backend_requested=%s backend_actual=%s "
        "outcome=success model_id=%s latency_ms=%d total_tokens=%d "
        "fallback_used=%s fallback_reason=%s backend_routing_reason=%s estimated_cost_usd=%.6f",
        node,
        backend_actual,
        backend_requested,
        backend_actual,
        out_model,
        latency_ms,
        int(usage.get("total_tokens") or 0),
        fallback_used,
        fallback_reason,
        backend_routing_reason,
        estimated_cost,
    )
    record_gateway_provenance(
        node=node,
        backend_requested=backend_requested,
        backend_actual=backend_actual,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        backend_routing_reason=backend_routing_reason,
    )
    response: dict[str, Any] = {
        "content": str(raw.get("content") or ""),
        "model_id": out_model,
        "provider": backend_actual,
        "latency_ms": latency_ms,
        "usage": usage,
        "backend_requested": backend_requested,
        "backend_actual": backend_actual,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "backend_routing_reason": backend_routing_reason,
        "estimated_cost_usd": estimated_cost,
    }
    if egress_decision is not None:
        response["egress_decision"] = egress_decision.model_dump()
    return response


def _resolve_backend_routing_reason(
    *,
    backend_requested: str,
    backend_actual: str,
    fallback_used: bool,
    fallback_reason: str,
) -> str:
    if not getattr(settings, "llm_burst_routing_audit", True):
        return ""

    kill_switch = bool(getattr(settings, "llm_burst_kill_switch", False))
    policy_reason: str | None = None

    if getattr(settings, "llm_burst_enabled", False) and not kill_switch:
        from apps.llm_backends.resilience import can_use_gpu_backend

        burst_healthy = True
        if (getattr(settings, "llm_burst_backend", "gpu") or "gpu").strip() == "gpu":
            if (
                bool(getattr(settings, "llm_local_only_mode", False))
                or get_active_protected_context() is not None
            ):
                burst_healthy = False
            else:
                burst_healthy, _ = can_use_gpu_backend()

        policy = decide_burst_route(
            BurstRoutingSignals(
                kill_switch=False,
                burst_enabled=True,
                primary_backend="openai",
                burst_backend=str(
                    getattr(settings, "llm_burst_backend", "gpu") or "gpu"
                ),
                primary_healthy=True,
                burst_healthy=burst_healthy,
                budget_ok=True,
                burst_within_cost_ceiling=True,
                burst_latency_p95_ms=None,
                latency_sla_ms=int(
                    getattr(settings, "llm_burst_latency_sla_ms", 2000) or 2000
                ),
            )
        )
        policy_reason = policy.backend_routing_reason

    return explain_gateway_routing_reason(
        backend_requested=backend_requested,
        backend_actual=backend_actual,
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        kill_switch=kill_switch,
        burst_policy_reason=policy_reason,
    )


def _fallback_to_openai_or_raise(
    *,
    prompt: str,
    model_id: str,
    temperature: float,
    fallback_reason: str,
    egress_context: EgressContext | None = None,
) -> tuple[dict[str, Any], EgressDecision | None]:
    local_only_setting = bool(getattr(settings, "llm_local_only_mode", False))
    effective_ctx = _resolve_effective_egress_context(egress_context)
    if local_only_setting or (effective_ctx is not None and effective_ctx.local_only):
        raise LLMEgressDeniedError(
            "LLM egress denied: cloud fallback from gpu to openai is forbidden in local-only mode"
        )
    fallback_prompt = prompt
    fallback_decision: EgressDecision | None = None
    if effective_ctx is not None:
        if not effective_ctx.allow_fallback:
            raise LLMEgressDeniedError(
                "LLM egress denied: unapproved fallback from gpu to openai"
            )
        fallback_prompt, fallback_decision = _enforce_gateway_egress(
            backend="openai",
            model_id=model_id,
            prompt=prompt,
            egress_context=effective_ctx,
        )
    openai_api_key = (getattr(settings, "openai_api_key", "") or "").strip()
    if not openai_api_key:
        raise LLMGatewayProviderError(
            "GPU backend unavailable and OPENAI_API_KEY missing; cannot fallback to openai."
        )
    LLM_BACKEND_FALLBACK_TOTAL.labels(
        from_backend="gpu", to_backend="openai", reason=fallback_reason
    ).inc()
    openai_fn = get_backend_generator("openai")
    with gateway_verified_scope():
        raw = openai_fn(
            prompt=fallback_prompt,
            model_id=model_id,
            temperature=temperature,
        )
    return raw, fallback_decision
