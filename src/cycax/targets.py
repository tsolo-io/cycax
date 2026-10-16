# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Mark the parts and assemblies in a Python file as CyCAx build targets.

    from cycax import cycax_assembly, cycax_part

    @cycax_part
    def bracket() -> SheetMetalBend: ...

    @cycax_part  # Classes work too, they must be constructible without arguments.
    class Psu(Print3D): ...

The decorators only tag the function or class, they return it unchanged, so it can still be
called directly, e.g. to add a part to an assembly. `cycax compile file.py` builds every target
defined in the file, `cycax compile file.py:bracket` builds only the named one.
"""

import importlib
import importlib.util
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from cycax.cycad import Assembly, CycadPart

TARGET_ATTRIBUTE = "__cycax_target__"


@dataclass(frozen=True)
class Target:
    """A CyCAx build target.

    Attributes:
        name: The name used to select the target, `file.py:<name>`.
        kind: Either "part" or "assembly".
        obj: The decorated function or class.
    """

    name: str
    kind: Literal["part", "assembly"]
    obj: Callable

    def make(self) -> list:
        """Call the target and return the parts or assemblies it made.

        Returns:
            A list of CycadPart (kind "part") or Assembly (kind "assembly") objects.

        Raises:
            TypeError: If the target returned something other than the expected type.
        """
        expected = CycadPart if self.kind == "part" else Assembly
        result = self.obj()
        results = result if isinstance(result, list | tuple) else [result]
        for item in results:
            if not isinstance(item, expected):
                msg = (
                    f"CyCAx {self.kind} target '{self.name}' returned {type(item).__name__}, "
                    f"expected {expected.__name__} or a list of {expected.__name__}."
                )
                raise TypeError(msg)
        return list(results)


def _mark(kind: Literal["part", "assembly"], obj: Callable | None, name: str | None):
    def decorator(_obj: Callable) -> Callable:
        setattr(_obj, TARGET_ATTRIBUTE, Target(name=name or _obj.__name__, kind=kind, obj=_obj))
        return _obj

    if obj is None:
        # Used with arguments: @cycax_part(name="...")
        return decorator
    return decorator(obj)


def cycax_part(obj: Callable | None = None, *, name: str | None = None):
    """Mark a function or class that makes a part as a CyCAx build target."""
    return _mark("part", obj, name)


def cycax_assembly(obj: Callable | None = None, *, name: str | None = None):
    """Mark a function or class that makes an assembly as a CyCAx build target."""
    return _mark("assembly", obj, name)


def collect_targets(module) -> dict[str, Target]:
    """Find the CyCAx targets defined in a module.

    Targets imported from other modules are ignored, a part that is only imported to be used
    in an assembly is built as part of that assembly.

    Args:
        module: The module to search.

    Returns:
        The targets, by name.
    """
    targets = {}
    for obj in vars(module).values():
        target = getattr(obj, TARGET_ATTRIBUTE, None)
        if isinstance(target, Target) and target.obj is obj and obj.__module__ == module.__name__:
            targets[target.name] = target
    return targets


def import_source(source: str | Path):
    """Import a CyCAx Python source, either a file path or a dotted module path.

    A file is imported with its directory on `sys.path`, so it can import its sibling modules.

    Args:
        source: A `.py` file path or a module path like `cycax_parts.powersupplies.meanwell`.

    Returns:
        The imported module.
    """
    path = Path(source).expanduser()
    if path.suffix != ".py":
        return importlib.import_module(str(source))

    path = path.resolve()
    if not path.exists():
        msg = f"File {path} does not exist."
        raise FileNotFoundError(msg)
    # A unique module name per file, so two files with the same name don't replace each other.
    module_name = f"cycax_src_{abs(hash(str(path))):x}_{path.stem}"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[module_name]
        raise
    finally:
        sys.path.remove(str(path.parent))
    return module


def load_targets(source: str | Path, name: str | None = None) -> list[Target]:
    """Import a source and return its CyCAx targets.

    Args:
        source: A `.py` file path or a dotted module path.
        name: Only return the target with this name.

    Returns:
        The targets in definition order.

    Raises:
        LookupError: If a name is given and the source has no target with that name.
    """
    targets = collect_targets(import_source(source))
    if name is None:
        return list(targets.values())
    if name not in targets:
        available = ", ".join(targets) or "none"
        msg = f"No CyCAx target '{name}' in {source}, available targets: {available}."
        raise LookupError(msg)
    return [targets[name]]
