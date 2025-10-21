import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("src"))

from models.family.family import RelationKind  # type: ignore[import-not-found]
from models.person.params import Sex as PersonSex  # type: ignore[import-not-found]
from parsers.ged.conversion import convert_legacy_database  # type: ignore[import-not-found]
from parsers.ged.models import GedcomDatabase, GedcomFamily, GedcomPerson  # type: ignore[import-not-found]
from parsers.ged.refresh import refresh_consanguinity  # type: ignore[import-not-found]


def _build_inbred_database() -> GedcomDatabase:
    db = GedcomDatabase()

    grand_father = GedcomPerson(xref_id="I1", first_name="Alan", surname="Ancestor", sex=PersonSex.MALE)
    grand_mother = GedcomPerson(xref_id="I2", first_name="Alice", surname="Ancestor", sex=PersonSex.FEMALE)
    father = GedcomPerson(xref_id="I3", first_name="Bernard", surname="Ancestor", sex=PersonSex.MALE)
    mother = GedcomPerson(xref_id="I4", first_name="Beatrice", surname="Ancestor", sex=PersonSex.FEMALE)
    child = GedcomPerson(xref_id="I5", first_name="Charles", surname="Ancestor", sex=PersonSex.MALE)

    grand_father.families_as_spouse = ["F1"]
    grand_mother.families_as_spouse = ["F1"]

    father.families_as_child = ["F1"]
    father.families_as_spouse = ["F2"]
    mother.families_as_child = ["F1"]
    mother.families_as_spouse = ["F2"]
    child.families_as_child = ["F2"]

    db.individuals = {
        person.xref_id: person
        for person in (grand_father, grand_mother, father, mother, child)
    }

    family_one = GedcomFamily(xref_id="F1")
    family_one.husband_id = "I1"
    family_one.wife_id = "I2"
    family_one.children_ids = ["I3", "I4"]
    family_one.relation = RelationKind.MARRIED

    family_two = GedcomFamily(xref_id="F2")
    family_two.husband_id = "I3"
    family_two.wife_id = "I4"
    family_two.children_ids = ["I5"]
    family_two.relation = RelationKind.MARRIED

    db.families = {
        family_one.xref_id: family_one,
        family_two.xref_id: family_two,
    }

    return db


def test_conversion_is_pure_by_default():
    database = _build_inbred_database()

    parsed = convert_legacy_database(database)

    child = parsed.individuals["I5"]
    assert child.consanguinity == pytest.approx(0.0)
    assert parsed.consanguinity_warnings == []
    assert parsed.consanguinity_errors == []


def test_refresh_consanguinity_computes_coefficients():
    database = _build_inbred_database()

    parsed = convert_legacy_database(database)
    refresh_consanguinity(parsed)

    child = parsed.individuals["I5"]
    assert pytest.approx(0.25, rel=1e-9, abs=1e-9) == child.consanguinity
    assert parsed.consanguinity_warnings == []


def test_conversion_can_opt_in_to_consanguinity():
    database = _build_inbred_database()

    parsed = convert_legacy_database(database, compute_consanguinity=True)

    child = parsed.individuals["I5"]
    assert pytest.approx(0.25, rel=1e-9, abs=1e-9) == child.consanguinity
    assert parsed.consanguinity_warnings == []
