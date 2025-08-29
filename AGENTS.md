# Repo Guidelines

This repository requires a basic workflow for setting up the environment and running tests.

1. Use **Python ≥3.7**.
2. Install dependencies with `pip install -r requirements.txt`.
3. Install the project in editable mode using `pip install -e .`.
4. For testing with coverage, install test dependencies: `pip install -e ".[test]"` or manually: `pip install pytest faker numpy pytest-cov coverage`.
5. Set the environment variable `MPLBACKEND=Agg` before running tests in headless environments.
6. Execute tests using:
   - Simple tests: `pytest -q`
   - With coverage: `pytest --cov=autobasedoc --cov-report=term-missing`
