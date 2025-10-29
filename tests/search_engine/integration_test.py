from __future__ import annotations

import importlib
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
from models.event import Event, Place  # type: ignore[import]
from models.family.family import Family  # type: ignore[import]
from models.person.params import PEventType, Sex  # type: ignore[import]
from models.person.person import Person  # type: ignore[import]


def _make_event(event_type: PEventType, *, year: int, town: str = "", country: str = "") -> Event:
    """Build a minimal event populated with an optional place."""

    place = Place(town=town, country=country) if town or country else None
    return Event(
        name=event_type.value,
        date=Date(dmy=DMY(year=year)),
        place=place,
    )


def _make_person(
    *,
    key_index: int,
    first_name: str,
    surname: str,
    sex: Sex,
    occupation: str | None = None,
    birth_year: int | None = None,
    birth_place: tuple[str, str] | None = None,
) -> Person:
    birth_event = None
    if birth_year is not None:
        town, country = birth_place or ("", "")
        birth_event = _make_event(
            PEventType.BIRTH,
            year=birth_year,
            town=town,
            country=country,
        )

    return Person(
        first_name=first_name,
        surname=surname,
        sex=sex,
        occupation=occupation,
        birth=birth_event,
        key_index=key_index,
    )


def _make_family(*, key_index: int, parent1: int, parent2: int, children: list[int]) -> Family:
    return Family(parent1=parent1, parent2=parent2, children=children, key_index=key_index)


@pytest.fixture
def sample_dataset() -> tuple[list[Person], list[Family]]:
    persons = [
        _make_person(
            key_index=1,
            first_name="John",
            surname="Smith",
            sex=Sex.MALE,
            occupation="Engineer",
            birth_year=1920,
            birth_place=("Edinburgh", "United Kingdom"),
        ),
        _make_person(
            key_index=2,
            first_name="Mary",
            surname="Smith",
            sex=Sex.FEMALE,
            occupation="Teacher",
            birth_year=1925,
            birth_place=("Edinburgh", "United Kingdom"),
        ),
        _make_person(
            key_index=3,
            first_name="Robert",
            surname="Smith",
            sex=Sex.MALE,
            occupation="Doctor",
            birth_year=1945,
            birth_place=("Glasgow", "United Kingdom"),
        ),
    ]

    families = [
        _make_family(key_index=1, parent1=1, parent2=2, children=[3]),
    ]

    return persons, families


def test_modules_are_importable() -> None:
    """The reorganised search-engine modules remain importable."""

    modules = [
        "search_engine.search_engine",
        "search_engine.relationship_search",
        "search_engine.statistics_engine",
        "search_engine.genealogy_search_api",
    ]

    for module in modules:
        importlib.import_module(module)


def test_search_engine_basic_queries(sample_dataset: tuple[list[Person], list[Family]]) -> None:
    persons, families = sample_dataset
    engine = SearchEngine(persons, families)

    exact_results = engine.simple_search("John", SearchField.FIRST_NAME, SearchType.EXACT)
    assert any(result.person.first_name == "John" for result in exact_results)

    fuzzy_results = engine.simple_search("Jon", SearchField.FIRST_NAME, SearchType.FUZZY)
    assert any(result.person.first_name == "John" for result in fuzzy_results)

    occupation_results = engine.simple_search("Doctor", SearchField.OCCUPATION, SearchType.EXACT)
    assert len(occupation_results) == 1
    assert occupation_results[0].person.first_name == "Robert"


def test_search_engine_advanced_and_logic(sample_dataset: tuple[list[Person], list[Family]]) -> None:
    persons, families = sample_dataset
    engine = SearchEngine(persons, families)

    criteria = AdvancedSearchCriteria(
        sex=Sex.MALE,
        birth_year_from=1940,
        birth_year_to=1950,
    )

    results = engine.advanced_search(criteria)
    assert len(results) == 1
    person = results[0].person
    assert person.first_name == "Robert"
    assert person.sex is Sex.MALE
    assert person.birth and person.birth.date and person.birth.date.dmy.year == 1945


def test_api_round_trip(sample_dataset: tuple[list[Person], list[Family]]) -> None:
    persons, families = sample_dataset
    api = GenealogySearchAPI(persons, families)

    search_response = api.search_persons("Smith", field="surname", search_type="exact")
    assert search_response.success
    assert search_response.data and len(search_response.data) == 3

    relationship_response = api.find_relationship(1, 3)
    assert relationship_response.success
    assert relationship_response.data is not None
    assert relationship_response.data["relationship_type"] in {"parent", "child"}

    stats_response = api.get_statistics_report()
    assert stats_response.success
    assert stats_response.data["total_persons"] == 3
    assert stats_response.data["total_families"] == 1
