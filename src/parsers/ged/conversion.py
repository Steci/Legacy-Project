"""Utilities to transform GEDCOM parser output into core domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional

from models.date import Date, DMY
from models.event import Event, Place, Witness
from models.family.family import Family, RelationKind
from models.person.params import Relation as PersonRelation, RelationType as PersonRelationType, Sex as PersonSex
from models.person.person import Person

from .models import GedcomDatabase, GedcomFamily, GedcomPerson, Note, Source


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@dataclass(slots=False)
class GedcomParsedDatabase:
    """Final GEDCOM representation using the domain models."""

    header: Dict[str, object]
    individuals: Dict[str, Person] = field(default_factory=dict)
    families: Dict[str, Family] = field(default_factory=dict)
    sources: Dict[str, Source] = field(default_factory=dict)
    notes: Dict[str, Note] = field(default_factory=dict)
    person_index: Dict[str, int] = field(default_factory=dict)
    family_index: Dict[str, int] = field(default_factory=dict)


def convert_legacy_database(database: GedcomDatabase) -> GedcomParsedDatabase:
    """Convert the GEDCOM parser structures into the domain data-model."""

    person_index = _build_index_map(database.individuals.keys())
    family_index = _build_index_map(database.families.keys())

    families = _convert_families(database.families, person_index, family_index)
    individuals = _convert_persons(database.individuals, families, person_index, family_index)

    return GedcomParsedDatabase(
        header=dict(database.header),
        individuals=individuals,
        families=families,
        sources=dict(database.sources),
        notes=dict(database.notes),
        person_index=person_index,
        family_index=family_index,
    )


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _build_index_map(keys: List[str]) -> Dict[str, int]:
    return {key: idx for idx, key in enumerate(sorted(keys), start=1)}


def _convert_persons(
    legacy_individuals: Dict[str, GedcomPerson],
    families: Dict[str, Family],
    person_index: Dict[str, int],
    family_index: Dict[str, int],
) -> Dict[str, Person]:
    converted: Dict[str, Person] = {}

    for xref, legacy in legacy_individuals.items():
        first_name = (legacy.first_name or "?").strip() or "?"
        surname = (legacy.surname or "?").strip() or "?"

        person = Person(
            first_name=first_name,
            surname=surname,
            public_name=legacy.public_name,
            aliases=list(legacy.aliases),
            first_names_aliases=list(legacy.first_names_aliases),
            surnames_aliases=list(legacy.surnames_aliases),
            sex=legacy.sex or PersonSex.NEUTER,
            titles=[replace(title) for title in legacy.titles],
            qualifiers=list(legacy.qualifiers),
            occupation=legacy.occupation,
            occ=legacy.occ,
            image=legacy.image,
            birth=_convert_event(legacy.birth),
            baptism=_convert_event(legacy.baptism),
            death=_convert_event(legacy.death),
            burial=_convert_event(legacy.burial),
            events=[evt for evt in (_convert_event(evt) for evt in legacy.events) if evt],
            notes=legacy.notes,
            psources=legacy.psources,
            access=legacy.access,
            key_index=person_index.get(xref),
        )

        person.related = list(legacy.related)
        person.families = [
            idx for idx in (_map_family_index(fam_xref, family_index) for fam_xref in legacy.families_as_spouse) if idx
        ]

        parents_relations: List[PersonRelation] = []
        for fam_xref in legacy.families_as_child:
            fam = families.get(fam_xref)
            if not fam:
                continue
            rel_type = PersonRelationType.RECOGNITION
            if legacy.adoption_details.get(fam_xref):
                rel_type = PersonRelationType.ADOPTION
            parents_relations.append(
                PersonRelation(
                    r_type=rel_type,
                    r_fath=fam.parent1 if fam.parent1 > 0 else None,
                    r_moth=fam.parent2 if fam.parent2 > 0 else None,
                    r_sources=fam.sources or "",
                )
            )
        person.parents = parents_relations

        setattr(person, "families_as_spouse", list(legacy.families_as_spouse))
        setattr(person, "families_as_child", list(legacy.families_as_child))
        setattr(person, "adoption_details", dict(legacy.adoption_details))
        setattr(person, "adoption_families", list(legacy.adoption_families))
        setattr(person, "godparents", list(legacy.godparents))
        setattr(person, "witnesses", [dict(entry) for entry in legacy.witnesses])
        setattr(person, "source_notes", getattr(legacy, "source_notes", ""))
        setattr(person, "xref_id", xref)

        converted[xref] = person

    return converted


def _convert_families(
    legacy_families: Dict[str, GedcomFamily],
    person_index: Dict[str, int],
    family_index: Dict[str, int],
) -> Dict[str, Family]:
    converted: Dict[str, Family] = {}

    for xref, legacy in legacy_families.items():
        parent1 = _map_person_index(legacy.husband_id, person_index)
        parent2 = _map_person_index(legacy.wife_id, person_index)
        if parent1 == 0 and parent2 == 0:
            parent2 = -1

        children = [idx for idx in (_map_person_index(child, person_index) for child in legacy.children_ids) if idx]
        relation = legacy.relation if legacy.relation else RelationKind.UNKNOWN
        family = Family(parent1=parent1, parent2=parent2, children=children, relation=relation)
        family.marriage = _convert_event(legacy.marriage)
        family.divorce = _convert_event(legacy.divorce)
        family.events = [evt for evt in (_convert_event(evt) for evt in legacy.events) if evt]
        family.notes = legacy.notes
        family.sources = legacy.sources
        family.key_index = family_index.get(xref)

        setattr(family, "adoption_notes", dict(legacy.adoption_notes))
        setattr(family, "witness_details", [dict(entry) for entry in legacy.witnesses])
        setattr(family, "witnesses", [_format_family_witness(entry) for entry in legacy.witnesses])
        setattr(family, "xref_id", xref)
        setattr(family, "husband_xref", legacy.husband_id)
        setattr(family, "wife_xref", legacy.wife_id)
        setattr(family, "children_xrefs", list(legacy.children_ids))

        converted[xref] = family

    return converted


def _convert_event(event: Optional[Event]) -> Optional[Event]:
    if not event:
        return None

    converted = Event(
        name=event.name,
        date=_clone_date(event.date),
        place=_clone_place(event.place),
        reason=event.reason,
        note=None,
        source=event.source,
        witnesses=_clone_witnesses(event.witnesses),
    )

    note = event.note or ""
    source_notes = getattr(event, "source_notes", "")
    if source_notes:
        note = _merge_note(note, source_notes)
    converted.note = note or None

    if hasattr(event, "gedcom_tag"):
        setattr(converted, "gedcom_tag", getattr(event, "gedcom_tag"))

    return converted


def _clone_date(date: Optional[Date]) -> Optional[Date]:
    if not date or not date.dmy:
        return date

    dmy = DMY(
        day=date.dmy.day,
        month=date.dmy.month,
        year=date.dmy.year,
        prec=date.dmy.prec,
        delta=date.dmy.delta,
    )
    return Date(dmy=dmy, calendar=date.calendar, text=date.text)


def _clone_place(place: Optional[Place]) -> Optional[Place]:
    if not place:
        return None

    return Place(
        country=place.country,
        region=place.region,
        district=place.district,
        county=place.county,
        township=place.township,
        canton=place.canton,
        town=place.town,
        other=place.other,
    )


def _clone_witnesses(witnesses: List[Witness]) -> List[Witness]:
    return [Witness(key_index=w.key_index, type=w.type) for w in witnesses]


def _map_person_index(xref: Optional[str], mapping: Dict[str, int]) -> int:
    return mapping.get(xref or "", 0)


def _map_family_index(xref: Optional[str], mapping: Dict[str, int]) -> Optional[int]:
    return mapping.get(xref or "")


def _merge_note(base: str, addition: str) -> str:
    if not base:
        return addition
    if not addition:
        return base
    return f"{base}<br>\n{addition}"


def _format_family_witness(entry: Dict[str, str]) -> str:
    witness = entry.get("witness") or entry.get("person") or ""
    role = entry.get("type") or entry.get("role") or ""
    if role:
        return f"{role}:{witness}"
    return witness or ""
