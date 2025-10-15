"""Simplified GeneWeb exporter used for regression comparisons."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from ..common.base_models import BaseDate, BaseEvent, Sex
from ..ged.models import GedcomDatabase, GedcomFamily, GedcomPerson


def _format_date(date: Optional[BaseDate]) -> str:
    """Return a human-readable date string."""

    if not date:
        return ""
    if date.original_text:
        return date.original_text
    parts: List[str] = []
    if date.day:
        parts.append(str(date.day))
    if date.month:
        parts.append(str(date.month))
    if date.year:
        parts.append(str(date.year))
    return "/".join(parts)


class GenewebExporter:
    """Render a minimal `.gw` representation from a `GedcomDatabase`."""

    def __init__(self) -> None:
        self._lines: List[str] = []

    def export(self, database: GedcomDatabase) -> str:
        self._lines = ["encoding: utf-8", "gwplus", ""]
        persons = database.individuals
        families = database.families

        for family in self._sort_families(families.values()):
            self._emit_family(family, persons)

        if self._lines[-1] != "":
            self._lines.append("")

        for person in self._sort_persons(persons.values()):
            self._emit_person_events(person)

        return "\n".join(self._lines).rstrip() + "\n"

    def _sort_families(self, families: Iterable[GedcomFamily]) -> List[GedcomFamily]:
        return sorted(families, key=lambda fam: fam.xref_id or "")

    def _sort_persons(self, persons: Iterable[GedcomPerson]) -> List[GedcomPerson]:
        return sorted(persons, key=lambda person: person.xref_id)

    def _emit_family(self, family: GedcomFamily, persons: Dict[str, GedcomPerson]) -> None:
        husband_name = self._format_name(persons.get(family.husband_id)) if family.husband_id else "0"
        wife_name = self._format_name(persons.get(family.wife_id)) if family.wife_id else "0"

        self._lines.append(f"fam {husband_name} + {wife_name}".strip())

        if family.marriage:
            marriage_parts: List[str] = []
            date_text = _format_date(family.marriage.date)
            if date_text:
                marriage_parts.append(f"#marr {date_text}")
            if family.marriage.place:
                marriage_parts.append(f"#p {family.marriage.place}")
            if family.marriage.source:
                marriage_parts.append(f"#s {family.marriage.source}")
            if marriage_parts:
                self._lines.append("fevt")
                self._lines.append(" ".join(marriage_parts))
                self._lines.append("end fevt")

        if family.children_ids:
            self._lines.append("beg")
            for child_id in family.children_ids:
                child = persons.get(child_id)
                if not child:
                    continue
                marker = "h" if child.sex == Sex.MALE else "f" if child.sex == Sex.FEMALE else "u"
                tokens: List[str] = [self._format_name(child)]
                if child.birth and (birth_date := _format_date(child.birth.date)):
                    tokens.append(birth_date)
                if child.death and (death_date := _format_date(child.death.date)):
                    tokens.append(death_date)
                self._lines.append(f"- {marker} {' '.join(tokens)}".rstrip())
            self._lines.append("end")

        self._lines.append("")

    def _emit_person_events(self, person: GedcomPerson) -> None:
        name = self._format_name(person)
        self._lines.append(f"pevt {name}")
        if person.birth:
            birth_line = self._format_event_line("#birt", person.birth)
            if birth_line:
                self._lines.append(birth_line)
        if person.death:
            death_line = self._format_event_line("#deat", person.death)
            if death_line:
                self._lines.append(death_line)
        self._lines.append("end pevt")
        self._lines.append("")

    def _format_name(self, person: Optional[GedcomPerson]) -> str:
        if not person:
            return "0"
        first = person.name.first_name or "0"
        last = person.name.surname or "?"
        return f"{last} {first}".strip()

    def _format_event_line(self, prefix: str, event: BaseEvent) -> str:
        components: List[str] = [prefix]
        if date_text := _format_date(event.date):
            components.append(date_text)
        if event.place:
            components.append(f"#p {event.place}")
        if event.source:
            components.append(f"#s {event.source}")
        return " ".join(components)
