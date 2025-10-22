"""Dataclasses used by the consanguinity computation engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class PersonNode:
    """Minimal representation of a person for consanguinity calculations."""

    person_id: int
    parent_family_id: Optional[int]
    consanguinity: float = 0.0
    needs_update: bool = True


@dataclass
class FamilyNode:
    """Minimal representation of a family (union) in the pedigree graph."""

    family_id: int
    father_id: Optional[int]
    mother_id: Optional[int]
    children: Tuple[int, ...] = field(default_factory=tuple)
