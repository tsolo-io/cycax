# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

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

    def add(self, part_operation: dict):
        """Add a part to the assembly."""
        name = part_operation["part_no"]
        part = None
        # Import Step files of Parts
        ext = "step"  # Only work with step files. STL import create a face only, we need a solid.
        file3d = self._base_path / name / f"{name}.{ext}"
        if file3d.exists():
            if ext == "step":
                part = build123d.import_step(file3d)
            else:
                part = build123d.import_stl(file3d)
            logging.warning("Imported %s", file3d)
        if part is None:
            msg = (
                f"No file found for part {name} - AssemblerBuild123d require STEP files,"
                f" please use an engine that produce STEP files. Expected file at {file3d}"
            )
            raise FileNotFoundError(msg)

        # Rotate and shift the parts
        for rotate in part_operation["rotate"]:
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
        colour = part_operation.get("colour")
        if colour:
            try:
                part.color = build123d.Color(colour)
            except ValueError:
                logging.warning("Using an incompatible color %s", colour)
        # Position the part - final transformation
        cpart = build123d.Pos(*part_operation["position"]) * part
        cpart.name = part_operation["part_no"]
        # Last thing we do is set the label. Sometimes the label changed to COMPOUND if we do a transformation.
        cpart.label = part_operation["part_no"]
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
