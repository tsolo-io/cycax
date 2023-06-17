from cycax.cycad.cycad_part import CycadPart
import os
import json


class Cuboid(CycadPart):
    """
    This class will contain information on the 3D printed part.
    This method will initialize a Cuboid at the desired location.

    Args:
        x_size : The size of x.
        y_size : The size of y.
        z_size : The siez of z.
        part_no : The unique name that will be given to a type of parts.
        colour: This will specify the colour of the object and can be overwritten from red.

    """

    def __init__(self, part_no: str, x_size: float, y_size: float, z_size: float, colour: str = "red"):
        super().__init__(
            x=0,
            y=0,
            z=0,
            side=None,
            part_no=part_no,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
        )  # initializes the cuboid to (0,0,0)
        self.colour = colour

    def export(self) -> dict:
        """
        This method will take the values stored within the part and export it to a dict so that it can be decoded.

        Returns:
            dict : The dictionary of the part.
        """

        dict_cube = {
            "name": "cube",
            "type": "add",
            "side": self.side,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "x_size": self.x_size,
            "y_size": self.y_size,
            "z_size": self.z_size,
            "center": False,
        }
        dict_part = []

        dict_part.append(dict_cube)
        for item in self.features:
            ret = item.export()
            if type(ret) != dict:
                for part in ret:
                    dict_part.append(part)
            else:
                dict_part.append(ret)
        return dict_part
    
    def save(self):
        """
        This takes the provided part and will create its dictionary and export it to a json
        """
        dir_name = f"{os.getcwd()}/{self.part_no}"
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        with open(f"{dir_name}/{self.part_no}.json", "w") as jsonfile:
            json.dump(self.export(), jsonfile, indent=4)
