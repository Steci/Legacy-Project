from __future__ import annotations

import json
from pathlib import Path

from tools.regenerate_sosa_goldens import PROJECT_ROOT, regenerate_fixture

FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "sosa" / "first_cousin_large.json"


def test_regenerate_fixture_check_mode_reports_clean():
    assert regenerate_fixture(FIXTURE_PATH, check=True) is False


def test_regenerate_fixture_updates_outdated_file(tmp_path):
    copied = tmp_path / "first_cousin_large.json"
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["expected_numbers"]["Parent Alex"] = 999
    copied.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    changed = regenerate_fixture(copied, check=False)
    assert changed is True

    refreshed = json.loads(copied.read_text(encoding="utf-8"))
    assert refreshed["expected_numbers"]["Parent Alex"] == 2
