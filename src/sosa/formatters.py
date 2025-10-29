"""Helpers for rendering Sosa numbering information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from .calculator import next_sosa, previous_sosa
from .types import SosaCacheState, SosaNavigation


@dataclass(frozen=True)
class SosaBadge:
    """Simple representation of a Sosa tag for CLI/HTML rendering."""

    number: int
    label: str


@dataclass(frozen=True)
class NavigationSummary:
    """Package previous/current/next navigation targets for display."""

    current: SosaNavigation
    previous: Optional[SosaNavigation]
    next: Optional[SosaNavigation]


def build_badge(number: Optional[int], *, fallback: str = "-" ) -> SosaBadge:
    """Create a badge using the provided Sosa number."""

    if number is None:
        label = fallback
        value = 0
    else:
        label = str(number)
        value = number
    return SosaBadge(number=value, label=label)


def build_navigation_summary(
    cache: SosaCacheState,
    person_id: int,
) -> Optional[NavigationSummary]:
    """Return navigation details for the given person identifier."""

    number = cache.get_number(person_id)
    if number is None:
        return None

    current = cache.navigation(number)
    if current is None:
        return None

    previous_entry = previous_sosa(cache, number)
    next_entry = next_sosa(cache, number)
    return NavigationSummary(current=current, previous=previous_entry, next=next_entry)


def summarize_numbers(cache: SosaCacheState, persons: Sequence[int]) -> Sequence[SosaBadge]:
    """Return badge information for a sequence of persons."""

    badges = []
    for person_id in persons:
        number = cache.get_number(person_id)
        badges.append(build_badge(number))
    return tuple(badges)
