from Part import Part


class Sheet_Metal(Part):
    """Class stores the data of the Bottom of a box."""

    def __init__(
        self, part_no: str, x_size: float, y_size: float, z_size: float, colour="grey"
    ):
        super().__init__(
            x=0,
            y=0,
            z=0,
            side=None,
            part_no=part_no,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
        )
        self.colour = colour

    def export(self):
        dict_metal = {
            "name": "cube",
            "type": "add",
            "side": None,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "X_width": self.x_size,
            "Y_length": self.y_size,
            "Z_depth": self.z_size,
            "center": False,
        }
        """This will eport the sheet_metal creating a dict of it."""

        dict_part = []

        dict_part.append(dict_metal)
        for item in self.features:
            ret = item.export()
            if type(ret) != dict:
                for part in ret:
                    dict_part.append(part)
            else:
                dict_part.append(ret)
        return dict_part
