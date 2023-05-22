from sheet_metal import sheet_metal
import json
from con_cube import con_cube
from decode import decode
from assembly_stl import assembly_stl
import os
from decode import decode

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class assembly:
    def __init__(self, part_number: str):
        """initializes the assmebly."""
        self.part_number = part_number
        self.decoder = decode()
        self.assembler = assembly_stl(part_number)
        self.pieces = []

    def render(self):
        """This class is used to control the assembly of the object and does a few checks to check its status."""
        datafile = self.export()
        for part in datafile:
            name = part["part_no"]

            SCADname = "./SCAD/" + name + ".scad"
            if os.path.exists(SCADname):
                pass
            else:
                print("Creating a SCAD file of the pieces of the object.")
                self.decoder.decode(name)

            STLname = "./STL/" + name + ".stl"
            if os.path.exists(STLname):
                pass
            else:
                self.decoder.render_stl(name)

        jsonFile = open("./JSON/" + self.part_number + ".json", "w")
        jsonStr = json.dumps(datafile, indent=4)
        jsonFile.write(jsonStr)
        jsonFile.close()
        print("moving to the assembler")
        self.assembler.assembly_stl()

    def add(self, part, make_file=False):
        """This adds a new object into the assembly and decodes it into a json if that's what the user wants

        !!!make_file is there so that making the json can be avoided when a duplicate part is added but only one side has holes trasfered onto it
        In the main, the Left has holes transferred onto it but not the right, so we want to make sure that we only json the right.

        This make_file will be deprecated once the commented code is functional, it will save the json that is bigger and therefor containing more information.
        """

        if make_file:
            jsonFile = open("./JSON/" + part.part_no + ".json", "w")
            jsonStr = json.dumps(part.export(), indent=4)
            jsonFile.write(jsonStr)
            jsonFile.close()

        # JSONname="./JSON/" + part.part_no + ".json"
        # if(os.path.exists(JSONname)):
        #     current =  os.stat(JSONname).st_size
        #     new= os.stat("./JSON/temp.json").st_size
        #     print(current, new)
        #     print("This is the OS stat")
        #     if new>=current:
        #         os.rename("./JSON/temp.json", JSONname)
        #         print("The new one is bigger")
        #     else:
        #        os.remove("./JSON/temp.json")
        #        print("The current one is bigger")
        # else:
        #     os.rename("./JSON/temp.json", JSONname)

        self.pieces.append(part)

    def export(self):
        """This creates a dict of the assembly, used to make the json."""
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

    def rotateFreezeTop(self, part):
        """This method will hold the front and the left while holding the top where it currently is."""

        part.rotate[2] = part.rotate[2] + 90
        part.x_max, part.y_max = part.y_max, part.x_max
        part.x_min, part.y_min = part.y_min, part.x_min
        part.make_bounding_box()
        part.rotmax = [
            part.x_max - part.x_min,
            part.y_max - part.y_min,
            part.z_max - part.z_min,
        ]

    def rotateFreezeLeft(self, part):
        """This method will rotate the top and front while holding the left where it currently is."""

        part.rotate[0] = part.rotate[0] + 90
        part.y_max, part.z_max = part.z_max, part.y_max
        part.y_min, part.z_min = part.z_min, part.y_min
        part.make_bounding_box()
        part.rotmax = [
            part.x_max - part.x_min,
            part.y_max - part.y_min,
            part.z_max - part.z_min,
        ]

    def rotateFreezeFront(self, part):
        """This method will rotate the left and top while holding the front where it currently is."""

        part.rotate[1] = part.rotate[1] + 90
        part.x_max, part.z_max = part.z_max, part.x_max
        part.x_min, part.z_min = part.z_min, part.x_min
        part.make_bounding_box()
        part.rotmax = [
            part.x_max - part.x_min,
            part.y_max - part.y_min,
            part.z_max - part.z_min,
        ]

    def level(self, part1, side1: str, part2, side2: str):
        """level takes the plane of part 2 specified and moves part 1 so that its specified side has a plane equal to part 2.
        part1 "FRONT" part2 "BACK" will gve part 1 and part 2 a front and back which are on the same plane. It moves part1.
        """
        part2.make_bounding_box()
        part1.make_bounding_box()
        to_here = part2.bounding_box[side2]
        if side1 == BOTTOM:
            part1.at(Z=to_here)
        if side1 == TOP:
            z_size = part1.z_max - part1.z_min
            part1.at(Z=to_here - z_size)
        if side1 == LEFT:
            part1.at(X=to_here)
            x_size = part1.x_max - part1.x_min
        if side1 == RIGHT:
            x_size = part1.x_max - part1.x_min
            part1.at(X=to_here - x_size)
        if side1 == FRONT:
            part1.at(Y=to_here)
        if side1 == BACK:
            y_size = part1.y_max - part1.y_min
            part1.at(Y=to_here - y_size)

        part1.make_bounding_box()

    def final_place(self, part):
        """This class should be private. It is used to move the move_holes to their final location before they are subtracted from the other part."""
        for hole in part.move_holes:
            hole.swapYZ(part.rotate[0] / 90, part.rotmax[1])
            hole.swapXZ(part.rotate[1] / 90, part.rotmax[2])
            hole.swapXY(part.rotate[2] / 90, part.rotmax[0])
            if part.moves[0] != 0:
                hole.at(x=part.moves[0])
            if part.moves[1] != 0:
                hole.at(y=part.moves[1])
            if part.moves[2] != 0:
                hole.at(z=part.moves[2])
        part.final_location = True

    def subtract(self, part1, side: str, part2):
        """This method adds the hols of part2 to the part1 on the side where they touch. This method will be used for moving around concube and harddive screw holes."""
        if (part2.final_location) != True:
            self.final_place(part2)
        Holes = part2.move_holes

        for hole in Holes:
            if side == TOP:
                if hole.z == part1.bounding_box[TOP]:
                    hole.side = TOP
                    part1.insert_hole(hole)
            if side == BOTTOM:
                if hole.z == part1.bounding_box[BOTTOM]:
                    hole.side = BOTTOM
                    part1.insert_hole(hole)
            if side == LEFT:
                if hole.x == part1.bounding_box[LEFT]:
                    hole.side = LEFT
                    part1.insert_hole(hole)
            if side == RIGHT:
                if hole.x == part1.bounding_box[RIGHT]:
                    hole.side = RIGHT
                    part1.insert_hole(hole)
            if side == FRONT:
                if hole.y == part1.bounding_box[FRONT]:
                    hole.side = FRONT
                    part1.insert_hole(hole)
            if side == BACK:
                if hole.y == part1.bounding_box[BACK]:
                    hole.side = BACK
                    part1.insert_hole(hole)
