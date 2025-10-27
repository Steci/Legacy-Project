"""Exceptions raised by the Sosa numbering helpers."""

from __future__ import annotations

from dataclasses import dataclass


class SosaError(Exception):
    """Base error for Sosa computations."""


class MissingRootError(SosaError):
    """Raised when the requested root person is absent from the dataset."""

    def __init__(self, root_id: int) -> None:
        super().__init__(f"root person {root_id} is not available")
        self.root_id = root_id


@dataclass
class InconsistencyContext:
    """Details about a conflicting numbering assignment."""

    person_id: int
    attempted_value: int
    existing_value: int
    conflicting_person_id: int | None = None


class InconsistentSosaNumberError(SosaError):
    """Raised when two incompatible Sosa numbers are assigned."""

    def __init__(self, context: InconsistencyContext) -> None:
        if context.conflicting_person_id is not None:
            message = (
                "Sosa number "
                f"{context.attempted_value} already reserved for person {context.conflicting_person_id}; "
                f"cannot assign it to person {context.person_id}"
            )
        else:
            message = (
                f"person {context.person_id} already mapped to Sosa {context.existing_value}; "
                f"cannot reassign to {context.attempted_value}"
            )
        super().__init__(message)
        self.context = context
