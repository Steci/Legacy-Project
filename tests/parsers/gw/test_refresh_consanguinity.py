from __future__ import annotations

import math
from textwrap import dedent

import pytest

from parsers.gw.parser import GWParser
from parsers.gw.refresh import RelationshipSummaryCache, refresh_consanguinity


def build_sample_tree():
    return dedent(
        """
        Smith John 1900
        Doe Jane 1905
        Brown Alice 1930
        Green Mary 1932
        fam Smith John + Doe Jane
        beg
        - h Smith Senior
        - h Smith Sibling
        end

        fam Smith Senior + Brown Alice
        beg
        - h Smith Cousin1
        end

        fam Smith Sibling + Green Mary
        beg
        - h Smith Cousin2
        end
        """
    ).strip()


@pytest.fixture()
def parsed_database():
    parser = GWParser()
    return parser.parse_text(build_sample_tree())


def test_refresh_populates_relationship_info(parsed_database):
    refresh_consanguinity(parsed_database)

    assert parsed_database.relationship_info is not None
    assert parsed_database.relationship_key_to_index
    assert parsed_database.relationship_index_to_key

    cousin1_id = parsed_database.relationship_key_to_index["Smith Cousin1"]
    cousin2_id = parsed_database.relationship_key_to_index["Smith Cousin2"]

    result = parsed_database.relationship_info.relationship_and_links(
        cousin1_id, cousin2_id, include_branches=True
    )

    assert math.isclose(result.coefficient, 0.0625, rel_tol=1e-9, abs_tol=1e-9)
    ancestor_keys = {
        parsed_database.relationship_index_to_key[ancestor]
        for ancestor in result.top_ancestors
    }
    assert ancestor_keys == {"Smith John", "Doe Jane"}


def test_refresh_builds_relationship_summaries(parsed_database):
    refresh_consanguinity(parsed_database)

    summaries = parsed_database.relationship_summaries
    assert isinstance(summaries, RelationshipSummaryCache)
    expected_pairs = {
        ("Smith John", "Doe Jane"),
        ("Smith Senior", "Brown Alice"),
        ("Smith Sibling", "Green Mary"),
    }
    assert set(summaries) == expected_pairs

    key = ("Smith John", "Doe Jane")
    summary = summaries[key]
    assert summary is summaries[key]
    assert summary.person_a == "Smith John"
    assert summary.person_b == "Doe Jane"
    assert summary.coefficient == pytest.approx(0.0)


def test_refresh_updates_relation_blocks(parsed_database):
    refresh_consanguinity(parsed_database)

    blocks = {block.person_key: block.lines for block in parsed_database.relations}
    assert "Smith John" in blocks
    assert "Doe Jane" in blocks
    assert any("- rel: Doe Jane" in line for line in blocks["Smith John"])
    assert any("- rel: Smith John" in line for line in blocks["Doe Jane"])


def test_refresh_handles_repeated_calls(parsed_database):
    # First call should populate caches
    refresh_consanguinity(parsed_database)
    initial_summary = parsed_database.relationship_summaries["Smith John", "Doe Jane"]

    # Second call should reuse cached summaries without raising
    refresh_consanguinity(parsed_database)
    refreshed_summary = parsed_database.relationship_summaries["Smith John", "Doe Jane"]

    assert refreshed_summary == initial_summary
    assert refreshed_summary.coefficient == pytest.approx(0.0)


def test_refresh_handles_missing_relations(parsed_database):
    parsed_database.persons.pop("Brown Alice")

    refresh_consanguinity(parsed_database)

    info = parsed_database.relationship_info
    assert info is not None
    assert isinstance(parsed_database.relationship_summaries, RelationshipSummaryCache)
