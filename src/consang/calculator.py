"""High-level orchestration for consanguinity computations."""

from __future__ import annotations

from typing import Dict

from .exceptions import AncestralLoopError, ConsanguinityComputationError
from .graph import topological_order
from .kinship import KinshipCalculator
from .models import FamilyNode, PersonNode


def compute_consanguinity(
    persons: Dict[int, PersonNode],
    families: Dict[int, FamilyNode],
    *,
    from_scratch: bool = False,
) -> Dict[int, float]:
    """Compute consanguinity for all persons in the pedigree.

    Args:
        persons: Mapping of person ids to nodes.
        families: Mapping of family ids to nodes.
        from_scratch: If True, ignore existing consanguinity values.

    Returns:
        Mapping of person id to computed consanguinity.

    Raises:
        AncestralLoopError: When a cycle is detected in the ancestry graph.
        ConsanguinityComputationError: When required family data is missing.
    """

    if not persons:
        return {}

    if from_scratch:
        for node in persons.values():
            node.consanguinity = 0.0

    consanguinity = {pid: node.consanguinity for pid, node in persons.items()}
    kinship = KinshipCalculator(persons, families, consanguinity)

    ordering = topological_order(persons, families)

    for person_id in ordering:
        node = persons[person_id]
        parent_family_id = node.parent_family_id
        if parent_family_id is None:
            consanguinity[person_id] = 0.0
            node.consanguinity = 0.0
            continue

        family = families.get(parent_family_id)
        if family is None:
            raise ConsanguinityComputationError(
                f"Missing family {parent_family_id} for person {person_id}"
            )

        father_id = family.father_id
        mother_id = family.mother_id
        consang_value = kinship.kinship(father_id, mother_id)
        consanguinity[person_id] = consang_value
        node.consanguinity = consang_value

    return consanguinity
