from typing import List, Optional, TYPE_CHECKING

from models.event import Event, Place

from ..event_utils import EventParsingUtils
from ..models import GedcomFamily, GedcomRecord

if TYPE_CHECKING:
    from ..event_utils import SpecialRelationshipProcessor


class FamilyParserMixin:
    """Family parsing helpers extracted from GedcomParser."""

    relationship_processor: "SpecialRelationshipProcessor"

    def _parse_family(self, record: GedcomRecord) -> GedcomFamily:
        """Parse family record into the new domain model wrapper."""

        family = GedcomFamily(xref_id=record.xref_id or "")

        husb_record = self._find_sub_record(record, "HUSB")
        if husb_record:
            family.husband_id = husb_record.value

        wife_record = self._find_sub_record(record, "WIFE")
        if wife_record:
            family.wife_id = wife_record.value

        for chil_rec in self._find_all_sub_records(record, "CHIL"):
            if chil_rec.value and chil_rec.value not in family.children_ids:
                family.children_ids.append(chil_rec.value)

        family.events = self._parse_all_family_events(record, family.xref_id)
        self._finalize_family_events(family)

        base_note = self._extract_notes(record)
        source_details = self._extract_source(record, f"{record.tag} SOUR")
        family.sources = self._apply_default_source(source_details.combined_text())

        note_with_sources = self._merge_notes(base_note, source_details.combined_notes())

        event_note_segments = self._collect_source_note_segments(
            family.marriage,
            family.divorce,
        )
        additional_events = [
            evt
            for evt in family.events
            if getattr(evt, "gedcom_tag", evt.name or "").upper() not in {"MARR", "DIV", "ANUL", "SEP", "SEPA"}
        ]
        event_note_segments.extend(self._collect_source_note_segments(*additional_events))
        if event_note_segments:
            note_with_sources = self._merge_notes(
                note_with_sources,
                "<br>\n".join(event_note_segments),
            )

        family.notes = note_with_sources
        family.witnesses = self.relationship_processor.consume_family_witnesses(family.xref_id)
        adoption_map = self.relationship_processor.consume_family_adoptions(family.xref_id)
        if adoption_map:
            family.adoption_notes.update(adoption_map)

        record.used = True
        return family

    def _parse_all_family_events(self, record: GedcomRecord, family_xref: str) -> List[Event]:
        """Parse all family-level events mirroring ged2gwb."""

        events: List[Event] = []

        for sub_record in record.sub_records:
            tag = (sub_record.tag or "").upper()
            if tag not in EventParsingUtils.FAMILY_EVENT_TYPES:
                continue

            event = self._build_family_event(sub_record, family_xref)
            if event:
                events.append(event)

        return events

    def _build_family_event(self, event_record: GedcomRecord, family_xref: str) -> Optional[Event]:
        """Create a family event entry mirroring treat_fam_fevent."""

        event_type = self._determine_family_event_type(event_record)
        display_name = event_type
        event = Event(name=display_name)
        setattr(event, "gedcom_tag", event_type)

        date_record = self._find_sub_record(event_record, "DATE")
        if date_record:
            event.date = self._parse_date(date_record.value)

        place_record = self._find_sub_record(event_record, "PLAC")
        if place_record:
            event.place = Place(other=place_record.value)

        event.note = self._extract_notes(event_record)
        source_details = self._extract_source(event_record, f"{event_record.tag} SOUR")
        event.source = source_details.combined_text()
        setattr(event, "source_notes", source_details.combined_notes())

        name_info = self._strip_spaces(event_record.value)
        if name_info and name_info.upper() != "Y":
            event.note = self._merge_notes(name_info, event.note)

        self.relationship_processor.process_family_event_witnesses(event_record, event_type, family_xref)

        if not self._should_include_event(event, event_record):
            return None

        return event

    def _determine_family_event_type(self, event_record: GedcomRecord) -> str:
        """Determine event type based on tag and TYPE sub-record."""

        type_record = self._find_sub_record(event_record, "TYPE")
        if type_record and type_record.value:
            return type_record.value.upper()
        return (event_record.tag or "").upper()

    def _should_include_event(self, event: Event, event_record: GedcomRecord) -> bool:
        """Decide whether an event contains meaningful data to retain."""

        place_value = event.place.other if event.place else ""
        if event.date or place_value or event.note or event.source or getattr(event, "source_notes", ""):
            return True
        value_text = self._strip_spaces(event_record.value).upper()
        if value_text == "Y":
            return True
        if any(sub.tag == "ASSO" for sub in event_record.sub_records):
            return True
        return bool(event_record.sub_records)

    def _finalize_family_events(self, family: GedcomFamily) -> None:
        """Sort family events and derive marriage/divorce fields."""

        if family.events:
            family.events = self._sort_events(family.events, self._FAMILY_EVENT_ORDER)

            for event in family.events:
                event_type = getattr(event, "gedcom_tag", event.name or "").upper()
                field_name = self._FAMILY_PRIMARY_EVENT_MAP.get(event_type)
                if not field_name:
                    continue
                self._merge_family_primary_event(family, field_name, event)

        marriage_event_type = getattr(family.marriage, "gedcom_tag", family.marriage.name if family.marriage else "").upper() if family.marriage else ""
        relation = self._FAMILY_RELATION_BY_EVENT.get(marriage_event_type)
        if relation:
            family.relation = relation

    def _merge_family_primary_event(self, family: GedcomFamily, field_name: str, candidate: Event) -> None:
        """Merge candidate data into family primary event fields."""

        primary: Optional[Event] = getattr(family, field_name)
        if primary is None:
            setattr(family, field_name, self._clone_event(candidate))
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

