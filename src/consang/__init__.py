"""Top-level API for consanguinity computations."""

from .adapters import compute_for_domain
from .calculator import compute_consanguinity
from .relationship import (
	RelationshipInfo,
	RelationshipResult,
	build_relationship_info,
)
from .cousin_degree import (
	CousinDegree,
	RelationshipKind,
	describe_cousin_degree,
	infer_cousin_degree,
)

__all__ = [
	"compute_consanguinity",
	"compute_for_domain",
	"CousinDegree",
	"RelationshipKind",
	"RelationshipInfo",
	"RelationshipResult",
	"build_relationship_info",
	"infer_cousin_degree",
	"describe_cousin_degree",
]
