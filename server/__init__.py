"""Server package initialization."""

from importlib import import_module
import sys

from .bootstrap import ensure_bootstrapped

# Normalize environment for any consumer importing `server`
ensure_bootstrapped()

# Provide convenient aliases for selected subpackages (optional)
for _alias in ("semantic", "features", "primitives"):
    if _alias not in sys.modules:
        try:
            sys.modules[_alias] = import_module(f"server.{_alias}")
        except ModuleNotFoundError:
            continue

