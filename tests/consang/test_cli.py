from __future__ import annotations

from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "consang"


def _run_cli(args):
    module = __import__("consang.__main__", fromlist=["run"])
    return module.run(args)


def test_cli_relationship_output(capsys):
    gw_path = FIXTURE_DIR / "first_cousin_large.gw"

    exit_code = _run_cli(
        [
            str(gw_path),
            "--scratch",
            "--relationship",
            "Cousin Adam",
            "Cousin Bella",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()

    expected_output = (FIXTURE_DIR / "first_cousin_large_cli.txt").read_text(encoding="utf-8").strip()
    assert captured.out.strip() == expected_output
