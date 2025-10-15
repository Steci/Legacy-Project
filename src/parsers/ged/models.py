from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union

# Import base models instead of redefining them
from ..common.base_models import (
    Sex, DeathType, RelationType, DatePrecision, 
    BaseDate, BaseEvent, BaseName, BaseNote, BaseSource,
    BasePersonProtocol, BaseFamilyProtocol, BaseDatabaseProtocol
)

@dataclass
class GedcomRecord:
    """Represents a GEDCOM record with level, tag, value and sub-records"""
    level: int
    tag: str
    value: str
    xref_id: Optional[str] = None
    sub_records: List['GedcomRecord'] = field(default_factory=list)
    line_number: int = 0
    used: bool = False
    raw_value: bytes = b""

# Use BaseDate and BaseEvent from common models
# GedcomDate is now just an alias to BaseDate for backwards compatibility
GedcomDate = BaseDate
GedcomEvent = BaseEvent

@dataclass
class GedcomPerson:
    """Represents a GEDCOM individual that implements BasePersonProtocol"""
    xref_id: str
    name: BaseName = field(default_factory=BaseName)
    sex: Sex = Sex.NEUTER
    birth: Optional[BaseEvent] = None
    death: Optional[BaseEvent] = None
    baptism: Optional[BaseEvent] = None
    burial: Optional[BaseEvent] = None
    occupation: str = ""
    note: str = ""
    source: str = ""
    events: List[BaseEvent] = field(default_factory=list)
    families_as_spouse: List[str] = field(default_factory=list)
    families_as_child: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    
    # Special relationships (following OCaml implementation)
    adoption_families: List[str] = field(default_factory=list)  # Families where adopted
    adoption_details: Dict[str, str] = field(default_factory=dict)  # family -> parent role
    godparents: List[str] = field(default_factory=list)  # Godparent person XREFs
    witnesses: List[Dict[str, str]] = field(default_factory=list)  # Witness relationships
    
    # Backward compatibility properties
    @property
    def first_name(self) -> str:
        return self.name.first_name
    
    @first_name.setter
    def first_name(self, value: str):
        self.name.first_name = value
    
    @property
    def surname(self) -> str:
        return self.name.surname
    
    @surname.setter
    def surname(self, value: str):
        self.name.surname = value
    
    # Implement BasePersonProtocol
    def get_id(self) -> str:
        return self.xref_id
    
    def get_name(self) -> BaseName:
        return self.name
    
    def get_sex(self) -> Sex:
        return self.sex
    
    def get_birth(self) -> Optional[BaseEvent]:
        return self.birth
    
    def get_death(self) -> Optional[BaseEvent]:
        return self.death
    
@dataclass
class GedcomFamily:
    """Represents a GEDCOM family that implements BaseFamilyProtocol"""
    xref_id: str
    husband_id: Optional[str] = None
    wife_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    marriage: Optional[BaseEvent] = None
    divorce: Optional[BaseEvent] = None
    relation_type: RelationType = RelationType.MARRIED
    events: List[BaseEvent] = field(default_factory=list)
    note: str = ""
    source: str = ""
    witnesses: List[Dict[str, str]] = field(default_factory=list)
    adoption_notes: Dict[str, str] = field(default_factory=dict)
    
    # Implement BaseFamilyProtocol
    def get_id(self) -> str:
        return self.xref_id
    
    def get_husband_id(self) -> Optional[str]:
        return self.husband_id
    
    def get_wife_id(self) -> Optional[str]:
        return self.wife_id
    
    def get_children_ids(self) -> List[str]:
        return self.children_ids
    
    def get_marriage(self) -> Optional[BaseEvent]:
        return self.marriage

@dataclass
class GedcomDatabase:
    """Complete GEDCOM database that implements BaseDatabaseProtocol"""
    header: Dict[str, Any] = field(default_factory=dict)
    individuals: Dict[str, GedcomPerson] = field(default_factory=dict)
    families: Dict[str, GedcomFamily] = field(default_factory=dict)
    sources: Dict[str, BaseSource] = field(default_factory=dict)
    notes: Dict[str, BaseNote] = field(default_factory=dict)
    
    # Implement BaseDatabaseProtocol
    def get_person(self, person_id: str) -> Optional[BasePersonProtocol]:
        return self.individuals.get(person_id)
    
    def get_family(self, family_id: str) -> Optional[BaseFamilyProtocol]:
        return self.families.get(family_id)
    
    def get_all_persons(self) -> Dict[str, BasePersonProtocol]:
        return self.individuals
    
    def get_all_families(self) -> Dict[str, BaseFamilyProtocol]:
        return self.families
