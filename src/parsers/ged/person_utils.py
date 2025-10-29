"""Person parsing utilities for the GEDCOM parser."""

from typing import List, Optional

from models.person.params import Sex, Title

from .models import GedcomRecord, GedcomPerson
from .name_utils import NameParsingUtils, ParsedName


class PersonParsingUtils:
    """Utility class for parsing GEDCOM individual records."""
    
    @staticmethod
    def parse_basic_attributes(person: GedcomPerson, record: GedcomRecord, parser) -> None:
        """Parse basic person attributes (name, sex, occupation)."""
        name_record = PersonParsingUtils._find_sub_record(record, "NAME")
        if name_record:
            parsed_name: ParsedName = parser._parse_name(name_record.value)
            person.first_name = parsed_name.first_name
            person.surname = parsed_name.surname
            person.public_name = parsed_name.nickname or None
            if parsed_name.suffix and parsed_name.suffix not in person.qualifiers:
                person.qualifiers.append(parsed_name.suffix)
            if parsed_name.title:
                title_entry = Title(name=parsed_name.title)
                if all(existing.name != parsed_name.title for existing in person.titles):
                    person.titles.append(title_entry)
            PersonParsingUtils._parse_name_aliases(person, record)
        else:
            # Ensure required fields exist
            person.first_name = getattr(person, "first_name", "x")
            person.surname = getattr(person, "surname", "?")
        PersonParsingUtils._parse_sex(person, record)
        PersonParsingUtils._parse_occupation(person, record)
    
    @staticmethod
    def parse_family_relationships(person: GedcomPerson, record: GedcomRecord) -> None:
        """Parse family relationship references."""
        # Parse family relationships as spouse
        for fams_rec in PersonParsingUtils._find_all_sub_records(record, "FAMS"):
            if fams_rec.value and fams_rec.value not in person.families_as_spouse:
                person.families_as_spouse.append(fams_rec.value)
            
        # Parse family relationships as child
        for famc_rec in PersonParsingUtils._find_all_sub_records(record, "FAMC"):
            if famc_rec.value and famc_rec.value not in person.families_as_child:
                person.families_as_child.append(famc_rec.value)
    
    @staticmethod
    def parse_events(person: GedcomPerson, record: GedcomRecord, parser) -> None:
        """Parse all person events."""

        person.birth = parser._parse_event_enhanced(record, "BIRT", person.xref_id)
        person.death = parser._parse_event_enhanced(record, "DEAT", person.xref_id)
        person.baptism = (
            parser._parse_event_enhanced(record, "BAPM", person.xref_id)
            or parser._parse_event_enhanced(record, "CHR", person.xref_id)
        )
        person.burial = parser._parse_event_enhanced(record, "BURI", person.xref_id)
        person.events = parser._parse_all_personal_events(record, person.xref_id)
    
    @staticmethod
    def _parse_name_aliases(person: GedcomPerson, record: GedcomRecord) -> None:
        """Parse additional name records as aliases."""
        name_records = PersonParsingUtils._find_all_sub_records(record, "NAME")
        for name_rec in name_records[1:]:  # Skip first name record
            parsed_alias = NameParsingUtils.parse_gedcom_name(name_rec.value)
            person.aliases.append(name_rec.value)
            if parsed_alias.first_name and parsed_alias.first_name != "x" and parsed_alias.first_name not in person.first_names_aliases:
                person.first_names_aliases.append(parsed_alias.first_name)
            if parsed_alias.surname and parsed_alias.surname not in person.surnames_aliases:
                person.surnames_aliases.append(parsed_alias.surname)
    
    @staticmethod
    def _parse_sex(person: GedcomPerson, record: GedcomRecord) -> None:
        """Parse sex field."""
        sex_record = PersonParsingUtils._find_sub_record(record, "SEX")
        if sex_record:
            if sex_record.value == "M":
                person.sex = Sex.MALE
            elif sex_record.value == "F":
                person.sex = Sex.FEMALE
            else:
                person.sex = Sex.NEUTER
        else:
            person.sex = getattr(person, "sex", Sex.NEUTER)
    
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
