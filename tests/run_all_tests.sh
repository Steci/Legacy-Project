#!/bin/bash
# run_all_tests.sh - Run all unit tests and show coverage for the Legacy Project
# Usage: bash tests/run_all_tests.sh

set -e

# Ensure we're in the project root
dirname=$(dirname "$0")
cd "$dirname/.."

# Run pytest with coverage for the src/ directory
PYTHONPATH=$(pwd)/src pytest tests --cov=src --cov-report=term-missing -v --cov-config=<(echo '[run]'; echo 'omit = */__init__.py */__main__.py')
