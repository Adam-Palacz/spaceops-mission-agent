"""
SpaceOps Mission Agent Lab — MCP Telemetry Server
Tool: query_telemetry(time_range_start, time_range_end, channels, mission_id, dataset_ids)
Reads from data/telemetry (NDJSON) via InvestigationTelemetryView (RD1.3).
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from opentelemetry.trace import SpanKind, Status, StatusCode

from apps.mission_data.isolation import InvestigationTelemetryView
from apps.telemetry import get_tracer
from apps.tracing import extract_w3c_context_from_headers

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_TELEMETRY = REPO_ROOT / "data" / "telemetry"


mcp = FastMCP(
    "SpaceOps Telemetry",
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


def _extract_headers_from_ctx(ctx: Context | None) -> dict[str, str]:
    if ctx is None:
        return {}
    request = getattr(ctx.request_context, "request", None)
    headers = getattr(request, "headers", None)
    if headers is None:
        return {}
    return {str(k): str(v) for k, v in headers.items()}


@mcp.tool()
def query_telemetry(
    time_range_start: str,
    time_range_end: str,
    channels: list[str] | None = None,
    mission_id: str | None = None,
    dataset_ids: list[str] | None = None,
    ctx: Context | None = None,
) -> list[dict]:
    """
    Query telemetry data within a time range, optionally filtered by channel names and
    isolated by (mission_id, dataset_ids). Reads from data/telemetry (fixtures and ingest
    files) via InvestigationTelemetryView and returns values, units, and non-label
    provenance only (never ground-truth labels).
    """
    parent_context = extract_w3c_context_from_headers(
        _extract_headers_from_ctx(ctx) if ctx else {}
    )
    tracer = get_tracer("apps.mcp.telemetry")
    with tracer.start_as_current_span(
        "mcp.telemetry.query_telemetry",
        context=parent_context,
        kind=SpanKind.SERVER,
    ) as span:
        span.set_attribute("tool", "query_telemetry")
        view = InvestigationTelemetryView.from_ndjson_dir(DATA_TELEMETRY)
        out = view.query(
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            channels=channels,
            mission_id=mission_id,
            dataset_ids=dataset_ids,
            role="investigation",
        )
        span.set_attribute("outcome", "success" if out else "empty")
        try:
            span.set_attribute("result_count", len(out))
        except Exception:
            span.set_status(Status(StatusCode.ERROR, "span attribute error"))
        return out


if __name__ == "__main__":
    import uvicorn

    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)
