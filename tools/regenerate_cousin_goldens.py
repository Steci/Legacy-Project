from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from consang.__main__ import run as consang_cli

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "consang"


def regenerate_first_cousin_cli() -> None:
    target = FIXTURE_ROOT / "first_cousin_large_cli.txt"
    gw_path = FIXTURE_ROOT / "first_cousin_large.gw"

    buffer = io.StringIO()
    errors = io.StringIO()

    exit_code: int
    with redirect_stdout(buffer), redirect_stderr(errors):
        exit_code = consang_cli(
            [
                str(gw_path),
                "--scratch",
                "--relationship",
                "Cousin Adam",
                "Cousin Bella",
            ]
        )

    if exit_code != 0:
        raise SystemExit(
            f"consang CLI returned exit code {exit_code}\n" f"stderr:\n{errors.getvalue()}"
        )

    target.write_text(buffer.getvalue().strip() + "\n", encoding="utf-8")


def main() -> None:
    regenerate_first_cousin_cli()
    print("Regenerated consang CLI goldens.")


if __name__ == "__main__":
    main()
