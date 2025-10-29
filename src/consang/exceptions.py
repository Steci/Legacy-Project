"""Custom exceptions for the consanguinity module."""

from typing import Optional


class ConsanguinityComputationError(Exception):
    """Base error for consanguinity computation failures."""


class AncestralLoopError(ConsanguinityComputationError):
    """Raised when a cycle is detected in the ancestry graph."""

    def __init__(
        self,
        person_id: Optional[int] = None,
        cycle: Optional[list[int]] = None,
    ) -> None:
        message = "Cycle detected in ancestry graph"
        if cycle:
            cycle_str = " -> ".join(str(node) for node in cycle)
            message += f": {cycle_str}"
        elif person_id is not None:
            message += f" involving person {person_id}"
        super().__init__(message)
        self.person_id = person_id
        self.cycle = cycle or []
