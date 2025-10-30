# Unit Test Technical Document — Legacy Project

This document explains how to structure, run, and extend the pytest-based test suite for the Python rewrite of the Legacy Project.

Tests are organized into sub-packages under `tests/` (e.g., `tests/consang/`, `tests/parsers/`) to mirror the source tree in `src/` and keep fixtures close to the code they exercise.

---

## Test Structure

* **Consanguinity tests** (`tests/consang/`):
  Cover the domain logic, cousin-degree calculations, CLI commands, and helper functions.

* **Parser tests** (`tests/parsers/`):
  Include GeneWeb/GED parsing, exporters, regression fixtures, and functional pipelines.

* **Database tests** (`tests/db/`):
  Validate the Pythonized storage layer (`DiskStorage`, database operations, serialization/deserialization).

* **Search engine tests** (`tests/search_engine/`):
  Cover search functionality, API behavior, and statistics.

* **Sosa tests** (`tests/sosa/`):
  Test caching, branch calculation, CLI integration, and formatter output.

---

## Prerequisites

Make sure the following are installed:

* Python 3.12 or later
* `pytest`
* `pytest-mock` (for mocking functionality)

Install dependencies via pip:

```bash
pip install pytest pytest-mock
```

---

## Running the Tests

### Run the full test suite

From the root of the project:

```bash
PYTHONPATH=$(pwd)/src pytest tests --cov=src --cov-report=term-missing -v
```

* `PYTHONPATH=$(pwd)/src` ensures Python can find the source modules.
* `--cov=src` collects coverage.
* `--cov-report=term-missing` shows lines not covered.
* `-v` provides verbose output.

### Run a specific test file

```bash
PYTHONPATH=$(pwd)/src pytest tests/consang/test_cousin_degree.py -v
```

### Run a specific test function

Use the `-k` option with a keyword matching the test name:

```bash
PYTHONPATH=$(pwd)/src pytest -k test_parse_family_normal_case -v
```

---

## Writing New Tests

When adding new tests:

1. **File location:** Place them alongside the feature they cover. Example:

   * Domain logic → `tests/consang/`
   * Parser → `tests/parsers/gw/`

2. **Test naming:** Use descriptive names that clearly indicate what the test validates.
   Example: `test_load_non_dict_pickle_triggers_warning`.

3. **Docstrings:** Include a brief docstring explaining the purpose of each test.

4. **Fixtures & assertions:** Follow pytest conventions. Use `capsys` to capture stdout if needed.

5. **Coverage:** Ensure all branches of the code are tested.

---

## Debugging Test Failures

* Pytest output shows the assertion failure with expected vs. actual values.
* Use `print()` or `capsys` in tests for debugging.
* Check for edge cases such as empty files, corrupted data, or unexpected types (important for storage/database tests).

---

## Contribution Guidelines

* All tests must pass before submitting code.
* Add tests for new functionality or bug fixes.
* Keep test names and descriptions clear and concise.
* Avoid side effects: tests should clean up temporary files or mock external dependencies.

---

## Golden Fixtures (Cousin-Degree)

The cousin-degree feature uses **golden fixtures** stored in `tests/fixtures/consang/`.

To regenerate:

```bash
PYTHONPATH=$(pwd)/src python tools/regenerate_cousin_goldens.py
```

To add or update JSON scenarios:

1. Edit `tests/fixtures/consang/cousin_degrees/*.json`
2. Run the targeted tests:

```bash
PYTHONPATH=$(pwd)/src pytest tests/consang/test_cousin_degree.py
```

---

## Example: Covering DiskStorage Edge Cases

For instance, to cover `DiskStorage.load()` when the pickle file exists but contains a **non-dict**, you could write:

```python
import tempfile
import pickle
from src.db.disk_storage import DiskStorage

def test_load_non_dict_pickle_triggers_warning(capsys):
    """DiskStorage should reset data when a non-dict pickle is loaded"""
    with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
        pickle.dump([1, 2, 3], tmp)
        tmp.flush()
        filepath = tmp.name

    storage = DiskStorage(filepath)
    storage.load()
    captured = capsys.readouterr()
    assert "contained invalid data" in captured.out
    assert storage.data == {}
```

This ensures **all branches in `disk_storage.py` are tested**, including the warning print.

---

## Notes

* Functional tests verify the Python rewrite against original COBOL logic.
* Mocking is used to simulate I/O or external dependencies where necessary.
* Always validate that regenerated fixtures produce consistent results.

---

This document is now **fully adapted** to your current project context, directory structure, and `PYTHONPATH`-based test execution.
