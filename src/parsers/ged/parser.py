import logging
from typing import List, Optional, Union

from models.date import Date, Precision
from models.family.family import RelationKind
from .event_utils import EventParsingUtils, SpecialRelationshipProcessor
from .mixins.base_helpers import RecordTraversalMixin
from .mixins.charset_mixin import CharsetMixin
from .mixins.family_mixin import FamilyParserMixin
from .mixins.notes_sources import NoteSourceMixin, SourceCollection
from .mixins.person_mixin import PersonParserMixin
from .mixins.record_reader import RecordReaderMixin
from .models import GedcomDatabase, GedcomFamily, GedcomPerson, GedcomRecord, Note

logger = logging.getLogger(__name__)

class GedcomParseError(Exception):
    """Exception raised for GEDCOM parsing errors"""
    pass

class GedcomParser(
    RecordTraversalMixin,
    RecordReaderMixin,
    CharsetMixin,
    NoteSourceMixin,
    PersonParserMixin,
    FamilyParserMixin,
):
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
        "MARR": RelationKind.MARRIED,
        "ENGA": RelationKind.ENGAGED,
        "MARB": RelationKind.MARRIED,
        "MARC": RelationKind.MARRIED,
        "MARL": RelationKind.MARRIED,
        "ANUL": RelationKind.UNKNOWN,
        "DIV": RelationKind.DIVORCED,
        "SEP": RelationKind.SEPARATED,
        "SEPA": RelationKind.SEPARATED,
    }
    
    def __init__(self):
        super().__init__()
        self.line_count = 0
        self.charset = "ASCII"
        self.charset_override = None
        self.database = GedcomDatabase()
        self._note_records = {}
        self._source_records = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
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

    def add_error(self, message: str, line_number: Optional[int] = None) -> None:
        """Record a parsing error, keeping original line context when provided."""
        if line_number is not None:
            self.errors.append(f"Line {line_number}: {message}")
        else:
            self.errors.append(message)

    def add_warning(self, message: str, line_number: Optional[int] = None) -> None:
        """Record a warning encountered during GEDCOM import."""
        if line_number is not None:
            self.warnings.append(f"Line {line_number}: {message}")
        else:
            self.warnings.append(message)

    def has_errors(self) -> bool:
        """Check whether any parsing errors were recorded."""
        return bool(self.errors)

    def get_error_summary(self) -> str:
        """Return a formatted summary of accumulated errors and warnings."""
        summary: List[str] = []
        if self.errors:
            summary.append(f"Errors ({len(self.errors)}):")
            summary.extend(f"  - {error}" for error in self.errors)
        if self.warnings:
            summary.append(f"Warnings ({len(self.warnings)}):")
            summary.extend(f"  - {warning}" for warning in self.warnings)
        return "\n".join(summary) if summary else "No errors or warnings"

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


    def _pass1_notes_sources(self, records: List[GedcomRecord]):
        """First pass: parse notes and sources"""
        for record in records:
            if record.tag == "NOTE" and record.xref_id:
                self._note_records[record.xref_id] = record
                note_content = self._render_note_content(record)
                self.database.notes[record.xref_id] = Note(content=note_content)
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

        note_records = self._find_all_sub_records(record, "NOTE")
        if note_records:
            note_segments = [self._compose_note_text(note) for note in note_records]
            combined = "<br>\n".join(seg for seg in note_segments if seg)
            if combined:
                self.database.header["notes_db"] = combined



    
    def _apply_genealogos_bug_fixes(self):
        """Apply bug fixes for genealogos software compatibility."""
        for person in self.database.individuals.values():
            self._fix_person_genealogos_issues(person)
                
    def _fix_genealogos_date(self, date: Date) -> None:
        """Normalize legacy Genealogos markers on new Date objects."""

        raw_text = (getattr(date, "text", "") or "").strip()
        if "~" not in raw_text:
            return

        cleaned = raw_text.replace("~", "").strip()
        if getattr(date, "dmy", None) and getattr(date.dmy, "prec", None) != Precision.ABOUT:
            date.dmy.prec = Precision.ABOUT
        if hasattr(date, "text"):
            date.text = cleaned
            
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
        surname = (person.surname or "").strip()
        if surname:
            person.surname = self._fix_genealogos_name_case(surname)

def parse_gedcom_file(file_path: str) -> GedcomDatabase:
    """Convenience function to parse a GEDCOM file"""
    parser = GedcomParser()
    return parser.parse_file(file_path)
