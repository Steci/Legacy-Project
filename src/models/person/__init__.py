"""
Person model module.

Exports:
    - Person class from person.py
    - Parameter types from params.py (Sex, PEventType, etc.)
"""

from .person import Person
from .params import Sex, PEventType, RelationType, Relation, Title

__all__ = [
    'Person',
    'Sex',
    'PEventType',
    'RelationType',
    'Relation',
    'Title',
]
