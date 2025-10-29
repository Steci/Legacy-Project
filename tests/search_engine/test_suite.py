from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (PROJECT_ROOT, SRC_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from search_engine.search_engine import (  # type: ignore[import]
    AdvancedSearchCriteria,
    SearchEngine,
    SearchField,
    SearchType,
)
from search_engine.genealogy_search_api import GenealogySearchAPI  # type: ignore[import]
from models.date import Date, DMY  # type: ignore[import]
from models.event import Event  # type: ignore[import]
from models.family.family import Family  # type: ignore[import]
from models.person.params import PEventType, Sex  # type: ignore[import]
from models.person.person import Person  # type: ignore[import]


def _person(
    *,
    key_index: int,
    first_name: str,
    surname: str,
    sex: Sex,
    occupation: str,
    birth_year: int,
) -> Person:
    birth_event = Event(
        name=PEventType.BIRTH.value,
        date=Date(dmy=DMY(year=birth_year)),
    )
    return Person(
        first_name=first_name,
        surname=surname,
        sex=sex,
        occupation=occupation,
        birth=birth_event,
        key_index=key_index,
    )


def _family(*, key_index: int, parent1: int, parent2: int, children: list[int]) -> Family:
    return Family(parent1=parent1, parent2=parent2, children=children, key_index=key_index)


@pytest.fixture
def dataset() -> tuple[list[Person], list[Family]]:
    persons = [
        _person(key_index=1, first_name="John", surname="Smith", sex=Sex.MALE, occupation="Engineer", birth_year=1920),
        _person(key_index=2, first_name="Mary", surname="Smith", sex=Sex.FEMALE, occupation="Teacher", birth_year=1925),
        _person(key_index=3, first_name="Robert", surname="Johnson", sex=Sex.MALE, occupation="Doctor", birth_year=1935),
        _person(key_index=4, first_name="Patricia", surname="Jones", sex=Sex.FEMALE, occupation="Nurse", birth_year=1945),
        _person(key_index=5, first_name="James", surname="Brown", sex=Sex.MALE, occupation="Lawyer", birth_year=1950),
        _person(key_index=6, first_name="Michael", surname="Davis", sex=Sex.MALE, occupation="Farmer", birth_year=1885),
    ]

    families = [
        _family(key_index=1, parent1=1, parent2=2, children=[3, 4]),
        _family(key_index=2, parent1=3, parent2=4, children=[5]),
    ]

    return persons, families


def test_basic_exact_search(dataset: tuple[list[Person], list[Family]]) -> None:
    persons, families = dataset
    engine = SearchEngine(persons, families)

    results = engine.simple_search("John", SearchField.FIRST_NAME, SearchType.EXACT)
    assert len(results) == 1
    assert results[0].person.first_name == "John"


def test_fuzzy_first_name_lookup(dataset: tuple[list[Person], list[Family]]) -> None:
    persons, families = dataset
    engine = SearchEngine(persons, families)

    results = engine.simple_search("Jon", SearchField.FIRST_NAME, SearchType.FUZZY)
    assert any(result.person.first_name == "John" for result in results)


def test_advanced_search_filters_all_criteria(dataset: tuple[list[Person], list[Family]]) -> None:
    persons, families = dataset
    engine = SearchEngine(persons, families)

    criteria = AdvancedSearchCriteria(
        sex=Sex.MALE,
        birth_year_from=1940,
        birth_year_to=1950,
    )

    results = engine.advanced_search(criteria)
    assert len(results) == 1
    person = results[0].person
    assert person.first_name == "James"
    assert person.sex is Sex.MALE
    assert person.birth and person.birth.date and person.birth.date.dmy.year == 1950


def test_api_searches_use_indexes(dataset: tuple[list[Person], list[Family]]) -> None:
    persons, families = dataset
    api = GenealogySearchAPI(persons, families)

    surname_results = api.search_persons("Smith", field="surname", search_type="exact")
    assert surname_results.success
    assert surname_results.data and len(surname_results.data) == 2

    occupation_results = api.search_persons("Lawyer", field="occupation", search_type="exact")
    assert occupation_results.success
    assert occupation_results.data and occupation_results.data[0]["person"]["first_name"] == "James"
