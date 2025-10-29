from __future__ import annotations

import json
from pathlib import Path

from consang.__main__ import run
from parsers.gw.loader import load_geneweb_file


BASE_DIR = Path(__file__).resolve().parents[2]
GOLDEN_PATH = BASE_DIR / "tests" / "fixtures" / "sosa" / "first_cousin_large.json"


def _load_golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_cli_with_sosa_outputs_navigation(monkeypatch, capsys):
    golden = _load_golden()
    source_path = BASE_DIR / golden["source"]
    database = load_geneweb_file(str(source_path), compute_consanguinity=True)
    key_to_index = database.relationship_key_to_index

    root_id = key_to_index[golden["root_key"]]
    monkeypatch.setenv("SOSA_ROOT", str(root_id))

    exit_code = run([str(source_path), "--with-sosa", "--quiet"])
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Sosa navigation" in captured.out
