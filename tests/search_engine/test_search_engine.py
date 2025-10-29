import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from search_engine.search_engine import SearchEngine, SearchField, SearchType, AdvancedSearchCriteria
from models.person.person import Person
from models.family.family import Family
from models.person.params import Sex


# Helper to create Person and Family with correct fields
def make_person(key_index, first_name, surname, sex=None, occupation=None):
    return Person(
        first_name=first_name,
        surname=surname,
        sex=sex if sex is not None else Sex.NEUTER,
        occupation=occupation,
        key_index=key_index
    )

def make_family(key_index, parent1=None, parent2=None, children=None):
    # parent1, parent2, children are integer key_index values
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
        make_person(1, "John", "Smith", Sex.MALE, "Engineer"),
        make_person(2, "Mary", "Smith", Sex.FEMALE, "Teacher"),
        make_person(3, "Robert", "Smith", Sex.MALE, "Doctor"),
    ]

@pytest.fixture
def families():
    # parent1=1 (John), parent2=2 (Mary), children=[3] (Robert)
    return [make_family(1, parent1=1, parent2=2, children=[3])]


class TestSimpleSearch:
    def test_exact_first_name(self, persons, families):
        engine = SearchEngine(persons, families)
        results = engine.simple_search("John", SearchField.FIRST_NAME, SearchType.EXACT)
        assert any(r.person.first_name == "John" for r in results)

    def test_fuzzy_first_name(self, persons, families):
        engine = SearchEngine(persons, families)
        results = engine.simple_search("Jon", SearchField.FIRST_NAME, SearchType.FUZZY)
        assert any(r.person.first_name == "John" for r in results)

    def test_occupation_search(self, persons, families):
        engine = SearchEngine(persons, families)
        results = engine.simple_search("Doctor", SearchField.OCCUPATION, SearchType.EXACT)
        assert any(r.person.occupation == "Doctor" for r in results)

class TestAdvancedSearch:
    def test_advanced_criteria(self, persons, families):
        engine = SearchEngine(persons, families)
        criteria = AdvancedSearchCriteria(sex=Sex.MALE, occupation="Engineer")
        results = engine.advanced_search(criteria)
        assert any(r.person.first_name == "John" for r in results)

    def test_combined_criteria(self, persons, families):
        engine = SearchEngine(persons, families)
        criteria = AdvancedSearchCriteria(sex=Sex.FEMALE, occupation="Teacher")
        results = engine.advanced_search(criteria)
        assert any(r.person.first_name == "Mary" for r in results)
