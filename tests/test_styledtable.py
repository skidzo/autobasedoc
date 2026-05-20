import importlib
import os
import sys
from pathlib import Path

import pytest
from reportlab.platypus import Table

ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = ROOT / "tests"
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import autobasedoc.autorpt as ar


def test_create_table_forwards_row_heights_in_cm(monkeypatch):
    monkeypatch.chdir(TESTS_DIR)
    flowables = importlib.import_module("flowables")

    table = flowables.create_table(
        body=[["A", "B"], ["C", "D"]],
        colWidths=[2, 3],
        rowHeights=[1.5, 2.5],
        withHLines=False,
    )

    assert isinstance(table, Table)
    assert list(table._rowHeights) == pytest.approx([1.5 * ar.cm, 2.5 * ar.cm])
    assert list(table._colWidths) == pytest.approx([2 * ar.cm, 3 * ar.cm])
