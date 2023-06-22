import copy
import json
import logging
import os
from pathlib import Path

from cycax.cycad.assembly_openscad import AssemblyOpenSCAD
from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.cycad_side import CycadSide
from cycax.cycad.engine_openscad import EngineOpenSCAD
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class Assembly:
    """
    This Assembly class will take multiple different cycad parts and combine them together to form complex parts.

    Args:
        part_number: this is the destinct part number that the conplex part will have.
    """

    def __init__(self, part_number: str):
        self.part_number = part_number
        self.decoder = EngineOpenSCAD()
        self.assembler = AssemblyOpenSCAD(part_number)
        self.pieces = []
        self._base_path = Path(".")

    def render(self):
        """
        This class is used to control the assembly of the object and does a few checks to determine its status.
        """
        data = self.export()
        self.decoder.set_path(self._base_path)
        for part in data:
            # FIXME: Should just be: `part.render()` the part render should sort out its own stuff.
            name = part["part_no"]

            stl_name = "{cwd}/{name}/{name}.stl".format(cwd=self._base_path, name=name)
            if not os.path.exists(stl_name):
                scad_name = "{cwd}/{name}/{name}.scad".format(cwd=self._base_path, name=name)
                if not os.path.exists(scad_name):
                    logging.info("Creating SCAD file %s of the pieces of the object.", scad_name)
                    self.decoder.decode(name)
                self.decoder.render_stl(name)

        logging.info("Calling to the assembler")
        self.assembler.assembly_openscad(self._base_path)

    def save(self, path: Path | None = None):
        """
        Save the assembly and added part to JSON files.
        Args:
            path: The location where the assembly is stored. A directory for each part will be created in this path.
        """

        if path is None:
            path = Path(".")
        if not path.exists():
            msg = f"The directory {path} does not exists."
            raise FileNotFoundError(msg)

        for item in self.pieces:
            item.save(path)

        self._base_path = path
        data = self.export()
        data_filename = path / f"{self.part_number}.json"
        data_filename.write_text(json.dumps(data))

    def merge(self, part1: CycadPart, part2: CycadPart):
        """This method will be used to merge 2 parts together whcich have identical sizes but different features.

        Args:
            part1: this part will receive the features present on part2.
            part2: this part will receive the features present on part1.

        Raises:
            ValueError: if the sizes of the parts are not identical.
        """
        if (
            part1.size.x_size == part2.size.x_size
            and part1.size.y_size == part2.size.y_size
            and part1.size.z_size == part2.size.z_size
        ):
            for item in part2.features:
                if item not in part1.features:
                    part1.features.append(item)
            for item in part2.move_holes:
                if item not in part1.move_holes:
                    part1.move_holes.append(item)
            part2.features = part1.features
            part2.move_holes = part1.move_holes
        else:
            msg = f"merging {part1} and {part2} but they are not of the same size."
            raise ValueError(msg)

    def add(self, part: CycadPart):
        """
        This adds a new object into the assembly and decodes it into a json if that's what the user wants.
        Once the part has been added to the assembler it can no longer be moved around or eddited.

        Args:
            part: this in the part that will be added to the assembly.
        """

        self.pieces.append(part)

    def export(self):
        """
        This creates a dict of the assembly, used to make the json.
        """
        dict_out = []
        for item in self.pieces:
            dict_part = {
                "part_no": item.part_no,
                "rotmax": item.rotmax,
                "moves": item.moves,
                "rotate": item.rotate,
                "colour": item.colour,
            }
            dict_out.append(dict_part)
        return dict_out

    def rotateFreezeTop(self, part: CycadPart):
        """
        This method will hold the front and the left while holding the top where it currently is.
        Args:
            part: This is the part that will be rotated.
        """
        part.rotate[part.pos["z"]] = (part.rotate[part.pos["z"]] + 90) % 360
        part.x_max, part.y_max = part.y_max, part.x_max
        part.x_min, part.y_min = part.y_min, part.x_min
        part.pos["x"], part.pos["y"] = part.pos["y"], part.pos["x"]
        part.make_bounding_box()

    def rotateFreezeLeft(self, part: CycadPart):
        """
        This method will rotate the top and front while holding the left where it currently is.
        Args:
            part: This is the part that will be rotated.
        """
        part.rotate[part.pos["x"]] = (part.rotate[part.pos["x"]] + 90) % 360
        part.y_max, part.z_max = part.z_max, part.y_max
        part.y_min, part.z_min = part.z_min, part.y_min
        part.pos["z"], part.pos["y"] = part.pos["y"], part.pos["z"]
        part.make_bounding_box()

    def rotateFreezeFront(self, part: CycadPart):
        """
        This method will rotate the left and top while holding the front where it currently is.
        Args:
            part: This is the part that will be rotated.
        """
        part.rotate[part.pos["y"]] = (part.rotate[part.pos["y"]] + 90) % 360
        part.x_max, part.z_max = part.z_max, part.x_max
        part.x_min, part.z_min = part.z_min, part.x_min
        part.pos["x"], part.pos["z"] = part.pos["z"], part.pos["x"]
        part.make_bounding_box()

    def level(self, partside1: CycadSide, partside2: CycadSide):
        """
        level takes the plane of part 2 specified and moves part 1 so that its specified side has a plane equal to part 2.
        part1.front part2.back will gve part 1 and part 2 a front and back which are on the same plane. It moves part1.
        Args:
            partside1:This is the CycadSide that will be moved to match the plane of the other part.
            partside2: This is the Cycadside which will dictate the plane used to as a reference to move part1.
        Raises:
            ValueError: if the side present in CycadSide does not match one of the expected side.
        """
        part1 = partside1._parent
        part2 = partside2._parent
        side1 = partside1.name
        side2 = partside2.name
        part2.make_bounding_box()
        part1.make_bounding_box()
        to_here = part2.bounding_box[side2]

        if side1 == BOTTOM:
            part1.move(z=to_here)
        elif side1 == TOP:
            z_size = part1.z_max - part1.z_min
            part1.move(z=to_here - z_size)
        elif side1 == LEFT:
            part1.move(x=to_here)
            x_size = part1.x_max - part1.x_min
        elif side1 == RIGHT:
            x_size = part1.x_max - part1.x_min
            part1.move(x=to_here - x_size)
        elif side1 == FRONT:
            part1.move(y=to_here)
        elif side1 == BACK:
            y_size = part1.y_max - part1.y_min
            part1.move(y=to_here - y_size)
        else:
            msg = f"Side: {side1} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
            raise ValueError(msg)

        part1.make_bounding_box()

    def _final_place_(self, part):
        """
        This class should be private. It is used to move the move_holes to their final location before they are subtracted from the other part.
        """
        for hole_i, hole in enumerate(part.move_holes):
            temp_hole = copy.deepcopy(hole)
            rotation = [part.x_size, part.y_size, part.z_size]
            rotation = temp_hole.swap_yz(rot=part.rotate[0] / 90, rotmax=rotation)
            rotation = temp_hole.swap_xz(rot=part.rotate[1] / 90, rotmax=rotation)
            rotation = temp_hole.swap_xy(rot=part.rotate[2] / 90, rotmax=rotation)
            if part.moves[0] != 0:
                temp_hole.move(x=part.moves[0])
            if part.moves[1] != 0:
                temp_hole.move(y=part.moves[1])
            if part.moves[2] != 0:
                temp_hole.move(z=part.moves[2])
            part.move_holes[hole_i] = temp_hole
        part.final_location = True

    def subtract(self, partside1: CycadSide, part2: CycadPart):
        """
        This method adds the hols of part2 to the part1 on the side where they touch.
        This method will be used for moving around concube and harddive screw holes.

        Args:
            partside1: This is the part side that will receive the holes.
            part2: This is the part while will be used as the template when transferring holes.

        Raises:
            ValueError: if the side present in CycadSide does not match one of the expected side.
        """
        part1 = partside1._parent
        side = partside1.name

        if part2.final_location is not True:
            self._final_place_(part2)
        Holes = part2.move_holes

        for hole in Holes:
            if side == TOP:
                if hole.z == part1.bounding_box[TOP]:
                    hole.side = TOP
                    part1.insert_hole(hole)
            elif side == BOTTOM:
                if hole.z == part1.bounding_box[BOTTOM]:
                    hole.side = BOTTOM
                    part1.insert_hole(hole)
            elif side == LEFT:
                if hole.x == part1.bounding_box[LEFT]:
                    hole.side = LEFT
                    part1.insert_hole(hole)
            elif side == RIGHT:
                if hole.x == part1.bounding_box[RIGHT]:
                    hole.side = RIGHT
                    part1.insert_hole(hole)
            elif side == FRONT:
                if hole.y == part1.bounding_box[FRONT]:
                    hole.side = FRONT
                    part1.insert_hole(hole)
            elif side == BACK:
                if hole.y == part1.bounding_box[BACK]:
                    hole.side = BACK
                    part1.insert_hole(hole)
            else:
                msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
                raise ValueError(msg)
