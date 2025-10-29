from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from consang import compute_consanguinity
from consang.models import FamilyNode, PersonNode
from consang.relationship import RelationshipSummary
from parsers.gw.loader import load_geneweb_file

TESTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = TESTS_DIR.parent
FIXTURE_DIR = TESTS_DIR / "fixtures" / "consang"


def load_graph_fixture(name: str):
    payload = json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))

    persons = {
        entry["id"]: PersonNode(
            person_id=entry["id"],
            parent_family_id=entry.get("parent_family"),
        )
        for entry in payload["persons"]
    }

    families = {
        entry["id"]: FamilyNode(
            family_id=entry["id"],
            father_id=entry.get("father"),
            mother_id=entry.get("mother"),
            children=tuple(entry.get("children", [])),
        )
        for entry in payload["families"]
    }

    expected = {int(pid): value for pid, value in payload["expected_consanguinity"].items()}
    return persons, families, expected


def _serialise_paths(summary_paths):
    serialised = {}
    for ancestor in summary_paths:
        serialised[ancestor] = [
            {
                "length": branch.length,
                "multiplicity": branch.multiplicity,
                "path": list(branch.path),
            }
            for branch in summary_paths[ancestor]
        ]
    return serialised


def _serialise_summary(summary: RelationshipSummary) -> dict:
    return {
        "coefficient": summary.coefficient,
        "ancestors": list(summary.ancestors),
        "paths_to_a": _serialise_paths(summary.paths_to_a),
        "paths_to_b": _serialise_paths(summary.paths_to_b),
    }


@pytest.mark.parametrize(
    "fixture_name",
    [
        "simple_family",
        "first_cousin",
        "full/extended",
    ],
)
def test_compute_consanguinity_matches_golden_master(fixture_name: str):
    persons, families, expected = load_graph_fixture(fixture_name)

    result = compute_consanguinity(persons, families, from_scratch=True)

    assert set(result.keys()) == set(expected.keys())
    for pid, expected_value in expected.items():
        assert math.isclose(result[pid], expected_value, rel_tol=1e-6, abs_tol=1e-6)

    for pid, person in persons.items():
        assert math.isclose(person.consanguinity, expected[pid], rel_tol=1e-6, abs_tol=1e-6)


@pytest.mark.parametrize(
    ("gw_fixture", "golden_fixture"),
    [
        ("first_cousin_large.gw", "first_cousin_large_coefficients.json"),
        (PROJECT_ROOT / "examples_files" / "galichet_ref.gw", "galichetref_coefficients.json"),
    ],
)
def test_geneweb_text_refresh_matches_golden(gw_fixture, golden_fixture):
    gw_path = FIXTURE_DIR / gw_fixture if isinstance(gw_fixture, str) else Path(gw_fixture)

    golden_path = FIXTURE_DIR / golden_fixture
    expected_payload = json.loads(golden_path.read_text(encoding="utf-8"))

    expected_cons = expected_payload["expected_consanguinity"]
    expected_relationships = expected_payload.get("expected_relationships", {})

    database = load_geneweb_file(str(gw_path))

    observed = {
        person_key: database.persons[person_key].consanguinity
        for person_key in expected_cons.keys()
    }

    for key, value in expected_cons.items():
        assert math.isclose(observed[key], value, rel_tol=1e-6, abs_tol=1e-6)

    serialised_actual = {
        f"{person_a}|{person_b}": _serialise_summary(summary)
        for (person_a, person_b), summary in database.relationship_summaries.items()
    }

    assert set(serialised_actual.keys()) == set(expected_relationships.keys())

    for pair_key, expected_summary in expected_relationships.items():
        actual_summary = serialised_actual[pair_key]
        assert math.isclose(
            actual_summary["coefficient"],
            expected_summary["coefficient"],
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
        assert actual_summary["ancestors"] == expected_summary["ancestors"]
        assert actual_summary["paths_to_a"] == expected_summary["paths_to_a"]
        assert actual_summary["paths_to_b"] == expected_summary["paths_to_b"]
