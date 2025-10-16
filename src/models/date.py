# date.py

from typing import Optional
from enum import Enum
from dataclasses import dataclass

class Calendar(Enum):
    GREGORIAN = "gregorian"
    JULIAN = "julian"
    FRENCH = "french"
    HEBREW = "hebrew"

class Precision(Enum):
    SURE = "sure"
    ABOUT = "about"
    MAYBE = "maybe"
    BEFORE = "before"
    AFTER = "after"
    OR_YEAR = "orYear"
    YEAR_INT = "yearInt"

@dataclass
class DMY:
    day: int = 0
    month: int = 0
    year: int = 0
    prec: Optional[Precision] = None
    delta: Optional[int] = None

@dataclass
class Date:
    dmy: 'DMY'
    calendar: Optional['Calendar'] = None
    text: Optional[str] = None
