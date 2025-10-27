from __future__ import annotations

import pytest

from consang.models import FamilyNode, PersonNode

from sosa import (
    InconsistentSosaNumberError,
    MissingRootError,
    SosaNumber,
    build_sosa_cache,
)


def build_simple_tree():
    persons = {
        1: PersonNode(person_id=1, parent_family_id=1),
        2: PersonNode(person_id=2, parent_family_id=2),
        3: PersonNode(person_id=3, parent_family_id=3),
        4: PersonNode(person_id=4, parent_family_id=None),
        5: PersonNode(person_id=5, parent_family_id=None),
        6: PersonNode(person_id=6, parent_family_id=None),
        7: PersonNode(person_id=7, parent_family_id=None),
    }
    families = {
        1: FamilyNode(family_id=1, father_id=2, mother_id=3, children=(1,)),
        2: FamilyNode(family_id=2, father_id=4, mother_id=5, children=(2,)),
        3: FamilyNode(family_id=3, father_id=6, mother_id=7, children=(3,)),
    }
    return persons, families


def test_build_sosa_cache_assigns_basic_numbers():
    persons, families = build_simple_tree()
    cache = build_sosa_cache(persons, families, root_id=1)

    assert cache.get_number(1) == 1
    assert cache.get_number(2) == 2
    assert cache.get_number(3) == 3
    assert cache.get_number(4) == 4
    assert cache.get_number(5) == 5
    assert cache.get_number(6) == 6
    assert cache.get_number(7) == 7

    ordered = list(cache.iter_numbers())
    assert ordered == [
        SosaNumber(person_id=1, value=1),
        SosaNumber(person_id=2, value=2),
        SosaNumber(person_id=3, value=3),
        SosaNumber(person_id=4, value=4),
        SosaNumber(person_id=5, value=5),
        SosaNumber(person_id=6, value=6),
        SosaNumber(person_id=7, value=7),
    ]


def test_missing_parents_are_skipped_gracefully():
    persons = {
        1: PersonNode(person_id=1, parent_family_id=1),
        2: PersonNode(person_id=2, parent_family_id=None),
    }
    families = {
        1: FamilyNode(family_id=1, father_id=2, mother_id=None, children=(1,)),
    }

    cache = build_sosa_cache(persons, families, root_id=1)
    assert cache.get_number(1) == 1
    assert cache.get_number(2) == 2
    assert cache.get_person(3) is None


def test_reference_to_unknown_parent_is_ignored():
    persons = {
        1: PersonNode(person_id=1, parent_family_id=1),
    }
    families = {
        1: FamilyNode(family_id=1, father_id=2, mother_id=None, children=(1,)),
    }

    cache = build_sosa_cache(persons, families, root_id=1)
    assert cache.get_number(1) == 1
    assert cache.get_number(2) is None


def test_cycle_detection_raises_error():
    persons = {
        1: PersonNode(person_id=1, parent_family_id=1),
    }
    families = {
        1: FamilyNode(family_id=1, father_id=1, mother_id=None, children=(1,)),
    }

    with pytest.raises(InconsistentSosaNumberError):
        build_sosa_cache(persons, families, root_id=1)


def test_missing_root_raises_error():
    persons = {
        2: PersonNode(person_id=2, parent_family_id=None),
    }
    families = {}

    with pytest.raises(MissingRootError):
        build_sosa_cache(persons, families, root_id=1)
