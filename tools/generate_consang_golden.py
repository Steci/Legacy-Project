#!/usr/bin/env python3
"""Regenerate golden consanguinity fixtures for GeneWeb samples.

This helper loads one or more `.gw` files using the Python GeneWeb loader,
triggers the refresh step to compute consanguinity coefficients, and stores the
per-person values in the JSON format consumed by the test suite.

Usage
-----
    python tools/generate_consang_golden.py tests/fixtures/consang/first_cousin_large.gw

The script writes `{stem}_coefficients.json` files alongside the input.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from parsers.gw.loader import load_geneweb_file  # type: ignore[import]
from consang.relationship import RelationshipSummary  # type: ignore[import]


def _serialize_paths(paths: Mapping[str, Iterable]) -> Dict[str, list]:
    serialised: Dict[str, list] = {}
    for ancestor in sorted(paths):
        branches = paths[ancestor]
        serialised[ancestor] = [
            {
                "length": branch.length,
                "multiplicity": branch.multiplicity,
                "path": list(branch.path),
            }
            for branch in branches
        ]
    return serialised


def _serialize_summary(summary: RelationshipSummary) -> Dict[str, object]:
    return {
        "coefficient": summary.coefficient,
        "ancestors": list(summary.ancestors),
        "paths_to_a": _serialize_paths(summary.paths_to_a),
        "paths_to_b": _serialize_paths(summary.paths_to_b),
    }


def generate_fixture(gw_path: Path, output_dir: Path) -> Path:
    database = load_geneweb_file(str(gw_path))

    summaries = {
        f"{person_a}|{person_b}": _serialize_summary(summary)
        for (person_a, person_b), summary in sorted(database.relationship_summaries.items())
    }

    payload = {
        "source": gw_path.name,
        "expected_consanguinity": {
            key: person.consanguinity for key, person in sorted(database.persons.items())
        },
        "expected_relationships": summaries,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{gw_path.stem}_coefficients.json"
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Path(s) to GeneWeb .gw fixtures to convert into golden JSON baselines.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where JSON files should be written. Defaults to the parent directory of each input file.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    for gw_path in args.inputs:
        if not gw_path.exists():
            raise SystemExit(f"Missing GeneWeb fixture: {gw_path}")

        target_dir = (args.output_dir or gw_path.parent).resolve()
        output_path = generate_fixture(gw_path, target_dir)
        print(f"Wrote {output_path.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
