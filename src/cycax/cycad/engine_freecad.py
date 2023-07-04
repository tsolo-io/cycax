import Part
# from PySide import QtGui
from FreeCAD import Vector, Rotation
import Draft
from math import sqrt
import json
import sys
from pathlib import Path

# 1. Open the file up in FreeCAD and run as a Macro.
# 2. Run from command line. ./FreeCAD.AppImage img.py


def box(feature):
    if feature["center"]==True:
        x=feature["x"]-feature["x_size"]/2
        y=feature["y"]-feature["y_size"]/2
        z=feature["z"]-feature["z_size"]/2
    else:
        x=feature["x"]
        y=feature["y"]
        z=feature["z"]
    pos_vec = (x, y, z)
        
    pos_vec=_move_cube(feature, pos_vec)
    pos=FreeCAD.Vector(pos_vec[0],pos_vec[1], pos_vec[2])
    length = feature["x_size"]
    width = feature["y_size"]
    depth = feature["z_size"]
    return Part.makeBox(length, width, depth, pos)

def calc_hex(depth, diameter):
    a=diameter/2
    vector_list=[]
    z=depth
    for x in [a, -a]:
        vector_list.append(Vector(x, 0, z))
    for x in [a/2, -a/2]:
        for y in [a*sqrt(3)/2, -a*sqrt(3)/2]:
            vector_list.append(Vector(x, y, z))
    vector_list.append(Vector(a, 0, depth))
    return vector_list

def cut_hex(feature):
        hex=Part.makePolygon(calc_hex(depth=0, diameter=3))
        hex2=Part.makePolygon(calc_hex(depth=feature["depth"], diameter=2))
        nut=Part.makeSolid(Part.makeRuledSurface(hex, hex2))
        if feature["side"]=="FRONT" or feature["side"]=="BACK":
            nut.Placement = App.Placement(
                Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(1, 0, 0), 270)
            )
    

        elif feature["side"]=="TOP" or feature["side"]=="BOTTOM":
            nut.Placement = App.Placement(
                Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(0, 0, 1), 0)
            )

        elif feature["side"]=="LEFT" or feature["side"]=="RIGHT":
            nut.Placement = App.Placement(
                Vector(feature["x"], feature["y"], feature["z"]),App.Rotation(Vector(0, 1, 0), 90)
            )
        return nut

def _move_cube(features: dict, pos_vec) -> str:
        """
        Accounts for when a cube is not going to penetrate the surface but rather sit above is.

        Args:
            features: This is the dictionary that contains the deatails of where the cube must be places and its details.
        """

        angles = [0, 0, 0]
        if features["side"] is not None:
            angles = features["side"]
            angles = {
                "TOP": [pos_vec[0], pos_vec[1], pos_vec[2]-features["z_size"]],
                "BACK": [pos_vec[0]-features["y_size"], pos_vec[1], pos_vec[2]],
                "BOTTOM": [pos_vec[0], pos_vec[1], pos_vec[2]],
                "FRONT": [pos_vec[0], pos_vec[1], pos_vec[2]],
                "LEFT": [pos_vec[0], pos_vec[1], pos_vec[2]],
                "RIGHT": [pos_vec[0],pos_vec[1]-features["x_size"], pos_vec[2]],
            }[angles]

        return angles


def cylinder(feature):
    pos_vec = FreeCAD.Vector(0, 0, 0)
    cyl = Part.makeCylinder(feature["diameter"]/2, feature["depth"], pos_vec)
    if feature["side"] == "FRONT" or feature["side"] == "BACK":
        cyl.Placement = App.Placement(
            Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(1, 0, 0), 270)
        )
    elif feature["side"] == "TOP" or feature["side"] == "BOTTOM":
        cyl.Placement = App.Placement(
            Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(0, 0, 1), 0)
        )
    elif feature["side"] == "LEFT" or feature["side"] == "RIGHT":
        cyl.Placement = App.Placement(
            Vector(feature["x"], feature["y"], feature["z"]), App.Rotation(Vector(0, 1, 0), 90)
        )
    #cyl.Placement = App.Placement(Vector(0, 0, 0), App.Rotation(Vector(1, 0, 0), 90))
    return cyl

def render_to_png(active_doc, target_path, name):
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


def render_to_dxf(active_doc, target_path, name):
    __objs__ = []
    __objs__.append(FreeCAD.getDocument(name).getObject("Shape"))
    import importDXF

    print(__objs__, str(f"{target_path}{name}-perspective.dxf"))
    importDXF.export(__objs__, str(f"{target_path}{name}-perspective.dxf"))



with open("definition.json") as fp:
    definition = json.load(fp)

name=definition["name"]
filepath = "/home/helen/tsolo/test_room/"
cut_features = []
for data in definition["parts"]:
    if data:
        if FreeCAD.ActiveDocument:
            FreeCAD.closeDocument(name)
        doc = App.newDocument(name)
        
        if data["type"]=="add":
            solid = box(data)

        if data["type"]=="cut":
            if data["name"] == "hole":
                cut_features.append(cylinder(data))
            elif data["name"] == "cube":
                cut_features.append(box(data))
            elif data["name"] == "nut":
                cut_features.append(cut_hex(data))

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
App.closeDocument(name)

# QtGui.QApplication.quit()
