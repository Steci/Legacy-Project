"""Graph utilities supporting consanguinity computations."""

from __future__ import annotations

from typing import Dict, List

from .exceptions import AncestralLoopError
from .models import FamilyNode, PersonNode


def _iter_parent_ids(
    person: PersonNode, families: Dict[int, FamilyNode]
) -> List[int]:
    if person.parent_family_id is None:
        return []
    family = families.get(person.parent_family_id)
    if family is None:
        return []
    return [pid for pid in (family.father_id, family.mother_id) if pid is not None]


def topological_order(
    persons: Dict[int, PersonNode], families: Dict[int, FamilyNode]
) -> List[int]:
    """Return a person ordering where ancestors appear before descendants.

    Raises:
        AncestralLoopError: if a cycle is detected in the ancestry graph.
    """

    order: List[int] = []
    visit_state: Dict[int, int] = {}
    stack: List[int] = []

    def dfs(person_id: int) -> None:
        state = visit_state.get(person_id, 0)
        if state == 1:
            if person_id in stack:
                cycle_start = stack.index(person_id)
                cycle = stack[cycle_start:] + [person_id]
            else:
                cycle = [person_id]
            raise AncestralLoopError(person_id=person_id, cycle=cycle)
        if state == 2:
            return
        visit_state[person_id] = 1
        stack.append(person_id)
        person = persons[person_id]
        for parent_id in _iter_parent_ids(person, families):
            if parent_id in persons:
                dfs(parent_id)
        visit_state[person_id] = 2
        order.append(person_id)
        stack.pop()

    for person_id in persons:
        dfs(person_id)

    return order
