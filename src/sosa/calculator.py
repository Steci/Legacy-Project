"""Core helpers for computing Sosa-Stradonitz numbering."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import deque
from typing import Deque, Dict, Optional, Tuple

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
