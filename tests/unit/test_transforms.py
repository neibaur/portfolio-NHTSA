"""Tests for transformation helpers."""

from nhtsa_pipeline.transforms.placeholders import normalize_text


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("  Honda   Civic  ") == "Honda Civic"


def test_normalize_text_preserves_none() -> None:
    assert normalize_text(None) is None
