import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from parsers.gw.parser import GWParser
from parsers.gw.models import GWDatabase

@pytest.fixture
def parser():
    """Fixture to initialize the GWParser with debug mode enabled."""
    return GWParser(debug=True)

def test_parse_family_normal_case(parser):
    """
    Validate that a family line is correctly parsed into a Family object.
    Business Rule: A family line should create a Family object with the correct husband and wife names.
    """
    input_data = "fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne"
    db = parser.parse_text(input_data)
    
    assert len(db.families) == 1, "Expected one family to be parsed"
    family = db.families[0]
    assert family.husband == "CORNO Joseph_Marie_Vincent", "Husband name mismatch"
    assert family.wife == "THOMAS Marie_Julienne", "Wife name mismatch"

def test_parse_family_empty_input(parser):
    """
    Validate behavior when input is empty.
    Business Rule: Empty input should result in an empty database.
    """
    input_data = ""
    db = parser.parse_text(input_data)
    
    assert len(db.families) == 0, "Expected no families to be parsed"

def test_parse_family_invalid_format(parser):
    """
    Validate behavior when input has an invalid format.
    Business Rule: Invalid family lines should be ignored.
    """
    input_data = "invalid data line"
    db = parser.parse_text(input_data)
    
    assert len(db.families) == 0, "Expected no families to be parsed from invalid input"

def test_parse_children_block_normal_case(parser):
    """
    Validate that a children block is correctly parsed into child objects.
    Business Rule: A children block should create child objects with correct attributes.
    """
    input_data = """
    fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne
    beg
    - h Corno Yann 1935 #bp Soisy 1997
    - f Thomas Marie_Julienne 0
    end
    """
    db = parser.parse_text(input_data)
    
    assert len(db.families) == 1, "Expected one family to be parsed"
    family = db.families[0]
    assert len(family.children) == 2, "Expected two children to be parsed"
    assert family.children[0][1].surname == "Corno", "First child's last name mismatch"
    assert family.children[0][1].first_name == "Yann", "First child's first name mismatch"
    assert family.children[1][1].surname == "Thomas", "Second child's last name mismatch"
    assert family.children[1][1].first_name == "Marie_Julienne", "Second child's first name mismatch"

def test_parse_notes_block(parser):
    """
    Validate that a notes block is correctly parsed into a NoteBlock object.
    Business Rule: Notes should be associated with the correct person.
    """
    input_data = """
    notes Corno Yann
    beg
    This is a note for Yann Corno.
    end
    """
    db = parser.parse_text(input_data)
    
    assert len(db.notes) == 1, "Expected one note to be parsed"
    note = db.notes[0]
    assert note.person_key == "Corno Yann", "Note person key mismatch"
    assert "This is a note for Yann Corno." in note.text, "Note text mismatch"

def test_parse_relations_block(parser):
    """
    Validate that a relations block is correctly parsed into a RelationBlock object.
    Business Rule: Relations should be associated with the correct person and include all specified lines.
    """
    input_data = """
    rel Corno Yann
    beg
    - godp: Martin Paul + Smith Jane
    end
    """
    db = parser.parse_text(input_data)

    assert len(db.relations) == 1, "Expected one relation to be parsed"
    relation = db.relations[0]
    assert relation.person_key == "Corno Yann", "Relation person key mismatch"
    assert "- godp: Martin Paul + Smith Jane" in [line.strip() for line in relation.lines], "Relation line mismatch"

def test_parse_file_with_realistic_data(parser, mocker):
    """
    Validate that a file with realistic data is parsed correctly.
    Business Rule: The parser should handle a complete file and produce a valid database.
    """
    mock_data = """
    fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne
    beg
    - h Corno Yann 1935 #bp Soisy 1997
    - f Thomas Marie_Julienne 0
    end
    notes Corno Yann
    beg
    This is a note for Yann Corno.
    end
    rel Corno Yann
    beg
    - godp: Martin Paul + Smith Jane
    end
    """
    mocker.patch("builtins.open", mocker.mock_open(read_data=mock_data))
    db = parser.parse_file("mock_file.gw")

    assert isinstance(db, GWDatabase), "Expected the result to be a GWDatabase object"
    assert len(db.families) == 1, "Expected one family to be parsed"
    assert len(db.notes) == 1, "Expected one note to be parsed"
    assert len(db.relations) == 1, "Expected one relation to be parsed"

def test_parse_text_with_boundary_values(parser):
    """
    Validate behavior with boundary values for input data.
    Business Rule: The parser should handle maximum and minimum input sizes gracefully.
    """
    max_input = "fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne\n" * 1000
    db = parser.parse_text(max_input)
    assert len(db.families) == 1000, "Expected 1000 families to be parsed"

    parser.reset()

    min_input = ""
    db = parser.parse_text(min_input)
    assert len(db.families) == 0, "Expected no families to be parsed"
