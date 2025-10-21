import json
import math
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath("src"))

from consang import compute_consanguinity
from consang.models import FamilyNode, PersonNode

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "consang"


def load_fixture(name: str):
    payload = json.loads((FIXTURE_DIR / f"{name}.json").read_text())
    persons = {
        entry["id"]: PersonNode(
            person_id=entry["id"],
            parent_family_id=entry.get("parent_family")
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


@pytest.mark.parametrize(
    "fixture_name",
    [
        "simple_family",
        "first_cousin",
        "full/extended",
    ],
)
def test_compute_consanguinity_matches_golden_master(fixture_name: str):
    persons, families, expected = load_fixture(fixture_name)

    result = compute_consanguinity(persons, families, from_scratch=True)

    assert set(result.keys()) == set(expected.keys())
    for pid, expected_value in expected.items():
        assert math.isclose(
            result[pid], expected_value, rel_tol=1e-6, abs_tol=1e-6
        )

    for pid, person in persons.items():
        assert math.isclose(
            person.consanguinity,
            expected[pid],
            rel_tol=1e-6,
            abs_tol=1e-6,
        )
