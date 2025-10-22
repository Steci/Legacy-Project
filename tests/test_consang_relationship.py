import math
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("src"))

from consang import build_relationship_info
from consang.models import FamilyNode, PersonNode


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
