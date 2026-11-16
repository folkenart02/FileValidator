from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from .config import Config
from .runner import ValidationRunner
from .Rules.base import Severity


def _coerce_severity(value: str | None) -> Severity | None:
    if value is None:
        return None
    normalized = value.lower()
    for severity in Severity:
        if severity.value.lower() == normalized:
            return severity
    raise argparse.ArgumentTypeError(f"Unsupported severity: {value}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validator",
        description="Validate files and assets with the FileValidator ruleset.",
    )
    parser.add_argument(
        "--directory",
        "-d",
        dest="directory",
        default=".",
        help="Directory to validate (defaults to the current working directory).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to a JSON config file.",
    )
    parser.add_argument(
        "--asset-type",
        choices=("env", "chr"),
        help="Limit validation to environment or character assets.",
    )
    parser.add_argument(
        "--severity",
        choices=[severity.value.lower() for severity in Severity],
        help="Filter console output to one severity level.",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Filter reporting to one rule category.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the console summary output.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose reporting.",
    )
    parser.add_argument(
        "--show-passed",
        action="store_true",
        help="Include passing checks in the console summary.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to the JSON report file.",
    )
    return parser


def run_cli(args: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    target_directory = Path(parsed.directory).expanduser()
    if not target_directory.exists():
        parser.error(f"Directory does not exist: {target_directory}")
    if not target_directory.is_dir():
        parser.error(f"Path is not a directory: {target_directory}")

    config = Config(path=parsed.config)
    runner = ValidationRunner(
        config,
        category=parsed.category,
        severity=_coerce_severity(parsed.severity),
        asset_type=parsed.asset_type,
    )

    results = runner.validate_directory(str(target_directory))
    output_path = runner.json_parser(results, output_path=parsed.output)

    if not parsed.quiet:
        runner.Summary(
            results,
            severity=_coerce_severity(parsed.severity),
            category=parsed.category,
            show_passed=parsed.show_passed,
            verbose=parsed.verbose,
            quiet=parsed.quiet,
        )

    print(f"[CLI] JSON report written to: {output_path}")
    return 0


def main(args: Sequence[str] | None = None) -> int:
    try:
        return run_cli(args)
    except KeyboardInterrupt:
        print("[CLI] Interrupted by user.", file=sys.stderr)
        return 130
    except Exception as exc:  # pragma: no cover - defensive CLI handling
        print(f"[CLI] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
