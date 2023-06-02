import os
import sys

import stl
from CycadPart import CycadPart
from stl import mesh


class ExternalPart(CycadPart):
    def __init__(self, part_no: str, colour="purple"):
        """This class allows for external parts to be added into the object. These external stls can be editted in similar ways to ones created in the program."""
        super().__init__(0, 0, 0, None, part_no, 0, 0, 0)
        self.calculate()
        self.colour = colour

    def calculate(self):
        """This function will be used to find the bounding box of the stl that is being imported. It makes use of the python stl function."""
        STLname = "./parts_stl/" + self.part_no + ".stl"
        if not os.path.exists(STLname):
            sys.exit("ERROR: file %s was not found!" % STLname)
        stl_object = mesh.Mesh.from_file(STLname)
        for point in stl_object.points:
            self.x_max = max(point[stl.Dimension.X], self.x_max)
            self.x_min = min(point[stl.Dimension.X], self.x_min)
            self.y_max = max(point[stl.Dimension.Y], self.y_max)
            self.y_min = min(point[stl.Dimension.Y], self.y_min)
            self.z_max = max(point[stl.Dimension.Z], self.z_max)
            self.z_min = min(point[stl.Dimension.Z], self.z_min)

        self.x_size = self.x_max - self.x_min
        self.y_size = self.y_max - self.y_min
        self.z_size = self.z_max - self.z_min

        self.x, self.y, self.z = self.x_size / 2, self.y_size / 2, self.z_size / 2

        self.x_max = self.x_size
        self.x_min = 0
        self.y_max = self.y_size
        self.y_min = 0
        self.z_max = self.z_size
        self.z_min = 0

    def export(self):
        """This creates a dictionary for the external part so that is can be exported into a json and decoded."""
        dict_external = {
            "name": "external",
            "type": "add",
            "side": None,
            "x": str(self.x),
            "y": str(self.y),
            "z": str(self.z),
        }
        dict_part = []

        dict_part.append(dict_external)
        for item in self.features:
            ret = item.export()
            if type(ret) != dict:
                for part in ret:
                    dict_part.append(part)
            else:
                dict_part.append(ret)
        return dict_part
