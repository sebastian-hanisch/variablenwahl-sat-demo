"""Gemeinsame Fixtures: das Handbeispiel F3 (von Hand durchgerechnet, DEMO-PLAYBOOK §1b) und kleine Hilfen."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import vsd_scenario as S  # noqa: E402


@pytest.fixture
def f3():
    """Handbeispiel F3: 7 Variablen, 14 Klauseln; Handrechnung im README und in test_algorithm.py (Zerfall 1/2: drei Konflikte)."""
    return S.hand_formel()
