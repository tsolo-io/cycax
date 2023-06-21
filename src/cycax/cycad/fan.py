from cycax.cycad.cuboid import Cuboid


class Fan(Cuboid):
    """This class will initializa a fan cut out in the sheet metal specified.

    Args:
        width: Width of the fan. This will be used to create the fan's square bounding box.
        depth: The depth of the fan, used to make the bounding box.
        part_no: The specific part number of the fan.
        internal: This is a boolean to establish whether the fan is external or internal. If the fan is internal slots will be cut out and if it is external a big hole will be cut.
        hole_depth: The depth of the material the fan will be set to cut out. This is automated for 2mm steel.
        hole_diameter: The diamter of the securing holes of the fan. This is automated to 3mm.
    """

    def __init__(
        self,
        width: float,
        depth: float,
        part_no: str,
        internal: bool = True,
        hole_depth: float = 2.0,
        hole_diameter: float = 3.0,
    ):
        super().__init__(part_no=part_no, x_size=width, y_size=width, z_size=depth)
        self.border = 1
        self.diameter = width - 2 * self.border
        self.internal = internal
        self.hole_x = width / 2
        self.hole_y = width / 2
        self.hole_depth = hole_depth
        self.hole_diameter = hole_diameter

        self.calculate()

    def calculate(self):
        """
        This method will be called within the init method and based on whether the specfied fan is external or internal it will call the relevant method.
        """
        if self.internal:
            self.interna()
        else:
            self.externa()

        self.securing_holes()

    def securing_holes(self):
        """
        This method will cut the securing_holes of the fan into the sheet_metal.
        """
        start_x = self.hole_x - self.diameter / 2 + self.hole_diameter / 2
        start_y = self.hole_y - self.diameter / 2 + self.hole_diameter / 2
        end_x = self.hole_x + self.diameter / 2 - self.hole_diameter / 2
        end_y = self.hole_y + self.diameter / 2 - self.hole_diameter / 2
        for working_x in [start_x, end_x]:
            for working_y in [start_y, end_y]:
                self.top.hole(pos=[working_x, working_y], diameter=self.hole_diameter, depth=2, external_only=True)
                self.top.hole(pos=[working_x, working_y], diameter=self.hole_diameter, depth=self.z_size)

    def externa(self):
        """
        This method will cut a large hole in the SheetMetal for the fan.
        """
        self.top.hole(pos=[self.hole_x, self.hole_y], diameter=self.diameter, depth=2, external_only=True)

    def interna(self):
        """
        This method will cut multiple slots into the SheetMetal surface to make gaps that will allow the internal fan to circulate the air.
        """
        slot_area = self.diameter - 16
        slots = int((slot_area) / 8)
        spaces = (slot_area + 8 - slots * 4) / (slots + 1)
        start_x = self.hole_x - self.diameter / 2
        finish_y = self.hole_y - spaces / 2 - 2
        start_y = self.hole_y + spaces / 2 + 2
        while start_y < self.diameter / 2 + self.hole_y - 8:
            self.top.slot(
                pos=[start_x, start_y],
                width=self.diameter,
                length=4,
                depth=self.hole_depth,
                external_only=True,
            )
            self.top.slot(
                pos=[start_x, finish_y],
                width=self.diameter,
                length=4,
                depth=self.hole_depth,
                external_only=True,
            )
            start_y = start_y + spaces + 4
            finish_y = finish_y - spaces - 4
        self.top.slot(
            pos=[
                self.hole_x - self.diameter / 2 + self.hole_diameter + 2,
                self.hole_y + self.diameter / 2 - self.hole_diameter / 2,
            ],
            width=self.diameter - 2 * self.hole_diameter - 4,
            length=4,
            depth=self.hole_depth,
            external_only=True,
        )
        self.top.slot(
            pos=[
                self.hole_x - self.diameter / 2 + self.hole_diameter + 2,
                self.hole_y - self.diameter / 2 + self.hole_diameter / 2,
            ],
            width=self.diameter - 2 * self.hole_diameter - 4,
            length=4,
            depth=self.hole_depth,
            external_only=True,
        )
