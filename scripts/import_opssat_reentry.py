"""Offline OPS-SAT re-entry importer CLI (RD2.2).

Real campaign rows are refused until a license and file checksums are recorded.
The lookalike path never creates a ground-truth file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from apps.mission_data.adapter import AdapterError
from apps.mission_data.opssat_reentry import (
    DEFAULT_REENTRY_LOOKALIKE_DIR,
    import_opssat_reentry,
    write_reentry_telemetry,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=None)
    parser.add_argument(
        "--lookalike",
        action="store_true",
        help="Map the checked-in synthetic table instead of the real campaign.",
    )
    parser.add_argument(
        "--telemetry-out",
        type=Path,
        default=None,
        help="Directory for lookalike telemetry NDJSON. No ground-truth file is written.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if not args.lookalike:
            import_opssat_reentry(args.source_dir, mode="real")
            return 0
        report, events = import_opssat_reentry(
            args.source_dir or DEFAULT_REENTRY_LOOKALIKE_DIR,
            mode="lookalike",
        )
        if args.telemetry_out is not None:
            write_reentry_telemetry(events, args.telemetry_out)
    except AdapterError as exc:
        print(json.dumps({"reason": str(exc), "status": "refused"}, sort_keys=True))
        return 1
    print(json.dumps(report.model_dump(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
