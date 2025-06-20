# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

from cycax.cycad.engines.base_assembly_engine import AssemblyEngine


class AssemblyOpenSCAD(AssemblyEngine):
    """Assemble the parts into an OpenSCAD model.

    Attributes:
        name: The part number of the complex part that is being assembled.
        config: Configuration for the OpenSCAD assembly engine.
    """

    def __init__(self, name: str, config: dict | None = None) -> None:
        self.name = name
        self._base_path = Path(".")
        self._config = {} if config is None else config
        self._scad_ops = []

    def _fetch_part(self, part: str) -> str:
        """Retrieves the STL file that represents part and position it in the assembly.

        Args:
            part: The name of the part to be imported.
        """
        stl_file = self._base_path / part / f"{part}.stl"
        if not stl_file.exists():
            logging.warning("Referencing a file that does not exists. File name %s", stl_file)
        return f'import("{stl_file}");'

    def _swap_xy_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Rotate the part on the spot while freezing the top."""

        while rot != 0:
            max_y = rotmax[1]
            rotation[0], rotation[1] = max_y - rotation[1], rotation[0]
            rotmax[0], rotmax[1] = rotmax[1], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def _swap_xz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Rotate the part on the spot while freezing the front."""
        while rot != 0:
            max_x = rotmax[0]
            rotation[0], rotation[2] = rotation[2], max_x - rotation[0]
            rotmax[0], rotmax[2] = rotmax[2], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def _swap_yz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Rotate the part on the spot while freezing the left."""
        while rot != 0:
            max_z = rotmax[2]
            rotation[1], rotation[2] = max_z - rotation[2], rotation[1]
            rotmax[2], rotmax[1] = rotmax[1], rotmax[2]
            rot = rot - 1
        return rotation, rotmax

    def _move(self, rotmax: tuple, position: tuple, rotate: tuple) -> str:
        """
        Computes the moving and rotating of the STL to the desired location.

        Args:
            rotmax: This is the tuple that contains the original (x,y,z) location.
            position: This is the tuple that contains the amount which the (x,y,z) needs to move by.
            rotate: This is the tuple that contains the amount which the (x,y,z) needs to be rotated.
        """
        rotation = [0, 0, 0]
        rotout = ""
        for item in rotate:
            rotwork = item["axis"]
            rotwork = {
                "x": "rotate([90, 0, 0])",
                "y": "rotate([0, 90, 0])",
                "z": "rotate([0, 0, 90])",
            }[rotwork]
            rotout = rotwork + rotout
            if item["axis"] == "x":
                working = self._swap_yz_(rotation, 1, rotmax)

            elif item["axis"] == "y":
                working = self._swap_xz_(rotation, 1, rotmax)

            elif item["axis"] == "z":
                working = self._swap_xy_(rotation, 1, rotmax)

            rotation = working[0]
            rotmax = working[1]

        output = f"translate([{rotation[0] + float(position[0])}, {rotation[1] + float(position[1])}, {rotation[2] + float(position[2])}])"
        output = output + rotout
        return output

    def _colour(self, colour: str) -> str:
        """Set the part colour.

        Args:
            colour: Colour which the part will become.
        """
        return f'color("{colour}")'

    def add(self, part_operation: dict):
        """Add the part to the assembly."""
        self._scad_ops.append(
            self._move(part_operation["rotmax"], part_operation["position"], part_operation["rotate"])
        )
        self._scad_ops.append(self._colour(part_operation["colour"]))
        self._scad_ops.append(self._fetch_part(part_operation["part_no"]))

    def build(self, path: Path | None = None):
        """Create the assembly of the parts added."""
        if path is not None:
            self._base_path = path

        assert self._scad_ops, "No SCAD operations defined. Please call add() on the AssemblyEngine"
        scad_file = self._base_path / f"{self.name}.scad"
        with scad_file.open("w") as scad_fh:
            for out in self._scad_ops:
                scad_fh.write(out)
                scad_fh.write("\n")
