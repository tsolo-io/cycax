import json
import logging
import os
import subprocess

from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class EngineOpenSCAD:
    """
    This class willbe used to decode a json to a scad file which can be rendered in openscad for 3D view.
    """

    dif = 0

    def decode_cube(self, lookup: dict) -> str:
        """
        This method will return the string that will have the scad for a cube.

        Args:
            lookup: this will be the dictionary that contains the details about the cube so that is can be encoded in scad.

        """
        res = self.move_cube(lookup)
        center = ""
        if "center" in lookup is True:
            center = ", center=true"
        res = res + (
            "cube(["
            + str(lookup["x_size"])
            + ", "
            + str(lookup["y_size"])
            + ","
            + str(lookup["z_size"])
            + "]"
            + center
            + ");"
        )
        return res

    def decode_external(self, data_file: str) -> str:
        """
        This method will return the scad string necessary for processing the external part.

        Args:
            data_file : This will contain the part number of the external part so that it can be fetched from the parts_stl folder.

        """

        return 'import("../parts_stl/' + data_file + '.stl");'

    def decode_hole(self, lookup: dict) -> str:
        """
        This method will return the string that will have the scad for a hole.

        Args:
            lookup : This will be a dictionary containing the necessary information about the hole.

        """
        tempdiam = lookup["diameter"] / 2
        res = []
        res.append(self.translate(lookup))
        res.append(self.rotate(lookup["side"]))
        res.append("cylinder(r=" + str(tempdiam) + ", h=" + str(lookup["depth"]) + ", $fn=64);")
        return res

    def decode_nut(self, lookup: dict) -> str:
        """
        This method will return the string that will have the scad for a nut cut out.

        Args:
            lookup : This will be a dictionary containing the necessary information about the nut.

        """
        res = []
        res.append(self.translate(lookup))
        res.append(self.rotate(lookup["side"]))
        res.append("cylinder(r=" + str(lookup["nut_type"]) + ", h=" + str(lookup["depth"]) + ", $fn=6);")
        return res

    def decode_cut(self) -> str:
        """
        This method returns a simple OpenSCAD string neceseray to cut.
        """
        return "difference(){"

    def translate(self, lookup: dict) -> str:
        """
        This will move the object around and return the scad necessary.

        Args:
            lookup : This will be a dictionary containing the necessary information about the hole.
        """
        res = "translate([" + str(lookup["x"]) + ", " + str(lookup["y"]) + ", " + str(lookup["z"]) + "])"
        return res

    def move_cube(self, features: dict) -> str:
        """
        Accounts for when a cube is not going to penetrate the surface but rather sit above is.

        Args:
            features: This is the dictionary that contains the deatails of where the cube must be places and its details.
        """

        angles = [0, 0, 0]
        if features["side"] is not None:
            angles = features["side"]
            angles = {
                TOP: [0, 0, -features["z_size"]],
                BACK: [-features["y_size"], 0, 0],
                BOTTOM: [0, 0, 0],
                FRONT: [0, 0, 0],
                LEFT: [0, 0, 0],
                RIGHT: [0, -features["x_size"], 0],
            }.get(angles)

        output = (
            "translate(["
            + str(angles[0] + features["x"])
            + ", "
            + str(angles[1] + features["y"])
            + ", "
            + str(angles[2] + features["z"])
            + "])"
        )

        return output

    def rotate(self, side: str) -> str:
        """
        This will rotate the object and return the scad necessary.

        ???Would it make sense to also have a dictionary here similar to location swap methods???

        Args:
            side : this is the side as retrieved form the dictionary.
        """
        side = {
            TOP: "rotate([0, 180, 0])",
            BACK: "rotate([90, 0, 0])",
            BOTTOM: "rotate([0, 0, 0])",
            FRONT: "rotate([270, 0, 0])",
            LEFT: "rotate([0, 90, 0])",
            RIGHT: "rotate([0, 270, 0])",
        }.get(side)

        return side

    def decode(self, data_file: str):
        """
        This is the main working class for decoding the scad. It is necessary for it to be refactored.

        !!!For this method to work properly it will be necessary to add a JSON, STL and SCAD file into the working repository.!!!

        Args:
            data_file : name of the file that is to be decoded into a scad.
        """
        out_name = os.getcwd() + "/" + data_file + "/" + data_file + ".scad"
        SCAD = open(out_name, "w")
        in_name = os.getcwd() + "/" + data_file + "/" + data_file + ".json"

        with open(in_name) as f:
            data = json.load(f)

        output = []
        dif = 0
        for action in data:
            if action["type"] == "cut":
                dif = dif + 1
                output.insert(0, self.decode_cut())

            if action["name"] == "cube":
                output.append(self.decode_cube(action))

            if action["name"] == "external":
                output.append(self.decode_external(data_file))

            if action["name"] == "hole":
                output.append(self.decode_hole(action))

            if action["name"] == "nut":
                output.append(self.decode_nut(action))

        i = 0
        while i < dif:
            i = i + 1
            output.append("}")

        for out in output:
            if type(out) == list:
                for small in out:
                    SCAD.write(small)
            else:
                SCAD.write(out)

        SCAD.close()

    def render_stl(self, filename: str):
        """

        This takes a SCAD object and runs a command through linex that converts it into an stl.
        Depending on the complexity of the object it can take long to compute.
        It prints out some messages to the terminal so that the impatient user will hopefully wait.(Similar to many windows request.)

        Args:
            filename : This is the name of the file which will be converted from a scad to a stl

        """
        out_name = os.getcwd() + "/" + filename + "/" + filename + ".scad"
        out_stl_name = os.getcwd() + "/" + filename + "/" + filename + ".stl"

        logging.info("!!! THIS WILL TAKE SOME TIME, BE PATIENT !!!")
        result = subprocess.run(["openscad", "-o", out_stl_name, out_name], capture_output=True, text=True)

        if result.stdout:
            logging.info("OpenSCAD: %s", result.stdout)
        if result.stderr:
            logging.error("OpenSCAD: %s", result.stderr)

    def add(self, part):
        """
        This takes the provided part and will create its dictionary and export it to a json

        Args:
            part(CycadPart) : This is the part that will be eported to a json.
        """
        dir_name = os.getcwd() + "/" + part.part_no
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        with open(dir_name + "/" + part.part_no + ".json", "w") as jsonfile:
            json.dump(part.export(), jsonfile, indent=4)
