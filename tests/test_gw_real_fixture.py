import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from parsers.gw.loader import load_geneweb_file
from parsers.gw.canonical import canonicalize_gw


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "examples_files" / "example.gw"


def test_real_geneweb_fixture_refreshes_consanguinity():
    db = load_geneweb_file(str(FIXTURE_PATH))

    assert len(db.persons) == 2
    assert len(db.families) == 1

    warnings = db.consanguinity_warnings
    assert warnings != []
    assert "Thomas Marie_Julienne" in " ".join(warnings)

    thomas = db.persons.get("Thomas Marie_Julienne")
    assert thomas is not None
    assert thomas.consanguinity == pytest.approx(0.0)
    assert thomas.consanguinity_issue == "ancestral_loop"

    yann = db.persons.get("Corno Yann")
    assert yann is not None
    assert yann.consanguinity == pytest.approx(0.0)
    assert yann.consanguinity_issue is None

    canonical = canonicalize_gw(db)
    assert canonical.consanguinity_warnings
    canonical_thomas = next(p for p in canonical.persons if p.key == "Thomas Marie_Julienne")
    assert canonical_thomas.consanguinity == pytest.approx(0.0)
    assert canonical_thomas.consanguinity_issue == "ancestral_loop"
