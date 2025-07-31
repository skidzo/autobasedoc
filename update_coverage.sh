#!/bin/bash
# update_coverage.sh - Script to run tests and update coverage badge

echo "Running tests with coverage..."
.venv/bin/python -m pytest --cov=autobasedoc --cov-report=xml --cov-report=term-missing

echo "Generating coverage badge..."
# Remove existing badge if it exists
if [ -f "coverage.svg" ]; then
    rm coverage.svg
    echo "Removed existing coverage badge"
fi
.venv/bin/python -m coverage_badge -o coverage.svg

echo "Coverage badge updated!"
echo "Current coverage can be found in:"
echo "  - HTML report: htmlcov/index.html"
echo "  - Badge: coverage.svg"
