"""Placeholder module for future Silver and Gold transformations."""


def normalize_text(value: str | None) -> str | None:
    """Normalize simple string fields for future Silver transformations."""
    if value is None:
        return None
    return " ".join(value.strip().split())
