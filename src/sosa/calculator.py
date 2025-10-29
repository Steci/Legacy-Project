"""Core helpers for computing Sosa-Stradonitz numbering."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import deque
from typing import Deque, Dict, List, Mapping, Optional, Tuple

from consang.models import FamilyNode, PersonNode

from .exceptions import InconsistentSosaNumberError, MissingRootError
from .types import SosaCacheState, SosaNavigation


def build_sosa_cache(
    persons: Dict[int, PersonNode],
    families: Dict[int, FamilyNode],
    root_id: int,
) -> SosaCacheState:
    """Compute Sosa numbers for known ancestors of ``root_id``.

    Only individuals present in ``persons`` are considered. Missing parents or
    absent families are ignored gracefully, mirroring GeneWeb's lazy cache.
    Raises MissingRootError when ``root_id`` is unknown. Raises
    InconsistentSosaNumberError when the ancestry graph introduces a cycle or
    conflicting numbering.
    """

    if root_id not in persons:
        raise MissingRootError(root_id)

    cache = SosaCacheState(root_id=root_id)
    pending: Deque[Tuple[int, int]] = deque([(root_id, 1)])

    while pending:
        person_id, value = pending.popleft()
        person = persons.get(person_id)
        if person is None:
            continue

        try:
            is_new = cache.register(person_id, value)
        except InconsistentSosaNumberError:
            raise

        if not is_new:
            continue

        father_id, mother_id = _lookup_parents(person, families)

        if father_id is not None:
            pending.append((father_id, value * 2))
        if mother_id is not None:
            pending.append((mother_id, value * 2 + 1))

    return cache


def get_sosa_number(cache: SosaCacheState, person_id: int) -> Optional[int]:
    """Return the cached Sosa number for ``person_id`` if present."""

    return cache.get_number(person_id)


def compute_single_sosa(
    persons: Dict[int, PersonNode],
    families: Dict[int, FamilyNode],
    root_id: int,
    person_id: int,
    *,
    cache: Optional[SosaCacheState] = None,
) -> Tuple[Optional[int], SosaCacheState]:
    """Ensure the Sosa number for ``person_id`` is available and return it.

    Reuses ``cache`` when provided and rooted at the same individual. Otherwise
    builds a fresh cache. The returned tuple exposes the resolved number (or
    ``None`` when ``person_id`` is not an ancestor of ``root_id``) and the cache
    used for the computation.
    """

    if cache is None or cache.root_id != root_id:
        cache = build_sosa_cache(persons, families, root_id)

    number = cache.get_number(person_id)
    return number, cache


def next_sosa(cache: SosaCacheState, current_number: int) -> Optional[SosaNavigation]:
    """Return the navigation target that follows ``current_number``."""

    numbers = cache.sorted_numbers()
    index = bisect_right(numbers, current_number)
    if index >= len(numbers):
        return None
    return cache.navigation(numbers[index])


def previous_sosa(cache: SosaCacheState, current_number: int) -> Optional[SosaNavigation]:
    """Return the navigation target that precedes ``current_number``."""

    numbers = cache.sorted_numbers()
    index = bisect_left(numbers, current_number) - 1
    if index < 0:
        return None
    return cache.navigation(numbers[index])


def branch_of_sosa(
    persons: Mapping[int, PersonNode],
    families: Mapping[int, FamilyNode],
    *,
    root_id: int,
    number: int,
) -> Optional[List[int]]:
    """Return the ancestor branch for ``number`` starting from ``root_id``.

    The returned list starts with the ancestor referenced by ``number`` and
    continues down to the root individual. Missing parent links return
    ``None``. ``number`` must be a positive integer.
    """

    if number < 1:
        raise ValueError("Sosa numbers must be positive integers")

    if root_id not in persons:
        raise MissingRootError(root_id)

    if number == 1:
        return [root_id]

    directions = _expand_branch(number)
    current_id = root_id
    visited: List[int] = []

    for direction in directions:
        visited.append(current_id)
        person = persons.get(current_id)
        if person is None:
            return None

        family_id = getattr(person, "parent_family_id", None)
        if family_id is None:
            return None

        family = families.get(family_id)
        if family is None:
            return None

        next_id = family.father_id if direction == 0 else family.mother_id
        if next_id in (None, 0):
            return None

        current_id = next_id

    return [current_id] + list(reversed(visited))


def p_of_sosa(
    persons: Mapping[int, PersonNode],
    families: Mapping[int, FamilyNode],
    *,
    root_id: int,
    number: int,
) -> Optional[int]:
    """Return the identifier of the ancestor referenced by ``number``."""

    branch = branch_of_sosa(
        persons,
        families,
        root_id=root_id,
        number=number,
    )
    if not branch:
        return None
    return branch[0]


def sosa_of_branch(
    persons: Mapping[int, PersonNode],
    families: Mapping[int, FamilyNode],
    *,
    branch: List[int],
) -> Optional[int]:
    """Return the Sosa number represented by ``branch`` when valid.

    ``branch`` must list ancestor identifiers starting from the targeted
    ancestor down to the root individual. When inconsistent ancestry links are
    encountered the function returns ``None`` rather than guessing.
    """

    if not branch:
        raise ValueError("Branch must contain at least one person identifier")

    if len(branch) == 1:
        return 1

    current_number = 1
    ordered_branch = list(reversed(branch))

    for index in range(1, len(ordered_branch)):
        child_id = ordered_branch[index - 1]
        parent_id = ordered_branch[index]

        child = persons.get(child_id)
        if child is None:
            return None

        family_id = getattr(child, "parent_family_id", None)
        if family_id is None:
            return None

        family = families.get(family_id)
        if family is None:
            return None

        current_number *= 2

        if family.mother_id == parent_id:
            current_number += 1
        elif family.father_id == parent_id:
            pass
        else:
            return None

    return current_number


def _lookup_parents(
    person: PersonNode,
    families: Dict[int, FamilyNode],
) -> Tuple[Optional[int], Optional[int]]:
    """Return the parent identifiers for ``person`` if available."""

    family_id = person.parent_family_id
    if family_id is None:
        return None, None

    family = families.get(family_id)
    if family is None:
        return None, None

    father_id: Optional[int] = family.father_id if family.father_id not in (None, 0) else None
    mother_id: Optional[int] = family.mother_id if family.mother_id not in (None, 0) else None
    return father_id, mother_id


def _expand_branch(number: int) -> List[int]:
    """Return branch directions for ``number`` (0 for father, 1 for mother)."""

    directions: List[int] = []
    current = number
    while current > 1:
        directions.append(0 if current % 2 == 0 else 1)
        current //= 2
    directions.reverse()
    return directions
