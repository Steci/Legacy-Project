"""
Common utilities and converters for both GW and GEDCOM parsers
"""
from typing import Dict, Any, Optional
from datetime import datetime
from ..ged.models import GedcomDatabase, GedcomPerson, GedcomFamily
from ..gw.models import GWDatabase, Person, Family

class DatabaseConverter:
    """Convert between GW and GEDCOM databases"""
    
    def gw_to_gedcom(self, gw_db: GWDatabase) -> GedcomDatabase:
        """Convert GW database to GEDCOM format"""
        gedcom_db = GedcomDatabase()
        
        # Convert persons
        for person_key, gw_person in gw_db.persons.items():
            gedcom_person = self._convert_gw_person_to_gedcom(gw_person)
            gedcom_db.individuals[f"@I{len(gedcom_db.individuals)}@"] = gedcom_person
        
        # Convert families
        for i, gw_family in enumerate(gw_db.families):
            gedcom_family = self._convert_gw_family_to_gedcom(gw_family, i)
            gedcom_db.families[f"@F{i}@"] = gedcom_family
        
        return gedcom_db
    
    def gedcom_to_gw(self, gedcom_db: GedcomDatabase) -> GWDatabase:
        """Convert GEDCOM database to GW format"""
        gw_db = GWDatabase()
        
        # Convert individuals
        for xref_id, gedcom_person in gedcom_db.individuals.items():
            gw_person = self._convert_gedcom_person_to_gw(gedcom_person)
            gw_db.persons[gw_person.key()] = gw_person
        
        # Convert families
        for xref_id, gedcom_family in gedcom_db.families.items():
            gw_family = self._convert_gedcom_family_to_gw(gedcom_family)
            gw_db.families.append(gw_family)
        
        return gw_db
    
    def _convert_gw_person_to_gedcom(self, gw_person: Person) -> GedcomPerson:
        """Convert GW Person to GEDCOM Person"""
        # Implementation details...
        pass
    
    def _convert_gedcom_person_to_gw(self, gedcom_person: GedcomPerson) -> Person:
        """Convert GEDCOM Person to GW Person"""
        # Implementation details...
        pass
    
    def _convert_gw_family_to_gedcom(self, gw_family: Family, index: int) -> GedcomFamily:
        """Convert GW Family to GEDCOM Family"""
        # Implementation details...
        pass
    
    def _convert_gedcom_family_to_gw(self, gedcom_family: GedcomFamily) -> Family:
        """Convert GEDCOM Family to GW Family"""
        # Implementation details...
        pass

class DateParser:
    """Common date parsing utilities"""
    
    @staticmethod
    def parse_gw_date(date_str: str) -> Optional[datetime]:
        """Parse GW date format"""
        # Common date parsing logic
        pass
    
    @staticmethod
    def parse_gedcom_date(date_str: str) -> Optional[datetime]:
        """Parse GEDCOM date format"""
        # Common date parsing logic
        pass

class NameParser:
    """Common name parsing utilities"""
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize name format"""
        return name.strip().title()
    
    @staticmethod
    def split_full_name(full_name: str) -> tuple[str, str]:
        """Split full name into first and last name"""
        parts = full_name.strip().split()
        if len(parts) >= 2:
            return " ".join(parts[:-1]), parts[-1]
        elif len(parts) == 1:
            return "", parts[0]
        return "", ""
