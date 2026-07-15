"""Module system: base class and auto-discovery.

To add a setup step, drop a new file in devenv/modules/ that subclasses
``Module`` and sets a ``name``. It is auto-discovered — no registration needed.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


class Module:
    """Base class for setup modules.

    Attributes:
        name:               Short identifier (e.g. "packages", "casks").
        description:        One-line description shown in `list`.
        order:              Execution order (lower = earlier). Default 50.
        requires_sudo:      If True, skipped when sudo is unavailable.
        enabled_by_default: If False, only runs when explicitly enabled via CLI.
    """

    name: str = ""
    description: str = ""
    order: int = 50
    requires_sudo: bool = False
    enabled_by_default: bool = True

    def run(self, ctx) -> None:
        raise NotImplementedError


def discover_modules() -> list[Module]:
    """Scan this package for Module subclasses and return sorted instances."""
    modules: list[Module] = []
    package_dir = Path(__file__).parent
    for _importer, modname, _ispkg in pkgutil.iter_modules([str(package_dir)]):
        if modname.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{modname}")
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Module)
                and attr is not Module
                and attr.name  # skip unnamed base classes
            ):
                modules.append(attr())
    modules.sort(key=lambda m: m.order)
    return modules
