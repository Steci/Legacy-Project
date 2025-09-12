import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../consang')))
from relationship import Relationship, RelationshipInfo, relationship_and_links


@pytest.fixture
def mock_data():
    base = {
        1: {"father": 2, "mother": 3, "consang": 0},
        2: {"father": None, "mother": None, "consang": 0},
        3: {"father": None, "mother": None, "consang": 0},
    }
    ri = RelationshipInfo()
    ri.tstab = {1: 0, 2: 1, 3: 1}
    return base, ri


def test_same_individual(mock_data):
    base, ri = mock_data
    result = relationship_and_links(base, ri, False, 1, 1)
    assert result == (1.0, [])


def test_unrelated_individuals(mock_data):
    base, ri = mock_data
    result = relationship_and_links(base, ri, False, 2, 3)
    assert result == (0.0, [])


def test_direct_parent_child_relationship(mock_data):
    base, ri = mock_data
    base[4] = {"father": 2, "mother": 3, "consang": 0}
    ri.tstab[4] = 0
    result = relationship_and_links(base, ri, False, 2, 4)
    assert result[0] > 0.0
    assert 2 in result[1]


def test_full_relationship(mock_data):
    base, ri = mock_data
    base[5] = {"father": 2, "mother": 3, "consang": 0}
    base[6] = {"father": 5, "mother": None, "consang": 0}
    ri.tstab[5] = 0
    ri.tstab[6] = 0
    result = relationship_and_links(base, ri, True, 5, 6)
    assert result[0] > 0.0
    assert 5 in result[1]


def test_consanguinity(mock_data):
    base, ri = mock_data
    base[7] = {"father": 2, "mother": 3, "consang": 50}
    ri.tstab[7] = 0
    result = relationship_and_links(base, ri, False, 2, 7)
    assert result[0] > 0.0
    assert 2 in result[1]
