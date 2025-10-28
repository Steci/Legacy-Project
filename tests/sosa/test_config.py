from __future__ import annotations

import os

import pytest

from consang.models import FamilyNode, PersonNode

from sosa import MissingRootError, SosaCacheManager, resolve_root_id


@pytest.fixture
def simple_tree():
    persons = {
        1: PersonNode(person_id=1, parent_family_id=1),
        2: PersonNode(person_id=2, parent_family_id=None),
        3: PersonNode(person_id=3, parent_family_id=None),
    }
    families = {
        1: FamilyNode(family_id=1, father_id=2, mother_id=3, children=(1,)),
    }
    return persons, families


def test_resolve_root_id_prefers_explicit(monkeypatch):
    monkeypatch.setenv("SOSA_ROOT", "50")
    settings = {"sosa_root": "20"}

    result = resolve_root_id(10, settings=settings)
    assert result == 10


def test_resolve_root_id_falls_back_to_settings(monkeypatch):
    monkeypatch.delenv("SOSA_ROOT", raising=False)
    settings = {"sosa_root": "25"}

    result = resolve_root_id(None, settings=settings)
    assert result == 25


def test_resolve_root_id_reads_environment(monkeypatch):
    monkeypatch.setenv("SOSA_ROOT", "42")

    result = resolve_root_id(None, settings={})
    assert result == 42


def test_resolve_root_id_returns_none_without_sources(monkeypatch):
    monkeypatch.delenv("SOSA_ROOT", raising=False)

    assert resolve_root_id(None, settings={}) is None


def test_cache_manager_builds_once(simple_tree):
    persons, families = simple_tree
    manager = SosaCacheManager(persons, families)

    first = manager.get_cache(1)
    second = manager.get_cache(1)

    assert first is second
    assert first.get_number(1) == 1


def test_cache_manager_drop_and_rebuild(simple_tree):
    persons, families = simple_tree
    manager = SosaCacheManager(persons, families)

    cache = manager.get_cache(1)
    manager.drop_cache(1)
    rebuilt = manager.get_cache(1)

    assert rebuilt is not cache
    assert rebuilt.get_number(2) == 2


def test_cache_manager_update_data(simple_tree):
    persons, families = simple_tree
    manager = SosaCacheManager(persons, families)
    _ = manager.get_cache(1)

    new_persons = {
        5: PersonNode(person_id=5, parent_family_id=None),
    }
    new_families = {}
    manager.update_data(new_persons, new_families)

    with pytest.raises(MissingRootError):
        manager.get_cache(1)


def test_ensure_from_config_requires_root(simple_tree):
    persons, families = simple_tree
    manager = SosaCacheManager(persons, families)

    with pytest.raises(MissingRootError):
        manager.ensure_from_config(settings={})


def test_ensure_from_config_uses_settings(simple_tree):
    persons, families = simple_tree
    manager = SosaCacheManager(persons, families)

    cache = manager.ensure_from_config(settings={"sosa_root": 1})
    assert cache.get_number(1) == 1


def test_ensure_from_config_uses_override(simple_tree):
    persons, families = simple_tree
    manager = SosaCacheManager(persons, families)

    cache = manager.ensure_from_config(root_override=1, settings={"sosa_root": 2})
    assert cache.get_number(2) == 2
