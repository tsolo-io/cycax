# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

# PEP 810 (Python 3.15+): load build123d only when it is first used. No effect on older
# Pythons. build123d takes ~2.7 s to import, which commands that never build should not pay.
__lazy_modules__ = ["build123d"]

import build123d

from cycax.cycad.engines.base_assembly_engine import AssemblyEngine


class AssemblyBuild123d(AssemblyEngine):
    """Assemble the parts into an Build123d model.

    Attributes:
        name: The part number of the complex part that is being assembled.
        config: Configuration for the Build123d assembly engine.
    """

    def __init__(self, name: str, config: dict | None = None) -> None:
        self.name = name
        self._base_path = Path(".")
        self._config = {} if config is None else config
        self._children = []

    def add(self, part_operation: dict, step_file: Path | None = None):
        """Add a part to the assembly.

        Args:
            part_operation: The part entry of the assembly spec.
            step_file: The part's STEP file. Default `<base path>/<name>/<name>.step`; the builder
                passes the cached file of the part's hash (same-name parts can differ).
        """
        name = part_operation["name"]
        part = None
        # Import Step files of Parts
        ext = "step"  # Only work with step files. STL import create a face only, we need a solid.
        file3d = step_file or self._base_path / name / f"{name}.{ext}"
        if file3d.exists():
            if ext == "step":
                part = build123d.import_step(file3d)
            else:
                part = build123d.import_stl(file3d)
            logging.debug("Imported %s", file3d)
        if part is None:
            msg = (
                f"No file found for part {name} - AssemblerBuild123d require STEP files,"
                f" please use an engine that produce STEP files. Expected file at {file3d}"
            )
            raise FileNotFoundError(msg)

        transform = part_operation.get("transform")
        if transform:
            # The placement matrix (task cycax/32): one transform, any angle.
            part = _location(transform) * part
        # Old specs: rotate and shift the parts
        for rotate in [] if transform else part_operation["rotate"]:
            kwarg = {rotate["axis"].upper(): rotate["angle"]}
            part = build123d.Rotation(**kwarg) * part
            bb = part.bounding_box()
            x, y, z = bb.size
            if rotate["axis"] == "x":
                part.move(build123d.Location((0, y, 0)))
            elif rotate["axis"] == "y":
                part.move(build123d.Location((0, 0, z)))
            elif rotate["axis"] == "z":
                part.move(build123d.Location((x, 0, 0)))

        # Set the parts colour.
        colour = part_operation.get("meta", {}).get("colour")
        if colour:
            try:
                part.color = build123d.Color(*colour)
            except ValueError:
                logging.warning("Using an incompatible color %s", colour)
        # Position the part - final transformation (already in the transform when there is one)
        position = (0, 0, 0) if transform else (part_operation["x"], part_operation["y"], part_operation["z"])
        cpart = build123d.Pos(*position) * part
        cpart.name = part_operation["name"]
        # Last thing we do is set the label. Sometimes the label changed to COMPOUND if we do a transformation.
        # `<instance>#<part hash>` (task cycax/39): read-back (cycax.testing) splits it.
        instance = part_operation.get("instance") or part_operation["name"]
        part_hash = part_operation.get("hash")
        cpart.label = f"{instance}#{part_hash}" if part_hash else instance
        self._children.append(cpart)

    def build(self, path: Path | None = None):
        """Create the assembly."""
        if path is not None:
            self._base_path = path
        if len(self._children) == 0:
            self._children.append(build123d.Sphere(10))  # The Sphere of emptiness
            logging.error("No parts added to the assembly - We added a sphere for you")
        copy_assembly = build123d.Compound(children=self._children)
        stl_file = self._base_path / f"{self.name}.stl"
        build123d.export_stl(copy_assembly, stl_file)
        step_file = self._base_path / f"{self.name}.step"
        build123d.export_step(copy_assembly, step_file)


def _location(matrix: list[list[float]]) -> "build123d.Location":
    """A build123d Location from a 4 x 4 row-major placement matrix."""
    from OCP.gp import gp_Trsf  # noqa: PLC0415

    trsf = gp_Trsf()
    trsf.SetValues(*matrix[0], *matrix[1], *matrix[2])
    return build123d.Location(trsf)
