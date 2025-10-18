from dataclasses import replace
from typing import List, Optional, Tuple, TYPE_CHECKING

from ...common.base_models import BaseDate, BaseEvent, BaseName
from ..calendar_utils import CalendarUtils
from ..date_grammar import DateGrammarParser
from ..event_utils import EventParsingUtils
from ..name_utils import NameParsingUtils
from ..person_utils import PersonParsingUtils
from ..models import GedcomRecord, GedcomPerson

if TYPE_CHECKING:
    from ..event_utils import SpecialRelationshipProcessor


class PersonParserMixin:
    """Person parsing logic extracted from GedcomParser."""

    relationship_processor: "SpecialRelationshipProcessor"

    def _parse_individual(self, record: GedcomRecord) -> GedcomPerson:
        """Parse individual record using PersonParsingUtils to reduce complexity."""
        person = GedcomPerson(xref_id=record.xref_id)

        PersonParsingUtils.parse_basic_attributes(person, record, self)

        PersonParsingUtils.parse_events(person, record, self)
        self._finalize_individual_events(person)

        PersonParsingUtils.parse_family_relationships(person, record)

        self._process_special_relationships(record, person.xref_id)

        base_note = self._extract_notes(record)
        source_details = self._extract_source(record, f"{record.tag} SOUR")
        person.source = self._apply_default_source(source_details.combined_text())

        note_with_sources = self._merge_notes(base_note, source_details.combined_notes())

        event_note_segments = self._collect_source_note_segments(
            person.birth,
            person.baptism,
            person.death,
            person.burial,
        )
        additional_events = [
            evt
            for evt in person.events
            if (evt.event_type or "").upper() not in {"BIRT", "BAPM", "CHR", "DEAT", "BURI", "CREM"}
        ]
        event_note_segments.extend(self._collect_source_note_segments(*additional_events))
        if event_note_segments:
            note_with_sources = self._merge_notes(
                note_with_sources,
                "<br>\n".join(event_note_segments),
            )

        person.note = note_with_sources

        record.used = True
        return person

    def _parse_name(self, name_value: str) -> BaseName:
        """Parse GEDCOM name using NameParsingUtils to reduce complexity."""
        name = NameParsingUtils.parse_gedcom_name(name_value)

        if self.lowercase_first_names and name.first_name != "x":
            name.first_name = NameParsingUtils.capitalize_name(name.first_name)

        if not name.surname:
            name.surname = "?"

        return name

    def _parse_date(self, date_str: str) -> Optional[BaseDate]:
        """Parse GEDCOM date using DateGrammarParser to reduce complexity."""
        if not date_str:
            return None

        original_date_str = date_str
        date_str = date_str.strip()

        try:
            tokens = DateGrammarParser.tokenize_date(date_str)
            date = DateGrammarParser.parse_date_grammar(tokens)

            if date:
                date.original_text = original_date_str
                return date
            else:
                self.add_warning(f"Cannot parse date with grammar: {original_date_str}")
                return BaseDate(original_text=original_date_str)

        except Exception as e:  # noqa: BLE001 - propagate detailed warning
            self.add_warning(f"Date parsing error: {original_date_str} - {str(e)}")
            return BaseDate(original_text=original_date_str)

    def _parse_month(self, month_str: str) -> int:
        """Parse month string using CalendarUtils to reduce complexity."""
        return CalendarUtils.parse_month(month_str)

    def _parse_event(self, record: GedcomRecord, event_tag: str, family_xref: Optional[str] = None) -> Optional[BaseEvent]:
        """Parse an event using base model"""
        event_record = self._find_sub_record(record, event_tag)
        if not event_record:
            return None

        event = BaseEvent(event_type=event_tag)

        date_record = self._find_sub_record(event_record, "DATE")
        if date_record:
            event.date = self._parse_date(date_record.value)

        place_record = self._find_sub_record(event_record, "PLAC")
        if place_record:
            event.place = place_record.value

        event.note = self._extract_notes(event_record)
        source_details = self._extract_source(event_record, f"{event_tag} SOUR")
        event.source = source_details.combined_text()
        event.source_notes = source_details.combined_notes()

        if family_xref:
            self.relationship_processor.process_family_event_witnesses(event_record, event_tag, family_xref)

        return event

    def _parse_event_enhanced(self, record: GedcomRecord, event_type: str, person_xref: str) -> Optional[BaseEvent]:
        """Parse an event with enhanced processing for witnesses and adoption."""
        event = self._parse_event(record, event_type)
        if not event:
            return None

        event_record = self._find_sub_record(record, event_type)

        self.relationship_processor.process_event_witnesses(event_record, event_type, person_xref)

        return event

    def _parse_all_personal_events(self, record: GedcomRecord, person_xref: str) -> List[BaseEvent]:
        """Parse all personal events using EventParsingUtils to reduce complexity."""
        events = []

        for event_type in EventParsingUtils.PERSONAL_EVENT_TYPES:
            event_records = self._find_all_sub_records(record, event_type)
            for event_record in event_records:
                event_data = EventParsingUtils.parse_basic_event_data(event_record, self._parse_date)

                event = EventParsingUtils.create_event_from_data(
                    event_type, event_data, self._extract_notes, self._extract_source, event_record
                )

                self.relationship_processor.process_event_witnesses(event_record, event_type, person_xref)

                events.append(event)

        return events

    def _finalize_individual_events(self, person: GedcomPerson) -> None:
        """Sort events and reconstruct primary fields like ged2gwb."""

        if not person.events:
            return

        person.events = self._sort_events(person.events, self._PERSON_EVENT_ORDER)

        for event in person.events:
            event_type = (event.event_type or "").upper()
            field_name = self._PERSON_PRIMARY_EVENT_MAP.get(event_type)
            if not field_name:
                continue
            self._merge_primary_event(person, field_name, event)

    def _merge_primary_event(self, person: GedcomPerson, field_name: str, candidate: BaseEvent) -> None:
        """Merge candidate data into the primary event field."""

        primary: Optional[BaseEvent] = getattr(person, field_name)
        if primary is None:
            setattr(person, field_name, self._clone_event(candidate))
            return

        if not primary.date and candidate.date:
            primary.date = candidate.date
        if not primary.place and candidate.place:
            primary.place = candidate.place
        primary.note = self._merge_notes(primary.note, candidate.note)
        primary.source = self._merge_notes(primary.source, candidate.source)
        primary.source_notes = self._merge_notes(
            getattr(primary, "source_notes", ""), getattr(candidate, "source_notes", "")
        )

    def _sort_events(self, events: List[BaseEvent], priority_map: dict) -> List[BaseEvent]:
        """Sort events using GEDCOM parity ordering."""

        def sort_key(event: BaseEvent) -> Tuple[int, Tuple[int, int, int, str], str, str, str]:
            event_type = (event.event_type or "").upper()
            priority = priority_map.get(event_type, len(priority_map))
            return (
                priority,
                self._event_date_key(event.date),
                event_type,
                event.place or "",
                event.note or "",
            )

        return sorted(events, key=sort_key)

    def _event_date_key(self, date: Optional[BaseDate]) -> Tuple[int, int, int, str]:
        """Return sortable key for BaseDate instances."""

        if not date:
            return (9999, 12, 31, "")

        year = date.year if date.year else 9999
        month = date.month if date.month else 12
        day = date.day if date.day else 31
        original = date.original_text or ""
        return (year, month, day, original)

    def _clone_event(self, event: BaseEvent) -> BaseEvent:
        """Create a shallow clone of an event dataclass."""

        return replace(event)

    def _process_special_relationships(self, record: GedcomRecord, person_xref: str):
        """Process special relationships using SpecialRelationshipProcessor."""
        adop_records = self._find_all_sub_records(record, "ADOP")
        for adop_record in adop_records:
            self.relationship_processor.process_adoption_event(adop_record, person_xref)

        for famc_record in self._find_all_sub_records(record, "FAMC"):
            self.relationship_processor.process_famc_adoption(famc_record, person_xref)
