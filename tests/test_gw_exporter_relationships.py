import os
import sys

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")),
)

from consang.relationship import BranchPath, RelationshipSummary  # type: ignore[import]
from parsers.ged.models import GedcomDatabase, GedcomFamily, GedcomPerson  # type: ignore[import]
from parsers.gw.exporter import GenewebExporter  # type: ignore[import]


def _build_minimal_gedcom_database():
    database = GedcomDatabase()

    husband = GedcomPerson(xref_id="@I1@", first_name="John", surname="Smith")
    wife = GedcomPerson(xref_id="@I2@", first_name="Jane", surname="Doe")

    database.individuals = {
        husband.xref_id: husband,
        wife.xref_id: wife,
    }

    family = GedcomFamily(xref_id="@F1@")
    family.husband_id = husband.xref_id
    family.wife_id = wife.xref_id
    database.families = {family.xref_id: family}

    return database


def test_geneweb_exporter_emits_relationship_blocks():
    database = _build_minimal_gedcom_database()

    summary = RelationshipSummary(
        person_a="Smith John",
        person_b="Doe Jane",
        coefficient=0.125,
        ancestors=("Ancestor One",),
        paths_to_a={
            "Ancestor One": (
                BranchPath(length=1, multiplicity=1, path=("Ancestor One", "Smith John")),
            )
        },
        paths_to_b={
            "Ancestor One": (
                BranchPath(length=1, multiplicity=1, path=("Ancestor One", "Doe Jane")),
            )
        },
    )

    exporter = GenewebExporter()
    output = exporter.export(
        database,
        relationship_summaries={("Smith John", "Doe Jane"): summary},
    )

    expected_output = (
        "encoding: utf-8\n"
        "gwplus\n\n"
        "fam Smith John 0 + Doe Jane 0\n\n"
        "rel Doe Jane\n"
        "beg\n"
        "- rel: Smith John coef=0.125000\n"
        "  ancestor: Ancestor One\n"
        "    self-path: length=1 mult=1 route=Ancestor One -> Doe Jane\n"
        "    other-path: length=1 mult=1 route=Ancestor One -> Smith John\n"
        "end\n\n"
        "rel Smith John\n"
        "beg\n"
        "- rel: Doe Jane coef=0.125000\n"
        "  ancestor: Ancestor One\n"
        "    self-path: length=1 mult=1 route=Ancestor One -> Smith John\n"
        "    other-path: length=1 mult=1 route=Ancestor One -> Doe Jane\n"
        "end\n"
    )

    assert output == expected_output
