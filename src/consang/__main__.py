"""CLI entry-point emulating GeneWeb's `consang` utility."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from parsers.gw.loader import load_geneweb_file
from parsers.gw.refresh import refresh_consanguinity
from parsers.gw.exporter import GenewebExporter
from consang.relationship import summarize_relationship


def _format_branch_path(path: Tuple[str, ...]) -> str:
    return " -> ".join(path)


def _emit_relationship_report(
    database,
    person_keys: List[str],
    *,
    quiet_level: int,
) -> int:
    rel_info = getattr(database, "relationship_info", None)
    if rel_info is None:
        print("No relationship data available for this database.", file=sys.stderr)
        return 1

    if len(person_keys) != 2:
        print("--relationship expects exactly two person keys.", file=sys.stderr)
        return 1

    key_a, key_b = person_keys
    key_to_index = getattr(database, "relationship_key_to_index", {})
    index_to_key = getattr(database, "relationship_index_to_key", {})

    missing: List[str] = [key for key in (key_a, key_b) if key not in key_to_index]
    if missing:
        print(
            "Unknown person key(s): " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    person_a_id = key_to_index[key_a]
    person_b_id = key_to_index[key_b]

    try:
        summary = summarize_relationship(
            rel_info, person_a_id, person_b_id, index_to_key
        )
    except KeyError as exc:
        print(f"Relationship computation failed: {exc}", file=sys.stderr)
        return 1

    if quiet_level >= 2:
        return 0

    print(
        f"Relationship coefficient between {key_a} and {key_b}: "
        f"{summary.coefficient:.6f}"
    )
    if not summary.ancestors:
        print("  No common ancestors identified.")
        return 0

    for ancestor in summary.ancestors:
        print(f"  Ancestor {ancestor}:")
        for branch in summary.paths_to_a.get(ancestor, ()):
            mult = "∞" if branch.multiplicity < 0 else str(branch.multiplicity)
            print(
                f"    Path to {key_a}: length={branch.length}, multiplicity={mult}, "
                f"path={_format_branch_path(branch.path)}"
            )
        for branch in summary.paths_to_b.get(ancestor, ()):
            mult = "∞" if branch.multiplicity < 0 else str(branch.multiplicity)
            print(
                f"    Path to {key_b}: length={branch.length}, multiplicity={mult}, "
                f"path={_format_branch_path(branch.path)}"
            )

    return 0


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
    parser.add_argument(
        "--relationship",
        nargs=2,
        metavar=("PERSON_A", "PERSON_B"),
        help="Print the relationship coefficient and branches between two persons.",
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

    status = 0

    if args.relationship:
        status = max(
            status,
            _emit_relationship_report(
                database, list(args.relationship), quiet_level=args.quiet or 0
            ),
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

    return status


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
