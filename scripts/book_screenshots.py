#!/usr/bin/env python3
"""Plan or capture captioned SpaceOps engineering-book screenshots."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "build" / "book" / "screenshots"
TARGETS = {
    "spaceops-ui": {
        "env": "BOOK_UI_URL",
        "caption": "SpaceOps operator UI showing a synthetic incident workflow.",
    },
    "grafana": {
        "env": "BOOK_GRAFANA_URL",
        "caption": "Production-readiness SLO dashboard with synthetic data.",
    },
    "prometheus": {
        "env": "BOOK_PROMETHEUS_URL",
        "caption": "Prometheus target/rule health for the SpaceOps stage stack.",
    },
    "jaeger": {
        "env": "BOOK_JAEGER_URL",
        "caption": "Jaeger trace search for the SpaceOps API.",
    },
}


def timestamp() -> str:
    epoch = os.getenv("SOURCE_DATE_EPOCH", "").strip()
    value = datetime.fromtimestamp(int(epoch), tz=UTC) if epoch else datetime.now(UTC)
    return value.replace(microsecond=0).isoformat()


def parse_urls(items: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError("--url must use name=https://example format")
        name, url = item.split("=", 1)
        if name not in TARGETS:
            raise ValueError(f"unknown screenshot target: {name}")
        result[name] = url.strip()
    for name, metadata in TARGETS.items():
        env_url = os.getenv(str(metadata["env"]), "").strip()
        if env_url and name not in result:
            result[name] = env_url
    return result


def build_plan(urls: dict[str, str], mode: str) -> dict[str, Any]:
    items = []
    for name, metadata in TARGETS.items():
        url = urls.get(name, "")
        items.append(
            {
                "name": name,
                "caption": metadata["caption"],
                "url": url,
                "file": f"{name}.png",
                "status": "planned"
                if mode == "live" and url
                else "unavailable"
                if mode == "live"
                else "dry-run",
            }
        )
    return {
        "schema_version": "spaceops.book-screenshots.v1",
        "mode": mode,
        "generated_at": timestamp(),
        "cloud_console_automation": False,
        "items": items,
    }


async def capture(plan: dict[str, Any], output: Path) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for --mode live; install playwright and Chromium"
        ) from exc

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        for item in plan["items"]:
            if item["status"] != "planned":
                continue
            try:
                await page.goto(item["url"], wait_until="networkidle", timeout=30000)
                await page.screenshot(path=str(output / item["file"]), full_page=True)
                item["status"] = "captured"
            except Exception as exc:  # pragma: no cover - live environment dependent
                item["status"] = "failed"
                item["error"] = type(exc).__name__
        await browser.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry-run", "live"), default="dry-run")
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    urls = parse_urls(args.url)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    plan = build_plan(urls, args.mode)
    if args.mode == "live":
        asyncio.run(capture(plan, output))
    manifest = output / "screenshots.json"
    manifest.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    failed = any(item["status"] == "failed" for item in plan["items"])
    print(
        json.dumps({"result": "fail" if failed else "pass", "manifest": str(manifest)})
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
