import re
from dataclasses import dataclass, field, replace
from typing import List, Optional, Dict, Any, Iterator, Tuple, Union
import logging

from ..common.base_models import (
    BaseParser, BaseDate, BaseEvent, BaseName, BaseNote, BaseSource,
    DatePrecision, Sex, RelationType, standardize_date_string, 
    parse_name_components
)
from .models import (
    GedcomRecord, GedcomPerson, GedcomFamily, GedcomDatabase
)
from .calendar_utils import CalendarUtils
from .date_grammar import DateGrammarParser
from .encoding_utils import decode_bytes
from .event_utils import EventParsingUtils, SpecialRelationshipProcessor
from .name_utils import NameParsingUtils
from .person_utils import PersonParsingUtils

logger = logging.getLogger(__name__)


@dataclass
class SourceCollection:
    """Aggregate structure mirroring ged2gwb treat_source results."""

    context: str = ""
    texts: List[str] = field(default_factory=list)
    note_texts: List[str] = field(default_factory=list)
    html_segments: List[str] = field(default_factory=list)
    raw_subrecords: List[List['GedcomRecord']] = field(default_factory=list)

    def combined_text(self) -> str:
        return " ".join(text for text in self.texts if text).strip()

    def combined_notes(self) -> str:
        note_segments = [seg for seg in self.note_texts if seg]
        html_segments = [seg for seg in self.html_segments if seg]

        notes = "<br>\n".join(note_segments)
        html = "".join(html_segments)

        if notes and html:
            return f"{notes}<br>\n{html}"
        return notes or html

class GedcomParseError(Exception):
    """Exception raised for GEDCOM parsing errors"""
    pass

class GedcomParser(BaseParser):
    """GEDCOM parser following the logic of geneweb ged2gwb.ml"""

    _PERSON_EVENT_ORDER = {
        tag.upper(): index for index, tag in enumerate(EventParsingUtils.PERSONAL_EVENT_TYPES)
    }
    _FAMILY_EVENT_ORDER = {
        tag.upper(): index for index, tag in enumerate(EventParsingUtils.FAMILY_EVENT_TYPES)
    }
    _PERSON_PRIMARY_EVENT_MAP = {
        "BIRT": "birth",
        "BAPM": "baptism",
        "CHR": "baptism",
        "BURI": "burial",
        "CREM": "burial",
        "DEAT": "death",
    }
    _FAMILY_PRIMARY_EVENT_MAP = {
        "MARR": "marriage",
        "ENGA": "marriage",
        "MARB": "marriage",
        "MARC": "marriage",
        "MARL": "marriage",
        "ANUL": "marriage",
        "DIV": "divorce",
        "SEP": "divorce",
        "SEPA": "divorce",
    }
    _FAMILY_RELATION_BY_EVENT = {
        "MARR": RelationType.MARRIED,
        "ENGA": RelationType.ENGAGED,
        "MARB": RelationType.MARRIED,
        "MARC": RelationType.MARRIED,
        "MARL": RelationType.MARRIED,
        "ANUL": RelationType.UNKNOWN,
        "DIV": RelationType.DIVORCED,
        "SEP": RelationType.SEPARATED,
        "SEPA": RelationType.SEPARATED,
    }
    
    def __init__(self):
        super().__init__()
        self.line_count = 0
        self.charset = "ASCII"
        self.charset_override = None
        self.database = GedcomDatabase()
        self._note_records = {}
        self._source_records = {}
        
        # Configuration options (similar to ged2gwb.ml)
        self.lowercase_first_names = False
        self.case_surnames = "NoCase"  # NoCase, LowerCase, UpperCase
        self.extract_first_names = False
        self.extract_public_names = True
        self.no_public_if_titles = False
        self.untreated_in_notes = False
        self.default_source = ""
        self.alive_years = 80
        self.dead_years = 120
        
        # Special relationship tracking using utility class
        self.relationship_processor = SpecialRelationshipProcessor()

    def parse_file(self, file_path: str) -> GedcomDatabase:
        """Parse a GEDCOM file while preserving original byte content."""
        raw_bytes = self._read_file_bytes(file_path)
        return self.parse_content(raw_bytes)

    def _read_file_bytes(self, file_path: str) -> bytes:
        """Read the GEDCOM file as bytes and detect BOM."""

        with open(file_path, "rb") as handle:
            data = handle.read()

        if data.startswith(b"\xef\xbb\xbf"):
            self.charset_override = "UTF-8"
            return data[3:]

        return data

    def parse_content(self, content: Union[str, bytes]) -> GedcomDatabase:
        """Parse GEDCOM content supplied as text or raw bytes."""

        if isinstance(content, str):
            raw_bytes = content.encode("latin-1")
        else:
            raw_bytes = content

        lines = raw_bytes.splitlines()
        records = self._parse_records(lines)
        self._initialize_charset(records)
        self._decode_record_values(records)
        
        # Four-pass parsing like in ged2gwb.ml with special relationships
        self._pass1_notes_sources(records)
        self._pass2_individuals(records)
        self._pass3_families(records)
        self._pass4_special_relationships()
        
        return self.database

    def _parse_records(self, lines: List[bytes]) -> List[GedcomRecord]:
        """Parse GEDCOM lines into records."""

        records: List[GedcomRecord] = []
        stack: List[GedcomRecord] = []

        for line_num, line in enumerate(lines, 1):
            clean_line = line.rstrip(b"\r\n")
            record = self._parse_line(clean_line, line_num)
            if not record:
                continue
                
            # Build tree structure based on level
            while stack and stack[-1].level >= record.level:
                stack.pop()
                
            if stack:
                stack[-1].sub_records.append(record)
            else:
                records.append(record)
                
            stack.append(record)
            
        return records

    def _parse_line(self, line: bytes, line_num: int) -> Optional[GedcomRecord]:
        """Parse a single GEDCOM line with simplified validation."""

        if not self._is_valid_line(line):
            return None
            
        # Parse components
        level, xref_id, tag, value, raw_value = self._extract_line_components(line)
        
        record = GedcomRecord(
            level=level,
            tag=tag,
            value=value,
            xref_id=xref_id,
            line_number=line_num,
            raw_value=raw_value
        )
        
        return record
    
    def _is_valid_line(self, line: bytes) -> bool:
        """Validate GEDCOM line format."""
        if not line or line.startswith(b"//"):
            return False
        parts = line.split(b" ", 1)
        return bool(parts and parts[0].isdigit())

    def _extract_line_components(self, line: bytes) -> Tuple[int, Optional[str], str, str, bytes]:
        """Extract level, xref, tag and value bytes from line."""

        parts = line.split(b" ", 2)
        level = int(parts[0])

        xref_id: Optional[str] = None
        tag_bytes = b""
        value_bytes = b""

        if len(parts) >= 2:
            second = parts[1]
            if second.startswith(b"@") and second.endswith(b"@"):
                xref_id = second.decode("latin-1")
                if len(parts) == 3:
                    tag_and_value = parts[2]
                    tag_parts = tag_and_value.split(b" ", 1)
                    tag_bytes = tag_parts[0]
                    if len(tag_parts) > 1:
                        value_bytes = tag_parts[1]
            else:
                tag_bytes = second
                if len(parts) == 3:
                    value_bytes = parts[2]

        tag = tag_bytes.decode("latin-1") if tag_bytes else ""
        value = value_bytes.decode("latin-1") if value_bytes else ""

        return level, xref_id, tag, value, value_bytes

    def _initialize_charset(self, records: List[GedcomRecord]) -> None:
        """Determine the charset from BOM or HEAD record."""

        if self.charset_override:
            self.charset = self.charset_override
            return

        head_record = next((rec for rec in records if rec.tag == "HEAD"), None)
        if not head_record:
            return

        for sub_record in head_record.sub_records:
            if sub_record.tag == "CHAR":
                token_bytes = sub_record.raw_value or sub_record.value.encode("latin-1")
                charset_token = token_bytes.decode("latin-1").strip()
                if charset_token:
                    self.charset = self._normalise_charset_name(charset_token)
                return

    def _normalise_charset_name(self, token: str) -> str:
        """Map GEDCOM CHAR token to canonical charset name."""

        upper = token.upper()
        mapping = {
            "ANSEL": "ANSEL",
            "ANSI": "ANSI",
            "ASCII": "ASCII",
            "IBMPC": "ASCII",
            "MACINTOSH": "MACINTOSH",
            "MSDOS": "MSDOS",
            "UTF-8": "UTF-8",
            "UTF8": "UTF-8",
        }
        return mapping.get(upper, "ASCII")

    def _decode_record_values(self, records: List[GedcomRecord]) -> None:
        """Decode raw GEDCOM values according to detected charset."""

        for record in records:
            record.value = decode_bytes(record.raw_value, self.charset) if record.raw_value else ""
            self._fix_genealogos_bug(record)
            if record.sub_records:
                self._decode_record_values(record.sub_records)

    def _fix_genealogos_bug(self, record: GedcomRecord) -> GedcomRecord:
        """Fix genealogos-specific GEDCOM bugs"""
        if record.tag and record.tag.startswith("@"):
            record.tag, record.value = record.value, record.tag
        # Handle common genealogos export issues
        if record.tag == "NAME" and "~" in record.value:
            record.value = record.value.replace("~", "")
        
        return record

    def _pass1_notes_sources(self, records: List[GedcomRecord]):
        """First pass: parse notes and sources"""
        for record in records:
            if record.tag == "NOTE" and record.xref_id:
                self._note_records[record.xref_id] = record
                note_content = self._render_note_content(record)
                self.database.notes[record.xref_id] = BaseNote(content=note_content)
            elif record.tag == "SOUR" and record.xref_id:
                self._source_records[record.xref_id] = record
                source = self._parse_source_record(record)
                self.database.sources[record.xref_id] = source
            elif record.tag == "HEAD":
                self._parse_header(record)

    def _pass2_individuals(self, records: List[GedcomRecord]):
        """Second pass: parse individuals"""
        for record in records:
            if record.tag == "INDI" and record.xref_id:
                person = self._parse_individual(record)
                self.database.individuals[record.xref_id] = person

    def _pass3_families(self, records: List[GedcomRecord]):
        """Third pass: parse families"""
        for record in records:
            if record.tag == "FAM" and record.xref_id:
                family = self._parse_family(record)
                self.database.families[record.xref_id] = family

    def _pass4_special_relationships(self):
        """Fourth pass: finalize special relationships using SpecialRelationshipProcessor."""
        # Apply all processed relationships to database
        self.relationship_processor.finalize_relationships(self.database)
                
        # Apply genealogos bug fixes
        self._apply_genealogos_bug_fixes()

    def _parse_header(self, record: GedcomRecord):
        """Parse GEDCOM header"""
        char_record = self._find_sub_record(record, "CHAR")
        if char_record:
            header_charset = self._normalise_charset_name(char_record.value)
            if not self.charset_override:
                self.charset = header_charset
            self.database.header["charset"] = header_charset
            
        # Extract other header information
        sour_record = self._find_sub_record(record, "SOUR")
        if sour_record:
            self.database.header["source"] = sour_record.value
            
        date_record = self._find_sub_record(record, "DATE")
        if date_record:
            self.database.header["date"] = date_record.value

    def _parse_individual(self, record: GedcomRecord) -> GedcomPerson:
        """Parse individual record using PersonParsingUtils to reduce complexity."""
        person = GedcomPerson(xref_id=record.xref_id)
        
        # Parse basic attributes (name, sex, occupation)
        PersonParsingUtils.parse_basic_attributes(person, record, self)
        
        # Parse events
        PersonParsingUtils.parse_events(person, record, self)
        self._finalize_individual_events(person)
        
        # Parse family relationships
        PersonParsingUtils.parse_family_relationships(person, record)
        
        # Handle special relationships
        self._process_special_relationships(record, person.xref_id)
        
        # Parse notes and sources
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

    def _parse_family(self, record: GedcomRecord) -> GedcomFamily:
        """Parse family record"""
        family = GedcomFamily(xref_id=record.xref_id)
        
        # Parse parents
        husb_record = self._find_sub_record(record, "HUSB")
        if husb_record:
            family.husband_id = husb_record.value
            
        wife_record = self._find_sub_record(record, "WIFE")
        if wife_record:
            family.wife_id = wife_record.value
        
        # Parse children
        for chil_rec in self._find_all_sub_records(record, "CHIL"):
            family.children_ids.append(chil_rec.value)

        # Parse all family events and finalize primary fields
        family.events = self._parse_all_family_events(record, family.xref_id)
        self._finalize_family_events(family)
        
        # Parse notes and sources
        base_note = self._extract_notes(record)
        source_details = self._extract_source(record, f"{record.tag} SOUR")
        family.source = self._apply_default_source(source_details.combined_text())

        note_with_sources = self._merge_notes(base_note, source_details.combined_notes())

        event_note_segments = self._collect_source_note_segments(
            family.marriage,
            family.divorce,
        )
        additional_events = [
            evt
            for evt in family.events
            if (evt.event_type or "").upper() not in {"MARR", "DIV", "ANUL", "SEP", "SEPA"}
        ]
        event_note_segments.extend(self._collect_source_note_segments(*additional_events))
        if event_note_segments:
            note_with_sources = self._merge_notes(
                note_with_sources,
                "<br>\n".join(event_note_segments),
            )

        family.note = note_with_sources
        family.witnesses = self.relationship_processor.consume_family_witnesses(family.xref_id)
        adoption_map = self.relationship_processor.consume_family_adoptions(family.xref_id)
        if adoption_map:
            family.adoption_notes.update(adoption_map)
        
        record.used = True
        return family

    def _parse_name(self, name_value: str) -> BaseName:
        """Parse GEDCOM name using NameParsingUtils to reduce complexity."""
        name = NameParsingUtils.parse_gedcom_name(name_value)
        
        # Apply naming conventions if configured
        if self.lowercase_first_names and name.first_name != "x":
            name.first_name = NameParsingUtils.capitalize_name(name.first_name)
        
        # Apply OCaml-compatible surname default 
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
            # Tokenize and parse using utility classes
            tokens = DateGrammarParser.tokenize_date(date_str)
            date = DateGrammarParser.parse_date_grammar(tokens)
            
            if date:
                date.original_text = original_date_str
                return date
            else:
                # Fallback for unparseable dates
                self.add_warning(f"Cannot parse date with grammar: {original_date_str}")
                return BaseDate(original_text=original_date_str)
                
        except Exception as e:
            # Recovery parsing for malformed dates
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
        
        # Parse date using base model
        date_record = self._find_sub_record(event_record, "DATE")
        if date_record:
            event.date = self._parse_date(date_record.value)
        
        # Parse place
        place_record = self._find_sub_record(event_record, "PLAC")
        if place_record:
            event.place = place_record.value

        # Parse note and source
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
        
        # Parse witnesses using relationship processor
        self.relationship_processor.process_event_witnesses(event_record, event_type, person_xref)
        
        return event
        
    def _parse_all_personal_events(self, record: GedcomRecord, person_xref: str) -> List[BaseEvent]:
        """Parse all personal events using EventParsingUtils to reduce complexity."""
        events = []
        
        for event_type in EventParsingUtils.PERSONAL_EVENT_TYPES:
            event_records = self._find_all_sub_records(record, event_type)
            for event_record in event_records:
                # Parse basic event data using utility
                event_data = EventParsingUtils.parse_basic_event_data(event_record, self._parse_date)
                
                # Create event using utility
                event = EventParsingUtils.create_event_from_data(
                    event_type, event_data, self._extract_notes, self._extract_source, event_record
                )
                
                # Process witnesses using relationship processor
                self.relationship_processor.process_event_witnesses(event_record, event_type, person_xref)
                        
                events.append(event)
                
        return events

    def _parse_all_family_events(self, record: GedcomRecord, family_xref: str) -> List[BaseEvent]:
        """Parse all family-level events mirroring ged2gwb."""

        events: List[BaseEvent] = []

        for sub_record in record.sub_records:
            tag = (sub_record.tag or "").upper()
            if tag not in EventParsingUtils.FAMILY_EVENT_TYPES:
                continue

            event = self._build_family_event(sub_record, family_xref)
            if event:
                events.append(event)

        return events

    def _build_family_event(self, event_record: GedcomRecord, family_xref: str) -> Optional[BaseEvent]:
        """Create a family event entry mirroring treat_fam_fevent."""

        event_type = self._determine_family_event_type(event_record)
        event = BaseEvent(event_type=event_type)

        date_record = self._find_sub_record(event_record, "DATE")
        if date_record:
            event.date = self._parse_date(date_record.value)

        place_record = self._find_sub_record(event_record, "PLAC")
        if place_record:
            event.place = place_record.value

        event.note = self._extract_notes(event_record)
        source_details = self._extract_source(event_record, f"{event_record.tag} SOUR")
        event.source = source_details.combined_text()
        event.source_notes = source_details.combined_notes()

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

    def _should_include_event(self, event: BaseEvent, event_record: GedcomRecord) -> bool:
        """Decide whether an event contains meaningful data to retain."""

        if event.date or event.place or event.note or event.source or event.source_notes:
            return True
        value_text = self._strip_spaces(event_record.value).upper()
        if value_text == "Y":
            return True
        if any(sub.tag == "ASSO" for sub in event_record.sub_records):
            return True
        return bool(event_record.sub_records)

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

    def _finalize_family_events(self, family: GedcomFamily) -> None:
        """Sort family events and derive marriage/divorce fields."""

        if family.events:
            family.events = self._sort_events(family.events, self._FAMILY_EVENT_ORDER)

            for event in family.events:
                event_type = (event.event_type or "").upper()
                field_name = self._FAMILY_PRIMARY_EVENT_MAP.get(event_type)
                if not field_name:
                    continue
                self._merge_family_primary_event(family, field_name, event)

        marriage_event_type = (family.marriage.event_type or "").upper() if family.marriage else ""
        relation = self._FAMILY_RELATION_BY_EVENT.get(marriage_event_type)
        if relation:
            family.relation_type = relation

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
        primary.source_notes = self._merge_notes(getattr(primary, "source_notes", ""), getattr(candidate, "source_notes", ""))

    def _merge_family_primary_event(self, family: GedcomFamily, field_name: str, candidate: BaseEvent) -> None:
        """Merge candidate data into family primary event fields."""

        primary: Optional[BaseEvent] = getattr(family, field_name)
        if primary is None:
            setattr(family, field_name, self._clone_event(candidate))
            return

        if not primary.date and candidate.date:
            primary.date = candidate.date
        if not primary.place and candidate.place:
            primary.place = candidate.place
        primary.note = self._merge_notes(primary.note, candidate.note)
        primary.source = self._merge_notes(primary.source, candidate.source)
        primary.source_notes = self._merge_notes(getattr(primary, "source_notes", ""), getattr(candidate, "source_notes", ""))

    def _sort_events(self, events: List[BaseEvent], priority_map: Dict[str, int]) -> List[BaseEvent]:
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
        # Handle adoption relationships (ADOP event)
        adop_records = self._find_all_sub_records(record, "ADOP")
        for adop_record in adop_records:
            self.relationship_processor.process_adoption_event(adop_record, person_xref)
            
        # Handle family relationships with adoption/foster info
        for famc_record in self._find_all_sub_records(record, "FAMC"):
            self.relationship_processor.process_famc_adoption(famc_record, person_xref)

    def _find_sub_record(self, record: GedcomRecord, tag: str) -> Optional[GedcomRecord]:
        """Find first sub-record with given tag"""
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                return sub_record
        return None

    def _find_all_sub_records(self, record: GedcomRecord, tag: str) -> List[GedcomRecord]:
        """Find all sub-records with given tag"""
        found = []
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                found.append(sub_record)
        return found

    def _extract_notes(self, record: GedcomRecord) -> str:
        """Extract notes from record using ged2gwb rules."""

        rendered_notes: List[str] = []

        for note_record in self._find_all_sub_records(record, "NOTE"):
            text = self._render_note_reference(note_record)
            if text:
                rendered_notes.append(text)

        return "<br>\n".join(rendered_notes)

    def _process_note_record(self, note_record: GedcomRecord) -> str:
        """Process a single note record."""

        if note_record.value.startswith('@') and note_record.value.endswith('@'):
            referenced = self._note_records.get(note_record.value)
            if referenced:
                return self._compose_note_text(referenced)
            return self.database.notes.get(note_record.value, BaseNote()).content

        return self._compose_note_text(note_record)

    def _render_note_content(self, note_record: GedcomRecord) -> str:
        """Render a top-level NOTE record to text."""

        return self._compose_note_text(note_record)

    def _compose_note_text(self, note_record: GedcomRecord) -> str:
        """Combine NOTE, CONC and CONT records into a single string."""

        text = self._strip_spaces(note_record.value)
        trailing_space = note_record.value.endswith(" ") if note_record.value else False
        if trailing_space:
            text += " "

        for sub_rec in note_record.sub_records:
            value = sub_rec.value
            if not value:
                continue
            stripped = self._strip_spaces(value)
            end_space = value.endswith(" ")

            if sub_rec.tag == "CONC":
                text += stripped
                if end_space:
                    text += " "
            elif sub_rec.tag == "CONT":
                text += "<br>\n" + stripped
                if end_space:
                    text += " "

        return text

    def _render_note_reference(self, note_record: GedcomRecord) -> str:
        """Render either inline or referenced note using compose helper."""

        if note_record.value.startswith('@') and note_record.value.endswith('@'):
            referenced = self._note_records.get(note_record.value)
            if referenced:
                return self._compose_note_text(referenced)
            stored = self.database.notes.get(note_record.value)
            return stored.content if stored else ""

        return self._compose_note_text(note_record)

    def _strip_spaces(self, value: Optional[str]) -> str:
        """Utility mirroring ged2gwb strip_spaces."""

        return value.strip() if value else ""

    def _rebuild_text(self, record: Optional[GedcomRecord]) -> str:
        """Rebuild text with CONT/CONC semantics like ged2gwb."""

        if not record:
            return ""

        text = self._strip_spaces(record.value)
        trailing_space = record.value.endswith(" ") if record.value else False
        if trailing_space:
            text += " "

        for sub_rec in record.sub_records:
            value = sub_rec.value
            if not value:
                continue
            stripped = self._strip_spaces(value)
            end_space = value.endswith(" ")

            if sub_rec.tag == "CONC":
                text += stripped
                if end_space:
                    text += " "
            elif sub_rec.tag == "CONT":
                text += "<br>\n" + stripped
                if end_space:
                    text += " "

        return text

    def _find_in_records(self, records: List[GedcomRecord], tag: str) -> Optional[GedcomRecord]:
        """Find first record with tag within a record list."""

        for record in records:
            if record.tag == tag:
                record.used = True
                return record
        return None

    def _render_source_notes(self, sub_records: List[GedcomRecord]) -> str:
        """Render TITL/TEXT blocks from a source record list."""

        if not sub_records:
            return ""

        title = self._rebuild_text(self._find_in_records(sub_records, "TITL"))
        text = self._rebuild_text(self._find_in_records(sub_records, "TEXT"))

        if title:
            bold_title = f"<b>{title}</b>"
            return f"{bold_title}<br>\n{text}" if text else bold_title

        return text

    def _record_content(self, record: Optional[GedcomRecord]) -> str:
        """Return record content with CONC/CONT applied."""

        if not record:
            return ""

        return self._strip_spaces(self._rebuild_text(record))

    def _process_source_reference(
        self,
        sour_record: GedcomRecord,
        context_label: str,
    ) -> Tuple[str, str, List[str], List[GedcomRecord], Optional[str]]:
        """Return structured details for a SOUR reference."""

        value = sour_record.value or ""
        sub_records: List[GedcomRecord] = []

        if value.startswith('@') and value.endswith('@'):
            referenced = self._source_records.get(value)
            if referenced:
                text = self._record_content(referenced)
                sub_records = referenced.sub_records
                note_text = self._render_source_notes(sub_records)
                extras = self._extract_additional_source_notes(sub_records)
                html = self._build_html_from_subrecords(context_label, sub_records)
                return text, note_text, extras, sub_records, html

            stored = self.database.sources.get(value)
            if stored:
                parts = [stored.title, stored.author, stored.publication]
                text = ", ".join(part for part in parts if part)
                return text or value, "", [], [], None

            self.add_warning(f"Source {value} not found", sour_record.line_number)
            return "", "", [], [], None

        text = self._record_content(sour_record)
        sub_records = sour_record.sub_records
        note_text = self._render_source_notes(sub_records)
        extras = self._extract_additional_source_notes(sub_records)
        html = self._build_html_from_subrecords(context_label, sub_records)
        return text, note_text, extras, sub_records, html

    def _extract_source(self, record: GedcomRecord, context_label: Optional[str] = None) -> SourceCollection:
        """Extract source information and associated note fragments."""

        context = context_label or f"{record.tag} SOUR"
        collection = SourceCollection(context=context)

        for sour_record in self._find_all_sub_records(record, "SOUR"):
            text, note_text, extras, sub_records, html_segment = self._process_source_reference(
                sour_record,
                context,
            )
            if text:
                collection.texts.append(text)
            if note_text:
                collection.note_texts.append(note_text)
            if extras:
                collection.note_texts.extend(extras)
            if html_segment:
                collection.html_segments.append(html_segment)
            if sub_records:
                collection.raw_subrecords.append(list(sub_records))

        return collection

    def _extract_additional_source_notes(self, sub_records: List[GedcomRecord]) -> List[str]:
        """Pull PAGE/QUAY/NOTE/DATA details into note text like ged2gwb."""

        segments: List[str] = []
        for sub in sub_records:
            if sub.tag == "PAGE":
                sub.used = True
                page_text = self._record_content(sub)
                if page_text:
                    segments.append(f"Page: {page_text}")
            elif sub.tag == "QUAY":
                sub.used = True
                certainty = self._strip_spaces(sub.value)
                if certainty:
                    segments.append(f"Certainty: {certainty}")
            elif sub.tag == "NOTE":
                sub.used = True
                note_text = self._render_note_reference(sub)
                if note_text:
                    segments.append(note_text)
            elif sub.tag == "DATA":
                sub.used = True
                segments.extend(self._render_source_data_segments(sub))
        return segments

    def _render_source_data_segments(self, data_record: GedcomRecord) -> List[str]:
        """Render DATA sub-records (DATE/TEXT/NOTE) for source notes."""

        segments: List[str] = []

        date_record = self._find_sub_record(data_record, "DATE")
        if date_record:
            date_text = self._record_content(date_record)
            if date_text:
                segments.append(f"Data date: {date_text}")

        for sub in data_record.sub_records:
            if sub.tag == "TEXT":
                sub.used = True
                text_value = self._rebuild_text(sub)
                if text_value:
                    segments.append(text_value)
            elif sub.tag == "NOTE":
                sub.used = True
                note_text = self._render_note_reference(sub)
                if note_text:
                    segments.append(note_text)

        return segments

    def _build_html_from_subrecords(self, context: str, sub_records: List[GedcomRecord]) -> Optional[str]:
        """Reproduce ged2gwb html_text_of_tags for untreated source tags."""

        if not self.untreated_in_notes or not sub_records:
            return None

        lines = []

        def walk(records: List[GedcomRecord], level: int) -> List[str]:
            collected: List[str] = []
            for rec in records:
                child_lines = walk(rec.sub_records, level + 1)
                include = not rec.used or child_lines
                if not include:
                    continue
                pieces = [str(level), rec.tag]
                value = self._strip_spaces(rec.value)
                if value:
                    pieces.append(value)
                collected.append(" ".join(pieces))
                collected.extend(child_lines)
            return collected

        body_lines = walk(sub_records, 1)
        if not body_lines:
            return None

        header = "-- GEDCOM --" if not context else f"-- GEDCOM ({context}) --"
        lines.append(header)
        lines.extend(body_lines)
        return "<pre>\n" + "\n".join(lines) + "\n</pre>"

    def _merge_notes(self, base: str, addition: str) -> str:
        """Merge two note fragments with GEDCOM line break semantics."""

        if not addition:
            return base
        if not base:
            return addition
        return f"{base}<br>\n{addition}"

    def _collect_source_note_segments(self, *events: Optional[BaseEvent]) -> List[str]:
        """Collect source-derived note fragments from events."""

        segments: List[str] = []
        for event in events:
            if not event:
                continue
            note_fragment = getattr(event, "source_notes", "")
            if note_fragment:
                segments.append(note_fragment)
        return segments

    def _apply_default_source(self, source_text: str) -> str:
        """Apply default source fallback when configured."""

        text = self._strip_spaces(source_text)
        if not text and self.default_source:
            return self.default_source
        return text

    def _parse_source_record(self, record: GedcomRecord) -> BaseSource:
        """Parse source record"""
        source = BaseSource(source_id=record.xref_id or "")
        
        titl_record = self._find_sub_record(record, "TITL")
        if titl_record:
            source.title = self._rebuild_text(titl_record)
        
        auth_record = self._find_sub_record(record, "AUTH")
        if auth_record:
            source.author = self._rebuild_text(auth_record)
        
        publ_record = self._find_sub_record(record, "PUBL")
        if publ_record:
            source.publication = self._rebuild_text(publ_record)
        
        return source
    
    def _apply_genealogos_bug_fixes(self):
        """Apply bug fixes for genealogos software compatibility."""
        for person in self.database.individuals.values():
            self._fix_person_genealogos_issues(person)
                
    def _fix_genealogos_date(self, date: BaseDate):
        """Fix date formatting quirks observed in Genealogos exports."""

        raw_text = getattr(date, "text", None) or date.original_text
        if raw_text and "~" in raw_text:
            date.precision = DatePrecision.ABOUT
            cleaned = raw_text.replace("~", "").strip()
            if hasattr(date, "text"):
                date.text = cleaned
            else:
                date.original_text = cleaned
            
    def _fix_genealogos_name_case(self, surname: str) -> str:
        """Fix name case issues from genealogos software."""
        if surname.isupper() and len(surname) > 2:
            return surname.title()
        return surname
    
    def _fix_person_genealogos_issues(self, person: GedcomPerson) -> None:
        """Fix all genealogos issues for a person."""
        # Fix birth date
        if person.birth and person.birth.date:
            self._fix_genealogos_date(person.birth.date)
            
        # Fix death date
        if person.death and person.death.date:
            self._fix_genealogos_date(person.death.date)
            
        # Fix surname capitalization
        if person.name.surname:
            person.name.surname = self._fix_genealogos_name_case(person.name.surname)

def parse_gedcom_file(file_path: str) -> GedcomDatabase:
    """Convenience function to parse a GEDCOM file"""
    parser = GedcomParser()
    return parser.parse_file(file_path)
