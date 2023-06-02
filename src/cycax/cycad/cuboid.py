from cycax.cycad.cycad_part import CycadPart


class Cuboid(CycadPart):
    def __init__(self, part_no: str, x_size: float, y_size: float, z_size: float, colour="red"):
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
        dict_cube = {
            "name": "cube",
            "type": "add",
            "side": None,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            # TODO: Update. Maybe just ?_size and not width,length, or depth.
            "x_width": self.x_size,
            "y_length": self.y_size,
            "z_depth": self.z_size,
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
