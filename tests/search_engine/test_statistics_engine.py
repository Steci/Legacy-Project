import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from search_engine.statistics_engine import StatisticsEngine
from models.person.person import Person
from models.family.family import Family
from models.person.params import Sex


from models.event import Event
from models.date import Date, DMY

def make_person(key_index, first_name, surname, sex=None, birth_year=None, death_year=None):
    birth_event = None
    death_event = None
    if birth_year:
        birth_event = Event(name="birth", date=Date(dmy=DMY(year=birth_year)))
    if death_year:
        death_event = Event(name="death", date=Date(dmy=DMY(year=death_year)))
    return Person(
        first_name=first_name,
        surname=surname,
        sex=sex if sex is not None else Sex.NEUTER,
        birth=birth_event,
        death=death_event,
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
        make_person(1, "John", "Smith", Sex.MALE, 1920, 1990),
        make_person(2, "Mary", "Smith", Sex.FEMALE, 1925, 2000),
        make_person(3, "Robert", "Smith", Sex.MALE, 1950, 2020),
    ]

@pytest.fixture
def families():
    # parent1=1 (John), parent2=2 (Mary), children=[3] (Robert)
    return [make_family(1, parent1=1, parent2=2, children=[3])]

class TestStatisticsEngine:
    def test_basic_report(self, persons, families):
        engine = StatisticsEngine(persons, families)
        report = engine.generate_comprehensive_report()
        assert report.total_persons == 3
        assert report.total_families == 1
        assert report.males == 2
        assert report.females == 1
        assert report.living_persons == 0
        assert report.deceased_persons == 3

    def test_name_statistics(self, persons, families):
        engine = StatisticsEngine(persons, families)
        stats = engine.analyze_name_popularity("first_name")
        names = [s.name for s in stats]
        assert "John" in names and "Mary" in names and "Robert" in names
