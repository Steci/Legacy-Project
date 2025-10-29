from __future__ import annotations

import hashlib
import pickle
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from consang.relationship import BranchPath, RelationshipSummary
from models.date import Precision

from .types import (
    CousinComputationSettings,
    CousinDegree,
    CousinListing,
    CousinMatrixEntry,
    PersonTemporalData,
    RelationshipKind,
)


_MATRIX_CACHE: Dict[Tuple, Dict[int, Dict[int, List[CousinMatrixEntry]]]] = {}
_DEFAULT_SETTINGS = CousinComputationSettings()


def set_cousin_degree_settings(settings: CousinComputationSettings) -> None:
    """Override the module-level defaults used by cousin helpers."""

    global _DEFAULT_SETTINGS
    _DEFAULT_SETTINGS = settings


def get_cousin_degree_settings() -> CousinComputationSettings:
    """Return the current module-level settings."""

    return _DEFAULT_SETTINGS


@dataclass(frozen=True)
class _Candidate:
    ancestor: str
    generations_a: int
    generations_b: int

    @property
    def ordering(self) -> Tuple[int, int, int, int]:
        # Prefer closest common ancestor; minimise the deeper branch first,
        # then the combined path length.
        deeper = max(self.generations_a, self.generations_b)
        total = self.generations_a + self.generations_b
        return (deeper, total, self.generations_a, self.generations_b)


def infer_all_cousin_degrees(summary: RelationshipSummary) -> list[CousinDegree]:
    """Return all qualifying cousin-degree candidates in priority order."""

    if summary.person_a == summary.person_b:
        return [CousinDegree(kind=RelationshipKind.SELF, ancestor=summary.person_a, generations_a=0, generations_b=0)]

    candidates = _collect_candidates(summary)
    results: list[tuple[Tuple[int, int, int, int], CousinDegree]] = []

    for candidate in candidates:
        degree = _candidate_to_degree(candidate)
        if degree is not None:
            results.append((candidate.ordering, degree))

    results.sort(key=lambda item: item[0])
    return [degree for _, degree in results]


def infer_cousin_degree(summary: RelationshipSummary) -> CousinDegree:
    """Infer the top-priority cousin-degree information from a relationship summary."""

    all_candidates = infer_all_cousin_degrees(summary)
    if not all_candidates:
        return CousinDegree(kind=RelationshipKind.UNRELATED)
    return all_candidates[0]


def build_cousin_matrix(
    summary: RelationshipSummary,
    *,
    max_depth_a: Optional[int] = None,
    max_depth_b: Optional[int] = None,
    use_cache: bool = True,
    settings: Optional[CousinComputationSettings] = None,
) -> Dict[int, Dict[int, List[CousinMatrixEntry]]]:
    """Construct an l1×l2 matrix of cousin information similar to GeneWeb's output."""

    effective_settings = settings or _DEFAULT_SETTINGS
    depth_a_limit = max_depth_a if max_depth_a is not None else effective_settings.max_depth_a
    depth_b_limit = max_depth_b if max_depth_b is not None else effective_settings.max_depth_b

    cache_key = _make_matrix_cache_key(
        summary,
        depth_a_limit,
        depth_b_limit,
        effective_settings.cache_key_fragment(),
    )
    if use_cache:
        cached = _MATRIX_CACHE.get(cache_key)
        if cached is not None:
            return cached
        disk_cached = _load_disk_cache(cache_key, effective_settings)
        if disk_cached is not None:
            _MATRIX_CACHE[cache_key] = disk_cached
            return disk_cached

    matrix: Dict[int, Dict[int, List[CousinMatrixEntry]]] = {}
    if not summary.ancestors:
        if use_cache:
            _store_in_caches(cache_key, matrix, effective_settings)
        return matrix

    seen_paths: set[Tuple[str, Tuple[str, ...], Tuple[str, ...]]] = set()
    total_entries = 0
    max_results = effective_settings.max_results if effective_settings.max_results is None else max(0, effective_settings.max_results)

    for ancestor in summary.ancestors:
        paths_a = summary.paths_to_a.get(ancestor, ())
        paths_b = summary.paths_to_b.get(ancestor, ())
        if not paths_a or not paths_b:
            continue

        for path_a in paths_a:
            len_a = path_a.length
            if depth_a_limit is not None and len_a > depth_a_limit:
                continue

            for path_b in paths_b:
                len_b = path_b.length
                if depth_b_limit is not None and len_b > depth_b_limit:
                    continue

                signature = (ancestor, path_a.path, path_b.path)
                if signature in seen_paths:
                    continue
                seen_paths.add(signature)

                candidate = _Candidate(ancestor=ancestor, generations_a=len_a, generations_b=len_b)
                degree = _candidate_to_degree(candidate)
                if degree is None:
                    continue

                matrix.setdefault(len_a, {}).setdefault(len_b, []).append(
                    CousinMatrixEntry(
                        ancestor=ancestor,
                        path_to_a=path_a,
                        path_to_b=path_b,
                        degree=degree,
                    )
                )
                total_entries += 1
                if max_results and total_entries >= max_results:
                    break
            if max_results and total_entries >= max_results:
                break
        if max_results and total_entries >= max_results:
            break

    if use_cache:
        _store_in_caches(cache_key, matrix, effective_settings)

    return matrix


def build_cousin_listings(
    summary: RelationshipSummary,
    *,
    spouse_lookup: Optional[Callable[[str], Iterable[str]]] = None,
    temporal_lookup: Optional[Callable[[str], Optional[PersonTemporalData]]] = None,
    max_depth_a: Optional[int] = None,
    max_depth_b: Optional[int] = None,
    use_cache: bool = True,
    settings: Optional[CousinComputationSettings] = None,
) -> List[CousinListing]:
    """Produce enriched cousin listings with descendant chains and optional spouses."""

    matrix = build_cousin_matrix(
        summary,
        max_depth_a=max_depth_a,
        max_depth_b=max_depth_b,
        use_cache=use_cache,
        settings=settings,
    )

    listings: List[CousinListing] = []

    for depth_a in sorted(matrix.keys()):
        depth_bucket = matrix[depth_a]
        for depth_b in sorted(depth_bucket.keys()):
            for entry in depth_bucket[depth_b]:
                descendants_a = _descendant_chain(entry.path_to_a)
                descendants_b = _descendant_chain(entry.path_to_b)

                spouses_a = _resolve_spouses(descendants_a, spouse_lookup)
                spouses_b = _resolve_spouses(descendants_b, spouse_lookup)

                birth_range, death_range = _aggregate_temporal_ranges(
                    entry, temporal_lookup
                )

                listings.append(
                    CousinListing(
                        ancestor=entry.ancestor,
                        degree=entry.degree,
                        path_to_a=entry.path_to_a,
                        path_to_b=entry.path_to_b,
                        descendants_a=descendants_a,
                        descendants_b=descendants_b,
                        spouses_a=spouses_a,
                        spouses_b=spouses_b,
                        birth_year_range=birth_range,
                        death_year_range=death_range,
                    )
                )

    return listings


def _collect_candidates(summary: RelationshipSummary) -> list[_Candidate]:
    candidates: list[_Candidate] = []

    for ancestor in summary.ancestors:
        paths_a = summary.paths_to_a.get(ancestor)
        paths_b = summary.paths_to_b.get(ancestor)
        if not paths_a or not paths_b:
            continue

        min_a = _min_generations(paths_a)
        min_b = _min_generations(paths_b)
        if min_a is None or min_b is None:
            continue

        candidates.append(_Candidate(ancestor=ancestor, generations_a=min_a, generations_b=min_b))

    candidates.sort(key=lambda candidate: candidate.ordering)
    return candidates


def _min_generations(paths: Iterable[BranchPath]) -> Optional[int]:
    try:
        return min(path.length for path in paths)
    except ValueError:
        return None


def _candidate_to_degree(candidate: _Candidate) -> Optional[CousinDegree]:
    ga = candidate.generations_a
    gb = candidate.generations_b

    if ga == 0 and gb == 0:
        return CousinDegree(
            kind=RelationshipKind.SELF,
            ancestor=candidate.ancestor,
            generations_a=0,
            generations_b=0,
        )

    if ga == 0 or gb == 0:
        return CousinDegree(
            kind=RelationshipKind.DIRECT_ANCESTOR,
            ancestor=candidate.ancestor,
            generations_a=ga,
            generations_b=gb,
        )

    if ga == 1 and gb == 1:
        return CousinDegree(
            kind=RelationshipKind.SIBLING,
            ancestor=candidate.ancestor,
            generations_a=ga,
            generations_b=gb,
        )

    degree = min(ga, gb) - 1
    if degree <= 0:
        return None

    removal = abs(ga - gb)
    return CousinDegree(
        kind=RelationshipKind.COUSIN,
        degree=degree,
        removal=removal,
        ancestor=candidate.ancestor,
        generations_a=ga,
        generations_b=gb,
    )


def _descendant_chain(path: BranchPath) -> Tuple[str, ...]:
    if not path.path:
        return ()
    return tuple(path.path[1:])


def _resolve_spouses(
    descendants: Tuple[str, ...],
    lookup: Optional[Callable[[str], Iterable[str]]],
) -> Tuple[str, ...]:
    if lookup is None or not descendants:
        return ()
    terminal = descendants[-1]
    result = lookup(terminal)
    if result is None:
        return ()
    values = tuple(result)
    return tuple(dict.fromkeys(values))


def clear_cousin_degree_cache(
    *,
    include_disk: bool = False,
    settings: Optional[CousinComputationSettings] = None,
) -> None:
    """Reset in-memory (and optionally on-disk) cousin caches."""

    _MATRIX_CACHE.clear()
    if not include_disk:
        return
    active_settings = settings or _DEFAULT_SETTINGS
    cache_dir = active_settings.cache_directory
    if cache_dir is None:
        return
    try:
        entries = list(Path(cache_dir).glob(f"{active_settings.cache_prefix}-*.pkl"))
    except FileNotFoundError:
        return
    for entry in entries:
        try:
            entry.unlink()
        except FileNotFoundError:
            continue


def _make_matrix_cache_key(
    summary: RelationshipSummary,
    max_depth_a: Optional[int],
    max_depth_b: Optional[int],
    settings_fragment: Tuple[Optional[int], Optional[int], Optional[int], int],
) -> Tuple:
    encoded_summary = _encode_summary(summary)
    return (encoded_summary, max_depth_a, max_depth_b, settings_fragment)


def _encode_summary(summary: RelationshipSummary) -> Tuple:
    ancestor_entries = []
    for ancestor in sorted(summary.ancestors):
        paths_a = tuple(
            sorted(
                (
                    branch.length,
                    branch.multiplicity,
                    branch.path,
                )
                for branch in summary.paths_to_a.get(ancestor, ())
            )
        )
        paths_b = tuple(
            sorted(
                (
                    branch.length,
                    branch.multiplicity,
                    branch.path,
                )
                for branch in summary.paths_to_b.get(ancestor, ())
            )
        )
        ancestor_entries.append((ancestor, paths_a, paths_b))
    return (
        summary.person_a,
        summary.person_b,
        summary.coefficient,
        tuple(ancestor_entries),
    )


def build_default_spouse_lookup(database: object) -> Optional[Callable[[str], Tuple[str, ...]]]:
    persons = getattr(database, "persons", None)
    families = getattr(database, "families", None)
    if not persons or not families:
        return None

    index_to_key = getattr(database, "relationship_index_to_key", {}) or {}
    mapping: Dict[str, List[str]] = defaultdict(list)

    def resolve_key(candidate: object) -> Optional[str]:
        if candidate is None:
            return None
        if isinstance(candidate, str):
            if candidate in persons:
                return candidate
            lowered = candidate.lower()
            for key in persons:
                if key.lower() == lowered:
                    return key
            return None
        if isinstance(candidate, int):
            key = index_to_key.get(candidate)
            if key:
                return key
            for key, person in persons.items():
                if getattr(person, "key_index", None) == candidate:
                    return key
            return None
        return None

    for family in families:
        participants: List[str] = []
        for attr in ("husband", "wife"):
            key = resolve_key(getattr(family, attr, None))
            if key and key not in participants:
                participants.append(key)
        if len(participants) < 2:
            for attr in ("parent1", "parent2"):
                key = resolve_key(getattr(family, attr, None))
                if key and key not in participants:
                    participants.append(key)
        if len(participants) < 2:
            continue
        for key in participants:
            for other in participants:
                if other == key or other in mapping[key]:
                    continue
                mapping[key].append(other)

    if not mapping:
        return None

    def lookup(person_key: str) -> Tuple[str, ...]:
        values = mapping.get(person_key)
        if not values:
            return ()
        return tuple(values)

    return lookup


def _store_in_caches(
    cache_key: Tuple,
    matrix: Dict[int, Dict[int, List[CousinMatrixEntry]]],
    settings: CousinComputationSettings,
) -> None:
    _MATRIX_CACHE[cache_key] = matrix
    _store_disk_cache(cache_key, matrix, settings)


def _load_disk_cache(
    cache_key: Tuple,
    settings: CousinComputationSettings,
) -> Optional[Dict[int, Dict[int, List[CousinMatrixEntry]]]]:
    filepath = _cache_file_path(cache_key, settings)
    if filepath is None or not filepath.exists():
        return None
    try:
        with filepath.open("rb") as handle:
            return pickle.load(handle)
    except (OSError, pickle.UnpicklingError):
        return None


def _store_disk_cache(
    cache_key: Tuple,
    matrix: Dict[int, Dict[int, List[CousinMatrixEntry]]],
    settings: CousinComputationSettings,
) -> None:
    filepath = _cache_file_path(cache_key, settings)
    if filepath is None:
        return
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with filepath.open("wb") as handle:
            pickle.dump(matrix, handle)
    except OSError:
        return


def _cache_file_path(
    cache_key: Tuple,
    settings: CousinComputationSettings,
) -> Optional[Path]:
    if not settings.cache_enabled or settings.cache_directory is None:
        return None
    cache_dir = Path(settings.cache_directory)
    digest = hashlib.sha1(pickle.dumps(cache_key)).hexdigest()
    return cache_dir / f"{settings.cache_prefix}-{digest}.pkl"


def _aggregate_temporal_ranges(
    entry: CousinMatrixEntry,
    lookup: Optional[Callable[[str], Optional[PersonTemporalData]]],
) -> Tuple[Optional[Tuple[int, int]], Optional[Tuple[int, int]]]:
    if lookup is None:
        return (None, None)

    birth_years: set[int] = set()
    death_years: set[int] = set()
    today_year = datetime.now(timezone.utc).year

    for person_key in dict.fromkeys(tuple(entry.path_to_a.path) + tuple(entry.path_to_b.path)):
        info = lookup(person_key)
        if not info:
            continue
        birth_exact = _is_exact_precision(info.birth_precision)
        death_exact = _is_exact_precision(info.death_precision)
        is_alive = info.is_alive if info.is_alive is not None else info.death_year is None

        if info.birth_year is not None and birth_exact:
            birth_years.add(info.birth_year)

        if info.death_year is not None and death_exact:
            death_years.add(info.death_year)

        if is_alive and info.death_year is None:
            death_years.add(today_year)

        if info.birth_year is not None and birth_exact and (info.death_year is None or not death_exact) and is_alive:
            death_years.add(today_year)

    birth_range = (
        (min(birth_years), max(birth_years)) if birth_years else None
    )
    death_range = (
        (min(death_years), max(death_years)) if death_years else None
    )
    return (birth_range, death_range)


def _is_exact_precision(value: Optional[Precision]) -> bool:
    if value is None:
        return True
    return value not in {
        Precision.ABOUT,
        Precision.MAYBE,
        Precision.BEFORE,
        Precision.AFTER,
        Precision.OR_YEAR,
        Precision.YEAR_INT,
    }
