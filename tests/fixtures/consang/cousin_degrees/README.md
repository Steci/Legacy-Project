# Cousin-Degree Fixtures

This directory contains JSON fixtures that encode expected cousin-degree
classifications for a handful of synthetic relationship scenarios.

* `simple_cases.json` – baseline scenarios (self, siblings, first cousins,
  removals, direct ancestor, unrelated). These cases are intentionally small and
  kept in sync with GeneWeb expectations.

To regenerate or extend these fixtures:

1. Update the JSON with new cases (each entry lists the ancestor path lengths).
2. Run `pytest tests/consang/test_cousin_degree.py` to verify the new entries.
3. When deriving values from GeneWeb, record the observed degree/description in
   the `expected_*` fields so the Python implementation stays aligned.
