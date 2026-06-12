"""Regression: packaging metadata files must be UTF-8 for setuptools."""

from __future__ import annotations

from scripts.validate_packaging_utf8 import validate_packaging_utf8


def test_packaging_metadata_files_are_utf8() -> None:
    violations = validate_packaging_utf8()
    assert violations == [], "; ".join(violations)
