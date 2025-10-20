"""Compatibility shim exposing person parameter types via legacy absolute imports."""

from models.person.params import (
    PEventType,
    Relation,
    RelationType,
    Sex,
    Title,
)

__all__ = ["PEventType", "Relation", "RelationType", "Sex", "Title"]
