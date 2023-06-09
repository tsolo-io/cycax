#
# This file is called directly from FreeCAD.
# CyCAx launches the FreeCAD binary and pass in:
# 1. The fullpath to this file.
# 2. The path to the part JSON file.
# 3. The path where the output files are stored.
# 1. Open the file up in FreeCAD and run as a Macro.
# 2. Run from command line. ./FreeCAD.AppImage img.py
#
import json
import logging
import os
import sys
from math import sqrt
from pathlib import Path

import importDXF

# import QtGui
import Part
from FreeCAD import Rotation, Vector  # NoQa
from PySide import QtGui

logging.error("Open FreeCAD")

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"
REAR = "BACK"


class EngineFreecad:
    """This class will be used in FreeCAD to decode a json passed to it. The json will contain specific information of the object.

    Args:
        base_path: the path where the outputs need to be stored.
    """

    def __init__(self, base_path: Path):
        self._base_path = base_path

    def cube(self, feature: dict):
        """This method will draw a cube when given a dict that contains the necessary dimentions

        Args:
            feature: This is the dict that contains the necessary details of the cube to be cut out.
        """
        if feature["center"] is True:
            x = feature["x"] - feature["x_size"] / 2
            y = feature["y"] - feature["y_size"] / 2
            z = feature["z"] - feature["z_size"] / 2
        else:
            x = feature["x"]
            y = feature["y"]
            z = feature["z"]
        pos_vec = (x, y, z)

        pos_vec = self._move_cube(feature, pos_vec)
        pos = Vector(pos_vec[0], pos_vec[1], pos_vec[2])
        length = feature["x_size"]
        width = feature["y_size"]
        depth = feature["z_size"]
        return Part.makeBox(length, width, depth, pos)

    def _calc_hex(self, depth: float, diameter: float):
        """This method will be used to find out where the points of the hexigon are located and then drawing a 2D hexigon.

        Args:
            depth: this is the depth of the hexigon.
            diameter: this is the diameter of the hexigon.
        """

        radius = diameter / 2
        half_radius = radius / 2
        radius_sqrt = radius * sqrt(3) / 2
        vector_list = []
        z = depth

        vector_list.append(Vector(radius, 0, z))
        vector_list.append(Vector(half_radius, radius_sqrt, z))
        vector_list.append(Vector(-half_radius, radius_sqrt, z))
        vector_list.append(Vector(-radius, 0, z))
        vector_list.append(Vector(-half_radius, -radius_sqrt, z))
        vector_list.append(Vector(half_radius, -radius_sqrt, z))

        vector_list.append(vector_list[0])
        wire = Part.makePolygon(vector_list)
        shape = Part.Shape(wire)
        face = Part.Face(shape)
        return face

    def cut_nut(self, feature: dict):
        """This method will take the 2D hexigon and convert it to a 3D shape and place it where it needs to go.
        Args:
            feature: this is a dict containing the necessary details of the hexigon like its size and location.
        """

        hex = self._calc_hex(depth=0, diameter=3)
        nut = hex.extrude(App.Vector(0, 0, feature["depth"]))

        if feature["side"] in [FRONT, BACK]:
            nut.Placement = App.Placement(Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(0, 30, 270))

        elif feature["side"] in [TOP, BOTTOM]:
            nut.Placement = App.Placement(Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(30, 0, 0))

        elif feature["side"] in [LEFT, RIGHT]:
            nut.Placement = App.Placement(Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(0, 90, 0))

        return nut

    def _move_cube(self, features: dict, pos_vec):
        """
        Accounts for when a cube is not going to penetrate the surface but rather sit above is.

        Args:
            features: This is the dictionary that contains the deatails of where the cube must be places and its details.
            pos_vec(list): where part is positioned.

        Returns:
        """

        angles = [0, 0, 0]
        if features["side"] is not None:
            angles = features["side"]
            angles = {
                TOP: [pos_vec[0], pos_vec[1], pos_vec[2] - features["z_size"]],
                BACK: [pos_vec[0] - features["y_size"], pos_vec[1], pos_vec[2]],
                BOTTOM: [pos_vec[0], pos_vec[1], pos_vec[2]],
                FRONT: [pos_vec[0], pos_vec[1], pos_vec[2]],
                LEFT: [pos_vec[0], pos_vec[1], pos_vec[2]],
                RIGHT: [pos_vec[0], pos_vec[1] - features["x_size"], pos_vec[2]],
            }[angles]

        return angles

    def hole(
        self, feature: dict = None, depth: float = None, radius: float = None, move: dict = None, side: str = None
    ):
        """This method will be used for cutting a cylindical hole into a surface.

        Args:
            feature: This is the dictionary that contains the deatails of where the hole must be placed and its details.
        """
        pos_vec = Vector(0, 0, 0)
        if feature is not None:
            print(feature)
            cyl = Part.makeCylinder(feature["diameter"] / 2, feature["depth"], pos_vec)
            side = feature["side"]
            x = feature["x"]
            y = feature["y"]
            z = feature["z"]
        else:
            cyl = Part.makeCylinder(radius, depth, pos_vec)
            x = move["x"]
            y = move["y"]
            z = move["z"]
        if side in [FRONT, BACK]:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(1, 0, 0), 270))
        elif side in [TOP, BOTTOM]:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 0, 1), 0))
        elif side in [LEFT, RIGHT]:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 90))
        return cyl

    def render_to_png(self, target_path: Path):
        """This method will be used for creating a png of 2 specific views of the object.
        Args:
            target_path: The Path the png needs to be saved under.
        """
        active_doc = FreeCADGui.activeDocument()
        target_image_file = f"{target_path}-perspectiveAll.png"
        FreeCADGui.SendMsgToActiveView("ViewFit")
        active_doc.activeView().viewAxometric()
        active_doc.activeView().fitAll()
        active_doc.activeView().saveImage(str(target_image_file), 2000, 1800, "White")
        target_image_file = f"{target_path}-perspectiveTop.png"
        FreeCADGui.SendMsgToActiveView("ViewFit")
        active_doc.activeView().viewTop()
        active_doc.activeView().fitAll()
        active_doc.activeView().saveImage(str(target_image_file), 2000, 1800, "White")

    def render_to_dxf(self, active_doc: App.Document, target_path: Path):
        """This method will be used for creating a pdxf of the object currently in view.
        Args:
            active_doc: The active FreeCAD Gui
            target_path: The Path the png needs to be saved under.
        """
        __objs__ = []
        __objs__.append(active_doc.getObject("Shape"))

        importDXF.export(__objs__, str(f"{target_path}-perspective.dxf"))

    def render_to_stl(self, active_doc: App.Document, target_path: Path):
        """This method will be used for creating a stl of an object currently in view.
        Args:
            active_doc: The active FreeCAD Gui
            target_path: The Path the png needs to be saved under.
        """
        for obj in active_doc.Objects:
            if obj.ViewObject.Visibility:
                filename = f"{target_path}-FreeCAD.stl"
                obj.Shape.exportStl(filename)

    def _beveled_edge_cube(self, length: float, depth: float, side: str, move: dict):
        """
        Helper method for decode_beveled_edge.

        Args:
            length: Length of the beveled edge that will be cut.
            depth: Depth of the part.
            side: Side which the cutting will come from.
            center: set to True when the cube is centered at its center.
            rotate: set to True when the cube needs to be offset by 45 deg
        """

        x = move["x"]
        y = move["y"]
        z = move["z"]
        if side in [TOP, BOTTOM]:
            cube = Part.makeBox(length, length, depth, Vector(x, y, z))
        elif side in [FRONT, BACK]:
            cube = Part.makeBox(length, depth, length, Vector(x, y, z))
        elif side in [LEFT, RIGHT]:
            cube = Part.makeBox(depth, length, length, Vector(x, y, z))

        return cube

    def _rhombus(self, depth: float, length: float, move: dict, side: str):
        """This method will cut a rhombus with 90 degree andgles.

        Args:
            depth: this is the depth of the rhombus.
            length: this is the length of the rhombus.
            move: x, y, z of rhombut.
            side: side for rhombus to be cut into.
        """
        hypot = sqrt(length * 2 * length * 2 + length * 2 * length * 2) / 2
        vector_list = []

        vector_list.append(Vector(hypot, 0, 0))
        vector_list.append(Vector(0, hypot, 0))
        vector_list.append(Vector(-hypot, 0, 0))
        vector_list.append(Vector(0, -hypot, 0))

        vector_list.append(vector_list[0])
        wire = Part.makePolygon(vector_list)
        shape = Part.Shape(wire)
        face = Part.Face(shape)

        rhombus = face.extrude(App.Vector(0, 0, depth))

        x = move["x"]
        y = move["y"]
        z = move["z"]

        if side in [FRONT, BACK]:
            rhombus.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(1, 0, 0), 270))
        elif side in [TOP, BOTTOM]:
            rhombus.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 0, 1), 0))
        elif side in [LEFT, RIGHT]:
            rhombus.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 90))

        return rhombus

    def decode_beveled_edge(self, features: dict, solid):
        """
        This method will decode a beveled edge and either make a bevel or taper

        Args:
            features: This is the dictionary that contains the details of the beveled edge.
        """

        hypot = sqrt(features["size"] * 2 * features["size"] * 2 + features["size"] * 2 * features["size"] * 2) / 3
        move_cutter_cyl = {"x": 0, "y": 0, "z": 0}
        move_cutter_rhombus = {"x": 0, "y": 0, "z": 0}
        move_cube = {"x": 0, "y": 0, "z": 0}
        if features["bound1"] == 0:
            move_cutter_cyl[features["axis1"]] = features["size"]
            move_cutter_rhombus[features["axis1"]] = hypot
            move_cube[features["axis1"]] = 0
        else:
            move_cutter_cyl[features["axis1"]] = features["bound1"] - features["size"]
            move_cutter_rhombus[features["axis1"]] = features["bound1"] - hypot
            move_cube[features["axis1"]] = features["bound1"] - features["size"]
        if features["bound2"] == 0:
            move_cutter_cyl[features["axis2"]] = features["size"]
            move_cutter_rhombus[features["axis2"]] = hypot
            move_cube[features["axis2"]] = 0
        else:
            move_cutter_cyl[features["axis2"]] = features["bound2"] - features["size"]
            move_cutter_rhombus[features["axis2"]] = features["bound2"] - hypot
            move_cube[features["axis2"]] = features["bound2"] - features["size"]

        if features["edge_type"] == "round":
            cutter = self.hole(
                radius=features["size"], depth=features["depth"], side=features["side"], move=move_cutter_cyl
            )

        elif features["edge_type"] == "chamfer":
            cutter = self._rhombus(
                depth=features["depth"], length=features["size"], move=move_cutter_rhombus, side=features["side"]
            )

        cube = self._beveled_edge_cube(
            length=features["size"], depth=features["depth"], side=features["side"], move=move_cube
        )

        cutter = cube.cut(cutter)
        res = solid.cut(cutter)
        Part.cast_to_shape(res)

        return res

    def build(self, in_name: Path):
        """
        This is the main working class for decoding the FreeCAD

        Args:
            in_name: the path where the json is stored under.
        """

        definition = json.loads(in_name.read_text())

        name = definition["name"]
        cut_features = []
        if FreeCAD.ActiveDocument:
            FreeCAD.closeDocument(name)
        doc = App.newDocument(name)
        for data in definition["features"]:
            if data["type"] == "add":
                solid = self.cube(data)

            elif data["type"] == "cut":
                if data["name"] == "hole":
                    cut_features.append(self.hole(data))
                elif data["name"] == "beveled_edge":
                    solid = self.decode_beveled_edge(data, solid)
                elif data["name"] == "cube":
                    cut_features.append(self.cube(data))
                elif data["name"] == "nut":
                    cut_features.append(self.cut_nut(data))

        if len(cut_features) > 1:
            s1 = cut_features.pop()
            fused = s1.multiFuse(cut_features)
            result = solid.cut(fused)
        elif len(cut_features) == 1:
            s1 = cut_features.pop()
            result = solid.cut(s1)
        else:
            result = solid
        Part.show(result)
        doc.recompute()
        FreeCADGui.activeDocument().activeView().viewTop()
        FreeCADGui.SendMsgToActiveView("ViewFit")

        filepath = f"{self._base_path}/{name}/{name}"
        doc.saveCopy(str(f"{filepath}.FCStd"))
        self.render_to_png(Path(filepath))
        self.render_to_dxf(doc, Path(filepath))
        self.render_to_stl(doc, Path(filepath))
        App.closeDocument(name)

        QtGui.QApplication.quit()


json_file = os.getenv("CYCAX_JSON")
out_dir = os.getenv("CYCAX_CWD")
logging.error(f"Json file {json_file} out dir = {out_dir}")
engine = EngineFreecad(Path(out_dir))
engine.build(Path(json_file))
