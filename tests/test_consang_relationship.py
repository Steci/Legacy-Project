import math
import os
import sys
from textwrap import dedent

import pytest

sys.path.insert(0, os.path.abspath("src"))

from consang import build_relationship_info
from consang.models import FamilyNode, PersonNode
from parsers.gw.canonical import canonicalize_gw
from parsers.gw.parser import GWParser
from parsers.gw.refresh import refresh_consanguinity, RelationshipSummaryCache


def _build_first_cousin_graph():
    persons = {
        1: PersonNode(1, None),
        2: PersonNode(2, None),
        3: PersonNode(3, 1),
        4: PersonNode(4, 1),
        5: PersonNode(5, None),
        6: PersonNode(6, None),
        7: PersonNode(7, 2),
        8: PersonNode(8, 3),
    }

    families = {
        1: FamilyNode(1, 1, 2, (3, 4)),
        2: FamilyNode(2, 3, 5, (7,)),
        3: FamilyNode(3, 4, 6, (8,)),
    }
    return persons, families


def test_relationship_between_first_cousins():
    persons, families = _build_first_cousin_graph()
    info = build_relationship_info(persons, families)

    result = info.relationship_and_links(7, 8, include_branches=True)

    assert math.isclose(result.coefficient, 0.0625, rel_tol=1e-9, abs_tol=1e-9)
    assert set(result.top_ancestors) == {1, 2}

    for ancestor_id in result.top_ancestors:
        state = result.info.states[ancestor_id]
        assert state.lens1, "expected branch information for ancestor"
        assert state.lens2, "expected branch information for ancestor"


def test_relationship_same_person():
    persons, families = _build_first_cousin_graph()
    info = build_relationship_info(persons, families)
    result = info.relationship_and_links(7, 7)
    assert math.isclose(result.coefficient, 1.0, rel_tol=1e-9, abs_tol=1e-9)
    assert result.top_ancestors == []


def test_refresh_populates_relationship_info():
    gw_text = dedent(
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

    parser = GWParser()
    database = parser.parse_text(gw_text)
    refresh_consanguinity(database)

    assert database.relationship_info is not None
    assert database.relationship_key_to_index
    assert database.relationship_index_to_key

    cousin1_id = database.relationship_key_to_index["Smith Cousin1"]
    cousin2_id = database.relationship_key_to_index["Smith Cousin2"]

    result = database.relationship_info.relationship_and_links(
        cousin1_id, cousin2_id, include_branches=True
    )

    assert math.isclose(result.coefficient, 0.0625, rel_tol=1e-9, abs_tol=1e-9)
    ancestor_keys = {
        database.relationship_index_to_key[ancestor]
        for ancestor in result.top_ancestors
    }
    assert ancestor_keys == {"Smith John", "Doe Jane"}


def test_refresh_builds_relationship_summaries():
    gw_text = dedent(
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

    parser = GWParser()
    database = parser.parse_text(gw_text)
    refresh_consanguinity(database)

    summaries = database.relationship_summaries
    assert isinstance(summaries, RelationshipSummaryCache)
    expected_pairs = {
        ("Smith John", "Doe Jane"),
        ("Smith Senior", "Brown Alice"),
        ("Smith Sibling", "Green Mary"),
    }
    assert set(summaries) == expected_pairs

    key = ("Smith John", "Doe Jane")
    summary = summaries[key]
    # Cached results are reused across lookups
    assert summary is summaries[key]
    assert summary.person_a == "Smith John"
    assert summary.person_b == "Doe Jane"
    assert summary.coefficient == pytest.approx(0.0)


def test_canonical_includes_relationship_summaries():
    gw_text = dedent(
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

    parser = GWParser()
    database = parser.parse_text(gw_text)
    refresh_consanguinity(database)

    canonical_db = canonicalize_gw(database)

    john_rel = next((rel for rel in canonical_db.relations if rel.person_key == "Smith John"), None)
    assert john_rel is not None
    assert any("- rel: Doe Jane" in line for line in john_rel.lines)

    jane_rel = next((rel for rel in canonical_db.relations if rel.person_key == "Doe Jane"), None)
    assert jane_rel is not None
    assert any("- rel: Smith John" in line for line in jane_rel.lines)


def test_refresh_updates_relation_blocks_for_ui():
    gw_text = dedent(
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

    parser = GWParser()
    database = parser.parse_text(gw_text)
    refresh_consanguinity(database)

    blocks = {block.person_key: block.lines for block in database.relations}
    assert "Smith John" in blocks
    assert "Doe Jane" in blocks
    assert any("- rel: Doe Jane" in line for line in blocks["Smith John"])
    assert any("- rel: Smith John" in line for line in blocks["Doe Jane"])
