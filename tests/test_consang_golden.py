import json
import math
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath("src"))

from consang import compute_consanguinity
from consang.models import FamilyNode, PersonNode
from parsers.gw.loader import load_geneweb_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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


    @pytest.mark.parametrize(
        ("gw_fixture", "golden_fixture"),
        [
            ("first_cousin_large.gw", "first_cousin_large_coefficients.json"),
            (PROJECT_ROOT / "examples_files" / "galichet_ref.gw", "galichetref_coefficients.json"),
        ],
    )
    def test_geneweb_text_refresh_matches_golden(gw_fixture, golden_fixture):
        if isinstance(gw_fixture, str):
            gw_path = FIXTURE_DIR / gw_fixture
        else:
            gw_path = Path(gw_fixture)

        golden_path = FIXTURE_DIR / golden_fixture
        expected_payload = json.loads(golden_path.read_text(encoding="utf-8"))
        expected = expected_payload["expected_consanguinity"]

        database = load_geneweb_file(str(gw_path))

        observed = {
            person_key: database.persons[person_key].consanguinity
            for person_key in expected.keys()
        }

        for key, value in expected.items():
            assert math.isclose(observed[key], value, rel_tol=1e-6, abs_tol=1e-6)
