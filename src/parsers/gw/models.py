from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple

@dataclass
class EventLine:
    raw: str
    tag: str
    tokens: List[str] = field(default_factory=list)

@dataclass
class Person:
    raw_name: str
    last: str
    first: str
    number: Optional[int] = None
    tokens: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)
    events: List[EventLine] = field(default_factory=list)

    def key(self) -> str:
        if self.number is not None:
            return f"{self.last} {self.first}.{self.number}"
        return f"{self.last} {self.first}"

    def __repr__(self):
        return f"Person({self.key()}, tokens={self.tokens})"


@dataclass
class Family:
    husband: Optional[str] = None
    wife: Optional[str] = None
    wedding_date: Optional[str] = None
    options: List[str] = field(default_factory=list)
    src: Optional[str] = None
    comm: Optional[str] = None
    witnesses: List[str] = field(default_factory=list)
    children: List[Tuple[Optional[str], Person, List[str]]] = field(default_factory=list)
    events: List[EventLine] = field(default_factory=list)
    raw: List[str] = field(default_factory=list)

    def __repr__(self):
        return (f"Family(husband={self.husband}, wife={self.wife}, "
                f"children={len(self.children)}, options={self.options})")


@dataclass
class NoteBlock:
    person_key: str
    text: str


@dataclass
class RelationBlock:
    person_key: str
    lines: List[str]


@dataclass
class GWDatabase:
    families: List[Family] = field(default_factory=list)
    persons: Dict[str, Person] = field(default_factory=dict)
    notes: List[NoteBlock] = field(default_factory=list)
    relations: List[RelationBlock] = field(default_factory=list)
