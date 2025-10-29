from __future__ import annotations

from unittest.mock import mock_open

import pytest

from parsers.gw.models import GWDatabase
from parsers.gw.parser import GWParser


@pytest.fixture()
def parser() -> GWParser:
    return GWParser(debug=True)


def test_parse_family_normal_case(parser: GWParser) -> None:
    input_data = "fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne"
    db = parser.parse_text(input_data)

    assert len(db.families) == 1
    family = db.families[0]
    assert family.husband == "CORNO Joseph_Marie_Vincent"
    assert family.wife == "THOMAS Marie_Julienne"


def test_parse_family_empty_input(parser: GWParser) -> None:
    db = parser.parse_text("")

    assert len(db.families) == 0


def test_parse_family_invalid_format(parser: GWParser) -> None:
    db = parser.parse_text("invalid data line")

    assert len(db.families) == 0


def test_parse_children_block_normal_case(parser: GWParser) -> None:
    input_data = """
    fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne
    beg
    - h Corno Yann 1935 #bp Soisy 1997
    - f Thomas Marie_Julienne 0
    end
    """
    db = parser.parse_text(input_data)

    assert len(db.families) == 1
    family = db.families[0]
    assert len(family.children) == 2
    assert family.children[0][1].surname == "Corno"
    assert family.children[0][1].first_name == "Yann"
    assert family.children[1][1].surname == "Thomas"
    assert family.children[1][1].first_name == "Marie_Julienne"


def test_parse_notes_block(parser: GWParser) -> None:
    input_data = """
    notes Corno Yann
    beg
    This is a note for Yann Corno.
    end
    """
    db = parser.parse_text(input_data)

    assert len(db.notes) == 1
    note = db.notes[0]
    assert note.person_key == "Corno Yann"
    assert "This is a note for Yann Corno." in note.text


def test_parse_relations_block(parser: GWParser) -> None:
    input_data = """
    rel Corno Yann
    beg
    - godp: Martin Paul + Smith Jane
    end
    """
    db = parser.parse_text(input_data)

    assert len(db.relations) == 1
    relation = db.relations[0]
    assert relation.person_key == "Corno Yann"
    assert any(line.strip() == "- godp: Martin Paul + Smith Jane" for line in relation.lines)


def test_parse_file_with_realistic_data(parser: GWParser, monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr("builtins.open", mock_open(read_data=mock_data))
    db = parser.parse_file("mock_file.gw")

    assert isinstance(db, GWDatabase)
    assert len(db.families) == 1
    assert len(db.notes) == 1
    assert len(db.relations) == 1


def test_parse_text_with_boundary_values(parser: GWParser) -> None:
    max_input = "fam CORNO Joseph_Marie_Vincent + THOMAS Marie_Julienne\n" * 1000
    db = parser.parse_text(max_input)
    assert len(db.families) == 1000

    parser.reset()

    min_input = ""
    db = parser.parse_text(min_input)
    assert len(db.families) == 0
