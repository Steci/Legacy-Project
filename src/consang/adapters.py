"""Adapters between domain models and the consanguinity engine."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from models.family.family import Family
from models.person.person import Person

from .calculator import compute_consanguinity
from .exceptions import ConsanguinityComputationError
from .models import FamilyNode, PersonNode


def _normalize_parent(identifier: Any) -> int | None:
    """Return a usable parent identifier from mixed domain representations."""

    if hasattr(identifier, "key_index"):
        identifier = getattr(identifier, "key_index")

    if identifier in (None, 0):
        return None
    if isinstance(identifier, int):
        return identifier
    return None


def _extract_child_identifier(child: Any) -> int | None:
    """Return the integer identifier for a child entry.

    GeneWeb domain models may expose either numeric identifiers or Person
    instances depending on when the adapter is invoked. The consanguinity
    engine only accepts integers, so we normalize here.
    """

    if hasattr(child, "key_index"):
        child = getattr(child, "key_index")

    if child in (None, 0):
        return None
    return int(child) if isinstance(child, int) else None


def build_nodes_from_domain(
    persons: Iterable[Person],
    families: Iterable[Family],
    *,
    from_scratch: bool = False,
) -> Tuple[Dict[int, PersonNode], Dict[int, FamilyNode]]:
    """Convert domain models into lightweight nodes used by the engine."""

    person_lookup: Dict[int, Person] = {}
    for person in persons:
        if person.key_index is None:
            raise ConsanguinityComputationError(
                "Every person must have a key_index to compute consanguinity"
            )
        person_lookup[person.key_index] = person

    family_lookup: Dict[int, Family] = {}
    families_list: List[Family] = []
    for family in families:
        if family.key_index is None:
            raise ConsanguinityComputationError(
                "Every family must have a key_index to compute consanguinity"
            )
        family_lookup[family.key_index] = family
        families_list.append(family)

    parent_family_map: Dict[int, int] = {}
    for family in families_list:
        if family.key_index is None:
            continue
        for child in getattr(family, "children", ()):  # defensive for varied representations
            child_id = _extract_child_identifier(child)
            if child_id is None:
                continue
            parent_family_map[child_id] = family.key_index

    person_nodes: Dict[int, PersonNode] = {}
    for pid, person in person_lookup.items():
        initial_consang = float(getattr(person, "consanguinity", 0.0) or 0.0)
        known = bool(getattr(person, "consanguinity_known", False))
        needs_update = from_scratch or not known
        person_nodes[pid] = PersonNode(
            person_id=pid,
            parent_family_id=parent_family_map.get(pid),
            consanguinity=initial_consang,
            needs_update=needs_update,
        )

    family_nodes: Dict[int, FamilyNode] = {}
    for fid, family in family_lookup.items():
        father_id = _normalize_parent(getattr(family, "parent1", None))
        mother_id = _normalize_parent(getattr(family, "parent2", None))
        children = tuple(
            child_id
            for child_id in (
                _extract_child_identifier(child) for child in getattr(family, "children", ())
            )
            if child_id is not None
        )
        family_nodes[fid] = FamilyNode(
            family_id=fid,
            father_id=father_id,
            mother_id=mother_id,
            children=children,
        )

    return person_nodes, family_nodes


def compute_for_domain(
    persons: Iterable[Person],
    families: Iterable[Family],
    *,
    from_scratch: bool = False,
) -> Dict[int, float]:
    """High-level helper that works directly with domain models."""

    person_list = list(persons)
    family_list = list(families)

    person_nodes, family_nodes = build_nodes_from_domain(
        person_list, family_list, from_scratch=from_scratch
    )
    results = compute_consanguinity(
        person_nodes, family_nodes, from_scratch=from_scratch
    )

    person_lookup = {person.key_index: person for person in person_list if person.key_index is not None}
    for pid, value in results.items():
        person = person_lookup.get(pid)
        if person is not None:
            setattr(person, "consanguinity", value)
            setattr(person, "consanguinity_known", True)

    return results
