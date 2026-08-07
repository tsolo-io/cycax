# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# This file is called directly from FreeCAD.
# CyCAx launches the FreeCAD binary and passes in:
# 1. The fullpath to this file.
# 2. The path to the assembly JSON file; as environmental variable ("CYCAX_JSON")
# 3. The path to where the output files should be stored; as environmental variable ("CYCAX_CWD")
# 4. The file types that need to be generated; as environmental variable ("CYCAX_OUT_FORMATS")

# How to use this file:
# 1. Open the file up in FreeCAD and run as a Macro.
# 2. Run from command line. ./FreeCAD.AppImage cycax_assembly_freecad.py

import json
import logging
import os
from pathlib import Path

import FreeCAD
import FreeCAD as App
import FreeCADGui
import Import
import importDXF
import importSVG
import Part
from FreeCAD import Rotation, Vector
from PySide import QtGui

logging.info("Open FreeCAD for Assembly")

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


def axis_vector(axis: str) -> Vector:
    _axis = axis.lower()[0]
    if _axis == "x":
        return Vector(1, 0, 0)
    elif _axis == "y":
        return Vector(0, 1, 0)
    elif _axis == "z":
        return Vector(0, 0, 1)
    else:
        msg = f"Invalid axis: {_axis}"
        raise ValueError(msg)


class EngineFreecadAssembly:
    """This class will be used in FreeCAD to assemble parts from a JSON definition.

    Args:
        base_path: the path where the outputs need to be stored.
    """

    def __init__(self, base_path: Path):
        self._base_path = base_path
        self.filepath = ""
        self.name = ""

    def _import_part(self, part_no: str, base_path: Path):
        """Import a part STL or STEP file.

        Args:
            part_no: The part number/name to import.
            base_path: The base directory where parts are stored.

        Returns:
            The imported object in FreeCAD.
        """

        for made_by in ("freecad", "build123d", "openscad", None):
            for ext in ("step", "stl"):
                if made_by is None:
                    _file = base_path / part_no / f"{part_no}.{ext}"
                else:
                    _file = base_path / part_no / f"{part_no}-{made_by}.{ext}"
                if _file.exists():
                    obj = FreeCAD.ActiveDocument.addObject("Part::Feature", part_no)
                    obj.Shape = Part.read(str(_file))
                    logging.info(f"Imported {ext.upper()} made by {made_by} file: {_file}")
                    return obj

        logging.error(f"No STEP or STL file found for part: {part_no}")
        return None

    def _set_color(self, obj, colour: str):
        """Set the color of an object.

        Args:
            obj: FreeCAD object.
            colour: Color name (e.g., "orange", "blue").
        """
        color_map = {
            "orange": (1.0, 0.5, 0.0),
            "blue": (0.0, 0.0, 1.0),
            "red": (1.0, 0.0, 0.0),
            "green": (0.0, 1.0, 0.0),
            "yellow": (1.0, 1.0, 0.0),
            "purple": (0.5, 0.0, 0.5),
            "white": (1.0, 1.0, 1.0),
            "black": (0.0, 0.0, 0.0),
            "gray": (0.5, 0.5, 0.5),
            "grey": (0.5, 0.5, 0.5),
        }

        rgb = color_map.get(colour.lower(), (1.0, 0.5, 0.0))  # Default to orange
        if hasattr(obj, "ViewObject") and obj.ViewObject:
            obj.ViewObject.ShapeColor = rgb

    def render_to_png(self, view: str | None = None):
        """Used to create a png of the desired view.

        Args:
            view: The side of the object the png will be produced from.
        """
        active_doc = FreeCADGui.activeDocument()
        view = self.change_view(active_doc=active_doc, side=view, default="ALL")
        FreeCADGui.SendMsgToActiveView("ViewFit")

        target_image_file = f"{self.filepath}-{view}.png"
        active_doc.activeView().fitAll()
        active_doc.activeView().saveImage(str(target_image_file), 2000, 1800, "White")

    def change_view(self, active_doc: FreeCADGui.activeDocument, side: str, default: str | None = None):
        """This will change the gui view to show the specified side.

        Args:
            active_doc: FreeCAD active doc.
            side: The side the view is from.
            default: The default side for that view.
        """
        if side is None:
            side = default

        match side.upper().strip():
            case "TOP":
                active_doc.activeView().viewTop()
            case "BACK" | "REAR":
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
                msg = f"side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK OR ALL."
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
        __objs__ = [obj for obj in active_doc.Objects if obj.ViewObject.Visibility]

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
        __objs__ = [obj for obj in active_doc.Objects if obj.ViewObject.Visibility]

        importSVG.export(__objs__, str(f"{self.filepath}-{view}.svg"))

    def render_to_stl(self, active_doc: App.Document):
        """This method will be used for creating a STL of the assembly.

        Args:
            active_doc: The FreeCAD document.
        """
        # Export all visible objects
        visible_objects = [obj for obj in active_doc.Objects if obj.ViewObject.Visibility]

        if visible_objects:
            # Fuse all parts into a single compound
            shapes = [obj.Shape for obj in visible_objects if hasattr(obj, "Shape")]
            if shapes:
                compound = Part.makeCompound(shapes)
                filename = f"{self.filepath}.stl"
                compound.exportStl(filename)
                logging.info(f"Exported assembly STL: {filename}")

                # Also export STEP
                filename_step = f"{self.filepath}.step"
                compound.exportStep(filename_step)
                logging.info(f"Exported assembly STEP: {filename_step}")

    def build(self, definition: dict, outformats: str):
        """Assemble parts based on the JSON definition.

        Args:
            definition: Assembly definition from JSON.
            outformats: CSV containing output formats.
        """
        self.name = definition["name"]

        # Close existing document if it exists
        if FreeCAD.ActiveDocument:
            FreeCAD.closeDocument(self.name)

        # Create new document
        doc = FreeCAD.newDocument(self.name)

        # Import and position each part
        for part_data in definition["parts"]:
            part_no = part_data["part_no"]
            position = part_data["position"]
            rotate_list = part_data["rotate"]
            part_data["rotmax"]
            colour = part_data.get("colour", "orange")
            # Import the part
            obj = self._import_part(part_no, self._base_path)

            if obj:
                for rotation_spec in rotate_list:
                    rotation = Rotation(axis_vector(rotation_spec["axis"]), rotation_spec["angle"])
                    obj.Placement.Rotation = rotation * obj.Placement.Rotation

                bounding_box = obj.Shape.BoundBox
                mx = position[0] - bounding_box.XMin
                my = position[1] - bounding_box.YMin
                mz = position[2] - bounding_box.ZMin
                obj.Placement.Base += FreeCAD.Vector(mx, my, mz)

                # Set color
                self._set_color(obj, colour)

        # Recompute the document
        doc.recompute()
        FreeCADGui.activeDocument().activeView().viewAxometric()
        FreeCADGui.SendMsgToActiveView("ViewFit")

        # Save the assembly
        self.filepath = self._base_path / f"{self.name}-freecad"
        doc.saveCopy(f"{self.filepath}.FCStd")

        # Generate output formats
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
                    msg = f"file_type: {out_format} is not one of PNG, DXF, SVG or STL."
                    raise ValueError(msg)

        App.closeDocument(self.name)


try:
    json_file = os.getenv("CYCAX_JSON")
    out_dir = os.getenv("CYCAX_CWD")
    files_to_produce = os.getenv("CYCAX_OUT_FORMATS", "STL,PNG")

    engine = EngineFreecadAssembly(Path(out_dir))

    definition = json.loads(Path(json_file).read_text())
    logging.info(f"Assembly JSON file: {json_file}, output dir: {out_dir}")
    engine.build(definition, files_to_produce.replace(" ", ""))
except Exception as error:
    logging.exception(error)
    raise error
finally:
    QtGui.QApplication.quit()
