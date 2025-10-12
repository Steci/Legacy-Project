"""
gw_parser package

A parser for GeneWeb `.gw` files.

Usage:
    from gw_parser import GWParser, db_summary
"""

from .models import Person, Family, NoteBlock, RelationBlock, GWDatabase
from .parser import GWParser
from .summary import db_summary

__all__ = [
    "GWParser",
    "db_summary",
    "Person",
    "Family",
    "NoteBlock",
    "RelationBlock",
    "GWDatabase",
]
