# family/family.py

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from event import Event

class RelationKind(Enum):
    MARRIED = "married"
    NOT_MARRIED = "not_married"
    PACS = "pacs"
    ENGAGED = "engaged"
    SEPARATED = "separated"
    DIVORCED = "divorced"
    UNKNOWN = "unknown"

@dataclass
class Family:
    parent1: int = 0
    parent2: int = 0
    children: List[int] = field(default_factory=list) # List of unique identifiers of children
    relation: RelationKind = RelationKind.UNKNOWN

    marriage: Optional['Event'] = None
    divorce: Optional['Event'] = None
    events: List['Event'] = field(default_factory=list)

    notes: Optional[str] = None
    origin_file: Optional[str] = None
    sources: Optional[str] = None
    key_index: Optional[int] = None  # Unique identifier for the family

    def add_child(self, index: int):
        if index not in self.children:
            self.children.append(index)

    def add_event(self, event: Event):
        self.events.append(event)