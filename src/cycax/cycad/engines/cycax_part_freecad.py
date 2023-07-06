#
# This file is called directly from FreeCAD.
# CyCAx launches the FreeCAD binary and pass in:
# 1. The fullpath to this file.
# 2. The path to the part JSON file.
# 3. The path where the output files are stored.
#
import json
import logging
import sys
from math import sqrt
from pathlib import Path

import Draft  # NoQa
import Part

# from PySide import QtGui
from FreeCAD import Rotation, Vector  # NoQa

logging.error("Open FreeCAD")

# 1. Open the file up in FreeCAD and run as a Macro.
# 2. Run from command line. ./FreeCAD.AppImage img.py


class engine_freecad:
    def __init__(self):
        self._base_path = Path(".")

    def _cube(self, feature: dict):
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
        pos = FreeCAD.Vector(pos_vec[0], pos_vec[1], pos_vec[2])
        length = feature["x_size"]
        width = feature["y_size"]
        depth = feature["z_size"]
        return Part.makeBox(length, width, depth, pos)

    def _calc_hex(self, depth: float, diameter: float):
        """This method will be used to find out where the points of the hexigon are located so that is can be drawn.

        Args:
            depth: this is the depth of the hexigon.
            diameter: this is the diameter of the hexigon.
        """

        a = diameter / 2
        vector_list = []
        z = depth

        vector_list.append(Vector(a, 0, z))
        vector_list.append(Vector(a / 2, a * sqrt(3) / 2, z))
        vector_list.append(Vector(-a / 2, a * sqrt(3) / 2, z))
        vector_list.append(Vector(-a, 0, z))
        vector_list.append(Vector(-a / 2, -a * sqrt(3) / 2, z))
        vector_list.append(Vector(a / 2, -a * sqrt(3) / 2, z))

        vector_list.append(vector_list[0])
        wire = Part.makePolygon(vector_list)
        shape = Part.Shape(wire)
        face = Part.Face(shape)
        return face

    def _cut_hex(self, feature: dict):
        """This method will be used for drawing the actual hexigon that needs to be cut.
        Args:
            feature: this is a dict containing the necessary details of the hexigon like its size and location.
        """

        hex = _calc_hex(depth=0, diameter=3)
        nut = hex.extrude(App.Vector(0, 0, feature["depth"]))

        if feature["side"] in ["FRONT", "BACK"]:
            nut.Placement = App.Placement(Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(0, 30, 270))

        elif feature["side"] in ["TOP", "BOTTOM"]:
            nut.Placement = App.Placement(Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(30, 0, 0))

        elif feature["side"] in ["LEFT", "RIGHT"]:
            nut.Placement = App.Placement(Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(0, 90, 0))

        return nut

    def _move_cube(self, features: dict, pos_vec) -> tuple[float, float, float]:
        """
        Accounts for when a cube is not going to penetrate the surface but rather sit above is.

        Args:
            features: This is the dictionary that contains the deatails of where the cube must be places and its details.

        Returns:
        """

        angles = [0, 0, 0]
        if features["side"] is not None:
            angles = features["side"]
            angles = {
                "TOP": [pos_vec[0], pos_vec[1], pos_vec[2] - features["z_size"]],
                "BACK": [pos_vec[0] - features["y_size"], pos_vec[1], pos_vec[2]],
                "BOTTOM": [pos_vec[0], pos_vec[1], pos_vec[2]],
                "FRONT": [pos_vec[0], pos_vec[1], pos_vec[2]],
                "LEFT": [pos_vec[0], pos_vec[1], pos_vec[2]],
                "RIGHT": [pos_vec[0], pos_vec[1] - features["x_size"], pos_vec[2]],
            }[angles]

        return angles

    def _hole(self, feature):
        """This method will be used for cutting a cylindical hole into a surface."""
        pos_vec = FreeCAD.Vector(0, 0, 0)
        cyl = Part.makeCylinder(feature["diameter"] / 2, feature["depth"], pos_vec)
        if feature["side"] in ["FRONT", "BACK"]:
            cyl.Placement = App.Placement(
                Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(1, 0, 0), 270)
            )
        elif feature["side"] in ["TOP", "BOTTOM"]:
            cyl.Placement = App.Placement(
                Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(0, 0, 1), 0)
            )
        elif feature["side"] in ["LEFT", "RIGHT"]:
            cyl.Placement = App.Placement(
                Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(0, 1, 0), 90)
            )
        # cyl.Placement = App.Placement(Vector(0, 0, 0), App.Rotation(Vector(1, 0, 0), 90))
        return cyl

    def render_to_png(self, active_doc, target_path, name):
        active_doc = FreeCADGui.activeDocument()
        target_image_file = f"{target_path}{name}-perspective.png"
        FreeCADGui.SendMsgToActiveView("ViewFit")
        active_doc.activeView().viewAxometric()
        active_doc.activeView().fitAll()
        active_doc.activeView().saveImage(str(target_image_file), 2000, 1800, "White")
        print(f"Saved {target_image_file}")
        target_image_file = f"{target_path}{name}-perspective.png"
        FreeCADGui.SendMsgToActiveView("ViewFit")
        active_doc.activeView().viewTop()
        active_doc.activeView().fitAll()
        active_doc.activeView().saveImage(str(target_image_file), 2000, 1800, "White")
        print(f"Saved {target_image_file}")

    def render_to_dxf(self, active_doc, target_path, name):
        __objs__ = []
        __objs__.append(active_doc.getObject("Shape"))
        import importDXF

        print(__objs__, str(f"{target_path}{name}-perspective.dxf"))
        importDXF.export(__objs__, str(f"{target_path}{name}-perspective.dxf"))

    def decode(self, in_name: Path):
        # in_name = "{cwd}/{data}/{data}.json".format(cwd=self._base_path, data=part_name)
        definition = json.loads(in_name.read_text())

        name = definition["name"]
        filepath = self._base_path
        cut_features = []
        if FreeCAD.ActiveDocument:
            FreeCAD.closeDocument(name)
        doc = App.newDocument("beach")
        for data in definition.get("features", []):
            if data:
                if data["type"] == "add":
                    solid = _cube(data)

                if data["type"] == "cut":
                    if data["name"] == "hole":
                        cut_features.append(self._hole(data))
                    elif data["name"] == "cube":
                        cut_features.append(self._cube(data))
                    elif data["name"] == "nut":
                        cut_features.append(self._cut_hex(data))

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

        filepath = Path(filepath) / f"{name}.FCStd"
        doc.saveCopy(str(filepath))
        render_to_png(doc, Path(filepath), name)
        render_to_dxf(doc, Path(filepath), name)
        App.closeDocument("beach")

        # QtGui.QApplication.quit()


json_file = sys.argv[2]
out_dir = sys.argv[3]
logging.error(f"Json file {json_file} out dir = {out_dir}")
engine = engine_freecad()
engine._base_path = Path(out_dir)
engine.decode(Path(json_file))
