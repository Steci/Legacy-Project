"""Parser-local wrappers for GEDCOM imports.

We subclass the shared domain models here to attach GEDCOM-only metadata
such as xref identifiers, adoption notes, or raw record trees.  Keeping these
variants in the parser package preserves the clean API of ``src/models`` while
still letting conversion code work with the extra context captured during
parsing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models.event import Event
from models.family.family import Family
from models.person.person import Person


@dataclass
class Note:
    """Lightweight note representation used by the GEDCOM parser."""

    person_id: Optional[str] = None
    family_id: Optional[str] = None
    content: str = ""
    note_type: str = "general"
    source: str = ""


@dataclass
class Source:
    """Minimal source representation captured from GEDCOM SOUR records."""

    source_id: str
    title: str = ""
    author: str = ""
    publication: str = ""
    repository: str = ""
    call_number: str = ""
    note: str = ""


@dataclass
class GedcomRecord:
    """Represents a GEDCOM record with level, tag, value and sub-records."""

    level: int
    tag: str
    value: str
    xref_id: Optional[str] = None
    sub_records: List["GedcomRecord"] = field(default_factory=list)
    line_number: int = 0
    used: bool = False
    raw_value: bytes = b""


@dataclass
class GedcomDatabase:
    """Parsed GEDCOM data expressed with the new domain models."""

    header: Dict[str, Any] = field(default_factory=dict)
    individuals: Dict[str, "GedcomPerson"] = field(default_factory=dict)
    families: Dict[str, "GedcomFamily"] = field(default_factory=dict)
    sources: Dict[str, Source] = field(default_factory=dict)
    notes: Dict[str, Note] = field(default_factory=dict)


@dataclass(init=False)
class GedcomPerson(Person):
    """Person wrapper that augments the core domain model for parser needs."""

    xref_id: str = ""
    families_as_spouse: List[str] = field(default_factory=list)
    families_as_child: List[str] = field(default_factory=list)
    adoption_details: Dict[str, str] = field(default_factory=dict)
    adoption_families: List[str] = field(default_factory=list)
    godparents: List[str] = field(default_factory=list)
    witnesses: List[Dict[str, str]] = field(default_factory=list)
    source_notes: str = ""

    def __init__(self, *, xref_id: Optional[str] = None, first_name: str = "x", surname: str = "?", **kwargs):
        super().__init__(first_name=first_name, surname=surname, **kwargs)
        self.xref_id = xref_id or ""
        self.families_as_spouse = []
        self.families_as_child = []
        self.adoption_details = {}
        self.adoption_families = []
        self.godparents = []
        self.witnesses = []
        self.source_notes = ""


@dataclass(init=False)
class GedcomFamily(Family):
    """Family wrapper that keeps GEDCOM-centric metadata."""

    xref_id: str = ""
    husband_id: Optional[str] = None
    wife_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    adoption_notes: Dict[str, str] = field(default_factory=dict)
    witnesses: List[Dict[str, str]] = field(default_factory=list)

    def __init__(self, *, xref_id: Optional[str] = None, parent1: int = -1, parent2: int = 0, **kwargs):
        kwargs.setdefault("children", kwargs.get("children", []))
        super().__init__(parent1=parent1, parent2=parent2, **kwargs)
        self.xref_id = xref_id or ""
        self.husband_id = None
        self.wife_id = None
        self.children_ids = []
        self.adoption_notes = {}
        self.witnesses = []

    def __post_init__(self):
        # Override Family validation during initial GEDCOM import; detailed
        # consistency checks happen after conversion to domain indices.
        pass


GedcomNote = Note
GedcomSource = Source
