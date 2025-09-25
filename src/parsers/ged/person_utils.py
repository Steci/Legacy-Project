"""
Person parsing utilities for GEDCOM parser.
Extracted to reduce cyclomatic complexity in individual parsing.
"""
from typing import List, Optional
from ..common.base_models import Sex, BaseEvent
from .models import GedcomRecord, GedcomPerson
from .name_utils import NameParsingUtils


class PersonParsingUtils:
    """Utility class for parsing GEDCOM individual records."""
    
    @staticmethod
    def parse_basic_attributes(person: GedcomPerson, record: GedcomRecord, parser) -> None:
        """Parse basic person attributes (name, sex, occupation)."""
        # Parse name
        name_record = PersonParsingUtils._find_sub_record(record, "NAME")
        if name_record:
            person.name = parser._parse_name(name_record.value)
            PersonParsingUtils._parse_name_aliases(person, record)
        
        # Parse sex
        PersonParsingUtils._parse_sex(person, record)
        
        # Parse occupation
        PersonParsingUtils._parse_occupation(person, record)
    
    @staticmethod
    def parse_family_relationships(person: GedcomPerson, record: GedcomRecord) -> None:
        """Parse family relationship references."""
        # Parse family relationships as spouse
        for fams_rec in PersonParsingUtils._find_all_sub_records(record, "FAMS"):
            person.families_as_spouse.append(fams_rec.value)
            
        # Parse family relationships as child
        for famc_rec in PersonParsingUtils._find_all_sub_records(record, "FAMC"):
            person.families_as_child.append(famc_rec.value)
    
    @staticmethod
    def parse_events(person: GedcomPerson, record: GedcomRecord, parser) -> None:
        """Parse all person events."""
        person.birth = parser._parse_event_enhanced(record, "BIRT", person.xref_id)
        person.death = parser._parse_event_enhanced(record, "DEAT", person.xref_id)
        person.baptism = (parser._parse_event_enhanced(record, "BAPM", person.xref_id) or 
                         parser._parse_event_enhanced(record, "CHR", person.xref_id))
        person.burial = parser._parse_event_enhanced(record, "BURI", person.xref_id)
        person.events = parser._parse_all_personal_events(record, person.xref_id)
    
    @staticmethod
    def _parse_name_aliases(person: GedcomPerson, record: GedcomRecord) -> None:
        """Parse additional name records as aliases."""
        name_records = PersonParsingUtils._find_all_sub_records(record, "NAME")
        for name_rec in name_records[1:]:  # Skip first name record
            person.aliases.append(name_rec.value)
    
    @staticmethod
    def _parse_sex(person: GedcomPerson, record: GedcomRecord) -> None:
        """Parse sex field."""
        sex_record = PersonParsingUtils._find_sub_record(record, "SEX")
        if sex_record:
            person.sex = Sex(sex_record.value) if sex_record.value in ["M", "F"] else Sex.NEUTER
    
    @staticmethod
    def _parse_occupation(person: GedcomPerson, record: GedcomRecord) -> None:
        """Parse occupation fields."""
        occu_records = PersonParsingUtils._find_all_sub_records(record, "OCCU")
        if occu_records:
            person.occupation = ", ".join(r.value for r in occu_records if not r.sub_records)
    
    @staticmethod
    def _find_sub_record(record: GedcomRecord, tag: str) -> Optional[GedcomRecord]:
        """Find first sub-record with given tag."""
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                return sub_record
        return None
    
    @staticmethod
    def _find_all_sub_records(record: GedcomRecord, tag: str) -> List[GedcomRecord]:
        """Find all sub-records with given tag."""
        found = []
        for sub_record in record.sub_records:
            if sub_record.tag == tag:
                sub_record.used = True
                found.append(sub_record)
        return found
