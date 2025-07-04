# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import subprocess
from pathlib import Path

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.utils import check_source_hash
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class PartEngineOpenSCAD(PartEngine):
    """
    Decode a JSON to a OpenSCAD file which can be rendered in OpenSCAD for 3D view.
    """

    dif = 0

    def _decode_cube(self, lookup: dict) -> str:
        """
        This method will return the string that will have the OpenSCAD for a cube.

        Args:
            lookup: this will be the dictionary that contains the details about the cube.

        """
        res = self._move_cube(lookup, center=lookup["center"])
        center = ""
        if lookup["center"] is True:
            center = ", center=true"
        res = res + "cube([{x_size:}, {y_size:}, {z_size:}]{centered});".format(**lookup, centered=center)
        return res

    def _decode_external(self, lookup: dict) -> str:
        """
        This method will return the scad string necessary for processing the external part.

        Args:
            lookup: this will provide the details of the external part

        """

        return f'import("{lookup["label"]}");'

    def _decode_hole(self, lookup: dict) -> str:
        """
        This method will return the string that will have the scad for a hole.

        Args:
            lookup: This will be a dictionary containing the necessary information about the hole.

        """
        tempdiam = lookup["diameter"] / 2
        res = []
        res.append(self._translate(lookup))
        res.append(self._rotate(lookup["side"]))
        res.append("cylinder(r= {diam}, h={depth}, $fn=64);".format(diam=tempdiam, depth=lookup["depth"]))
        return res

    def _decode_nut(self, lookup: dict) -> str:
        """
        This method will return the string that will have the OpenSCAD for a nut cut out.

        Args:
            lookup: This will be a dictionary containing the necessary information about the nut.

        """
        res = []
        res.append(self._translate(lookup))
        res.append(self._rotate(lookup["side"], vertical=lookup["vertical"]))
        radius = lookup["diameter"] / 2
        res.append("cylinder(r={rad}, h={deep}, $fn=6);".format(rad=radius, deep=lookup["depth"]))

        return res

    def _decode_sphere(self, lookup: dict) -> str:
        """
        This method will return the string that will have the OpenSCAD for a sphere cut out.

        Args:
            lookup: This will be a dictionary containing the necessary information about the sphere.

        """
        res = []
        res.append(self._translate(lookup))
        radius = lookup["diameter"] / 2
        res.append(f"sphere(r={radius}, $fn=64);")

        return res

    def _decode_cut(self) -> str:
        """
        This method returns a simple OpenSCAD string neceseray to cut.
        """
        return "difference(){"

    def _translate(self, lookup: dict) -> str:
        """
        This will move the object around and return the scad necessary.

        Args:
            lookup: This will be a dictionary containing the necessary information about the hole.
        """
        res = "translate([{x:}, {y:}, {z:}])".format(**lookup)
        return res

    def _move_cube(self, features: dict, *, center: bool = False) -> str:
        """
        Accounts for when a cube is not going to penetrate the surface but rather sit above is.

        Args:
            features: This is the dictionary that contains the detail of where the cube must be places and its details.
        """

        angles = [0, 0, 0]
        if center is False:
            if features["side"] is not None:
                angles = features["side"]
                angles = {
                    TOP: [0, 0, -features["z_size"]],
                    BACK: [0, -features["y_size"], 0],
                    BOTTOM: [0, 0, 0],
                    FRONT: [0, 0, 0],
                    LEFT: [0, 0, 0],
                    RIGHT: [-features["x_size"], 0, 0],
                }[angles]

        output = "translate([{x}, {y}, {z}])".format(
            x=angles[0] + features["x"], y=angles[1] + features["y"], z=angles[2] + features["z"]
        )

        return output

    def _rotate(self, side: str, *, vertical: bool = False) -> str:
        """
        This will rotate the object and return the scad necessary.

        Args:
            side: this is the side as retrieved form the dictionary.
        """
        side = {
            TOP: "rotate([0, 180, 0])",
            BACK: "rotate([90, 0, 0])",
            BOTTOM: "rotate([0, 0, 0])",
            FRONT: "rotate([270, 0, 0])",
            LEFT: "rotate([0, 90, 0])rotate([0, 0, 30])",
            RIGHT: "rotate([0, 270, 0])rotate([0, 0, 30])",
        }[side]

        if vertical is True:
            side2 = "rotate([0, 0, 30])"
            side = side + side2

        return side

    def _beveled_edge_cube(self, size: float, depth: float, side: str, *, center: bool = False, rotate: bool = False):
        """
        Helper method for decode_beveled-Edge.

        Args:
            size: size of the beveled edge that will be cut.
            depth: Depth of the part.
            side: Side which the cutting will come from.
            center: set to True when the cube is centered at its center.
            rotate: set to True when the cube needs to be offset by 45 deg
        """
        if center:
            center = ", center=true"
        else:
            center = ""
        if side in [TOP, BOTTOM]:
            cube = f"cube([{size}, {size}, {depth}] {center});"
            if rotate:
                cube = f"rotate([0, 0, 45]){cube}"
        elif side in [FRONT, BACK]:
            cube = f"cube([{size}, {depth}, {size}] {center});"
            if rotate:
                cube = f"rotate([0, 45, 0]){cube}"
        elif side in [LEFT, RIGHT]:
            cube = f"cube([{depth}, {size}, {size}] {center});"
            if rotate:
                cube = f"rotate([45, 0, 0]){cube}"
        return cube

    def decode_beveled_edge(self, features: dict) -> str:
        """
        This method will decode a beveled edge and either make a bevel or taper

        Args:
            features: This is the dictionary that contains the details of the beveled edge.

        Returns:
            String of beveled edges.
        """
        if features["edge_type"] == "round":
            rotate = self._rotate(features["side"])
            cutter = "{rotate}cylinder(r= {diam}, h={depth}, $fn=64);".format(
                rotate=rotate, diam=features["size"], depth=features["depth"]
            )

        elif features["edge_type"] == "chamfer":
            cutter = self._beveled_edge_cube(
                size=features["size"] * 2,
                depth=features["depth"] * 2,
                side=features["side"],
                center=True,
                rotate=True,
            )

        cube = self._beveled_edge_cube(size=features["size"], depth=features["depth"], side=features["side"])
        move = {"x": 0, "y": 0, "z": 0}
        move_cube = {"x": 0, "y": 0, "z": 0}
        if features["bound1"] == 0:
            move[features["axis1"]] = features["size"]
            move_cube[features["axis1"]] = 0
        else:
            move[features["axis1"]] = 0
            move_cube[features["axis1"]] = features["bound1"] - features["size"]
        if features["bound2"] == 0:
            move[features["axis2"]] = features["size"]
            move_cube[features["axis2"]] = 0
        else:
            move[features["axis2"]] = 0
            move_cube[features["axis2"]] = features["bound2"] - features["size"]
        cutter = f"translate([{move['x']}, {move['y']}, {move['z']}])" + cutter
        template = "difference(){" + cube + cutter + "}"
        res = f"translate([{move_cube['x']}, {move_cube['y']}, {move_cube['z']}])" + template

        return res

    def build(self, part) -> list:  # noqa: ARG002 Unused argument
        """Create the output files for the part."""

        name = str(self.part_no)
        json_file = self._json_file
        scad_file = self._base_path / name / f"{name}.scad"
        stl_file = self._base_path / name / f"{name}.stl"
        if check_source_hash(json_file, scad_file):
            self.build_scad(json_file, scad_file)
        if self.config.get("stl"):
            if check_source_hash(scad_file, stl_file):
                self.build_stl(scad_file, stl_file)

        _files = [
            {"file": self._base_path / name / f"{name}.scad"},
            {"file": self._base_path / name / f"{name}.stl"},
            {"file": self._base_path / name / f"{name}.openscad.stl"},
        ]

        return self.file_list(files=_files, engine="OpenSCAD", score=3)

    def build_scad(self, json_file: Path, scad_file: Path):
        """
        This is the main working class for decoding the scad. It is necessary for it to be refactored.
        Raises:
            ValueError: if incorrect part_name is provided.
        """

        data = json.loads(json_file.read_text())

        output = []
        dif = 0
        for action in data["features"]:
            if action["type"] == "cut":
                dif = dif + 1
                output.insert(0, self._decode_cut())

            if action["name"] == "beveled_edge":
                output.append(self.decode_beveled_edge(action))

            elif action["name"] == "cube":
                output.append(self._decode_cube(action))

            elif action["name"] == "external":
                output.append(self._decode_external(self.name))

            elif action["name"] == "hole":
                output.append(self._decode_hole(action))

            elif action["name"] == "nut":
                output.append(self._decode_nut(action))

            elif action["name"] == "sphere":
                output.append(self._decode_sphere(action))

        i = 0
        while i < dif:
            i = i + 1
            output.append("}")

        with scad_file.open("w+") as fh:
            for out in output:
                if type(out) is list:
                    for small in out:
                        fh.write(small)
                        fh.write("\n")
                else:
                    fh.write(out)
                    fh.write("\n")

    def build_stl(self, scad_file: Path, stl_file: Path):
        """Calls OpenSCAD to create a STL for the part.

        Depending on the complexity of the object it can take long to compute.
        It prints out some messages to the terminal so that the impatient user will hopefully wait.
        Similar to many windows request.

        Raises:
            ValueError: If incorrect part_name is provided.

        """
        app_bin = self.get_appimage("OpenSCAD")
        logging.info("!!! THIS WILL TAKE SOME TIME, BE PATIENT !!! using %s", app_bin)
        result = subprocess.run([app_bin, "-o", stl_file, scad_file], capture_output=True, text=True, check=False)

        if result.stdout:
            logging.info("OpenSCAD: %s", result.stdout)
        if result.stderr:
            logging.error("OpenSCAD: %s", result.stderr)
