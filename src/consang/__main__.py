"""CLI entry-point emulating GeneWeb's `consang` utility."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Optional

from parsers.gw.loader import load_geneweb_file
from parsers.gw.refresh import refresh_consanguinity
from parsers.gw.exporter import GenewebExporter


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m consang",
        description="Recompute GeneWeb consanguinity coefficients.",
    )
    parser.add_argument("input", help="Path to a GeneWeb .gw file")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional path where the refreshed GeneWeb text should be written.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Reduce logging. Repeat (-qq) for silent mode.",
    )
    parser.add_argument(
        "-s",
        "--scratch",
        action="store_true",
        help="Recompute from scratch (matching GeneWeb's -scratch flag).",
    )
    parser.add_argument(
        "-f",
        "--fast",
        action="store_true",
        help="Compatibility flag; kept for parity but currently a no-op.",
    )
    return parser


def run(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Input file not found: {input_path}")

    database = load_geneweb_file(
        str(input_path), compute_consanguinity=False
    )

    refresh_consanguinity(database, from_scratch=args.scratch)

    if args.output:
        exporter = GenewebExporter()
        output_text = exporter.export(database)
        Path(args.output).write_text(output_text, encoding="utf-8")

    computed = sum(
        1 for person in database.persons.values() if getattr(person, "consanguinity_known", False)
    )

    if args.quiet == 0:
        print(
            f"Consanguinity refreshed for {computed} persons"
            f" ({'scratch' if args.scratch else 'incremental'} mode)."
        )
    if args.quiet <= 1:
        for message in database.consanguinity_errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in database.consanguinity_warnings:
            print(f"WARNING: {message}", file=sys.stderr)

    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
