"""Tests that the example configurations give the expected JSON."""

import json
from pathlib import Path

import pytest

from confl.converter import convert

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
SOURCES = sorted(EXAMPLES_DIR.glob("*.confl"))


def test_examples_are_present():
    """The repository contains example configurations."""
    assert SOURCES


@pytest.mark.parametrize("source", SOURCES, ids=lambda path: path.stem)
def test_example_matches_expected_json(source):
    """Translating an example gives the stored JSON document."""
    text = source.read_text(encoding="utf-8")
    expected = source.with_suffix(".json").read_text(encoding="utf-8")
    assert json.loads(convert(text)) == json.loads(expected)