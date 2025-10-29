# Tests for Legacy Project

This directory hosts the pytest suite for the Python rewrite. Tests now live in
sub-packages (for example `consang/` and `parsers/`) so they mirror the source
tree and keep fixtures close to the scenarios they exercise.

## Test Structure

- **Consanguinity tests**: Under `consang/`, focus on the domain calculator, CLI,
	and cousin-degree helpers.
- **Parser tests**: Under `parsers/`, cover GeneWeb/GED parsing, exporter
	pipelines, and regression fixtures.

## Prerequisites

Before running the tests, ensure the following dependencies are installed:

- Python 3.12 or later
- `pytest`
- `pytest-mock` (for mocking functionality)

You can install the required dependencies using:

```bash
pip install pytest pytest-mock
```

## Running the Tests

To run the tests, navigate to the root directory of the project and use the following command:
```bash
PYTHONPATH=$(pwd)/src pytest tests
```

This command sets the PYTHONPATH to include the src directory, allowing Python to locate the modules correctly.

Running Specific Test Files

Running a Specific Test

To run a specific test, use the -k option with a keyword matching the test name. For example:
```bash
PYTHONPATH=$(pwd)/src pytest -k test_parse_family_normal_case
```

## Writing New Tests

### When adding new tests:

1. Place unit tests alongside the feature they cover (e.g. `tests/consang/` or
	`tests/parsers/gw/`).
2. Use descriptive test names that clearly indicate the purpose of the test.
3. Include a docstring in each test to explain what it validates.
4. Follow pytest conventions for fixtures and assertions.

### Debugging Test Failures

If a test fails, pytest will display detailed output, including the assertion that failed and the expected vs. actual values. Use this information to debug the issue.

### Contribution Guidelines

- Ensure all tests pass before submitting changes.
- Add tests for any new functionality or bug fixes.
- Maintain clear and concise test descriptions.

### Additional Notes

- The functional tests are designed to validate the Python implementation against the original COBOL logic. If discrepancies are found, ensure the Python implementation aligns with the business rules defined in the COBOL program.
- Mocking is used in some tests to simulate file input/output and other external dependencies.


## Regenerating golden fixtures

The cousin-degree feature stores CLI and JSON goldens under
`tests/fixtures/consang/`. Regenerate them with:

```bash
PYTHONPATH=$(pwd)/src python tools/regenerate_cousin_goldens.py
```

Add or update JSON scenarios in
`tests/fixtures/consang/cousin_degrees/simple_cases.json`, then run the
targeted tests:

```bash
PYTHONPATH=$(pwd)/src pytest tests/consang/test_cousin_degree.py
```

For any questions or issues, please contact the project maintainers.

