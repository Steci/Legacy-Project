from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List

from .types import CousinDegree, CousinListing, RelationshipKind

_ORDINAL_WORDS: Dict[int, str] = {
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
    11: "eleventh",
    12: "twelfth",
}

_REMOVAL_WORDS: Dict[int, str] = {
    1: "once removed",
    2: "twice removed",
}


def _default_ordinal_word(degree: int) -> str:
    if degree in _ORDINAL_WORDS:
        return _ORDINAL_WORDS[degree]
    suffix = "th"
    if degree % 100 not in (11, 12, 13):
        if degree % 10 == 1:
            suffix = "st"
        elif degree % 10 == 2:
            suffix = "nd"
        elif degree % 10 == 3:
            suffix = "rd"
    return f"{degree}{suffix}"


def _default_removal_word(removal: int) -> str:
    if removal in _REMOVAL_WORDS:
        return _REMOVAL_WORDS[removal]
    if removal == 1:
        return "once removed"
    if removal == 2:
        return "twice removed"
    return f"{removal} times removed"


@dataclass(frozen=True)
class CousinTerminology:
    self_label: str = "same person"
    siblings_label: str = "siblings"
    unrelated_label: str = "unrelated"
    ancestor_descendant_label: str = "ancestor/descendant"
    ancestor_descendant_generations: str = "ancestor/descendant ({distance} generations)"
    cousin_generic_label: str = "cousins"
    cousin_phrase_template: str = "{ordinal} cousins"
    removal_joiner: str = " "
    ordinal_fn: Callable[[int], str] = field(
        default_factory=lambda: _default_ordinal_word
    )
    removal_fn: Callable[[int], str] = field(
        default_factory=lambda: _default_removal_word
    )


DEFAULT_TERMINOLOGY = CousinTerminology()


def describe_cousin_degree(
    result: CousinDegree,
    *,
    terminology: CousinTerminology | None = None,
) -> str:
    terms = terminology or DEFAULT_TERMINOLOGY

    if result.kind is RelationshipKind.SELF:
        return terms.self_label
    if result.kind is RelationshipKind.SIBLING:
        return terms.siblings_label
    if result.kind is RelationshipKind.UNRELATED:
        return terms.unrelated_label
    if result.kind is RelationshipKind.DIRECT_ANCESTOR:
        distance = max(result.generations_a or 0, result.generations_b or 0)
        if distance <= 1:
            return terms.ancestor_descendant_label
        return terms.ancestor_descendant_generations.format(distance=distance)

    if result.kind is RelationshipKind.COUSIN:
        degree = result.degree
        removal = result.removal or 0
        if degree is None:
            return terms.cousin_generic_label
        ordinal = terms.ordinal_fn(degree)
        base = terms.cousin_phrase_template.format(ordinal=ordinal)
        if removal == 0:
            return base
        removal_text = terms.removal_fn(removal)
        joiner = terms.removal_joiner
        if joiner:
            return f"{base}{joiner}{removal_text}"
        return f"{base}{removal_text}"

    return "relationship"


def format_cousin_listing(
    listing: CousinListing,
    *,
    joiner: str = " -> ",
    spouse_separator: str = ", ",
    empty_spouse_label: str = "none",
    terminology: CousinTerminology | None = None,
) -> str:
    """Return a single-line description combining descendant and spouse context."""

    degree_text = describe_cousin_degree(listing.degree, terminology=terminology)
    path_a = joiner.join(listing.path_to_a.path)
    path_b = joiner.join(listing.path_to_b.path)

    spouse_text_a = _format_spouse_segment(
        listing.spouses_a, spouse_separator, empty_spouse_label
    )
    spouse_text_b = _format_spouse_segment(
        listing.spouses_b, spouse_separator, empty_spouse_label
    )

    target_a = listing.path_to_a.path[-1] if listing.path_to_a.path else "person A"
    target_b = listing.path_to_b.path[-1] if listing.path_to_b.path else "person B"

    segments = [
        f"{listing.ancestor}: {degree_text}",
        f"path to {target_a}: {path_a} (spouses: {spouse_text_a})",
        f"path to {target_b}: {path_b} (spouses: {spouse_text_b})",
    ]

    if listing.birth_year_range:
        start, end = listing.birth_year_range
        if start == end:
            segments.append(f"birth year: {start}")
        else:
            segments.append(f"birth years: {start}-{end}")

    if listing.death_year_range:
        start, end = listing.death_year_range
        if start == end:
            segments.append(f"death year: {start}")
        else:
            segments.append(f"death years: {start}-{end}")

    return " | ".join(segments)


def format_cousin_listings(
    listings: Iterable[CousinListing],
    *,
    joiner: str = " -> ",
    spouse_separator: str = ", ",
    empty_spouse_label: str = "none",
    terminology: CousinTerminology | None = None,
) -> List[str]:
    """Format multiple cousin listings for CLI/HTML rendering."""

    return [
        format_cousin_listing(
            listing,
            joiner=joiner,
            spouse_separator=spouse_separator,
            empty_spouse_label=empty_spouse_label,
            terminology=terminology,
        )
        for listing in listings
    ]


def _format_spouse_segment(
    spouses: Iterable[str],
    separator: str,
    empty_label: str,
) -> str:
    values = list(dict.fromkeys(spouses))
    if not values:
        return empty_label
    return separator.join(values)
