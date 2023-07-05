import json
import logging
from pathlib import Path


class AssemblyOpenSCAD:
    """
     This class will use the STLs that have been printed and import them to a OpenSCAD file that will move them around to their correct location.

    Args:
        part_no: This is the part number of the complex part that is being assembled.

    """

    def __init__(self, part_no: str) -> None:
        self.part_no = part_no
        self._base_path = Path(".")

    def _fetch_part(self, part: str) -> str:
        """
        Retrieves the part that will be imported and possitioned.

        Args:
            part: this is the name of the part that will be imported.
        """
        stl_file = self._base_path / part / f"{part}.stl"
        if not stl_file.exists():
            logging.warning("Referencing a file that does not exists. File name %s", stl_file)
        return f'import("{stl_file}");'

    def _swap_xy_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the top"""

        while rot != 0:
            max_y = rotmax[1]
            rotation[0], rotation[1] = max_y - rotation[1], rotation[0]
            rotmax[0], rotmax[1] = rotmax[1], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def _swap_xz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the front"""
        while rot != 0:
            max_x = rotmax[0]
            rotation[0], rotation[2] = rotation[2], max_x - rotation[0]
            rotmax[0], rotmax[2] = rotmax[2], rotmax[0]
            rot = rot - 1
        return rotation, rotmax

    def _swap_yz_(self, rotation: tuple, rot: float, rotmax: tuple) -> tuple:
        """Used to help rotate the object on the spot while freezing the left"""
        while rot != 0:
            max_z = rotmax[2]
            rotation[1], rotation[2] = max_z - rotation[2], rotation[1]
            rotmax[2], rotmax[1] = rotmax[1], rotmax[2]
            rot = rot - 1
        return rotation, rotmax

    def _move(self, Rotmax: tuple, position: tuple, Rotate: tuple) -> str:
        """
        Computes the moving and rotating of the stl to the desired location.

        Args:
            Rotmax: This is the tuple that contains the original (x,y,z) location.
            position: This is the tuple that contains the amount which the (x,y,z) needs to move by.
            Rotate: This is the tuple that contains the amount which the (x,y,z) needs to be rotated.
        """
        rotation = [0, 0, 0]
        rotout = ""
        for item in Rotate:
            rotwork = item
            rotwork = {
                0: "rotate([90, 0, 0])",
                1: "rotate([0, 90, 0])",
                2: "rotate([0, 0, 90])",
            }[rotwork]
            rotout = rotwork + rotout
            if item == 0:
                working = self._swap_yz_(rotation, 1, Rotmax)

            elif item == 1:
                working = self._swap_xz_(rotation, 1, Rotmax)

            elif item == 2:
                working = self._swap_xy_(rotation, 1, Rotmax)

            rotation = working[0]
            Rotmax = working[1]

        output = "translate([{x}, {y}, {z}])".format(
            x=rotation[0] + float(position[0]), y=rotation[1] + float(position[1]), z=rotation[2] + float(position[2])
        )
        output = output + rotout
        return output

    def _colour(self, colour: str) -> str:
        """
        Gives the colour.
        Args:
            colour: Colour which the object will become.
        """
        return f'color("{colour}")'

    def build(self, path: Path | None = None):
        """
        Decodes the provided json and move the object around as required, making a new openSCAD which will use imported stl.
        """
        if path is not None:
            self._base_path = path

        json_file = self._base_path / f"{self.part_no}.json"
        data = json.loads(json_file.read_text())

        output = []
        for action in data["parts"]:
            output.append(self._move(action["rotmax"], action["position"], action["rotate"]))
            output.append(self._colour(action["colour"]))
            output.append(self._fetch_part(action["part_no"]))

        scad_file = self._base_path / f"{self.part_no}.scad"
        with scad_file.open("w") as scad_fh:
            for out in output:
                scad_fh.write(out)
                scad_fh.write("\n")
