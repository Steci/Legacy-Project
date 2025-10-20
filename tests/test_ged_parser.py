import os
import sys
from textwrap import dedent

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from parsers.ged.parser import GedcomParser
from models.person.params import Sex


def parse_ged(text: str):
    parser = GedcomParser()
    return parser.parse_content(text)


class TestHeaderParsing:
    def test_header_fields_and_notes_db(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 SOUR SampleSource
            1 DATE 01 JAN 2000
            1 CHAR UTF-8
            1 NOTE Title line
            2 CONT 
            2 CONT Another line
            0 TRLR
            """
        )

        database = parse_ged(ged_text)

        assert database.header["charset"] == "UTF-8"
        assert database.header["source"] == "SampleSource"
        assert database.header["date"] == "01 JAN 2000"
        assert database.header["notes_db"] == "Title line<br>\n<br>\nAnother line"


class TestIndividualParsing:
    def test_individual_events_and_notes(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 CHAR UTF-8
            0 @I1@ INDI
            1 NAME John /Doe/
            1 SEX M
            1 BIRT
            2 DATE 01 JAN 1980
            2 PLAC Exampletown
            1 BAPM
            2 DATE 05 FEB 1980
            2 PLAC Examplechurch
            1 DEAT
            2 DATE 2010
            2 PLAC Exampletown
            1 NOTE First line
            2 CONT 
            2 CONC continues here
            0 TRLR
            """
        )

        database = parse_ged(ged_text)
        person = database.individuals["@I1@"]

        assert person.first_name == "John"
        assert person.surname == "Doe"
        assert person.sex is Sex.MALE

        assert person.birth and person.birth.date and person.birth.date.dmy.year == 1980
        assert person.birth.date.dmy.month == 1
        assert person.birth.date.dmy.day == 1
        assert person.birth.place and person.birth.place.other == "Exampletown"

        assert person.baptism and person.baptism.date and person.baptism.date.dmy.month == 2
        assert person.baptism.place and person.baptism.place.other == "Examplechurch"

        assert person.death and person.death.date and person.death.date.dmy.year == 2010
        assert person.death.place and person.death.place.other == "Exampletown"

        assert person.notes == "First line<br>\ncontinues here"


class TestFamilyParsing:
    def test_family_members_events_and_notes(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 CHAR UTF-8
            0 @I1@ INDI
            1 NAME John /Doe/
            1 SEX M
            1 FAMS @F1@
            0 @I2@ INDI
            1 NAME Jane /Smith/
            1 SEX F
            1 FAMS @F1@
            0 @I3@ INDI
            1 NAME Junior /Doe/
            1 SEX M
            1 FAMC @F1@
            1 SOUR Child Source
            0 @F1@ FAM
            1 HUSB @I1@
            1 WIFE @I2@
            1 CHIL @I3@
            1 MARR
            2 DATE 12 DEC 2000
            2 PLAC Some Place
            1 NOTE Family line
            2 CONT More details
            0 TRLR
            """
        )

        database = parse_ged(ged_text)
        family = database.families["@F1@"]

        assert family.husband_id == "@I1@"
        assert family.wife_id == "@I2@"
        assert family.children_ids == ["@I3@"]

        assert family.marriage and family.marriage.date and family.marriage.date.dmy.year == 2000
        assert family.marriage.date.dmy.month == 12
        assert family.marriage.date.dmy.day == 12
        assert family.marriage.place and family.marriage.place.other == "Some Place"

        assert family.notes == "Family line<br>\nMore details"

        child = database.individuals["@I3@"]
        assert child.psources == "Child Source"


class TestNoteAndSourceAggregation:
    def test_person_note_reference_and_sources(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 CHAR UTF-8
            0 @N1@ NOTE
            1 CONT Referenced note line
            0 @S1@ SOUR Main Source
            1 NOTE Source note line
            0 @I1@ INDI
            1 NAME Alice /Smith/
            1 NOTE @N1@
            1 NOTE Inline section
            2 CONT 
            2 CONC continues
            1 SOUR @S1@
            1 BIRT
            2 DATE 01 JAN 2000
            2 SOUR @S1@
            0 TRLR
            """
        )

        database = parse_ged(ged_text)
        person = database.individuals["@I1@"]

        assert person.psources == "Main Source"
        assert "Referenced note line" in (person.notes or "")
        assert "Inline section<br>" in (person.notes or "")
        assert "continues" in (person.notes or "")
        assert "Source note line" in (person.notes or "")


class TestAliasesAndRelationships:
    def test_aliases_occupations_and_family_links(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 CHAR UTF-8
            0 @I1@ INDI
            1 NAME Primary /Name/
            1 NAME Alias /Name/
            1 OCCU Carpenter
            1 OCCU Farmer
            1 FAMS @F1@
            1 FAMC @F2@
            0 TRLR
            """
        )

        database = parse_ged(ged_text)
        person = database.individuals["@I1@"]

        assert person.first_name == "Primary"
        assert person.aliases == ["Alias /Name/"]
        assert person.occupation == "Carpenter, Farmer"
        assert person.families_as_spouse == ["@F1@"]
        assert person.families_as_child == ["@F2@"]


class TestSpecialRelationships:
    def test_adoption_and_witnesses(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 CHAR UTF-8
            0 @I1@ INDI
            1 NAME Child /Person/
            1 BAPM
            2 DATE 01 JAN 2000
            2 ASSO @I2@
            3 RELA godfather
            2 ASSO @I6@
            3 RELA witness
            1 ADOP
            2 FAMC @F1@
            3 ADOP HUSB
            1 FAMC @F1@
            2 PEDI adopted
            0 @I2@ INDI
            1 NAME Sponsor /Person/
            0 @I3@ INDI
            1 NAME Parent /One/
            1 SEX M
            1 FAMS @F1@
            0 @I4@ INDI
            1 NAME Parent /Two/
            1 SEX F
            1 FAMS @F1@
            0 @I5@ INDI
            1 NAME FamilyWitness /One/
            0 @I6@ INDI
            1 NAME EventWitness /Two/
            0 @F1@ FAM
            1 HUSB @I3@
            1 WIFE @I4@
            1 CHIL @I1@
            1 MARR
            2 DATE 02 FEB 1999
            2 ASSO @I5@
            3 RELA witness
            0 TRLR
            """
        )

        database = parse_ged(ged_text)

        child = database.individuals["@I1@"]
        assert child.godparents.count("@I2@") >= 1
        assert child.adoption_families == ["@F1@"]
        assert child.adoption_details["@F1@"] == "BOTH"
        assert child.families_as_child == ["@F1@"]
        assert any(
            record["witness"] == "@I6@" and record["event"] == "BAPM"
            for record in child.witnesses
        )

        family = database.families["@F1@"]
        assert any(
            entry["witness"] == "@I5@" and entry["event"] == "MARR"
            for entry in family.witnesses
        )
        assert family.adoption_notes["@I1@"] == "BOTH"


class TestFamilyEventHandling:
    def test_divorce_sets_relation_and_custom_events(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 CHAR UTF-8
            0 @S1@ SOUR
            1 TITL Divorce Records
            0 @I1@ INDI
            1 NAME Alex /Doe/
            1 SEX M
            1 FAMS @F1@
            0 @I2@ INDI
            1 NAME Casey /Roe/
            1 SEX F
            1 FAMS @F1@
            0 @I3@ INDI
            1 NAME Witness /One/
            0 @F1@ FAM
            1 HUSB @I1@
            1 WIFE @I2@
            1 DIV
            2 DATE 03 MAR 2003
            2 PLAC County Court
            2 ASSO @I3@
            3 RELA witness
            1 EVEN Trial Details
            2 TYPE Court
            2 NOTE Hearing note
            2 SOUR @S1@
            0 TRLR
            """
        )

        database = parse_ged(ged_text)

        family = database.families["@F1@"]
        assert family.divorce and family.divorce.date and family.divorce.date.dmy.year == 2003
        assert family.divorce.place and family.divorce.place.other == "County Court"
        assert family.divorce.name.upper() == "DIV"
        assert any(
            witness["witness"] == "@I3@" and witness["event"] == "DIV"
            for witness in family.witnesses
        )

        court_event = next(
            evt for evt in family.events if (evt.name or "").upper() == "COURT"
        )
        assert "Trial Details" in (court_event.note or "")
        assert "Hearing note" in (court_event.note or "")
        assert "Divorce Records" in (getattr(court_event, "source_notes", "") or "")


class TestPersonalEventVariants:
    def test_residence_flag_and_custom_event_type(self):
        ged_text = dedent(
            """\
            0 HEAD
            1 CHAR UTF-8
            0 @S1@ SOUR
            1 TITL Military Service Files
            0 @I1@ INDI
            1 NAME Pat /Taylor/
            1 RESI Y
            1 EVEN
            2 TYPE Military Service
            2 DATE 10 OCT 1990
            2 PLAC Fort Base
            2 NOTE Served overseas
            2 SOUR @S1@
            0 TRLR
            """
        )

        database = parse_ged(ged_text)
        person = database.individuals["@I1@"]

        residence_event = next(
            evt for evt in person.events if (evt.name or "") == "RESI"
        )
        assert residence_event and (residence_event.note or "") == ""

        custom_event = next(
            evt for evt in person.events if (evt.name or "") == "Military Service"
        )
        assert custom_event.place and custom_event.place.other == "Fort Base"
        assert custom_event.date and custom_event.date.dmy.year == 1990
        assert "Military Service Files" in (getattr(custom_event, "source_notes", "") or "")
        assert "Served overseas" in (custom_event.note or "")

