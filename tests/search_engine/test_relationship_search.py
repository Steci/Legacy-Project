import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from search_engine.relationship_search import RelationshipSearchEngine, RelationshipType
from models.person.person import Person
from models.family.family import Family


# Helper to create Person and Family with correct fields
def make_person(key_index, first_name, surname):
    return Person(
        first_name=first_name,
        surname=surname,
        key_index=key_index
    )

def make_family(key_index, parent1=None, parent2=None, children=None):
    return Family(
        parent1=parent1 if parent1 is not None else 0,
        parent2=parent2 if parent2 is not None else 0,
        children=children or [],
        key_index=key_index
    )

@pytest.fixture
def persons():
    # key_index: 1, 2, 3
    return [
        make_person(1, "John", "Smith"),
        make_person(2, "Mary", "Smith"),
        make_person(3, "Robert", "Smith"),
    ]

@pytest.fixture
def families():
    # parent1=1 (John), parent2=2 (Mary), children=[3] (Robert)
    return [make_family(1, parent1=1, parent2=2, children=[3])]

class TestRelationshipSearch:
    def test_parent_child(self, persons, families):
        engine = RelationshipSearchEngine(persons, families)
        rel = engine.find_relationship(1, 3)
        assert rel is not None
        assert rel.relationship_type in {RelationshipType.PARENT, RelationshipType.CHILD}

    def test_spouse(self, persons, families):
        engine = RelationshipSearchEngine(persons, families)
        rel = engine.find_relationship(1, 2)
        assert rel is not None
        assert rel.relationship_type == RelationshipType.SPOUSE

    def test_no_relationship(self, persons, families):
        engine = RelationshipSearchEngine(persons, families)
        rel = engine.find_relationship(1, 1)
        assert rel is not None
        assert rel.distance == 0
