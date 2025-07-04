# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""
This file is called directly from FreeCAD.

Run from command line. ./FreeCAD.AppImage cycax_part_freecad.py
"""

import json
import logging
import os
import time
from math import sqrt
from pathlib import Path

import FreeCAD as App
import FreeCADGui
import importDXF
import importSVG

# import QtGui
import Part
from FreeCAD import Rotation, Vector  # NoQa
from PySide import QtGui

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.info("Opened in FreeCAD")

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"
REAR = "BACK"


class EngineFreecad:
    """This class will be used in FreeCAD to decode a JSON passed to it.
    The JSON will contain specific information of the object.

    Args:
        part_path: the path where the outputs need to be stored.
    """

    def __init__(self, part_path: Path):
        self._part_path = part_path
        self.filepath = ""

    def cube(self, feature: dict):
        """This method will draw a cube when given a dict that contains the necessary dimensions

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

        pos_vec = self._move_cube(feature, pos_vec, center=feature["center"])
        pos = Vector(pos_vec[0], pos_vec[1], pos_vec[2])
        length = feature["x_size"]
        width = feature["y_size"]
        depth = feature["z_size"]
        return Part.makeBox(length, width, depth, pos)

    def sphere(self, feature: dict):
        """This method will draw a sphere when given a dict that contains the necessary dimensions

        Args:
            feature: This is the dict that contains the necessary details of the sphere to be cut out.
        """
        x = feature["x"]
        y = feature["y"]
        z = feature["z"]
        pos_vec = (x, y, z)
        radius = feature["diameter"] / 2

        pos = Vector(pos_vec[0], pos_vec[1], pos_vec[2])
        return Part.makeSphere(radius, pos)

    def _calc_hex(self, depth: float, diameter: float):
        """This method will be used to find out where the points of the hexigon are located and then drawing a hexigon.

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

        hexigon = self._calc_hex(depth=0, diameter=feature["diameter"])
        nut = hexigon.extrude(App.Vector(0, 0, feature["depth"]))

        side = feature["side"]
        x = feature["x"]
        y = feature["y"]
        z = feature["z"]

        if feature["vertical"] is True:
            rotation1 = App.Rotation(Vector(0, 0, 1), 0)
        else:
            rotation1 = App.Rotation(Vector(0, 0, 1), 30)

        if side == FRONT:
            rotation2 = App.Rotation(Vector(1, 0, 0), 270)
        elif side == BACK:
            rotation2 = App.Rotation(Vector(1, 0, 0), 90)
        elif side == TOP:
            rotation2 = App.Rotation(Vector(0, 1, 0), 180)
        elif side == BOTTOM:
            rotation2 = App.Rotation(Vector(0, 1, 0), 0)
        elif side == LEFT:
            rotation2 = App.Rotation(Vector(0, 1, 0), 90)
        elif side == RIGHT:
            rotation2 = App.Rotation(Vector(0, 1, 0), 270)

        nut.Placement = App.Placement(Vector(x, y, z), rotation2 * rotation1)

        return nut

    def _move_cube(self, features: dict, pos_vec, *, center=False):
        """
        Accounts for when a cube is not going to penetrate the surface but rather sit above is.

        Args:
            features: This is the dictionary that contains the details of where the cube must be placed.
            pos_vec(list): where part is positioned.

        Returns:
        """

        angles = [0, 0, 0]
        if center is False:
            if features["side"] is not None:
                angles = features["side"]
                angles = {
                    TOP: [pos_vec[0], pos_vec[1], pos_vec[2] - features["z_size"]],
                    BACK: [pos_vec[0], pos_vec[1] - features["y_size"], pos_vec[2]],
                    BOTTOM: [pos_vec[0], pos_vec[1], pos_vec[2]],
                    FRONT: [pos_vec[0], pos_vec[1], pos_vec[2]],
                    LEFT: [pos_vec[0], pos_vec[1], pos_vec[2]],
                    RIGHT: [pos_vec[0] - features["x_size"], pos_vec[1], pos_vec[2]],
                }[angles]
        else:
            angles = [pos_vec[0], pos_vec[1], pos_vec[2]]

        return angles

    def hole(
        self,
        feature: dict | None = None,
        depth: float | None = None,
        radius: float | None = None,
        move: dict | None = None,
        side: str | None = None,
    ):
        """This method will be used for cutting a cylindrical hole into a surface.

        Args:
            feature: This is the dictionary that contains the details of where the hole must be placed and its details.
        """
        pos_vec = Vector(0, 0, 0)
        if feature is not None:
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
        if side == FRONT:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(1, 0, 0), 270))
        elif side == BACK:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(1, 0, 0), 90))
        elif side == TOP:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 180))
        elif side == BOTTOM:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 0))
        elif side == LEFT:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 90))
        elif side == RIGHT:
            cyl.Placement = App.Placement(Vector(x, y, z), App.Rotation(Vector(0, 1, 0), 270))
        return cyl

    def render_to_png(self, view: str | None = None):
        """Used to create a png of the desired side.

        Args:
            view: The side of the object the png will be produced from.

        """
        active_doc = FreeCADGui.activeDocument()
        view = self.change_view(active_doc=active_doc, side=view, default="ALL")
        FreeCADGui.SendMsgToActiveView("ViewFit")

        target_image_file = f"{self.filepath}-{view}.png"
        active_doc.activeView().fitAll()
        active_doc.activeView().saveImage(str(target_image_file), 2000, 1800, "White")

    def change_view(
        self,
        active_doc: FreeCADGui.activeDocument,
        side: str,
        default: str | None = None,
    ):
        """This will change the gui view to show the specified side.
        Args:
            active_doc: Freecad active doc.
            side: The side the view is from.
            default: The default side for that view.
        """

        if side is None:
            side = default

        match side.upper().strip():
            case "TOP":
                active_doc.activeView().viewTop()
            case "BACK":
                active_doc.activeView().viewRear()
            case "REAR":
                active_doc.activeView().viewRear()
            case "BOTTOM":
                active_doc.activeView().viewBottom()
            case "FRONT":
                active_doc.activeView().viewFront()
            case "LEFT":
                active_doc.activeView().viewLeft()
            case "RIGHT":
                active_doc.activeView().viewRight()
            case "ALL":
                active_doc.activeView().viewAxometric()
            case _:
                msg = f"side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT BACK OR ALL."
                raise ValueError(msg)
        return side

    def render_to_dxf(self, active_doc: App.Document, view: str | None = None):
        """This method will be used for creating a dxf of the object currently in view.
        Args:
            active_doc: The FreeCAD document.
            view: The side from which to produce the output file.
        """
        view_doc = FreeCADGui.activeDocument()
        view = self.change_view(active_doc=view_doc, side=view, default="TOP")
        FreeCADGui.SendMsgToActiveView("ViewFit")
        __objs__ = []
        __objs__.append(active_doc.getObject("Shape"))

        importDXF.export(__objs__, str(f"{self.filepath}-{view}.dxf"))

    def render_to_svg(self, active_doc: App.Document, view: str | None = None):
        """This method will be used for creating a svg of the object currently in view.
        Args:
            active_doc: The FreeCAD document.
            view: The side from which to produce the output file.
        """
        view_doc = FreeCADGui.activeDocument()
        view = self.change_view(active_doc=view_doc, side=view, default="TOP")
        FreeCADGui.SendMsgToActiveView("ViewFit")
        __objs__ = []
        __objs__.append(active_doc.getObject("Shape"))

        importSVG.export(__objs__, str(f"{self.filepath}-{view}.svg"))

    def render_to_stl(self, active_doc: App.Document):
        """This method will be used for creating a STL of an object currently in view.
        Args:
            active_doc: The FreeCAD document.
        """
        for obj in active_doc.Objects:
            if obj.ViewObject.Visibility:
                filename = f"{self.filepath}.stl"
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
                radius=features["size"],
                depth=features["depth"],
                side=features["side"],
                move=move_cutter_cyl,
            )

        elif features["edge_type"] == "chamfer":
            cutter = self._rhombus(
                depth=features["depth"],
                length=features["size"],
                move=move_cutter_rhombus,
                side=features["side"],
            )

        cube = self._beveled_edge_cube(
            length=features["size"],
            depth=features["depth"],
            side=features["side"],
            move=move_cube,
        )

        cutter = cube.cut(cutter)
        res = solid.cut(cutter)
        Part.cast_to_shape(res)

        return res

    def build(self, in_name: Path, outformats: str):
        """
        This is the main working class for decoding the FreeCAD

        Args:
            in_name: The path where the JSON is stored under.
            outformats: CSV containing views..
        """

        definition = json.loads(in_name.read_text())

        logging.info("Definition loaded from: %s", in_name)
        name = definition["name"]
        cut_features = []
        if App.ActiveDocument:
            App.closeDocument(name)
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
                elif data["name"] == "sphere":
                    solid = solid.cut(self.sphere(data))
                    # This was necessary to avoid creating a shape that was too complicate for FreeCAD to follow.
                elif data["name"] == "nut":
                    cut_features.append(self.cut_nut(data))

        logging.info("Features applied")
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
        logging.info("Part created")
        FreeCADGui.activeDocument().activeView().viewTop()
        FreeCADGui.SendMsgToActiveView("ViewFit")

        self.filepath = self._part_path / name
        doc.saveCopy(f"{self.filepath}.FCStd")
        logging.info("Part Saved")
        for out_choice in outformats.lower().split(","):
            ftype, fview = out_choice.split(":") if ":" in out_choice else (out_choice, None)
            out_format = ftype.upper().strip()
            match out_format:
                case "PNG":
                    self.render_to_png(view=fview)
                case "DXF":
                    self.render_to_dxf(view=fview, active_doc=doc)
                case "SVG":
                    self.render_to_svg(view=fview, active_doc=doc)
                case "STL":
                    self.render_to_stl(active_doc=doc)
                case _:
                    msg = f"file_type: {out_format} is not one of PNG, DXF or STL."
                    raise ValueError(msg)
        App.closeDocument(name)
        QtGui.QApplication.quit()


def get_next_job_path(jobs_path) -> dict:
    """Find the next job to work on.

    The jobs_path variable should point to a directory containing symlinks
    to cycax parts. Each part directory is evaluated to see if there is an
    JSON definition for the part.

    Args:
        jobs_path: The directory with symlinks to parts to process.

    """
    for jpath in sorted(jobs_path.iterdir()):
        if jpath.is_dir() and jpath.is_symlink():
            ret_path = jpath.readlink().expanduser().absolute()
            json_file_path = ret_path / f"{ret_path.name}.json"
            if json_file_path.exists():
                return {
                    "job_path": jpath,
                    "part_path": ret_path,
                    "part_json": json_file_path,
                }
            else:
                logging.warning(
                    "The job link %s is not valid, no JSON part definition; expect the file %s",
                    jpath,
                    json_file_path,
                )
        else:
            logging.warning("The path %s is not a symlinked directory, not treated as a job.", jpath)
    return None


def control_file(jobs_path: Path, name: str, *, start=False) -> bool:
    if name in ("quit", "finnish"):
        quit_file = jobs_path / f".{name}"
    else:
        logging.warning("Undefined control file requested .%s", name)
        return False

    if quit_file.exists():
        if start:
            logging.info(
                "Remove existing quit file (%s), recreate this file if you want the application to quit.",
                quit_file,
            )
        quit_file.unlink()
        return False
    return True


def main(freecad_jobs_path: Path):
    running = True
    while running:
        job_path = get_next_job_path(freecad_jobs_path)
        if job_path is None:
            running = control_file(freecad_jobs_path, "finnish")
            if running:
                time.sleep(0.1)
        else:
            logging.info("Got a job %s", job_path)
            files_to_produce = "PNG,STL,DXF"
            _start = time.time()
            engine = EngineFreecad(job_path["part_path"])
            engine.build(job_path["part_json"], files_to_produce.replace(" ", ""))
            logging.warning("Part creation took %s seconds", time.time() - _start)
            logging.warning("Job completed, removing symlink to part.")
            job_path["job_path"].unlink()

        running &= control_file(freecad_jobs_path, "quit")


# START
freecad_jobs_dir = os.getenv("CYCAX_JOBS_DIR")
if freecad_jobs_dir is None:
    logging.error("CYCAX_JOBS_DIR environment variable is not defined or set.")
    QtGui.QApplication.quit()

freecad_jobs_path = Path(freecad_jobs_dir)
if not freecad_jobs_path.is_dir():
    logging.error(f"Could not open {freecad_jobs_path}")
    QtGui.QApplication.quit()

control_file(freecad_jobs_path, "quit", start=True)
try:
    main(freecad_jobs_path)
except Exception:
    logging.exception("Unexpected")
logging.info("End of application. Normal termination.")
QtGui.QApplication.quit()
