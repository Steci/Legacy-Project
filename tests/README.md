# Tests for Legacy Project

This directory contains all the test files for the Legacy Project. The tests are written using `pytest` and are designed to validate the functionality and correctness of the Python implementation, ensuring it behaves as expected and matches the original COBOL logic.

## Test Structure

- **Unit Tests**: Located in `test_gw_parser.py`, these tests validate individual functions and methods in isolation.
- **Functional Tests**: Located in `test_functional.py`, these tests validate the overall behavior of the system, ensuring that the Python implementation adheres to the business rules and logic of the original COBOL program.

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

To run only the unit tests:
```bash
PYTHONPATH=$(pwd)/src pytest tests/test_gw_parser.py
```

To run only the functional tests:
```bash
PYTHONPATH=$(pwd)/src pytest tests/test_functional.py
```

Running a Specific Test

To run a specific test, use the -k option with a keyword matching the test name. For example:
```bash
PYTHONPATH=$(pwd)/src pytest -k test_parse_family_normal_case
```

## Writing New Tests

### When adding new tests:

1. Place unit tests in test_gw_parser.py and functional tests in test_functional.py.
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

For any questions or issues, please contact the project maintainers.

