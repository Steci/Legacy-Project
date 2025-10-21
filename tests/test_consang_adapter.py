import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath("src"))

from consang import compute_for_domain
from models.family.family import Family
from models.person.person import Person

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "consang"


def load_fixture(name: str):
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text())


def make_domain_models(fixture_name: str):
    data = load_fixture(fixture_name)

    persons = {}
    for entry in data["persons"]:
        key = entry["id"]
        person = Person(first_name=f"P{key}", surname=f"P{key}", key_index=key)
        persons[key] = person

    families = {}
    for entry in data["families"]:
        key = entry["id"]
        family = Family(
            parent1=entry.get("father", 0) or 0,
            parent2=entry.get("mother", 0) or 0,
            children=list(entry.get("children", [])),
            key_index=key,
        )
        families[key] = family

    expected = {int(pid): value for pid, value in data["expected_consanguinity"].items()}
    return persons, families, expected


@pytest.mark.parametrize(
    "fixture_name",
    [
        "simple_family",
        "first_cousin",
        "full/extended",
    ],
)
def test_compute_for_domain_matches_golden(fixture_name: str):
    persons, families, expected = make_domain_models(fixture_name)

    result = compute_for_domain(persons.values(), families.values(), from_scratch=True)

    assert set(result.keys()) == set(expected.keys())
    for pid, value in expected.items():
        assert pytest.approx(value, rel=1e-6, abs=1e-6) == result[pid]
        assert pytest.approx(value, rel=1e-6, abs=1e-6) == getattr(persons[pid], "consanguinity", None)
