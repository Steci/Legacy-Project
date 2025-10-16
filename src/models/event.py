# event.py

from typing import List, Optional
from enum import Enum
from dataclasses import dataclass, field
from models.date import Date

@dataclass
class Place:
    country: str = ""
    region: str = ""
    district: str = ""
    county: str = ""
    township: str = ""
    canton: str = ""
    town: str = ""
    other: str = ""

class WitnessType(Enum):
    WITNESS = "witness"
    GOD_PARENT = "godParent"
    CIVIL_OFFICER = "civilOfficer"
    RELIGIOUS_OFFICER = "religiousOfficer"
    INFORMANT = "informant"
    ATTENDING = "attending"
    MENTIONED = "mentioned"
    OTHER = "other"

@dataclass
class Witness:
    key_index: int = 0
    type: WitnessType = WitnessType.OTHER

@dataclass
class Event:
    name: str
    date: Optional['Date'] = None
    place: Optional['Place'] = None
    reason: Optional[str] = None
    note: Optional[str] = None
    source: Optional[str] = None
    witnesses: List[Witness] = field(default_factory=list)
