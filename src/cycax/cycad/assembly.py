import copy
import json
import logging
import os

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

    def render(self):
        """
        This class is used to control the assembly of the object and does a few checks to determine its status.
        """
        datafile = self.export()
        for part in datafile:
            name = part["part_no"]

            STLname = "{cwd}/{name}/{name}.stl".format(cwd=os.getcwd(), name=name)
            if not os.path.exists(STLname):
                SCADname = "{cwd}/{name}/{name}.scad".format(cwd=os.getcwd(), name=name)
                if not os.path.exists(SCADname):
                    logging.info("Creating a SCAD file of the pieces of the object.")
                    self.decoder.decode(name)
                else:
                    pass
                self.decoder.render_stl(name)
            else:
                pass

        dir_name = f"{os.getcwd()}/{self.part_number}"
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        with open(f"{dir_name}/{self.part_number}.json", "w") as jsonfile:
            json.dump(self.export(), jsonfile, indent=4)

        logging.info("moving to the assembler")
        self.assembler.assembly_openscad()

    def save(self):
        """
        !!!!There is a comment about this method in the jira ticket to assert its relevance.
        """
        for item in self.pieces:
            self.add(item)
        self.export()

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
                part1.features.append(item)
            for item in part2.move_holes:
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

        dir_name = f"{os.getcwd()}/{part.part_no}"
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        with open("./temp.json", "w") as jsonfile:
            json.dump(part.export(), jsonfile, indent=4)

        JSONname = f"{dir_name}/{part.part_no}.json"
        if os.path.exists(JSONname):  # checking if the file is already in the directory.
            current = os.stat(JSONname).st_size
            new = os.stat("./temp.json").st_size
            if new >= current:  # addind the file if it is bigger.
                os.rename("./temp.json", JSONname)
            else:  # removing the file if it is not bigger.
                os.remove("./temp.json")
        else:  # renaming the file if there isn't one already in the file.
            os.rename("./temp.json", JSONname)

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

        part.rotate[2] = part.rotate[2] + 90
        part.x_max, part.y_max = part.y_max, part.x_max
        part.x_min, part.y_min = part.y_min, part.x_min
        part.make_bounding_box()

    def rotateFreezeLeft(self, part: CycadPart):
        """
        This method will rotate the top and front while holding the left where it currently is.
        Args:
            part: This is the part that will be rotated.
        """

        part.rotate[0] = part.rotate[0] + 90
        part.y_max, part.z_max = part.z_max, part.y_max
        part.y_min, part.z_min = part.z_min, part.y_min
        part.make_bounding_box()

    def rotateFreezeFront(self, part: CycadPart):
        """
        This method will rotate the left and top while holding the front where it currently is.
        Args:
            part: This is the part that will be rotated.
        """

        part.rotate[1] = part.rotate[1] + 90
        part.x_max, part.z_max = part.z_max, part.x_max
        part.x_min, part.z_min = part.z_min, part.x_min
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
        for hole in range(len(part.move_holes)):
            temp_hole = copy.deepcopy(part.move_holes[hole])
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
            part.move_holes[hole] = temp_hole
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
