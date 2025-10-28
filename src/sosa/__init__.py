"""Top-level exports for the Sosa numbering package."""

from .calculator import (
    branch_of_sosa,
    build_sosa_cache,
    compute_single_sosa,
    get_sosa_number,
    next_sosa,
    p_of_sosa,
    previous_sosa,
)
from .config import resolve_root_id, SosaCacheManager
from .exceptions import (
    InconsistentSosaNumberError,
    MissingRootError,
    SosaError,
)
from .formatters import (
    NavigationSummary,
    SosaBadge,
    build_badge,
    build_navigation_summary,
    summarize_numbers,
)
from .types import SosaCacheState, SosaNavigation, SosaNumber

__all__ = [
    "build_sosa_cache",
    "compute_single_sosa",
    "get_sosa_number",
    "next_sosa",
    "branch_of_sosa",
    "previous_sosa",
    "p_of_sosa",
    "resolve_root_id",
    "SosaCacheManager",
    "SosaCacheState",
    "SosaNavigation",
    "SosaNumber",
    "SosaBadge",
    "NavigationSummary",
    "build_badge",
    "build_navigation_summary",
    "summarize_numbers",
    "SosaError",
    "MissingRootError",
    "InconsistentSosaNumberError",
]
