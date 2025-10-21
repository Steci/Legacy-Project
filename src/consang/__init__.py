"""Top-level API for consanguinity computations."""

from .adapters import compute_for_domain
from .calculator import compute_consanguinity

__all__ = ["compute_consanguinity", "compute_for_domain"]
