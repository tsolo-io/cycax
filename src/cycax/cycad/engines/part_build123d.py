# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from pathlib import Path

import build123d

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.utils import check_source_hash
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class PartEngineBuild123d(PartEngine):
    """
    Decode a JSON and render with Build123d.
    """

    def _decode_cube(self, lookup: dict) -> str:
        """
        This method will return the string that will have the Build123d for a cube.

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
        This method will return the string that will have the Build123d for a nut cut out.

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
        This method will return the string that will have the Build123d for a sphere cut out.

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
        This method returns a simple Build123d string neceseray to cut.
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

    def build(self, part) -> list:
        """Create the output files for the part."""

        self.name = part.part_no
        self.set_path(part._base_path)
        str_file = self._base_path / self.name / f"{self.name}.stl"
        data = json.loads(self._json_file.read_text())
        self._build(data, str_file)
        _files = [
            {"file": str_file},
        ]

        return self.file_list(files=_files, engine="Build123d", score=3)


    def get_plane(self, part, side: str) -> build123d.Plane:
        SIDES = (LEFT, RIGHT, FRONT, BACK, TOP, BOTTOM)
        if side is None:
            side = BOTTOM
        elif not side in SIDES:
            raise ValueError()

        ref_plane = getattr(build123d.Plane, side.lower())
        for face in part.faces().filter_by(ref_plane):
            plane = build123d.Plane(face)
            if plane.z_dir == ref_plane.z_dir:
                return plane

    def _build(self, definition: dict, stl_file: Path):
        """
        This is the main working class for decoding the scad. It is necessary for it to be refactored.

        Raises:
            ValueError: if incorrect part_name is provided.
        """

        # ex2 = Box(length, width, thickness)
        # ex2 -= Cylinder(center_hole_dia / 2, height=thickness)
        #
        # {'name': 'cube', 'type': 'add', 'side': None, 'x': 0, 'y': 0, 'z': 0, 'x_size': 11, 'y_size': 11, 'z_size': 2, 'center': False}
        # {'x': 5.5, 'y': 5.5, 'z': 2.0, 'side': 'TOP', 'diameter': 2, 'depth': 2, 'name': 'hole', 'type': 'cut'}

        part = None
        for action in definition["features"]:
            print(action)
            if action["name"] == "cube":
                feature = build123d.Box(action["x_size"], action["y_size"], action["z_size"])
                if not action.get("center"):
                    # feature = build123d.Pos(action['x_size']/2, action['y_size']/2, action['z_size']/2) * feature
                    feature = (
                        build123d.Pos(
                            action["x"] + action["x_size"] / 2,
                            action["y"] + action["y_size"] / 2,
                            action["z"] + action["z_size"] / 2,
                        )
                        * feature
                    )
                    if action.get("side") == "TOP":
                        feature = build123d.Pos(0,0,-action["z_size"]) * feature
                    # elif action.get("side") == "BOTTOM":
                    #     feature = build123d.Plane.XZ * feature
                    # elif action.get("side") == "LEFT":
                    #     feature = build123d.Plane.YZ * feature
                    # elif action.get("side") == "RIGHT":
                    #     feature = build123d.Plane.YX * feature
            elif action["name"] == "hole":
                feature = build123d.Cylinder(action["diameter"] / 2, height=action["depth"])
                feature = build123d.Pos(action["x"], action["y"], action["z"] - action["depth"] / 2) * feature

            # feature = self.get_plane(feature, action.get("side")) * feature
            feature = build123d.Plane.XY * feature
            if part is None:
                part = feature
            elif action["type"] == "add":
                part += feature
            elif action["type"] == "cut":
                part -= feature

        print(f"Save {self.name} to {stl_file}")
        build123d.export_stl(to_export=part, file_path=stl_file)
        build123d.export_gltf(to_export=part, file_path=f"{stl_file}.gltf")
        build123d.export_step(to_export=part, file_path=f"{stl_file}.step")
        # exporter = build123d.ExportSVG(unit=build123d.Unit.MM, line_weight=0.5)
        # exporter.add_layer("Layer 1", fill_color=(255, 0, 0), line_color=(0, 0, 255))
        # exporter.add_shape(part, layer="Layer 1")
        # exporter.write(f"{stl_file.stem}.svg")
