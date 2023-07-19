import json
import logging
import math
from pathlib import Path

import bpy


class AssemblyBlender:
    """
    This class will use the STLs that have been printed and assemble them in a Blender file.

    Args:
        part_no: This is the part number of the complex part that is being assembled.

    """

    def __init__(self, part_no: str) -> None:
        self.part_no = part_no
        self._base_path = Path(".")
        self.parts = {}

    def fetch_part(self, part: str):
        """
        Retrieves the part that will be imported and possitioned.

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

    def swap_xy_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the top"""

        while rot != 0:
            max_y = rotmax[1]
            rotation[0], rotation[1] = max_y - rotation[1], rotation[0]
            rotmax[0], rotmax[1] = rotmax[1], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def swap_xz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the front"""
        while rot != 0:
            max_x = rotmax[0]
            rotation[0], rotation[2] = rotation[2], max_x - rotation[0]
            rotmax[0], rotmax[2] = rotmax[2], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def swap_yz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the left"""
        while rot != 0:
            max_z = rotmax[2]
            rotation[1], rotation[2] = max_z - rotation[2], rotation[1]
            rotmax[2], rotmax[1] = rotmax[1], rotmax[2]
            rot = rot - 1
        return rotation, rotmax

    def move(self, rotmax: tuple, position: tuple, rotate: tuple):
        """
        Computes the moving and rotating of the stl to the desired location.

        Args:
            rotmax: This is the tuple that contains the original (x,y,z) location.
            position: This is the tuple that contains the amount which the (x,y,z) needs to move by.
            rotate: This is the tuple that contains the amount which the (x,y,z) needs to be rotated.
        """
        rotation = [0, 0, 0]
        for item in rotate:
            if item["axis"] == "x":
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis="X")
                working = self.swap_yz_(rotation, 1, rotmax)

            if item["axis"] == "y":
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis="Y")
                working = self.swap_xz_(rotation, 1, rotmax)

            if item["axis"] == "z":
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis="Z")
                working = self.swap_xy_(rotation, 1, rotmax)

            rotation = working[0]
            rotmax = working[1]

        bpy.ops.transform.translate(
            value=(rotation[0] + position[0], rotation[1] + position[1], rotation[2] + position[2])
        )

    def colour(self, colour: str, part: str) -> str:
        """
        Gives the colour.
        Args:
            colour: Colour which the object will become.
        """
        working_part = f"{part}_{self.parts[part]}"
        template_object = bpy.data.objects.get(working_part)
        matcolour = bpy.data.materials.new(colour)
        matcolour.diffuse_color = (0, 1, 0, 0.8)

        template_object.active_material = matcolour

    def build(self, path: Path | None = None):
        """
        Decodes the provided json and move the object around as required, creating new file which will use imported stl.
        """
        if path is not None:
            self._base_path = path

        json_file = self._base_path / f"{self.part_no}.json"
        data = json.loads(json_file.read_text())

        for action in data["parts"]:
            self.fetch_part(action["part_no"])
            self.move(action["rotmax"], action["position"], action["rotate"])
            self.colour(action["colour"], action["part_no"])

        logging.info("Saving the .blend file.")
        save_file = str(self._base_path / "blender")
        bpy.ops.wm.save_as_mainfile(filepath=save_file)
        # bpy.ops.wm.save_mainfile()
