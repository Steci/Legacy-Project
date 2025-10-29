import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (PROJECT_ROOT, SRC_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from search_engine.genealogy_search_api import GenealogySearchAPI  # type: ignore[import]
from models.person.person import Person  # type: ignore[import]
from models.family.family import Family  # type: ignore[import]
from models.person.params import Sex  # type: ignore[import]


# Helper to create Person and Family with correct fields
def make_person(key_index, first_name, surname, sex=None):
    return Person(
        first_name=first_name,
        surname=surname,
        sex=sex if sex is not None else Sex.NEUTER,
        key_index=key_index
    )

def make_family(key_index, parent1, parent2, children=None):
    return Family(
        parent1=parent1,
        parent2=parent2,
        children=children or [],
        key_index=key_index
    )

@pytest.fixture
def persons():
    # key_index: 1, 2, 3
    return [
        make_person(1, "John", "Smith", Sex.MALE),
        make_person(2, "Mary", "Smith", Sex.FEMALE),
        make_person(3, "Robert", "Smith", Sex.MALE),
    ]

@pytest.fixture
def families():
    # parent1=1 (John), parent2=2 (Mary), children=[3] (Robert)
    return [make_family(1, parent1=1, parent2=2, children=[3])]

class TestGenealogySearchAPI:
    def test_search_persons(self, persons, families):
        api = GenealogySearchAPI(persons, families)
        resp = api.search_persons("John", field="first_name", search_type="exact")
        assert resp.success
        assert any(p["person"]["first_name"] == "John" for p in resp.data)

    def test_find_relationship(self, persons, families):
        api = GenealogySearchAPI(persons, families)
        resp = api.find_relationship(1, 3)
        assert resp.success
        assert resp.data["relationship_type"] in {"parent", "child"}

    def test_statistics_report(self, persons, families):
        api = GenealogySearchAPI(persons, families)
        resp = api.get_statistics_report()
        assert resp.success
        assert resp.data["total_persons"] == 3
        assert resp.data["total_families"] == 1
