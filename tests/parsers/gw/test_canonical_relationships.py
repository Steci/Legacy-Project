from __future__ import annotations

from textwrap import dedent

from parsers.gw.canonical import canonicalize_gw
from parsers.gw.parser import GWParser
from parsers.gw.refresh import refresh_consanguinity


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


def test_canonical_output_contains_relationship_blocks():
    parser = GWParser()
    database = parser.parse_text(build_sample_tree())
    refresh_consanguinity(database)

    canonical_db = canonicalize_gw(database)

    john_rel = next((rel for rel in canonical_db.relations if rel.person_key == "Smith John"), None)
    assert john_rel is not None
    assert any("- rel: Doe Jane" in line for line in john_rel.lines)

    jane_rel = next((rel for rel in canonical_db.relations if rel.person_key == "Doe Jane"), None)
    assert jane_rel is not None
    assert any("- rel: Smith John" in line for line in jane_rel.lines)
