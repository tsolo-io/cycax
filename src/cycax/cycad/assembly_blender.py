import logging
import math
from pathlib import Path

import bpy
import matplotlib.colors as mcolors

from cycax.cycad.engines.base_assembly_engine import AssemblyEngine


class AssemblyBlender(AssemblyEngine):
    """Assemble the parts into an Blender model.

    Args:
        name: The part number of the complex part that is being assembled.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._base_path = Path(".")
        self.parts = {}

    def _fetch_part(self, part: str):
        """Retrieves the part that will be imported and possitioned.

        Args:
            part: this is the name of the part that will be imported.
        """
        stl_file = self._base_path / part / f"{part}.stl"
        if not stl_file.exists():
            logging.warning("Referencing a file that does not exists. File name %s", stl_file)
        bpy.ops.import_mesh.stl(filepath=str(stl_file))
        for obj in bpy.context.selected_objects:
            if part in self.parts:
                obj.name = f"{part}_{self.parts[part] + 1}"
                self.parts[part] = self.parts[part] + 1
            else:
                obj.name = f"{part}_{1}"
                self.parts[part] = 1

    def _swap_xy_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the top"""
        while rot != 0:
            max_x = rotmax[0]
            rotation[0], rotation[1] = rotation[1], max_x - rotation[0]
            rotmax[0], rotmax[1] = rotmax[1], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def _swap_xz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the front"""
        while rot != 0:
            max_z = rotmax[2]
            rotation[0], rotation[2] = max_z - rotation[2], rotation[0]
            rotmax[0], rotmax[2] = rotmax[2], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def _swap_yz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the left"""
        while rot != 0:
            max_y = rotmax[1]
            rotation[1], rotation[2] = rotation[2], max_y - rotation[1]
            rotmax[2], rotmax[1] = rotmax[1], rotmax[2]
            rot = rot - 1
        return rotation, rotmax

    def _move(self, rotmax: tuple, position: tuple, rotate: tuple):
        """Computes the moving and rotating of the STL to the desired location.

        Args:
            rotmax: This is the tuple that contains the original (x,y,z) location.
            position: This is the tuple that contains the amount which the (x,y,z) needs to move by.
            rotate: This is the tuple that contains the amount which the (x,y,z) needs to be rotated.
        """
        rotation = [0, 0, 0]
        for item in rotate:
            if item["axis"] == "x":
                bpy.ops.transform.rotate(value=math.radians(360 - 90), orient_axis="X")
                working = self._swap_yz_(rotation, 3, rotmax)
            # blender does clockwise instead of anticlockwise rotations as we would expect in openscad.

            if item["axis"] == "y":
                bpy.ops.transform.rotate(value=math.radians(360 - 90), orient_axis="Y")
                working = self._swap_xz_(rotation, 3, rotmax)

            if item["axis"] == "z":
                bpy.ops.transform.rotate(value=math.radians(360 - 90), orient_axis="Z")
                working = self._swap_xy_(rotation, 3, rotmax)

            rotation = working[0]
            rotmax = working[1]

        bpy.ops.transform.translate(
            value=(rotation[0] + position[0], rotation[1] + position[1], rotation[2] + position[2])
        )

    def _colour(self, colour: str, part: str) -> str:
        """Set the part colour.

        Args:
            colour: Colour which the part will become.
        """
        working_part = f"{part}_{self.parts[part]}"
        template_object = bpy.data.objects.get(working_part)
        colour_rgb = mcolors.to_rgb(colour)
        matcolour = bpy.data.materials.new(colour)
        matcolour.diffuse_color = (colour_rgb[0], colour_rgb[1], colour_rgb[2], 0.8)

        template_object.active_material = matcolour

    def add(self, part_operation: dict):
        """Add the part to the assembly."""
        self._fetch_part(part_operation["part_no"])
        self._move(part_operation["rotmax"], part_operation["position"], part_operation["rotate"])
        self._colour(part_operation["colour"], part_operation["part_no"])

    def build(self, path: Path | None = None):
        """Create the assembly of the parts added."""
        if path is not None:
            self._base_path = path

        for screen_area in bpy.context.screen.areas:
            if screen_area.type == "VIEW_3D":
                # Set the clip depth from 1000 (1m) to 50m
                screen_area.spaces.active.clip_end = 50000
        logging.info("Saving the .blend file.")
        save_file = str(self._base_path / f"{self.name}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=save_file)
