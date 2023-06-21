import json
import os


class AssemblyOpenSCAD:
    """
     This class will use the STLs that have been printed and import them to a OpenSCAD file that will move them around to their correct location.

    Args:
        part_no: This is the part number of the complex part that is being assembled.

    """

    def __init__(self, part_no: str) -> None:
        self.part_no = part_no

    def _fetch_part(self, part: str) -> str:
        """
        Retrieves the part that will be imported and possitioned.

        Args:
            part: this is the name of the part that will be imported.
        """
        return 'import("{cwd}/{part}/{part}.stl");'.format(cwd=os.getcwd(), part=part)

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

    def _move(self, Rotmax: tuple, moves: tuple, Rotate: tuple) -> str:
        """
        Computes the moving and rotating of the stl to the desired location.

        Args:
            Rotmax: This is the tuple that contains the original (x,y,z) location.
            moves: This is the tuple that contains the amount which the (x,y,z) needs to move by.
            Rotate: This is the tuple that contains the amount which the (x,y,z) needs to be rotated.
        """

        for piece in [Rotmax, moves, Rotate]:
            for index in range(len(piece)):
                piece[index] = float(piece[index])

        rotation = [0, 0, 0]
        working = self._swap_yz_(rotation, Rotate[0] / 90, Rotmax)
        rotation = working[0]
        Rotmax = working[1]
        working = self._swap_xz_(rotation, Rotate[1] / 90, Rotmax)
        rotation = working[0]
        Rotmax = working[1]
        working = self._swap_xy_(rotation, Rotate[2] / 90, Rotmax)
        rotation = working[0]
        Rotmax = working[1]

        output = "translate([{x}, {y}, {z}])".format(
            x=rotation[0] + float(moves[0]), y=rotation[1] + float(moves[1]), z=rotation[2] + float(moves[2])
        )
        output = output + f"rotate([{Rotate[0]}, {Rotate[1]}, {Rotate[2]}])"
        return output

    def _colour(self, colour: str) -> str:
        """
        Gives the colour.
        Args:
            colour: Colour which the object will become.
        """
        return f'color("{colour}")'

    def assembly_openscad(self):
        """
        Decodes the provided json and moves the object around as required, making a new openSCAD which will use imported stl.
        """
        out_name = "{cwd}/{part_no}/{part_no}.scad".format(cwd=os.getcwd(), part_no=self.part_no)
        SCAD = open(out_name, "w")
        in_name = "{cwd}/{part_no}/{part_no}.json".format(cwd=os.getcwd(), part_no=self.part_no)
        with open(in_name) as f:
            data = json.load(f)
        f.close()

        output = []
        for action in data:
            output.append(self._move(action["rotmax"], action["moves"], action["rotate"]))
            output.append(self._colour(action["colour"]))
            output.append(self._fetch_part(action["part_no"]))

        for out in output:
            SCAD.write(out)

        SCAD.close()
