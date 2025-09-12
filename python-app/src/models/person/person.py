# person/person.py

from typing import List, Optional, Union
from dataclasses import dataclass, field

from event import Event
from params import Sex, Title, Relation

@dataclass
class Person:
    first_name: str
    surname: str
    public_name: Optional[str] = None
    aliases: List[str] = field(default_factory=list)
    first_names_aliases: List[str] = field(default_factory=list)
    surnames_aliases: List[str] = field(default_factory=list)

    sex: Sex = Sex.NEUTER
    titles: List[Title] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)
    occupation: Optional[str] = None

    occ: int = 0
    image: Optional[str] = None

    parents: List[Relation] = field(default_factory=list) # Parents' unique identifiers
    related: List[int] = field(default_factory=list)
    families: List[int] = field(default_factory=list) # List of unique identifiers of families

    birth: Event = None
    baptism: Optional['Event'] = None
    death: Optional['Event'] = None  # Could be a custom type
    burial: Optional['Event'] = None  # Could be a custom type
    events: List[Event] = field(default_factory=list)

    notes: Optional[str] = None
    psources: Optional[str] = None
    access: Optional[str] = None  # e.g., "public", "private"
    key_index: int = 0  # Unique identifier for the person

    def add_family(self, index: int):
        if index not in self.families:
            self.families.append(index)

    def add_event(self, event: Event):
        self.events.append(event)

    def add_relation(self, relation: Relation):
        self.pseudoparents.append(relation)

# Note: You will need to define the Family class and possibly custom types for death/burial.