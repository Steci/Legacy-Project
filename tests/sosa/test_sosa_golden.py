from __future__ import annotations

import json
from pathlib import Path

import pytest

from consang.adapters import build_nodes_from_domain
from parsers.gw.loader import load_geneweb_file

from sosa import build_sosa_cache, summarize_numbers


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "sosa" / "first_cousin_large.json"
)


@pytest.fixture(scope="module")
def first_cousin_golden():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def first_cousin_database(first_cousin_golden):
    source_path = Path(__file__).resolve().parents[2] / first_cousin_golden["source"]
    return load_geneweb_file(str(source_path), compute_consanguinity=True)


def test_first_cousin_sosa_matches_fixture(first_cousin_golden, first_cousin_database):
    key_to_index = first_cousin_database.relationship_key_to_index
    index_to_key = first_cousin_database.relationship_index_to_key

    root_key = first_cousin_golden["root_key"]
    root_id = key_to_index[root_key]

    persons = getattr(first_cousin_database, "consanguinity_persons", None) or list(
        first_cousin_database.persons.values()
    )
    families = getattr(first_cousin_database, "consanguinity_families", None) or list(
        first_cousin_database.families
    )

    person_nodes, family_nodes = build_nodes_from_domain(
        persons,
        families,
        from_scratch=False,
    )
    cache = build_sosa_cache(person_nodes, family_nodes, root_id)

    actual = {
        index_to_key[pid]: number
        for pid, number in cache.numbers_by_person.items()
        if pid in index_to_key
    }

    assert actual == first_cousin_golden["expected_numbers"]


def test_first_cousin_badges(first_cousin_golden, first_cousin_database):
    key_to_index = first_cousin_database.relationship_key_to_index

    persons = getattr(first_cousin_database, "consanguinity_persons", None) or list(
        first_cousin_database.persons.values()
    )
    families = getattr(first_cousin_database, "consanguinity_families", None) or list(
        first_cousin_database.families
    )

    person_nodes, family_nodes = build_nodes_from_domain(
        persons,
        families,
        from_scratch=False,
    )
    root_id = key_to_index[first_cousin_golden["root_key"]]
    cache = build_sosa_cache(person_nodes, family_nodes, root_id)

    person_ids = [key_to_index[key] for key in first_cousin_golden["expected_numbers"].keys()]
    badges = summarize_numbers(cache, person_ids)

    labels = [badge.label for badge in badges]
    assert labels == [str(value) for value in first_cousin_golden["expected_numbers"].values()]
