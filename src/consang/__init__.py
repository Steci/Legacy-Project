"""Top-level API for consanguinity computations."""

from .adapters import compute_for_domain
from .calculator import compute_consanguinity
from .relationship import (
	RelationshipInfo,
	RelationshipResult,
	build_relationship_info,
)

__all__ = [
	"compute_consanguinity",
	"compute_for_domain",
	"RelationshipInfo",
	"RelationshipResult",
	"build_relationship_info",
]
