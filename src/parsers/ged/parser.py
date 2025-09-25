import re
from typing import List, Optional, Dict, Any, Iterator, Tuple
from datetime import datetime
import logging
import math

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
from .event_utils import EventParsingUtils, SpecialRelationshipProcessor
from .name_utils import NameParsingUtils
from .person_utils import PersonParsingUtils

logger = logging.getLogger(__name__)

class GedcomParseError(Exception):
    """Exception raised for GEDCOM parsing errors"""
    pass

class GedcomParser(BaseParser):
    """GEDCOM parser following the logic of geneweb ged2gwb.ml"""
    
    def __init__(self):
        super().__init__()
        self.line_count = 0
        self.charset = "UTF-8"
        self.database = GedcomDatabase()
        
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
        """Parse a GEDCOM file with simplified encoding handling."""
        content = self._read_file_with_encoding(file_path)
        return self.parse_content(content)
    
    def _read_file_with_encoding(self, file_path: str) -> str:
        """Read file with fallback encoding detection."""
        encodings = ['utf-8-sig', 'latin1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise GedcomParseError(f"Cannot decode file {file_path}")

    def parse_content(self, content: str) -> GedcomDatabase:
        """Parse GEDCOM content and return a GedcomDatabase"""
        lines = content.splitlines()
        records = self._parse_records(lines)
        
        # Four-pass parsing like in ged2gwb.ml with special relationships
        self._pass1_notes_sources(records)
        self._pass2_individuals(records)
        self._pass3_families(records)
        self._pass4_special_relationships()
        
        return self.database

    def _parse_records(self, lines: List[str]) -> List[GedcomRecord]:
        """Parse GEDCOM lines into records"""
        records = []
        stack = []
        
        for line_num, line in enumerate(lines, 1):
            record = self._parse_line(line.strip(), line_num)
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

    def _parse_line(self, line: str, line_num: int) -> Optional[GedcomRecord]:
        """Parse a single GEDCOM line with simplified validation."""
        # Quick validation
        if not self._is_valid_line(line):
            return None
            
        # Parse components
        level, xref_id, tag, value = self._extract_line_components(line)
        
        record = GedcomRecord(
            level=level,
            tag=tag,
            value=value,
            xref_id=xref_id,
            line_number=line_num
        )
        
        return self._fix_genealogos_bug(record)
    
    def _is_valid_line(self, line: str) -> bool:
        """Validate GEDCOM line format."""
        if not line or line.startswith('//'):
            return False
        parts = line.split(' ', 1)
        return len(parts) > 0 and parts[0].isdigit()
    
    def _extract_line_components(self, line: str) -> tuple:
        """Extract level, xref, tag, and value from line."""
        parts = line.split(' ', 2)
        level = int(parts[0])
        
        # Determine if second part is XREF or tag
        if len(parts) >= 2 and parts[1].startswith('@') and parts[1].endswith('@'):
            xref_id = parts[1]
            tag = parts[2] if len(parts) > 2 else ""
            value = ""
        else:
            xref_id = None
            tag = parts[1] if len(parts) > 1 else ""
            value = parts[2] if len(parts) > 2 else ""
            
        return level, xref_id, tag, value

    def _fix_genealogos_bug(self, record: GedcomRecord) -> GedcomRecord:
        """Fix genealogos-specific GEDCOM bugs"""
        # Handle common genealogos export issues
        if record.tag == "NAME" and "~" in record.value:
            record.value = record.value.replace("~", "")
        
        return record

    def _decode_string(self, s: str) -> str:
        """Decode GEDCOM string with charset"""
        return s  # Simplified - charset handling done at file level

    def _pass1_notes_sources(self, records: List[GedcomRecord]):
        """First pass: parse notes and sources"""
        for record in records:
            if record.tag == "NOTE" and record.xref_id:
                note = BaseNote(content=record.value)
                self.database.notes[record.xref_id] = note
            elif record.tag == "SOUR" and record.xref_id:
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
            self.charset = char_record.value
            self.database.header["charset"] = self.charset
            
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
        
        # Parse family relationships
        PersonParsingUtils.parse_family_relationships(person, record)
        
        # Handle special relationships
        self._process_special_relationships(record, person.xref_id)
        
        # Parse notes and sources
        person.note = self._extract_notes(record)
        person.source = self._extract_source(record)
        
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
        
        # Parse marriage and divorce events
        family.marriage = self._parse_event(record, "MARR")
        family.divorce = self._parse_event(record, "DIV")
        
        # Parse notes and sources
        family.note = self._extract_notes(record)
        family.source = self._extract_source(record)
        
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

    def _parse_event(self, record: GedcomRecord, event_tag: str) -> Optional[BaseEvent]:
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
        event.source = self._extract_source(event_record)
        
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
        """Extract notes from record with simplified logic."""
        notes = []
        
        for note_record in self._find_all_sub_records(record, "NOTE"):
            note_text = self._process_note_record(note_record)
            if note_text:
                notes.append(note_text)
        
        return "\n".join(notes)
    
    def _process_note_record(self, note_record: GedcomRecord) -> str:
        """Process a single note record."""
        # Handle reference notes
        if note_record.value.startswith('@') and note_record.value.endswith('@'):
            return self.database.notes.get(note_record.value, BaseNote()).content
        
        # Handle inline notes with continuations
        note_text = note_record.value
        for sub_rec in note_record.sub_records:
            if sub_rec.tag == "CONC":
                note_text += sub_rec.value
            elif sub_rec.tag == "CONT":
                note_text += "\n" + sub_rec.value
                
        return note_text

    def _extract_source(self, record: GedcomRecord) -> str:
        """Extract source from record"""
        sources = []
        
        for sour_record in self._find_all_sub_records(record, "SOUR"):
            if sour_record.value.startswith('@') and sour_record.value.endswith('@'):
                # Reference to source record
                if sour_record.value in self.database.sources:
                    sources.append(sour_record.value)
            else:
                # Inline source
                sources.append(sour_record.value)
        
        return ", ".join(sources)

    def _parse_source_record(self, record: GedcomRecord) -> BaseSource:
        """Parse source record"""
        source = BaseSource()
        
        titl_record = self._find_sub_record(record, "TITL")
        if titl_record:
            source.title = titl_record.value
        
        auth_record = self._find_sub_record(record, "AUTH")
        if auth_record:
            source.author = auth_record.value
        
        publ_record = self._find_sub_record(record, "PUBL")
        if publ_record:
            source.publication = publ_record.value
        
        return source
    
    def _apply_genealogos_bug_fixes(self):
        """Apply bug fixes for genealogos software compatibility."""
        for person in self.database.individuals.values():
            self._fix_person_genealogos_issues(person)
                
    def _fix_genealogos_date(self, date: BaseDate):
        """Fix date formatting issues from genealogos software."""
        if date.text and "~" in date.text:
            date.precision = DatePrecision.ABOUT
            date.text = date.text.replace("~", "").strip()
            
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
