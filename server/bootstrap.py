"""Bootstrap utilities to normalize imports across runtimes.

This module ensures that running the code from tests, scripts, or the
production server all share the same sys.path setup and module aliases.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Iterable

_BOOTSTRAPPED = False


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _ensure_sys_path(root: Path) -> None:
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _ensure_aliases(pairs: Iterable[tuple[str, str]]) -> None:
    for module_name, alias in pairs:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        sys.modules.setdefault(alias, module)


def ensure_bootstrapped() -> None:
    """Idempotently ensure consistent import environment."""

    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    root = _project_root()
    _ensure_sys_path(root)

    _ensure_aliases(
        (
            ("server.engine", "engine"),
            ("server.domain", "domain"),
            ("server.terrain", "terrain"),
        )
    )

    _BOOTSTRAPPED = True


# Run immediately on import so `import server.bootstrap` is enough.
ensure_bootstrapped()
