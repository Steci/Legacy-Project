"""Helpers to project GeneWeb and GEDCOM data into a shared canonical model."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple, Set

from models.date import Date, Precision
from models.event import Event, Place
from models.person.params import Sex as PersonSex

from ..ged.models import GedcomDatabase, GedcomFamily, GedcomPerson
from .models import GWDatabase, Family as GWFamily
from .exporter import build_relationship_blocks


BR_TAG_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
_EVENT_KIND_ALIASES = {
    "bapm": "bapt",
}


@dataclass(frozen=True)
class CanonicalEvent:
    kind: str
    date: Optional[str] = None
    place: Optional[str] = None
    source: Optional[str] = None
    other: Tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalChild:
    key: str
    sex: Optional[str] = None


@dataclass(frozen=True)
class CanonicalFamily:
    husband: Optional[str]
    wife: Optional[str]
    options: Tuple[str, ...]
    source: Optional[str]
    comment: Optional[str]
    witnesses: Tuple[str, ...]
    events: Tuple[CanonicalEvent, ...]
    children: Tuple[CanonicalChild, ...]


@dataclass(frozen=True)
class CanonicalPerson:
    key: str
    sex: Optional[str]
    events: Tuple[CanonicalEvent, ...]
    consanguinity: float = 0.0
    consanguinity_issue: Optional[str] = None


@dataclass(frozen=True)
class CanonicalNote:
    target: str
    text: str


@dataclass(frozen=True)
class CanonicalRelation:
    person_key: str
    lines: Tuple[str, ...]


@dataclass(frozen=True)
class CanonicalDatabase:
    families: Tuple[CanonicalFamily, ...]
    persons: Tuple[CanonicalPerson, ...]
    notes: Tuple[CanonicalNote, ...]
    relations: Tuple[CanonicalRelation, ...]
    consanguinity_warnings: Tuple[str, ...] = ()
    consanguinity_errors: Tuple[str, ...] = ()


def canonicalize_gw(database: GWDatabase) -> CanonicalDatabase:
    """Convert a parsed GeneWeb database into the canonical representation."""

    sex_map: Dict[str, str] = _derive_sex_map(database.families)

    families: List[CanonicalFamily] = []
    for family in database.families:
        event_entries: List[CanonicalEvent] = []
        for event in family.events:
            event_entries.extend(_gw_event_to_canonical(event))
        events = tuple(event_entries)
        children = tuple(
            CanonicalChild(key=child.key(), sex=_gender_to_sex(gender))
            for gender, child, _ in family.children
        )
        families.append(
            CanonicalFamily(
                husband=_normalize_key(family.husband),
                wife=_normalize_key(family.wife),
                options=(),
                source=_normalize_text(family.src),
                comment=_normalize_text(family.comm),
                witnesses=tuple(family.witnesses),
                events=events,
                children=children,
            )
        )

    persons: List[CanonicalPerson] = []
    for key, person in sorted(database.persons.items()):
        event_entries: List[CanonicalEvent] = []
        for event in person.events:
            event_entries.extend(_gw_event_to_canonical(event))
        events = tuple(event_entries)
        persons.append(
            CanonicalPerson(
                key=key,
                sex=sex_map.get(key),
                events=events,
                consanguinity=float(getattr(person, "consanguinity", 0.0) or 0.0),
                consanguinity_issue=getattr(person, "consanguinity_issue", None),
            )
        )

    notes = tuple(
        CanonicalNote(
            target=f"person:{note.person_key}",
            text=_normalize_text(note.text, collapse_whitespace=False) or "",
        )
        for note in sorted(database.notes, key=lambda n: n.person_key)
    )

    relations = _build_canonical_relations(database)

    families_sorted = tuple(
        sorted(
            families,
            key=lambda fam: (
                fam.husband or "",
                fam.wife or "",
                len(fam.children),
                tuple(child.key for child in fam.children),
            ),
        )
    )

    persons_sorted = tuple(sorted(persons, key=lambda p: p.key))

    return CanonicalDatabase(
        families=families_sorted,
        persons=persons_sorted,
        notes=notes,
        relations=relations,
        consanguinity_warnings=tuple(getattr(database, "consanguinity_warnings", []) or ()),
        consanguinity_errors=tuple(getattr(database, "consanguinity_errors", []) or ()),
    )


def canonicalize_gedcom(database: GedcomDatabase) -> CanonicalDatabase:
    """Convert a GEDCOM database into the canonical representation."""

    person_key_map = _build_person_key_map(database.individuals.values())

    families: List[CanonicalFamily] = []
    for family in database.families.values():
        husband = _normalize_key(person_key_map.get(family.husband_id))
        wife = _normalize_key(person_key_map.get(family.wife_id))
        events = _collect_family_events(family)
        children = []
        for child_id in family.children_ids:
            child_key = _normalize_key(person_key_map.get(child_id))
            if not child_key:
                continue
            child_person = database.individuals.get(child_id)
            child_sex = _sex_to_str(child_person.sex) if child_person else None
            children.append(CanonicalChild(key=child_key, sex=child_sex))
        families.append(
            CanonicalFamily(
                husband=husband,
                wife=wife,
                options=(),
                source=_normalize_text(family.sources),
                comment=_normalize_text(family.notes, collapse_whitespace=False),
                witnesses=_collect_witnesses(family, person_key_map),
                events=events,
                children=tuple(children),
            )
        )

    persons: List[CanonicalPerson] = []
    note_lookup: Dict[str, Optional[str]] = {}
    for person in database.individuals.values():
        key = _normalize_key(person_key_map.get(person.xref_id))
        if not key:
            continue
        events = _collect_person_events(person)
        note_text = _normalize_text(person.notes, collapse_whitespace=False)
        note_lookup[key] = note_text
        if not events:
            continue
        persons.append(
            CanonicalPerson(
                key=key,
                sex=_sex_to_str(person.sex),
                events=events,
            )
        )

    note_entries: List[CanonicalNote] = []
    for person in sorted(database.individuals.values(), key=lambda p: person_key_map.get(p.xref_id) or ""):
        key = _normalize_key(person_key_map.get(person.xref_id))
        if not key:
            continue
        note_text = note_lookup.get(key)
        if not note_text:
            continue
        note_entries.append(
            CanonicalNote(
                target=f"person:{key}",
                text=note_text,
            )
        )
    notes = tuple(note_entries)

    relations: Tuple[CanonicalRelation, ...] = ()

    families_sorted = tuple(
        sorted(
            families,
            key=lambda fam: (
                fam.husband or "",
                fam.wife or "",
                len(fam.children),
                tuple(child.key for child in fam.children),
            ),
        )
    )

    persons_sorted = tuple(sorted(persons, key=lambda p: p.key))

    return CanonicalDatabase(
        families=families_sorted,
        persons=persons_sorted,
        notes=notes,
        relations=relations,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _derive_sex_map(families: Iterable[GWFamily]) -> Dict[str, str]:
    sex_map: Dict[str, str] = {}
    for family in families:
        husband = _normalize_key(family.husband)
        wife = _normalize_key(family.wife)
        if husband:
            sex_map.setdefault(husband, "M")
        if wife:
            sex_map.setdefault(wife, "F")
        for gender, person, _ in family.children:
            key = _normalize_key(person.key())
            if not key:
                continue
            sex = _gender_to_sex(gender)
            if sex:
                sex_map.setdefault(key, sex)
    return sex_map


def _gw_event_to_canonical(event: Event) -> List[CanonicalEvent]:
    kind_raw = getattr(event, "gw_kind", None) or getattr(event, "name", "")
    kind = (kind_raw or "").lower()
    if not kind:
        return []

    if kind in {"note", "csrc"}:
        text = getattr(event, "note_text", None) or getattr(event, "note", None)
        normalized = _normalize_text(text)
        if not normalized or normalized.lower() in {"<br>", "<br/>", "<br />"}:
            return []
        return [
            CanonicalEvent(
                kind=kind,
                date=None,
                place=None,
                source=None,
                other=(f"text:{normalized}",),
            )
        ]

    canonical_events = _base_event_to_canonical(kind, event)
    if canonical_events:
        return canonical_events

    other_tokens = tuple(
        str(token).strip()
        for token in getattr(event, "other_tokens", ())
        if str(token).strip()
    )
    if not other_tokens:
        return []

    return [
        CanonicalEvent(
            kind=kind,
            date=None,
            place=None,
            source=None,
            other=other_tokens,
        )
    ]


def _collect_family_events(family: GedcomFamily) -> Tuple[CanonicalEvent, ...]:
    events: List[CanonicalEvent] = []

    def _extend(kind: str, base_event: Optional[Event]) -> None:
        if not base_event:
            return
        events.extend(_base_event_to_canonical(kind, base_event))

    _extend("marr", family.marriage)
    _extend("div", family.divorce)

    for extra in family.events:
        tag = _event_tag(extra).lower() or "event"
        _extend(tag, extra)

    return tuple(_deduplicate_events(events))


def _collect_person_events(person: GedcomPerson) -> Tuple[CanonicalEvent, ...]:
    events: List[CanonicalEvent] = []

    for kind, event in (
        ("birt", person.birth),
        ("bapm", person.baptism),
        ("deat", person.death),
        ("buri", person.burial),
    ):
        if event:
            events.extend(_base_event_to_canonical(kind, event))

    for extra in person.events:
        tag = _event_tag(extra).lower() or "event"
        events.extend(_base_event_to_canonical(tag, extra))

    return tuple(_deduplicate_events(events))


def _collect_witnesses(family: GedcomFamily, key_map: Dict[str, str]) -> Tuple[str, ...]:
    witnesses: List[str] = []
    for witness in family.witnesses:
        person_id = witness.get("person_id") or witness.get("person") or witness.get("witness")
        role = witness.get("role") or witness.get("type") or ""
        key = _normalize_key(key_map.get(person_id))
        if key:
            entry = f"{role}:{key}" if role else key
            witnesses.append(entry)
    return tuple(sorted(set(witnesses)))


def _base_event_to_canonical(kind: str, event: Event) -> List[CanonicalEvent]:
    normalized_kind = _EVENT_KIND_ALIASES.get(kind, kind)
    entries: List[CanonicalEvent] = []

    date = _format_event_date(event.date)
    place = _normalize_text(_place_to_text(event.place))
    source = _normalize_text(event.source)
    other: List[str] = []

    confidence = getattr(event, "confidence", None)
    if confidence:
        other.append(f"confidence:{confidence}")

    for token in getattr(event, "other_tokens", ()):
        normalized = str(token).strip()
        if normalized:
            other.append(normalized)

    if any((date, place, source, other)):
        entries.append(
            CanonicalEvent(
                kind=normalized_kind,
                date=date,
                place=place,
                source=source,
                other=tuple(other),
            )
        )

    note_events = _notes_to_canonical(event.note)
    source_notes = getattr(event, "source_notes", None)
    if source_notes:
        note_events.extend(_notes_to_canonical(source_notes, prefix="source_note"))

    entries.extend(note_events)
    return entries


def _build_person_key_map(persons: Iterable[GedcomPerson]) -> Dict[str, str]:
    key_map: Dict[str, str] = {}
    counters: Dict[Tuple[str, str], int] = {}
    for person in sorted(persons, key=lambda p: p.xref_id or ""):
        surname = _sanitize_name_component(person.surname) or "?"
        first = _sanitize_name_component(person.first_name) or "0"
        base = (surname, first)
        index = counters.get(base, 0)
        counters[base] = index + 1
        first_with_index = f"{first}.{index}" if index > 0 else first
        key_map[person.xref_id] = f"{surname} {first_with_index}".strip()
    return key_map


def _gender_to_sex(gender: Optional[str]) -> Optional[str]:
    if not gender:
        return None
    token = gender.lower()
    if token in {"h", "m", "male"}:
        return "M"
    if token in {"f", "female"}:
        return "F"
    return None


def _sex_to_str(sex: Optional[PersonSex]) -> Optional[str]:
    if not sex:
        return None
    value = sex.value if isinstance(sex, PersonSex) else str(sex)
    token = value.upper()
    if token in {"MALE", "M"}:
        return "M"
    if token in {"FEMALE", "F"}:
        return "F"
    return None


def _normalize_key(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = value.strip()
    if not text or text == "0":
        return None
    return text
def _normalize_text(value: Optional[str], *, collapse_whitespace: bool = True) -> Optional[str]:
    if value is None:
        return None

    text = str(value)
    text = text.replace("\\_", " ")
    text = text.replace("\\ ", " ")
    text = text.replace("_", " ")
    text = text.replace("\u00a0", " ")

    if collapse_whitespace:
        segments: List[str] = []
        for segment in BR_TAG_RE.split(text):
            normalized_segment = " ".join(segment.split())
            if normalized_segment and normalized_segment not in segments:
                segments.append(normalized_segment)
        text = " ; ".join(segments)
    else:
        text = BR_TAG_RE.sub("<br>", text)
        text = re.sub(r"(?:<br>\s*){2,}", "<br>\n", text)
        lines = [line.rstrip() for line in text.splitlines()]
        text = "\n".join(lines).strip()

    return text or None


def _sanitize_name_component(value: Optional[str]) -> str:
    if not value:
        return ""
    stripped = value.strip()
    sanitized = "_".join(part for part in stripped.split())
    if sanitized and sanitized[0] in {'"', "'"}:
        sanitized = f"_{sanitized}"
    return sanitized


def _event_tag(event: Optional[Event]) -> str:
    if not event:
        return ""
    tag = getattr(event, "gedcom_tag", None)
    if tag:
        return str(tag)
    name = getattr(event, "name", "")
    return str(name or "")


def _place_to_text(place: Optional[Place]) -> str:
    if not place:
        return ""

    components = [
        getattr(place, "other", ""),
        getattr(place, "town", ""),
        getattr(place, "county", ""),
        getattr(place, "district", ""),
        getattr(place, "region", ""),
        getattr(place, "country", ""),
    ]
    values: List[str] = []
    for component in components:
        text = (component or "").strip()
        if text and text not in values:
            values.append(text)
    return ", ".join(values)


def _format_event_date(date: Optional[Date]) -> Optional[str]:
    if not date:
        return None

    original = _normalize_text(date.text) if date.text else None

    if original and original.startswith("@#"):
        converted = _convert_revolutionary_date(original)
        return converted or original

    prefix = ""
    precision = date.dmy.prec if date.dmy else None
    if precision == Precision.ABOUT:
        prefix = "~"
    elif precision == Precision.BEFORE:
        prefix = "<"
    elif precision == Precision.AFTER:
        prefix = ">"
    elif precision in {Precision.MAYBE, Precision.OR_YEAR, Precision.YEAR_INT}:
        return original

    dmy = date.dmy
    if dmy and dmy.year:
        if dmy.month:
            if dmy.day:
                return f"{prefix}{dmy.day}/{dmy.month}/{dmy.year}"
            return f"{prefix}{dmy.month}/{dmy.year}"
        return f"{prefix}{dmy.year}"

    return original


_REVOLUTIONARY_MONTH_MAP = {
    "VEND": 1,
    "BRUM": 2,
    "FRIM": 3,
    "NIVO": 4,
    "PLUV": 5,
    "VENT": 6,
    "GERM": 7,
    "FLO": 8,
    "FLOR": 8,
    "PRAI": 9,
    "PRAIR": 9,
    "MESS": 10,
    "THER": 11,
    "FRUC": 12,
    "COMP": 13,
}


_REVOLUTIONARY_PATTERN = re.compile(r"@#DFRENCH\s+R@\s*(\d{1,2})\s+([A-Z]+)\s+(\d+)")


def _convert_revolutionary_date(text: str) -> Optional[str]:
    match = _REVOLUTIONARY_PATTERN.match(text.upper())
    if not match:
        return None

    day_raw, month_raw, year_raw = match.groups()
    month_key = month_raw[:5]
    for size in range(len(month_key), 2, -1):
        month = _REVOLUTIONARY_MONTH_MAP.get(month_key[:size])
        if month is not None:
            break
    else:
        month = _REVOLUTIONARY_MONTH_MAP.get(month_raw[:4])
    if month is None:
        return None

    try:
        day = int(day_raw)
    except ValueError:
        return None

    return f"{day}/{month}/{year_raw}F"


def _notes_to_canonical(text: Optional[str], prefix: str = "text") -> List[CanonicalEvent]:
    entries: List[CanonicalEvent] = []
    if not text:
        return entries
    for line in _split_note_lines(text):
        normalized = _normalize_text(line)
        if not normalized:
            continue
        if normalized.strip().lower() in {"<br>", "<br/>", "<br />"}:
            continue
        entries.append(
            CanonicalEvent(
                kind="note",
                date=None,
                place=None,
                source=None,
                other=(f"{prefix}:{normalized}",),
            )
        )
    return entries


def _split_note_lines(text: str) -> List[str]:
    text_str = str(text).replace("<br>", "<br>\n")
    parts = text_str.splitlines()
    return parts if parts else [text_str]


def _deduplicate_events(events: List[CanonicalEvent]) -> List[CanonicalEvent]:
    seen = set()
    unique: List[CanonicalEvent] = []
    for event in events:
        key = (
            event.kind,
            event.date,
            event.place,
            event.source,
            event.other,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return unique


def _build_canonical_relations(database: GWDatabase) -> Tuple[CanonicalRelation, ...]:
    relation_lines: Dict[str, List[str]] = {}
    existing_targets: Dict[str, Set[str]] = {}

    for block in getattr(database, "relations", []) or []:
        lines = list(block.lines)
        if not lines:
            continue
        relation_lines.setdefault(block.person_key, []).extend(lines)
        targets = existing_targets.setdefault(block.person_key, set())
        targets.update(filter(None, (_parse_rel_target(line) for line in lines)))

    summaries = getattr(database, "relationship_summaries", {}) or {}
    summary_blocks = build_relationship_blocks(summaries)

    for person_key, blocks in summary_blocks.items():
        targets = existing_targets.setdefault(person_key, set())
        lines = relation_lines.setdefault(person_key, [])
        for block_lines in blocks:
            other = _parse_rel_target(block_lines[0]) if block_lines else None
            if other and other in targets:
                continue
            if lines and lines[-1] != "":
                lines.append("")
            lines.extend(block_lines)
            if other:
                targets.add(other)

    canonical_relations = tuple(
        CanonicalRelation(person_key=person_key, lines=tuple(lines))
        for person_key, lines in sorted(relation_lines.items(), key=lambda item: item[0])
    )

    return canonical_relations


def _parse_rel_target(line: str) -> Optional[str]:
    stripped = (line or "").strip()
    lower = stripped.lower()
    if not lower.startswith("- rel"):
        return None
    _, _, remainder = stripped.partition(":")
    target = remainder.strip()
    if not target:
        return None
    target = target.split(" coef", 1)[0].strip()
    return target or None
