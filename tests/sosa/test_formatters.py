from __future__ import annotations

from sosa import (
    SosaNavigation,
    build_badge,
    build_navigation_summary,
    build_sosa_cache,
    summarize_numbers,
)

from tests.sosa.common import build_simple_tree


def test_build_badge_with_number():
    badge = build_badge(12)
    assert badge.number == 12
    assert badge.label == "12"


def test_build_badge_without_number():
    badge = build_badge(None, fallback="?")
    assert badge.number == 0
    assert badge.label == "?"


def test_build_navigation_summary_returns_neighbors():
    persons, families = build_simple_tree()
    cache = build_sosa_cache(persons, families, root_id=1)

    summary = build_navigation_summary(cache, 3)
    assert summary is not None
    assert summary.current == SosaNavigation(number=3, person_id=3)
    assert summary.previous == SosaNavigation(number=2, person_id=2)
    assert summary.next == SosaNavigation(number=4, person_id=4)


def test_summarize_numbers_yields_badges():
    persons, families = build_simple_tree()
    cache = build_sosa_cache(persons, families, root_id=1)

    badges = summarize_numbers(cache, [1, 2, 99])
    assert len(badges) == 3
    assert [badge.number for badge in badges] == [1, 2, 0]
    assert [badge.label for badge in badges] == ["1", "2", "-"]
