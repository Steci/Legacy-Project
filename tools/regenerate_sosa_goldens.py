from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from consang.adapters import build_nodes_from_domain
from parsers.gw.loader import load_geneweb_file
from sosa import build_sosa_cache

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "sosa"


def _load_fixture(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse JSON fixture {path}: {exc}") from exc


def _resolve_root_id(database, fixture: Mapping[str, object]) -> int:
    if "root_id" in fixture:
        return int(fixture["root_id"])  # type: ignore[arg-type]

    root_key = fixture.get("root_key")
    if not isinstance(root_key, str):
        raise SystemExit("Fixture must define either 'root_id' or 'root_key'.")

    key_to_index = getattr(database, "relationship_key_to_index", {}) or {}
    if root_key not in key_to_index:
        raise SystemExit(f"Unknown root key '{root_key}' in fixture.")
    return key_to_index[root_key]


def _select_person_ids(
    fixture: Mapping[str, object],
    *,
    key_to_index: Mapping[str, int],
    root_id: int,
) -> Sequence[int]:
    keys: Iterable[str]

    person_keys = fixture.get("person_keys")
    if isinstance(person_keys, list) and all(isinstance(item, str) for item in person_keys):
        keys = person_keys  # type: ignore[assignment]
    else:
        expected = fixture.get("expected_numbers")
        if isinstance(expected, dict):
            keys = expected.keys()  # type: ignore[assignment]
        else:
            root_key = fixture.get("root_key")
            if not isinstance(root_key, str):
                return (root_id,)
            keys = (root_key,)

    person_ids: list[int] = []
    for key in keys:
        if key not in key_to_index:
            raise SystemExit(f"Person key '{key}' not found in GeneWeb mapping.")
        person_ids.append(key_to_index[key])
    return person_ids


def _build_expected_numbers(database, fixture: Mapping[str, object]) -> dict[str, int]:
    persons = getattr(database, "consanguinity_persons", None) or list(database.persons.values())
    families = getattr(database, "consanguinity_families", None) or list(database.families)

    person_nodes, family_nodes = build_nodes_from_domain(persons, families, from_scratch=False)

    root_id = _resolve_root_id(database, fixture)
    key_to_index = getattr(database, "relationship_key_to_index", {}) or {}
    index_to_key = getattr(database, "relationship_index_to_key", {}) or {}

    person_ids = _select_person_ids(fixture, key_to_index=key_to_index, root_id=root_id)

    cache = build_sosa_cache(person_nodes, family_nodes, root_id)

    result: dict[str, int] = {}
    for person_id in person_ids:
        label = index_to_key.get(person_id, str(person_id))
        number = cache.get_number(person_id)
        if number is None:
            raise SystemExit(f"Sosa number not found for person {label} (id {person_id}).")
        result[label] = number

    return result


def regenerate_fixture(path: Path, *, check: bool = False) -> bool:
    fixture = _load_fixture(path)
    source = fixture.get("source")
    if not isinstance(source, str):
        raise SystemExit(f"Fixture {path} missing 'source' entry.")

    source_path = PROJECT_ROOT / source
    if not source_path.exists():
        raise SystemExit(f"Source GeneWeb file not found: {source_path}")

    database = load_geneweb_file(str(source_path), compute_consanguinity=True)

    expected_numbers = _build_expected_numbers(database, fixture)

    unchanged = fixture.get("expected_numbers") == expected_numbers
    if unchanged:
        return False

    if check:
        print(f"Fixture {path} is out of date.")
        return True

    fixture["expected_numbers"] = expected_numbers
    path.write_text(json.dumps(fixture, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        display_path = path.relative_to(PROJECT_ROOT)
    except ValueError:
        display_path = path
    print(f"Updated {display_path}")
    return True


def _iter_target_paths(paths: Sequence[str], include_all: bool) -> list[Path]:
    if include_all:
        return sorted(FIXTURE_ROOT.glob("*.json"))

    if not paths:
        raise SystemExit("Provide fixture paths or use --all.")

    resolved: list[Path] = []
    for entry in paths:
        candidate = Path(entry)
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / entry
        if not candidate.exists():
            raise SystemExit(f"Fixture path does not exist: {candidate}")
        resolved.append(candidate)
    return resolved


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate Sosa numbering golden fixtures.")
    parser.add_argument("fixtures", nargs="*", help="Specific fixture paths to regenerate.")
    parser.add_argument("--all", action="store_true", help="Regenerate every known Sosa fixture.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Return non-zero when fixtures would change without writing them.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    targets = _iter_target_paths(args.fixtures, args.all)
    changed = False

    for path in targets:
        changed |= regenerate_fixture(path, check=args.check)

    if args.check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
