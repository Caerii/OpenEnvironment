"""Prompt loading utilities."""

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=8)
def load_template(name: str) -> str:
    """Load a prompt template by name (without extension)."""

    base = Path(__file__).resolve().parent
    path = base / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template '{name}' not found at {path}")
    return path.read_text(encoding="utf-8")
