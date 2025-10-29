"""Kinship (coancestry) calculator backing consanguinity computations."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .models import FamilyNode, PersonNode


class KinshipCalculator:
    """Compute kinship coefficients between pairs of individuals."""

    def __init__(
        self,
        persons: Dict[int, PersonNode],
        families: Dict[int, FamilyNode],
        consanguinity: Dict[int, float],
    ) -> None:
        self._persons = persons
        self._families = families
        self._consanguinity = consanguinity
        self._cache: Dict[Tuple[int, int], float] = {}

    def _parents(self, person_id: int) -> Tuple[Optional[int], Optional[int]]:
        person = self._persons.get(person_id)
        if person is None or person.parent_family_id is None:
            return None, None
        family = self._families.get(person.parent_family_id)
        if family is None:
            return None, None
        return family.father_id, family.mother_id

    def kinship(self, first: Optional[int], second: Optional[int]) -> float:
        """Return the kinship coefficient between two individuals."""

        if first is None or second is None:
            return 0.0

        key = (first, second) if first <= second else (second, first)
        if key in self._cache:
            return self._cache[key]

        if first == second:
            value = 0.5 * (1.0 + self._consanguinity.get(first, 0.0))
        else:
            f1, m1 = self._parents(first)
            f2, m2 = self._parents(second)
            value = 0.25 * (
                self.kinship(f1, f2)
                + self.kinship(f1, m2)
                + self.kinship(m1, f2)
                + self.kinship(m1, m2)
            )

        self._cache[key] = value
        return value
