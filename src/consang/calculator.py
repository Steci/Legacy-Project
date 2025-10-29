"""High-level orchestration for consanguinity computations."""

from __future__ import annotations

from typing import Dict, Optional

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

    for node in persons.values():
        if from_scratch:
            node.consanguinity = 0.0
            node.needs_update = True
        elif not hasattr(node, "needs_update"):
            # Backward compatibility for externally constructed nodes
            node.needs_update = True  # type: ignore[attr-defined]

    consanguinity: Dict[int, float] = {
        pid: node.consanguinity for pid, node in persons.items()
    }
    kinship = KinshipCalculator(persons, families, consanguinity)

    family_consanguinity: Dict[int, Optional[float]] = {
        fid: None for fid in families
    }
    if not from_scratch:
        for node in persons.values():
            if not node.needs_update and node.parent_family_id is not None:
                if family_consanguinity.get(node.parent_family_id) is None:
                    family_consanguinity[node.parent_family_id] = node.consanguinity

    ordering = topological_order(persons, families)

    remaining = sum(1 for node in persons.values() if node.needs_update)
    while remaining > 0:
        progress = False
        for person_id in ordering:
            node = persons[person_id]
            if not node.needs_update:
                continue

            parent_family_id = node.parent_family_id
            consang_value: float

            if parent_family_id is None:
                consang_value = 0.0
            else:
                cached = family_consanguinity.get(parent_family_id)
                if cached is not None:
                    consang_value = cached
                else:
                    family = families.get(parent_family_id)
                    if family is None:
                        raise ConsanguinityComputationError(
                            f"Missing family {parent_family_id} for person {person_id}"
                        )

                    father_id = family.father_id
                    mother_id = family.mother_id

                    father_ready = (
                        father_id is None
                        or father_id not in persons
                        or not persons[father_id].needs_update
                    )
                    mother_ready = (
                        mother_id is None
                        or mother_id not in persons
                        or not persons[mother_id].needs_update
                    )
                    if not (father_ready and mother_ready):
                        continue

                    consang_value = kinship.kinship(father_id, mother_id)
                    family_consanguinity[parent_family_id] = consang_value

            node.consanguinity = consang_value
            node.needs_update = False
            consanguinity[person_id] = consang_value
            remaining -= 1
            progress = True

        if not progress:
            unresolved = [pid for pid, node in persons.items() if node.needs_update]
            raise ConsanguinityComputationError(
                "Unable to compute consanguinity for persons: "
                + ", ".join(str(pid) for pid in unresolved)
            )

    return consanguinity
