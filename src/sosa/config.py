"""Configuration helpers for Sosa cache management."""

from __future__ import annotations

import os
from typing import Dict, Mapping, Optional

from consang.models import FamilyNode, PersonNode

from .calculator import build_sosa_cache
from .exceptions import MissingRootError
from .types import SosaCacheState


def _coerce_int(value: object) -> Optional[int]:
    """Attempt to coerce ``value`` to an integer, returning None on failure."""

    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def resolve_root_id(
    explicit: Optional[int] = None,
    *,
    settings: Optional[Mapping[str, object]] = None,
    env: Optional[Mapping[str, str]] = None,
    env_key: str = "SOSA_ROOT",
) -> Optional[int]:
    """Resolve the desired Sosa root identifier.

    Preference order:
    1. ``explicit`` argument.
    2. ``settings["sosa_root"]`` (if provided).
    3. ``env`` mapping (defaults to ``os.environ``) via ``env_key``.
    """

    root_id = _coerce_int(explicit)
    if root_id is not None:
        return root_id

    if settings is not None:
        root_id = _coerce_int(settings.get("sosa_root"))
        if root_id is not None:
            return root_id

    source = env if env is not None else os.environ
    root_id = _coerce_int(source.get(env_key))
    return root_id


class SosaCacheManager:
    """Lazily build and reuse Sosa caches for a given dataset."""

    def __init__(
        self,
        persons: Mapping[int, PersonNode],
        families: Mapping[int, FamilyNode],
    ) -> None:
        self._persons: Mapping[int, PersonNode] = persons
        self._families: Mapping[int, FamilyNode] = families
        self._caches: Dict[int, SosaCacheState] = {}

    def get_cache(self, root_id: int) -> SosaCacheState:
        """Return a cache for ``root_id``, building it on first use."""

        if root_id in self._caches:
            return self._caches[root_id]
        cache = build_sosa_cache(self._persons, self._families, root_id)
        self._caches[root_id] = cache
        return cache

    def ensure_from_config(
        self,
        *,
        root_override: Optional[int] = None,
        settings: Optional[Mapping[str, object]] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> SosaCacheState:
        """Resolve a root and return the corresponding cache."""

        root_id = resolve_root_id(
            root_override,
            settings=settings,
            env=env,
        )
        if root_id is None:
            raise MissingRootError(root_id)
        return self.get_cache(root_id)

    def drop_cache(self, root_id: Optional[int] = None) -> None:
        """Forget cached state for ``root_id`` or all caches when None."""

        if root_id is None:
            self._caches.clear()
            return
        self._caches.pop(root_id, None)

    def update_data(
        self,
        persons: Mapping[int, PersonNode],
        families: Mapping[int, FamilyNode],
        *,
        drop_existing: bool = True,
    ) -> None:
        """Point the manager to new datasets, optionally clearing caches."""

        self._persons = persons
        self._families = families
        if drop_existing:
            self._caches.clear()

    @property
    def persons(self) -> Mapping[int, PersonNode]:
        return self._persons

    @property
    def families(self) -> Mapping[int, FamilyNode]:
        return self._families

    @property
    def caches(self) -> Mapping[int, SosaCacheState]:
        return self._caches
