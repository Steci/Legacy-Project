import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from unittest.mock import mock_open, patch

import pytest
from parsers.gw.parser import GWParser
from parsers.gw.models import GWDatabase, Family, Person, NoteBlock, RelationBlock
from parsers.gw.utils import canonical_key_from_tokens

@pytest.fixture
def parser():
    return GWParser(debug=True)

def test_parse_file(parser):
    fake_data = "fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne"
    with patch("builtins.open", mock_open(read_data=fake_data)):
        db = parser.parse_file("mock_file.gw")
    assert isinstance(db, GWDatabase)
    assert len(db.families) == 1

def test_parse_text(parser):
    text = """
    fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne
    src Family source example
    comm Family comment example
    beg
    - h Corno Yann 1935 #bp Soisy 1997
    - f Thomas Marie_Julienne 0
    end
    """
    db = parser.parse_text(text)
    assert isinstance(db, GWDatabase)
    assert len(db.families) == 1
    assert db.families[0].husband == "CORNO Joseph_Marie_Vincent"
    assert db.families[0].wife == "THOMAS Marie_Julienne"

def test_parse_family_line(parser):
    raw = "fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne"
    toks = raw.split()
    family = parser._parse_family_line(raw, toks)
    assert isinstance(family, Family)
    assert family.husband == "CORNO Joseph_Marie_Vincent"
    assert family.wife == "THOMAS Marie_Julienne"

def test_parse_children_block(parser):
    lines = [
        "beg",
        "- h Corno Yann 1935 #bp Soisy 1997",
        "- f Thomas Marie_Julienne 0",
        "end"
    ]
    family = Family()
    i = parser._parse_children_block(0, lines, family)
    assert i == 4
    assert len(family.children) == 2
    assert family.children[0][1].last == "Corno"
    assert family.children[1][1].last == "Thomas"

def test_parse_child_line(parser):
    line = "- h Corno Yann 1935 #bp Soisy 1997"
    family = Family()
    gender, person, remaining = parser._parse_child_line(line, family)
    assert gender == "h"
    assert person.last == "Corno"
    assert person.first == "Yann"

def test_parse_notes_block(parser):
    lines = [
        "notes Corno Yann",
        "beg",
        "This is a note for Yann Corno.",
        "end"
    ]
    toks = lines[0].split()
    i = parser._parse_notes_block(0, lines, toks)
    assert i == 4
    assert len(parser.db.notes) == 1
    assert parser.db.notes[0].person_key == canonical_key_from_tokens(["Corno", "Yann"])
    assert "This is a note for Yann Corno." in parser.db.notes[0].text

def test_parse_relations_block(parser):
    lines = [
        "rel Corno Yann",
        "beg",
        "- godp: Martin Paul + Smith Jane",
        "end"
    ]
    toks = lines[0].split()
    i = parser._parse_relations_block(0, lines, toks)
    assert i == 4
    assert len(parser.db.relations) == 1
    assert parser.db.relations[0].person_key == canonical_key_from_tokens(["Corno", "Yann"])
    assert "- godp: Martin Paul + Smith Jane" in parser.db.relations[0].lines

def test_maybe_add_person(parser):
    raw = "Corno Yann 1935"
    parser._maybe_add_person(raw)
    assert len(parser.db.persons) == 1
    assert "Corno Yann" in parser.db.persons
