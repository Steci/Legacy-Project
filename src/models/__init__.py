"""
Genealogical Data Models Package

This package contains the core data models for representing genealogical information:
- Person: Individual people with biographical data
- Family: Family units with relationships and children
- Date: Flexible date representations for historical data
- Event: Life events (birth, death, marriage, etc.)
- Place: Geographic locations and addresses
"""

from .person.person import Person
from .family.family import Family
from .date import Date, DMY
from .event import Event
from .place import Place
from .person.params import Sex, PEventType
from .family.params import RelationKind

__all__ = [
    'Person',
    'Family', 
    'Date',
    'DMY',
    'Event',
    'Place',
    'Sex',
    'PEventType',
    'RelationKind'
]

__version__ = '1.0.0'