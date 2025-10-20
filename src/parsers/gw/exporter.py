"""Simplified GeneWeb exporter used for regression comparisons."""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from models.date import Date, Precision
from models.event import Event, Place
from models.person.params import Sex

from ..ged.models import GedcomDatabase, GedcomFamily, GedcomPerson


_MONTHS = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "SEPT": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}

_FRENCH_MONTHS = {
    "VEND": 1,
    "BRUM": 2,
    "FRIM": 3,
    "NIVO": 4,
    "PLUV": 5,
    "VENT": 6,
    "GERM": 7,
    "FLOR": 8,
    "PRAI": 9,
    "MESS": 10,
    "THER": 11,
    "FRUC": 12,
    "COMP": 13,
}


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
    ordered: List[str] = []
    for component in components:
        value = (component or "").strip()
        if value and value not in ordered:
            ordered.append(value)
    return ", ".join(ordered)


def _format_date(date: Optional[Date]) -> str:
    """Return a GeneWeb-friendly date string."""

    if not date:
        return ""

    text = (date.text or "").strip()
    if text.startswith("@#"):
        return _format_special_calendar(text)

    upper_text = text.upper()
    if upper_text.startswith("BET "):
        between = _format_between_expression(text)
        if between:
            return between

    qualifier = ""
    precision = date.dmy.prec if date.dmy else None
    if precision == Precision.BEFORE:
        qualifier = "<"
    elif precision == Precision.AFTER:
        qualifier = ">"
    elif precision == Precision.ABOUT:
        qualifier = "~"
    elif precision in {Precision.MAYBE, Precision.OR_YEAR, Precision.YEAR_INT}:
        return text

    qualifier_text = text
    if qualifier and upper_text.startswith(("BEF", "AFT", "ABT", "EST")):
        qualifier_text = qualifier_text[3:].strip()

    value = _format_numeric_components(date)
    if not value:
        value = _normalize_date_fragment(qualifier_text)

    if qualifier:
        return f"{qualifier}{value}".strip()

    return value or qualifier_text


def _tokenize(value: str) -> str:
    """Collapse whitespace and replace it with underscores for GeneWeb tokens."""

    collapsed = " ".join(value.replace("\r", "").replace("\n", " ").split())
    if not collapsed:
        return ""

    token = collapsed.replace(" ", "_")
    if token and not token[0].isalnum() and token[0] not in {"_", "#", "@", "%"}:
        token = "_" + token
    return token


_BETWEEN_RE = re.compile(r"^BET\s+(.*?)\s+AND\s+(.*)$", re.IGNORECASE)
_FRENCH_CALENDAR_RE = re.compile(r"^@#DFRENCH\s+R@\s+(\d{1,2})\s+([A-Z]{4})\s+(\d{1,4})$", re.IGNORECASE)


def _format_between_expression(text: str) -> str:
    match = _BETWEEN_RE.match(text.strip())
    if not match:
        return ""
    start_raw, end_raw = match.groups()
    start = _normalize_date_fragment(start_raw)
    end = _normalize_date_fragment(end_raw)
    if start and end:
        return f"{start}..{end}"
    return ""


def _format_numeric_components(date: Optional[Date]) -> str:
    if not date or not date.dmy:
        return ""

    day = date.dmy.day or 0
    month = date.dmy.month or 0
    year = date.dmy.year or 0

    if day and month and year:
        return f"{day}/{month}/{year}"
    if month and year:
        return f"{month}/{year}"
    if year:
        return str(year)
    return ""


_DAY_MONTH_YEAR = re.compile(r"^(\d{1,2})\s+([A-Z]{3,4})\s+(\d{1,4})$", re.IGNORECASE)
_MONTH_YEAR = re.compile(r"^([A-Z]{3,4})\s+(\d{1,4})$", re.IGNORECASE)


def _normalize_date_fragment(fragment: str) -> str:
    frag = fragment.strip()
    if not frag:
        return ""
    if frag.startswith("@#"):
        return frag

    match = _DAY_MONTH_YEAR.match(frag)
    if match:
        day_raw, month_raw, year_raw = match.groups()
        month = _MONTHS.get(month_raw.upper())
        if month:
            return f"{int(day_raw)}/{month}/{int(year_raw)}"

    match = _MONTH_YEAR.match(frag)
    if match:
        month_raw, year_raw = match.groups()
        month = _MONTHS.get(month_raw.upper())
        if month:
            return f"{month}/{int(year_raw)}"

    if frag.isdigit():
        return str(int(frag))

    return frag


def _format_special_calendar(text: str) -> str:
    candidate = text.strip()
    match = _FRENCH_CALENDAR_RE.match(candidate)
    if match:
        day_raw, month_raw, year_raw = match.groups()
        month = _FRENCH_MONTHS.get(month_raw.upper())
        if month:
            try:
                day = int(day_raw)
            except ValueError:
                return candidate
            year = year_raw.strip()
            suffix = "F" if not year.upper().endswith("F") else ""
            return f"{day}/{month}/{year}{suffix}"
    return candidate


class GenewebExporter:
    """Render a minimal `.gw` representation from a `GedcomDatabase`."""

    def __init__(self) -> None:
        self._lines: List[str] = []
        self._emitted_notes: Set[str] = set()
        self._emitted_persons: Set[str] = set()
        self._display_name_tokens: Dict[str, Tuple[str, ...]] = {}

    def export(self, database: GedcomDatabase) -> str:
        self._lines = ["encoding: utf-8", "gwplus", ""]
        self._emitted_notes = set()
        self._emitted_persons = set()
        self._display_name_tokens = {}
        persons = database.individuals
        families = database.families

        self._prepare_display_name_tokens(persons.values())

        ordered_families = self._sort_families(families.values())
        pending_people: List[Optional[GedcomPerson]] = []

        for index, family in enumerate(ordered_families):
            ordered_people = self._emit_family(family, persons)
            pending_people.extend(ordered_people)

            next_family = ordered_families[index + 1] if index + 1 < len(ordered_families) else None
            if next_family and self._families_share_spouse(family, next_family):
                if self._lines and self._lines[-1] == "":
                    self._lines.pop()
                continue

            remaining_family_ids = {
                fam.xref_id for fam in ordered_families[index + 1 :]
                if fam.xref_id
            }
            pending_people = self._flush_pending_people(pending_people, remaining_family_ids)

        pending_people = self._flush_pending_people(pending_people, set())

        for person in self._sort_persons(persons.values()):
            self._emit_person_events(person)

        db_note = database.header.get("notes_db") if database.header else None
        if db_note:
            note_lines = self._format_note_lines(db_note)
            if note_lines:
                while note_lines and note_lines[-1] == "<br>":
                    note_lines.pop()
                if self._lines and self._lines[-1] != "":
                    self._lines.append("")
                self._lines.append("notes-db")
                for line in note_lines:
                    self._lines.append(f"  {line}")
                self._lines.append("end notes-db")

        return "\n".join(self._lines).rstrip() + "\n"

    def _sort_families(self, families: Iterable[GedcomFamily]) -> List[GedcomFamily]:
        return sorted(families, key=lambda family: self._xref_sort_key(family.xref_id))

    def _sort_persons(self, persons: Iterable[GedcomPerson]) -> List[GedcomPerson]:
        return sorted(persons, key=lambda person: self._xref_sort_key(person.xref_id))

    def _xref_sort_key(self, xref: Optional[str]) -> Tuple[str, int, str]:
        if not xref:
            return ("", -1, "")
        stripped = xref.strip("@")
        prefix_chars = [ch for ch in stripped if ch.isalpha()]
        digit_chars = [ch for ch in stripped if ch.isdigit()]
        prefix = "".join(prefix_chars) or stripped
        number = int("".join(digit_chars)) if digit_chars else -1
        return (prefix, number, stripped)

    def _emit_family(self, family: GedcomFamily, persons: Dict[str, GedcomPerson]) -> List[GedcomPerson]:
        husband = persons.get(family.husband_id or "")
        wife = persons.get(family.wife_id or "")

        child_objects: List[GedcomPerson] = []
        child_source_counts: Dict[str, int] = {}
        child_source_order: List[str] = []
        for child_id in family.children_ids:
            child = persons.get(child_id)
            if not child:
                continue
            child_objects.append(child)
            if not child.psources:
                continue
            token = self._format_source_token(child.psources)
            if not token:
                continue
            child_source_counts[token] = child_source_counts.get(token, 0) + 1
            if token not in child_source_order:
                child_source_order.append(token)

        shared_child_sources = {
            token for token, count in child_source_counts.items() if count > 1
        }

        husband_tokens = self._format_family_person_segment(husband, shared_child_sources)
        wife_tokens = self._format_family_person_segment(wife, shared_child_sources)
        marriage_tokens = self._format_marriage_bridge(family.marriage)
        self._lines.append("fam " + " ".join(husband_tokens + marriage_tokens + wife_tokens))

        if family.sources:
            self._lines.append(f"src {self._format_token(family.sources)}")

        for token in child_source_order:
            if token in shared_child_sources:
                self._lines.append(f"csrc {token}")

        family_events = self._collect_family_events(family)

        note_segments: List[str] = []
        for _kind, event in family_events:
            if event.note:
                note_segments.append(event.note)
        if family.notes:
            note_segments.append(family.notes)

        note_payload = "\n".join(filter(None, note_segments))
        note_lines = self._format_note_lines(note_payload)
        if family_events or note_lines:
            self._lines.append("fevt")
            for kind, event in family_events:
                self._lines.append(self._format_family_event(kind, event))
            for idx, note in enumerate(note_lines):
                self._lines.append(f"note {note}")
            self._lines.append("end fevt")

        if child_objects:
            self._lines.append("beg")
            for child in child_objects:
                self._lines.append(self._format_child_line(child, shared_child_sources))
            self._lines.append("end")

        note_order: List[GedcomPerson] = []
        for child_id in family.children_ids:
            child = persons.get(child_id)
            if child:
                note_order.append(child)
        if wife:
            note_order.append(wife)
        if husband:
            note_order.append(husband)

        for person in note_order:
            if not person.notes or person.xref_id in self._emitted_notes:
                continue
            note_lines = self._format_note_lines(person.notes)
            if not note_lines:
                continue
            self._lines.append("")
            self._lines.append(f"notes {self._format_name(person)}")
            self._lines.append("beg")
            for line in note_lines:
                self._lines.append(line)
            self._lines.append("end notes")
            self._emitted_notes.add(person.xref_id)

        self._lines.append("")
        return note_order

    def _emit_person_events(self, person: Optional[GedcomPerson]) -> None:
        if not person:
            return

        if person.xref_id and person.xref_id in self._emitted_persons:
            return

        events = list(self._collect_person_events(person))
        if not events:
            return

        if person.xref_id:
            self._emitted_persons.add(person.xref_id)

        self._lines.append(f"pevt {self._format_name(person)}")
        for kind, event in events:
            formatted = self._format_person_event(kind, event)
            if formatted:
                self._lines.append(formatted)
        self._lines.append("end pevt")
        self._lines.append("")

    def _collect_person_events(self, person: GedcomPerson) -> Sequence[Tuple[str, Event]]:
        events: List[Tuple[str, Event]] = []
        seen: Set[Tuple[str, Tuple]] = set()
        allowed = {"birt", "bapt", "bapm", "chr", "deat", "bur", "buri"}

        def add(kind: str, event: Optional[Event]) -> None:
            if not event:
                return
            normalized_kind = self._normalize_person_event_kind(kind)
            if normalized_kind not in allowed:
                return
            signature = (normalized_kind, self._event_signature(event))
            if signature in seen:
                return
            seen.add(signature)
            events.append((normalized_kind, event))

        add("birt", person.birth)
        add("bapm", person.baptism)
        add("deat", person.death)
        add("buri", person.burial)
        for extra in person.events:
            add(_event_tag(extra), extra)
        return events

    def _prepare_display_name_tokens(self, persons: Iterable[GedcomPerson]) -> None:
        counts: Dict[Tuple[str, str], int] = {}
        for person in sorted(persons, key=lambda item: self._xref_sort_key(item.xref_id)):
            if not person or not person.xref_id:
                continue
            surname = self._format_token(person.surname or "?") or "?"
            first = self._format_token(person.first_name or "0") or "0"
            suffix_tokens: List[str] = []
            for qualifier in person.qualifiers:
                qualifier_token = self._format_token(qualifier)
                if qualifier_token:
                    suffix_tokens.append(qualifier_token)

            key = (surname, first)
            index = counts.get(key, 0)
            counts[key] = index + 1
            display_first = first if index == 0 else f"{first}.{index}"
            self._display_name_tokens[person.xref_id] = (surname, display_first, *suffix_tokens)

    def _get_person_name_tokens(self, person: Optional[GedcomPerson]) -> Tuple[str, ...]:
        if not person:
            return ("0",)
        cached = self._display_name_tokens.get(person.xref_id)
        if cached:
            return cached
        surname = self._format_token(person.surname or "?") or "?"
        first = self._format_token(person.first_name or "0") or "0"
        suffix_tokens: List[str] = []
        for qualifier in person.qualifiers:
            qualifier_token = self._format_token(qualifier)
            if qualifier_token:
                suffix_tokens.append(qualifier_token)
        tokens = (surname, first, *suffix_tokens)
        if person.xref_id:
            self._display_name_tokens[person.xref_id] = tokens
        return tokens

    def _get_display_first_token(self, person: Optional[GedcomPerson]) -> str:
        tokens = self._get_person_name_tokens(person)
        return tokens[1] if len(tokens) > 1 else tokens[0]

    def _format_family_person_segment(self, person: Optional[GedcomPerson], shared_sources: Set[str]) -> List[str]:
        if not person:
            return ["0"]

        tokens: List[str] = list(self._get_person_name_tokens(person))

        already_emitted = bool(person.xref_id and person.xref_id in self._emitted_persons)

        include_details = not person.families_as_child

        if person.occupation and include_details and not already_emitted:
            tokens.extend(["#occu", self._format_token(person.occupation)])
        if person.psources and not person.families_as_child:
            source_token = self._format_source_token(person.psources)
            if source_token:
                tokens.extend(["#src", source_token])

        if include_details and not already_emitted:
            birth_summary = self._format_event_summary(person.birth, include_place=True)
            death_summary = self._format_event_summary(person.death, include_place=True)

            tokens.extend(birth_summary)

            include_death = True
            if death_summary == ["0"]:
                include_death = birth_summary != ["0"]

            if include_death:
                tokens.extend(death_summary)

        return tokens

    def _format_child_line(self, child: GedcomPerson, shared_sources: Set[str]) -> str:
        marker = {
            Sex.MALE: "h",
            Sex.FEMALE: "f",
        }.get(child.sex, "u")

        parts: List[str] = [
            "-",
            marker,
            self._get_display_first_token(child),
        ]
        if child.occupation:
            parts.extend(["#occu", self._format_token(child.occupation)])
        if child.psources:
            source_token = self._format_source_token(child.psources)
            if source_token and source_token not in shared_sources:
                parts.extend(["#src", source_token])
        birth_summary = self._format_event_summary(child.birth)
        parts.extend(birth_summary)
        if "#bp" not in birth_summary and child.baptism and child.baptism.place:
            parts.extend(["#pp", self._format_place_token(_place_to_text(child.baptism.place))])
        parts.extend(self._format_event_summary(child.death))
        return " ".join(parts).rstrip()

    def _format_family_event(self, kind: str, event: Event) -> str:
        tokens: List[str] = [f"#{kind}"]
        date_text = _format_date(event.date)
        place_token = self._format_place_token(_place_to_text(event.place)) if event.place else ""
        source_token = self._format_source_token(event.source) if event.source else ""
        if date_text:
            tokens.append(date_text)
        elif place_token or source_token:
            tokens.append("")
        if place_token:
            tokens.append(f"#p {place_token}")
        if source_token:
            tokens.append(f"#s {source_token}")
        if len(tokens) == 1:
            tokens.append("")
        return " ".join(tokens)

    def _format_person_event(self, kind: str, event: Event) -> Optional[str]:
        normalized_kind = self._normalize_person_event_kind(kind)
        tokens: List[str] = [f"#{normalized_kind}"]
        date_text = _format_date(event.date)
        place_token = self._format_place_token(_place_to_text(event.place)) if event.place else ""
        source_token = self._format_source_token(event.source) if event.source else ""
        if date_text:
            tokens.append(date_text)
        elif place_token or source_token:
            tokens.append("")
        if place_token:
            tokens.append(f"#p {place_token}")
        if source_token:
            tokens.append(f"#s {source_token}")
        if len(tokens) == 1:
            tokens.append("")
        return " ".join(tokens)

    def _format_event_summary(self, event: Optional[Event], *, include_place: bool = True) -> List[str]:
        if not event:
            return ["0"]

        tokens: List[str] = []
        date_text = _format_date(event.date)
        tokens.append(date_text or "0")

        if include_place and event.place:
            place_tag = "#bp" if _event_tag(event).upper() in {"BIRT", "CHR", "BAPM"} else "#dp"
            place_token = self._format_place_token(_place_to_text(event.place))
            if place_token:
                tokens.extend([place_tag, place_token])

        if event.source:
            source_tag = "#bs" if _event_tag(event).upper() in {"BIRT", "CHR", "BAPM"} else "#ds"
            source_token = self._format_source_token(event.source)
            if source_token:
                tokens.extend([source_tag, source_token])

        return tokens

    def _format_note_lines(self, text: str) -> List[str]:
        if not text:
            return []

        formatted: List[str] = []
        raw_lines = text.replace("\r", "").split("\n")
        for raw_line in raw_lines:
            if raw_line.strip() == "":
                formatted.append("<br>")
                continue

            segments = re.split(r"(<br>)", raw_line)
            buffer = ""
            for segment in segments:
                if segment == "" or segment is None:
                    continue
                if segment == "<br>":
                    trimmed = buffer.strip()
                    if trimmed:
                        formatted.append(trimmed + "<br>")
                        buffer = ""
                    else:
                        formatted.append("<br>")
                else:
                    buffer += segment
            if buffer.strip():
                formatted.append(buffer.strip())

        return formatted

    def _format_token(self, value: str) -> str:
        return _tokenize(value)

    def _format_place_token(self, value: str) -> str:
        token = self._format_token(value)
        if not token:
            return token
        return self._escape_place_token(token)

    def _escape_place_token(self, token: str) -> str:
        if not token:
            return token
        if "[" in token or "]" in token:
            return token
        pieces: List[str] = []
        length = len(token)
        for index, char in enumerate(token):
            if char == "_":
                prev_alnum = index > 0 and token[index - 1].isalnum()
                next_alnum = index + 1 < length and token[index + 1].isalnum()
                if prev_alnum and next_alnum:
                    pieces.append("\\_")
                    continue
            pieces.append(char)
        return "".join(pieces)

    def _format_name(self, person: Optional[GedcomPerson]) -> str:
        tokens = self._get_person_name_tokens(person)
        return " ".join(filter(None, tokens)).strip()

    def _format_source_token(self, source: str) -> str:
        primary = source.replace("\r", "").split("\n", 1)[0]
        primary = primary.split("<br>", 1)[0]
        return self._format_token(primary)

    def _normalize_person_event_kind(self, kind: str) -> str:
        normalized = (kind or "").lower()
        mapping = {
            "bapm": "bapt",
            "bapt": "bapt",
            "chr": "bapt",
            "buri": "bur",
            "burial": "bur",
        }
        return mapping.get(normalized, normalized)

    def _format_marriage_bridge(self, event: Optional[Event]) -> List[str]:
        summary = self._format_marriage_summary(event)
        if not summary:
            return ["+"]
        first, *rest = summary
        if first.startswith("#"):
            return ["+"] + [first] + rest
        return ["+" + first] + rest

    def _format_marriage_summary(self, event: Optional[Event]) -> List[str]:
        if not event:
            return []

        tokens: List[str] = []
        date_text = _format_date(event.date)
        if date_text:
            tokens.append(date_text)
        if event.place:
            place_token = self._format_place_token(_place_to_text(event.place))
            if place_token:
                tokens.append(f"#mp {place_token}")
        if event.source:
            source_token = self._format_source_token(event.source)
            if source_token:
                tokens.append(f"#ms {source_token}")
        return tokens

    def _collect_family_events(self, family: GedcomFamily) -> List[Tuple[str, Event]]:
        events: List[Tuple[str, Event]] = []
        seen: Set[Tuple[str, Tuple]] = set()

        def add(kind: str, event: Optional[Event]) -> None:
            if not event:
                return
            signature = (kind, self._event_signature(event))
            if signature in seen:
                return
            seen.add(signature)
            events.append((kind, event))

        add("marr", family.marriage)
        add("div", family.divorce)
        for extra in family.events:
            add(_event_tag(extra).lower() or "event", extra)
        return events

    def _families_share_spouse(self, left: GedcomFamily, right: GedcomFamily) -> bool:
        left_ids = {left.husband_id or "", left.wife_id or ""}
        right_ids = {right.husband_id or "", right.wife_id or ""}
        left_ids.discard("")
        right_ids.discard("")
        return bool(left_ids and right_ids and left_ids.intersection(right_ids))

    def _flush_pending_people(
        self,
        pending: List[Optional[GedcomPerson]],
        remaining_family_ids: Set[str],
    ) -> List[Optional[GedcomPerson]]:
        deferred: List[Optional[GedcomPerson]] = []
        for person in pending:
            if not person:
                continue
            if self._should_defer_person(person, remaining_family_ids):
                deferred.append(person)
                continue
            self._emit_person_events(person)
        return deferred

    def _should_defer_person(self, person: GedcomPerson, remaining_family_ids: Set[str]) -> bool:
        if not remaining_family_ids or not person.families_as_child:
            return False
        return any(fid in remaining_family_ids for fid in person.families_as_child)

    def _event_signature(self, event: Event) -> Tuple:
        date = event.date
        date_signature: Tuple = ()
        if date:
            dmy = date.dmy
            date_signature = (
                dmy.day if dmy else 0,
                dmy.month if dmy else 0,
                dmy.year if dmy else 0,
                dmy.prec.value if (dmy and dmy.prec) else None,
                date.text or "",
            )
        return (
            _event_tag(event).lower(),
            date_signature,
            self._format_place_token(_place_to_text(event.place)) if event.place else "",
            self._format_source_token(event.source) if event.source else "",
            (event.note or "").strip(),
            (getattr(event, "source_notes", "") or "").strip(),
        )

    def _format_event_line(self, prefix: str, event: Event) -> str:  # pragma: no cover - backward compatibility
        return self._format_person_event(prefix.lstrip('#'), event) or ""
