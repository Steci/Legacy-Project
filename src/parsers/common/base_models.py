"""
Base models and interfaces that can be shared between GW and GEDCOM parsers.
These represent the core genealogy concepts that are common across formats.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Protocol
from enum import Enum
from datetime import datetime

class Sex(Enum):
    """Gender/sex enumeration"""
    MALE = "M"
    FEMALE = "F" 
    NEUTER = "U"
    UNKNOWN = "?"

class DeathType(Enum):
    """Death status enumeration"""
    NOT_DEAD = "NotDead"
    DEAD_DONT_KNOW_WHEN = "DeadDontKnowWhen" 
    DEAD = "Dead"
    DONT_KNOW_IF_DEAD = "DontKnowIfDead"
    UNKNOWN = "Unknown"

class RelationType(Enum):
    """Family relationship type"""
    MARRIED = "Married"
    NOT_MARRIED = "NotMarried"
    ENGAGED = "Engaged"
    DIVORCED = "Divorced"
    SEPARATED = "Separated"
    UNKNOWN = "Unknown"

class DatePrecision(Enum):
    """Date precision/qualifier"""
    SURE = "Sure"
    ABOUT = "About" 
    MAYBE = "Maybe"
    BEFORE = "Before"
    AFTER = "After"
    BETWEEN = "Between"
    UNKNOWN = "Unknown"

@dataclass
class BaseDate:
    """Base date representation that both formats can use"""
    day: int = 0
    month: int = 0  
    year: int = 0
    precision: DatePrecision = DatePrecision.SURE
    calendar: str = "GREGORIAN"
    original_text: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if date has valid values"""
        return (0 <= self.day <= 31 and 
                0 <= self.month <= 12 and 
                self.year >= 0)
    
    def to_datetime(self) -> Optional[datetime]:
        """Convert to Python datetime if possible"""
        if self.year > 0:
            try:
                return datetime(
                    year=self.year,
                    month=max(1, self.month) if self.month > 0 else 1,
                    day=max(1, self.day) if self.day > 0 else 1
                )
            except ValueError:
                return None
        return None

@dataclass  
class BaseEvent:
    """Base event that can represent birth, death, marriage, etc."""
    event_type: str
    date: Optional[BaseDate] = None
    place: str = ""
    note: str = ""
    source: str = ""
    confidence: Optional[str] = None

@dataclass
class BaseName:
    """Base name representation"""
    first_name: str = ""
    surname: str = ""
    prefix: str = ""  # von, de, etc.
    suffix: str = ""  # Jr., Sr., III, etc.
    nickname: str = ""
    
    def full_name(self) -> str:
        """Get full formatted name"""
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        if self.first_name:
            parts.append(self.first_name)
        if self.surname:
            parts.append(self.surname)
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts)
    
    def key(self) -> str:
        """Generate a key for indexing"""
        return f"{self.surname.upper()}, {self.first_name.upper()}"

class BasePersonProtocol(Protocol):
    """Protocol defining what a person should implement"""
    
    def get_id(self) -> str:
        """Get unique identifier"""
        ...
        
    def get_name(self) -> BaseName:
        """Get person's name"""
        ...
        
    def get_sex(self) -> Sex:
        """Get person's sex"""
        ...
        
    def get_birth(self) -> Optional[BaseEvent]:
        """Get birth event"""
        ...
        
    def get_death(self) -> Optional[BaseEvent]:
        """Get death event"""
        ...

class BaseFamilyProtocol(Protocol):
    """Protocol defining what a family should implement"""
    
    def get_id(self) -> str:
        """Get unique identifier"""
        ...
        
    def get_husband_id(self) -> Optional[str]:
        """Get husband's ID"""
        ...
        
    def get_wife_id(self) -> Optional[str]:
        """Get wife's ID"""
        ...
        
    def get_children_ids(self) -> List[str]:
        """Get list of children IDs"""
        ...
        
    def get_marriage(self) -> Optional[BaseEvent]:
        """Get marriage event"""
        ...

class BaseDatabaseProtocol(Protocol):
    """Protocol defining what a genealogy database should implement"""
    
    def get_person(self, person_id: str) -> Optional[BasePersonProtocol]:
        """Get person by ID"""
        ...
        
    def get_family(self, family_id: str) -> Optional[BaseFamilyProtocol]:
        """Get family by ID"""
        ...
        
    def get_all_persons(self) -> Dict[str, BasePersonProtocol]:
        """Get all persons"""
        ...
        
    def get_all_families(self) -> Dict[str, BaseFamilyProtocol]:
        """Get all families"""
        ...

@dataclass
class BaseNote:
    """Base note representation"""
    person_id: Optional[str] = None
    family_id: Optional[str] = None
    content: str = ""
    note_type: str = "general"  # general, medical, research, etc.
    source: str = ""
    date_created: Optional[datetime] = None

@dataclass
class BaseSource:
    """Base source representation"""
    source_id: str
    title: str = ""
    author: str = ""
    publication: str = ""
    repository: str = ""
    call_number: str = ""
    note: str = ""

class BaseParser(ABC):
    """Abstract base parser that both GW and GEDCOM parsers can inherit from"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    @abstractmethod
    def parse_file(self, file_path: str) -> BaseDatabaseProtocol:
        """Parse a file and return a database"""
        pass
    
    @abstractmethod
    def parse_content(self, content: str) -> BaseDatabaseProtocol:
        """Parse content string and return a database"""
        pass
    
    def add_error(self, message: str, line_number: Optional[int] = None):
        """Add an error message"""
        if line_number:
            self.errors.append(f"Line {line_number}: {message}")
        else:
            self.errors.append(message)
    
    def add_warning(self, message: str, line_number: Optional[int] = None):
        """Add a warning message"""
        if line_number:
            self.warnings.append(f"Line {line_number}: {message}")
        else:
            self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def get_error_summary(self) -> str:
        """Get summary of all errors and warnings"""
        summary = []
        if self.errors:
            summary.append(f"Errors ({len(self.errors)}):")
            summary.extend(f"  - {error}" for error in self.errors)
        if self.warnings:
            summary.append(f"Warnings ({len(self.warnings)}):")
            summary.extend(f"  - {warning}" for warning in self.warnings)
        return "\n".join(summary) if summary else "No errors or warnings"

# Utility functions that can be shared

def normalize_name(name: str) -> str:
    """Normalize a name string"""
    if not name:
        return ""
    # Remove extra whitespace and capitalize properly
    return " ".join(word.capitalize() for word in name.strip().split())

def parse_name_components(full_name: str) -> BaseName:
    """Parse a full name into components"""
    # This is a simplified version - could be made more sophisticated
    parts = full_name.strip().split()
    
    if not parts:
        return BaseName()
    
    name = BaseName()
    
    # Handle simple cases
    if len(parts) == 1:
        name.first_name = parts[0]
    elif len(parts) == 2:
        name.first_name = parts[0]
        name.surname = parts[1]
    else:
        # More complex case - could include prefixes, suffixes
        name.first_name = " ".join(parts[:-1])
        name.surname = parts[-1]
    
    return name

def standardize_date_string(date_str: str) -> str:
    """Standardize date string format"""
    if not date_str:
        return ""
    
    # Remove extra whitespace and normalize
    normalized = " ".join(date_str.strip().split())
    
    # Convert common abbreviations
    replacements = {
        "JAN": "January", "FEB": "February", "MAR": "March",
        "APR": "April", "MAY": "May", "JUN": "June",
        "JUL": "July", "AUG": "August", "SEP": "September", 
        "OCT": "October", "NOV": "November", "DEC": "December"
    }
    
    for abbrev, full in replacements.items():
        normalized = normalized.replace(abbrev, full)
    
    return normalized

def generate_person_key(first_name: str, surname: str, birth_year: Optional[int] = None) -> str:
    """Generate a unique key for a person"""
    key_parts = [surname.upper(), first_name.upper()]
    if birth_year:
        key_parts.append(str(birth_year))
    return "_".join(part for part in key_parts if part)
