import os
import sys

import stl  # TODO: Add to pyprojects

from cycax.cycad.cycad_part import CycadPart


class ExternalPart(CycadPart):
    """This class allows for external parts to be added into the object.
    These external STLs can be editted in similar ways to ones created in the program.

    Args:
        part_no : The unique name that will be given to a type of parts.
        colour: This will specify the colour of the object and can be overwritten from purple.

    """

    def __init__(self, part_no: str, x_size: float = 0.0, y_size: float = 0.0, z_size: float = 0.0, colour="purple"):
        super().__init__(
            x=0, y=0, z=0, side=None, part_no=part_no, x_size=x_size, y_size=y_size, z_size=z_size
        )  # initialized to location (0,0,0)
        self.name = "cube"
        if x_size == y_size == z_size == 0.0:
            self.name = "external"
            self.calculate()
        self.colour = colour

    def calculate(self):
        """
        This function will be used to find the bounding box of the STL that is being imported.
        It makes use of the python stl function.
        """
        STLname = "./parts_stl/" + self.part_no + ".stl"
        if not os.path.exists(STLname):
            sys.exit("ERROR: file %s was not found!" % STLname)
        stl_object = stl.mesh.Mesh.from_file(STLname)
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

    def export(self) -> dict:
        """
        This method will take the values stored within the part and export it to a dict so that it can be decoded.

        Returns:
            dict : The dictionary of the part.
        """
        dict_external = {
            "name": self.name,
            "type": "add",
            "side": None,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "x_size": self.x_size,
            "y_size": self.y_size,
            "z_size": self.z_size,
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
