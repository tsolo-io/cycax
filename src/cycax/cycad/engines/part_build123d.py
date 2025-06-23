# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
from pathlib import Path

import build123d

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


class PartEngineBuild123d(PartEngine):
    """
    Decode a JSON and render with Build123d.
    """

    def _decode_cube(self, feature_spec: dict) -> build123d.objects_part.Box:
        """
        This method will return the string that will have the Build123d for a cube.

        Args:
            feature: this will be the dictionary that contains the details about the cube.

        """
        feature = build123d.Box(feature_spec["x_size"], feature_spec["y_size"], feature_spec["z_size"])
        if not feature_spec.get("center"):
            feature = (
                build123d.Pos(
                    feature_spec["x"] + feature_spec["x_size"] / 2,
                    feature_spec["y"] + feature_spec["y_size"] / 2,
                    feature_spec["z"] + feature_spec["z_size"] / 2,
                )
                * feature
            )
            if feature_spec.get("side") == TOP:
                feature = build123d.Pos(0, 0, -feature_spec["z_size"]) * feature
            elif feature_spec.get("side") == BACK:
                feature = build123d.Pos(0, -feature_spec["y_size"], 0) * feature
            # TODO: The rest of the sides needs to be checked
        return feature

    def _decode_hole(self, feature_spec: dict) -> build123d.objects_part.Cylinder:
        """
        This method will return the string that will have the scad for a hole.

        Args:
            feature_spec: This will be a dictionary containing the necessary information about the hole.

        """
        feature = build123d.Cylinder(feature_spec["diameter"] / 2, height=feature_spec["depth"])
        if feature_spec["side"] == FRONT:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"] + feature_spec["depth"] / 2, feature_spec["z"])
            feature = pos * build123d.Rotation(X=270) * feature
        elif feature_spec["side"] == BACK:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"] - feature_spec["depth"] / 2, feature_spec["z"])
            feature = pos * build123d.Rotation(X=90) * feature
        elif feature_spec["side"] == TOP:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"] - feature_spec["depth"] / 2)
            feature = pos * build123d.Rotation(Y=180) * feature
        elif feature_spec["side"] == BOTTOM:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"] + feature_spec["depth"] / 2)
            feature = pos * build123d.Rotation(Y=0) * feature
        elif feature_spec["side"] == LEFT:
            pos = build123d.Pos(feature_spec["x"] + feature_spec["depth"] / 2, feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=90) * feature
        elif feature_spec["side"] == RIGHT:
            pos = build123d.Pos(feature_spec["x"] - feature_spec["depth"] / 2, feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=270) * feature

        return feature

    def _decode_nut(self, feature_spec: dict) -> str:
        """
        This method will return the string that will have the Build123d for a nut cut out.

        Example feature_spec:
          {
            'name': 'nut',
             'type': 'cut',
             'x': 10,
             'y': 7,
             'z': 7,
             'side': 'RIGHT',
             'nut_type': 'M3',
             'diameter': 6.2,
             'thickness': 2.5,
             'side_to_side': 5.5,
             'depth': 2.5,
             'vertical': True
           }

        Args:
            feature: This will be a dictionary containing the necessary information about the nut.
        """

        rot = 0 if feature_spec["vertical"] else 90
        hex2d = build123d.RegularPolygon(radius=feature_spec["diameter"] / 2, side_count=6, rotation=rot)
        feature = build123d.extrude(hex2d, amount=feature_spec["thickness"])
        if feature_spec["side"] == FRONT:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(X=270) * feature
        elif feature_spec["side"] == BACK:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(X=90) * feature
        elif feature_spec["side"] == TOP:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=180) * feature
        elif feature_spec["side"] == BOTTOM:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=0) * feature
        elif feature_spec["side"] == LEFT:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=90) * feature
        elif feature_spec["side"] == RIGHT:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=270) * feature
        return feature

    def _decode_sphere(self, feature_spec: dict) -> build123d.objects_part.Sphere:
        """
        This method will return the string that will have the Build123d for a sphere cut out.

        Args:
            feature: This will be a dictionary containing the necessary information about the sphere.

        """
        feature = build123d.Sphere(feature_spec["diameter"] / 2)
        feature = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"]) * feature
        return feature

    def build(self, part) -> list:
        """Create the output files for the part."""

        self.name = part.part_no
        self.set_path(part._base_path)
        file_no_ext = self._base_path / self.name / f"{self.name}"
        data = json.loads(self._json_file.read_text())
        files = self._build(data, file_no_ext)
        return self.file_list(files=files, engine="Build123d", score=3)

    def get_plane(self, part, side: str) -> build123d.Plane:
        if side is None:
            side = BOTTOM
        elif side not in SIDES:
            raise ValueError()

        ref_plane = getattr(build123d.Plane, side.lower())
        for face in part.faces().filter_by(ref_plane):
            plane = build123d.Plane(face)
            if plane.z_dir == ref_plane.z_dir:
                return plane

    def _build(self, definition: dict, file_no_ext: Path) -> list[Path]:
        """
        This is the main working class for decoding the scad. It is necessary for it to be refactored.

        Raises:
            ValueError: if incorrect part_name is provided.
        """

        part = None
        for action in definition["features"]:
            match action["name"]:
                case "cube":
                    feature = self._decode_cube(action)
                case "hole":
                    feature = self._decode_hole(action)
                case "sphere":
                    feature = self._decode_sphere(action)
                case "nut":
                    feature = self._decode_nut(action)
                case _:
                    msg = f"Unknown feature type: {action['name']}"
                    raise ValueError(msg)

            feature = (
                build123d.Plane.XY * feature
            )  # The position and direction in the JSON is all relevant to the XY Plane.
            if part is None:
                part = feature
            elif action["type"] == "add":
                part += feature
            elif action["type"] == "cut":
                part -= feature

        files = []
        build123d.export_stl(to_export=part, file_path=file_no_ext.with_suffix(".stl"))
        files.append({"file": file_no_ext.with_suffix(".stl"), "type": "stl"})
        build123d.export_gltf(to_export=part, file_path=file_no_ext.with_suffix(".gltf"))
        files.append({"file": file_no_ext.with_suffix(".gltf"), "type": "gltf"})
        build123d.export_step(to_export=part, file_path=file_no_ext.with_suffix(".step"))
        files.append({"file": file_no_ext.with_suffix(".step"), "type": "step"})
        return files
