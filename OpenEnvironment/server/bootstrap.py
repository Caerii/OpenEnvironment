"""Bootstrap utilities to normalize imports across runtimes.

Ensures the project root is on sys.path so `server.*` imports work
regardless of how the code is invoked (tests, scripts, uvicorn, etc.).
"""

from __future__ import annotations

import sys
from pathlib import Path

_BOOTSTRAPPED = False


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_bootstrapped() -> None:
    """Idempotently ensure consistent import environment."""

    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    root_str = str(_project_root())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

    _BOOTSTRAPPED = True


ensure_bootstrapped()
