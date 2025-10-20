from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from models.family.family import Family as DomainFamily
from models.person.person import Person as DomainPerson


@dataclass(init=False)
class Person(DomainPerson):
    """GeneWeb person representation backed by the domain model."""

    raw_name: str
    number: Optional[int]
    tokens: List[str]
    extra: Dict[str, Any]

    def __init__(self, raw_name: str, last: str, first: str, number: Optional[int] = None, tokens: Optional[List[str]] = None):
        super().__init__(first_name=first or "0", surname=last or "?")
        self.raw_name = raw_name
        self.number = number
        self.tokens = tokens or []
        self.extra = {}
        # Backwards compatibility aliases expected by legacy callers.
        self.first = self.first_name
        self.last = self.surname

    def key(self) -> str:
        suffix = f".{self.number}" if self.number is not None else ""
        return f"{self.surname} {self.first_name}{suffix}".strip()

    def __repr__(self) -> str:
        return f"Person({self.key()}, tokens={self.tokens})"


@dataclass(init=False)
class Family(DomainFamily):
    """GeneWeb family wrapper that stores textual context alongside domain data."""

    husband: Optional[str]
    wife: Optional[str]
    wedding_date: Optional[str]
    options: List[str]
    src: Optional[str]
    comm: Optional[str]
    witnesses: List[str]
    children: List[Tuple[Optional[str], Person, List[str]]]
    raw: List[str]

    def __init__(self):
        super().__init__(parent1=0, parent2=0, children=[])
        self.husband = None
        self.wife = None
        self.wedding_date = None
        self.options = []
        self.src = None
        self.comm = None
        self.witnesses = []
        self.children = []
        self.raw = []
        # Ensure events list matches GeneWeb textual capture semantics.
        self.events = []

    def __post_init__(self):
        # Skip domain-level validation: GeneWeb families may refer to textual keys only.
        pass

    def __repr__(self) -> str:
        return (
            f"Family(husband={self.husband}, wife={self.wife}, "
            f"children={len(self.children)}, options={self.options})"
        )


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
