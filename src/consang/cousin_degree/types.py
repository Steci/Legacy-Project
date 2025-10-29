from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Mapping, Optional, Tuple

from consang.relationship import BranchPath
from models.date import Precision


class RelationshipKind(Enum):
    SELF = auto()
    SIBLING = auto()
    DIRECT_ANCESTOR = auto()
    COUSIN = auto()
    UNRELATED = auto()


@dataclass(frozen=True)
class CousinDegree:
    kind: RelationshipKind
    degree: Optional[int] = None
    removal: Optional[int] = None
    generations_a: Optional[int] = None
    generations_b: Optional[int] = None
    ancestor: Optional[str] = None

    def swap(self) -> "CousinDegree":
        """Return a variant with people A/B swapped."""

        if self.generations_a is None or self.generations_b is None:
            return self
        return CousinDegree(
            kind=self.kind,
            degree=self.degree,
            removal=self.removal,
            generations_a=self.generations_b,
            generations_b=self.generations_a,
            ancestor=self.ancestor,
        )


@dataclass(frozen=True)
class CousinMatrixEntry:
    ancestor: str
    path_to_a: BranchPath
    path_to_b: BranchPath
    degree: CousinDegree


@dataclass(frozen=True)
class CousinListing:
    ancestor: str
    degree: CousinDegree
    path_to_a: BranchPath
    path_to_b: BranchPath
    descendants_a: Tuple[str, ...]
    descendants_b: Tuple[str, ...]
    spouses_a: Tuple[str, ...]
    spouses_b: Tuple[str, ...]
    birth_year_range: Optional[Tuple[int, int]] = None
    death_year_range: Optional[Tuple[int, int]] = None


@dataclass(frozen=True)
class PersonTemporalData:
    birth_year: Optional[int] = None
    birth_precision: Optional[Precision] = None
    death_year: Optional[int] = None
    death_precision: Optional[Precision] = None
    is_alive: Optional[bool] = None


@dataclass(frozen=True)
class CousinComputationSettings:
    """Configuration knobs that mirror GeneWeb's cousin defaults."""

    max_depth_a: Optional[int] = 12
    max_depth_b: Optional[int] = 12
    max_results: Optional[int] = 2000
    cache_directory: Optional[Path] = None
    cache_enabled: bool = False
    cache_prefix: str = field(default="cousin_cache", repr=False)
    cache_version: int = 1

    def cache_key_fragment(self) -> Tuple[Optional[int], Optional[int], Optional[int], int]:
        return (self.max_depth_a, self.max_depth_b, self.max_results, self.cache_version)


def load_cousin_settings(
    env: Mapping[str, str],
    *,
    base_path: Optional[Path] = None,
    defaults: Optional["CousinComputationSettings"] = None,
) -> CousinComputationSettings:
    """Translate GeneWeb-esque environment variables into computation settings."""

    settings = CousinComputationSettings() if defaults is None else defaults

    def _parse_int(name: str) -> Optional[int]:
        raw = env.get(name)
        if not raw:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    max_anc = _parse_int("max_anc_level")
    max_desc = _parse_int("max_desc_level")
    max_cousins_level = _parse_int("max_cousins_level")
    max_cousins = _parse_int("max_cousins")

    max_depth_a = settings.max_depth_a
    max_depth_b = settings.max_depth_b

    if max_anc is not None:
        max_depth_a = max_anc if max_depth_a is None else min(max_depth_a, max_anc)
    if max_desc is not None:
        max_depth_b = max_desc if max_depth_b is None else min(max_depth_b, max_desc)
    if max_cousins_level is not None:
        limit = max_cousins_level
        max_depth_a = limit if max_depth_a is None else min(max_depth_a, limit)
        max_depth_b = limit if max_depth_b is None else min(max_depth_b, limit)

    max_results = settings.max_results
    if max_cousins is not None:
        max_results = max_cousins if max_results is None else min(max_results, max_cousins)

    cache_enabled = env.get("cache_cousins_tool", "no").lower() in {"yes", "true", "1"}
    cache_directory = settings.cache_directory
    if cache_enabled and cache_directory is None and base_path is not None:
        cache_directory = Path(base_path)

    return CousinComputationSettings(
        max_depth_a=max_depth_a,
        max_depth_b=max_depth_b,
        max_results=max_results,
        cache_directory=cache_directory,
        cache_enabled=cache_enabled,
        cache_prefix=settings.cache_prefix,
        cache_version=settings.cache_version,
    )
