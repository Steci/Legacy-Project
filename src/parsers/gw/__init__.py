"""
gw_parser package

A parser for GeneWeb `.gw` files.

Usage:
    from gw_parser import GWParser, db_summary
"""

from .loader import load_geneweb_file, load_geneweb_text
from .models import Person, Family, NoteBlock, RelationBlock, GWDatabase
from .parser import GWParser
from .refresh import refresh_consanguinity
from .summary import db_summary

__all__ = [
    "GWParser",
    "db_summary",
    "refresh_consanguinity",
    "load_geneweb_file",
    "load_geneweb_text",
    "Person",
    "Family",
    "NoteBlock",
    "RelationBlock",
    "GWDatabase",
]
