"""Offline OPSSAT-AD importer CLI (RD2.1).

Never downloads from Zenodo. Dry-run audit by default; writes NDJSON outputs only
when both ``--telemetry-out`` and ``--ground-truth-out`` are explicitly provided.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from apps.mission_data.opssat_ad import (
    DEFAULT_LOOKALIKE_DIR,
    import_opssat_ad,
    write_opssat_ad_outputs,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Local directory containing manually downloaded OPSSAT-AD dataset.csv and segments.csv.",
    )
    parser.add_argument(
        "--lookalike",
        action="store_true",
        help="Run against the checked-in synthetic CI lookalike fixture instead of real Zenodo files.",
    )
    parser.add_argument(
        "--telemetry-out",
        type=Path,
        default=None,
        help="Explicit directory for telemetry NDJSON output (must differ from --ground-truth-out).",
    )
    parser.add_argument(
        "--ground-truth-out",
        type=Path,
        default=None,
        help="Explicit directory for evaluator-only ground-truth NDJSON output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if bool(args.telemetry_out) != bool(args.ground_truth_out):
        raise SystemExit(
            "Both --telemetry-out and --ground-truth-out must be specified together."
        )
    if args.lookalike:
        source_dir = args.source_dir or DEFAULT_LOOKALIKE_DIR
        bundle = import_opssat_ad(source_dir, mode="lookalike", verify_checksums=False)
    else:
        if args.source_dir is None:
            raise SystemExit(
                "Provide --source-dir <local-dir> for real OPSSAT-AD import, or pass --lookalike."
            )
        bundle = import_opssat_ad(args.source_dir, mode="real", verify_checksums=True)

    if (
        args.telemetry_out
        and args.ground_truth_out
        and bundle.report.status == "imported"
    ):
        write_opssat_ad_outputs(
            bundle,
            telemetry_out_dir=args.telemetry_out,
            ground_truth_out_dir=args.ground_truth_out,
        )

    print(json.dumps(bundle.report.model_dump(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
