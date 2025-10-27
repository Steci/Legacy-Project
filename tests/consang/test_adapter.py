from __future__ import annotations

import json
from pathlib import Path

import pytest

from consang import compute_for_domain
from models.family.family import Family
from models.person.person import Person

TESTS_DIR = next(parent for parent in Path(__file__).resolve().parents if parent.name == "tests")
FIXTURE_DIR = TESTS_DIR / "fixtures" / "consang"


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


def test_incremental_compute_respects_known_flags():
    persons, families, _expected = make_domain_models("simple_family")

    compute_for_domain(persons.values(), families.values(), from_scratch=True)

    child = persons[3]
    child.consanguinity = 0.5
    child.consanguinity_known = False

    compute_for_domain(persons.values(), families.values(), from_scratch=False)

    assert pytest.approx(0.0, rel=1e-9, abs=1e-9) == child.consanguinity
    assert child.consanguinity_known is True
    assert persons[1].consanguinity_known is True
    assert persons[2].consanguinity_known is True
