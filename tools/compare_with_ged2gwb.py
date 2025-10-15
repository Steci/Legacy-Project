#!/usr/bin/env python3
"""Compare Python GEDCOM parser output with OCaml ged2gwb results."""
from __future__ import annotations

import argparse
import dataclasses
import difflib
import enum
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from parsers.ged.parser import GedcomParser  # noqa: E402
from parsers.gw.exporter import GenewebExporter  # noqa: E402
from parsers.gw.canonical import canonicalize_gw, canonicalize_gedcom  # noqa: E402
from parsers.gw.parser import GWParser  # noqa: E402


def _normalize(value: Any) -> Any:
    """Recursively convert objects into JSON-serialisable structures."""

    if dataclasses.is_dataclass(value):
        return {k: _normalize(v) for k, v in dataclasses.asdict(value).items()}

    if isinstance(value, enum.Enum):
        return value.value

    if isinstance(value, dict):
        return {str(k): _normalize(value[k]) for k in sorted(value.keys())}

    if isinstance(value, (list, tuple, set)):
        return [_normalize(item) for item in value]

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    return value


def _dump_json(data: Any, target: Path) -> str:
    """Serialise *data* to *target* and return the textual representation."""

    text = json.dumps(_normalize(data), ensure_ascii=False, indent=2, sort_keys=True)
    target.write_text(text + "\n", encoding="utf-8")
    return text


def compare_databases(gedcom_path: Path, gw_path: Path, output_dir: Path, max_diff: int) -> int:
    """Run both parsers, persist artefacts, and print diff summaries."""

    parser = GedcomParser()
    py_db = parser.parse_file(str(gedcom_path))

    gw_parser = GWParser()
    ocaml_db = gw_parser.parse_file(str(gw_path))

    output_dir.mkdir(parents=True, exist_ok=True)
    py_json_path = output_dir / "python_canonical.json"
    ocaml_json_path = output_dir / "ocaml_canonical.json"
    py_gw_path = output_dir / "python_export.gw"

    py_canonical = canonicalize_gedcom(py_db)
    ocaml_canonical = canonicalize_gw(ocaml_db)

    py_text = _dump_json(py_canonical, py_json_path)
    ocaml_text = _dump_json(ocaml_canonical, ocaml_json_path)

    python_gw_text = GenewebExporter().export(py_db)
    py_gw_path.write_text(python_gw_text, encoding="utf-8")
    ocaml_gw_text = gw_path.read_text(encoding="utf-8")

    status = 0

    gw_diff = list(
        difflib.unified_diff(
            ocaml_gw_text.splitlines(),
            python_gw_text.splitlines(),
            fromfile=gw_path.name,
            tofile=py_gw_path.name,
            lineterm="",
        )
    )

    if not gw_diff:
        print("✅ .gw exports match the reference output.")
    else:
        print("❌ Differences detected in .gw export. Showing first lines of diff:\n")
        for line in gw_diff[:max_diff]:
            print(line)
        remaining_gw = len(gw_diff) - max_diff
        if remaining_gw > 0:
            print(f"\n… {remaining_gw} additional .gw diff lines truncated.")
        print(f"\nPython .gw export written to {py_gw_path}.")
        status = 1

    diff_lines = list(
        difflib.unified_diff(
            ocaml_text.splitlines(),
            py_text.splitlines(),
            fromfile=str(ocaml_json_path.name),
            tofile=str(py_json_path.name),
            lineterm="",
        )
    )

    if not diff_lines:
        print("✅ No structural differences detected in canonical snapshots.")
    else:
        print("❌ Differences detected in canonical comparison. Showing first lines of diff:\n")
        for line in diff_lines[:max_diff]:
            print(line)

        remaining = len(diff_lines) - max_diff
        if remaining > 0:
            print(f"\n… {remaining} additional canonical diff lines truncated.")

        print(
            f"\nCanonical snapshots saved to {py_json_path} and {ocaml_json_path}.",
        )
        status = 1

    return status


def _parse_arguments(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gedcom",
        type=Path,
        default=PROJECT_ROOT / "examples_files" / "galichet.ged",
        help="Path to the GEDCOM file to feed into the Python parser.",
    )
    parser.add_argument(
        "--gw",
        type=Path,
        default=PROJECT_ROOT / "examples_files" / "galichet_ref.gw",
        help="Path to the reference .gw file produced by ged2gwb/gwu.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "comparison_output",
        help="Directory where JSON snapshots will be written.",
    )
    parser.add_argument(
        "--max-diff-lines",
        type=int,
        default=200,
        help="Maximum number of unified-diff lines to display on stdout.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_arguments(argv or sys.argv[1:])

    for path, label in ((args.gedcom, "GEDCOM"), (args.gw, ".gw reference")):
        if not path.exists():
            raise SystemExit(f"Missing {label} file: {path}")

    return compare_databases(args.gedcom, args.gw, args.output_dir, args.max_diff_lines)


if __name__ == "__main__":
    raise SystemExit(main())
