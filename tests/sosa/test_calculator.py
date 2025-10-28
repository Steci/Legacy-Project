from __future__ import annotations

import pytest

from consang.models import FamilyNode, PersonNode
from sosa import (
    InconsistentSosaNumberError,
    MissingRootError,
    SosaNavigation,
    SosaNumber,
    branch_of_sosa,
    build_sosa_cache,
    compute_single_sosa,
    get_sosa_number,
    next_sosa,
    p_of_sosa,
    previous_sosa,
)

from tests.sosa.common import build_simple_tree


def test_build_sosa_cache_assigns_numbers_and_preserves_traversal_order():
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


def test_zero_parent_identifiers_are_treated_as_missing():
	persons = {
		1: PersonNode(person_id=1, parent_family_id=1),
	}
	families = {
		1: FamilyNode(family_id=1, father_id=0, mother_id=0, children=(1,)),
	}

	cache = build_sosa_cache(persons, families, root_id=1)
	assert cache.get_number(1) == 1
	assert cache.get_number(0) is None


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


def test_get_sosa_number_helper_returns_cached_value():
	persons, families = build_simple_tree()
	cache = build_sosa_cache(persons, families, root_id=1)

	assert get_sosa_number(cache, 2) == 2
	assert get_sosa_number(cache, 99) is None


def test_compute_single_sosa_reuses_cache_instance():
	persons, families = build_simple_tree()
	cache = build_sosa_cache(persons, families, root_id=1)

	number, reused_cache = compute_single_sosa(
		persons,
		families,
		root_id=1,
		person_id=4,
		cache=cache,
	)

	assert number == 4
	assert reused_cache is cache


def test_compute_single_sosa_builds_cache_when_missing():
	persons, families = build_simple_tree()

	number, cache = compute_single_sosa(
		persons,
		families,
		root_id=1,
		person_id=3,
		cache=None,
	)

	assert number == 3
	assert cache.get_number(3) == 3


def test_compute_single_sosa_returns_none_for_non_ancestor():
	persons, families = build_simple_tree()
	persons[42] = PersonNode(person_id=42, parent_family_id=None)

	number, cache = compute_single_sosa(
		persons,
		families,
		root_id=1,
		person_id=42,
	)

	assert number is None
	assert cache.get_number(42) is None


def test_next_sosa_returns_navigation_entry():
	persons, families = build_simple_tree()
	cache = build_sosa_cache(persons, families, root_id=1)

	navigation = next_sosa(cache, 1)
	assert navigation == SosaNavigation(number=2, person_id=2)

	navigation = next_sosa(cache, 6)
	assert navigation == SosaNavigation(number=7, person_id=7)

	assert next_sosa(cache, 7) is None


def test_previous_sosa_returns_navigation_entry():
	persons, families = build_simple_tree()
	cache = build_sosa_cache(persons, families, root_id=1)

	navigation = previous_sosa(cache, 3)
	assert navigation == SosaNavigation(number=2, person_id=2)

	navigation = previous_sosa(cache, 4)
	assert navigation == SosaNavigation(number=3, person_id=3)

	assert previous_sosa(cache, 1) is None


def test_navigation_handles_missing_reference():
	persons, families = build_simple_tree()
	cache = build_sosa_cache(persons, families, root_id=1)

	assert next_sosa(cache, 50) is None
	assert previous_sosa(cache, 0) is None


def test_branch_of_sosa_returns_path_to_ancestor():
	persons, families = build_simple_tree()

	path = branch_of_sosa(persons, families, root_id=1, number=4)
	assert path == [4, 2, 1]

	path = branch_of_sosa(persons, families, root_id=1, number=3)
	assert path == [3, 1]


def test_branch_of_sosa_returns_none_when_branch_missing():
	persons, families = build_simple_tree()
	families[2] = FamilyNode(family_id=2, father_id=4, mother_id=None, children=(2,))

	path = branch_of_sosa(persons, families, root_id=1, number=5)
	assert path is None


def test_branch_of_sosa_raises_for_invalid_inputs():
	persons, families = build_simple_tree()

	with pytest.raises(ValueError):
		branch_of_sosa(persons, families, root_id=1, number=0)

	with pytest.raises(MissingRootError):
		branch_of_sosa(persons, families, root_id=99, number=1)


def test_p_of_sosa_returns_first_element_of_branch():
	persons, families = build_simple_tree()

	assert p_of_sosa(persons, families, root_id=1, number=6) == 6

	families[3] = FamilyNode(family_id=3, father_id=6, mother_id=None, children=(3,))
	assert p_of_sosa(persons, families, root_id=1, number=7) is None
