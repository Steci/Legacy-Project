# Event.py

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import date

@dataclass
class Event:
    name: str
    event_date: Optional[date] = None
    place: Optional[str] = None
    reason: Optional[str] = None
    note: Optional[str] = None
    source: Optional[str] = None
    witnesses: List[int] = field(default_factory=list)