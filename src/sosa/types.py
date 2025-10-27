"""Dataclasses backing Sosa numbering caches."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional

from .exceptions import InconsistencyContext, InconsistentSosaNumberError


@dataclass(frozen=True)
class SosaNumber:
    """Pair an individual identifier with their Sosa number."""

    person_id: int
    value: int


@dataclass
class SosaCacheState:
    """Store computed Sosa numbers and navigation order."""

    root_id: int
    numbers_by_person: Dict[int, int] = field(default_factory=dict)
    persons_by_number: Dict[int, int] = field(default_factory=dict)
    traversal_order: List[int] = field(default_factory=list)

    def register(self, person_id: int, value: int) -> bool:
        """Record a Sosa number if not already present.

        Returns True when the assignment is new, False when it already existed.
        Raises InconsistentSosaNumberError if the assignment conflicts with
        an existing entry.
        """

        existing_value = self.numbers_by_person.get(person_id)
        if existing_value is not None:
            if existing_value != value:
                raise InconsistentSosaNumberError(
                    InconsistencyContext(
                        person_id=person_id,
                        attempted_value=value,
                        existing_value=existing_value,
                    )
                )
            return False

        conflicting_person_id = self.persons_by_number.get(value)
        if conflicting_person_id is not None and conflicting_person_id != person_id:
            raise InconsistentSosaNumberError(
                InconsistencyContext(
                    person_id=person_id,
                    attempted_value=value,
                    existing_value=value,
                    conflicting_person_id=conflicting_person_id,
                )
            )

        self.numbers_by_person[person_id] = value
        self.persons_by_number[value] = person_id
        self.traversal_order.append(person_id)
        return True

    def get_number(self, person_id: int) -> Optional[int]:
        """Return the Sosa number for a person, if available."""

        return self.numbers_by_person.get(person_id)

    def get_person(self, value: int) -> Optional[int]:
        """Return the person identifier owning a given Sosa number."""

        return self.persons_by_number.get(value)

    def iter_numbers(self) -> Iterator[SosaNumber]:
        """Yield SosaNumber entries in traversal order."""

        for person_id in self.traversal_order:
            yield SosaNumber(person_id=person_id, value=self.numbers_by_person[person_id])

    def extend(self, entries: Iterable[SosaNumber]) -> None:
        """Bulk-register precomputed numbers.

        Useful for replaying cached results or seeding fixtures.
        """

        for entry in entries:
            self.register(entry.person_id, entry.value)
