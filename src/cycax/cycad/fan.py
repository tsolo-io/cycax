from cycax.cycad.sheet_metal import SheetMetal


class Fan:
    """This class will initializa a fan cut out in the sheet metal specified.

    Args:
        diameter: This is the diameter of the fan.
        internal: This is a boolean to establish whether the fan is external or internal. If the fan is internal slots will be cut out and if it is external a big hole will be cut.
        surface: This is the CycaxPart which the fan template will be cut into.
        x: x location of th center of the fan.
        y: y location of the center of the fan.
        depth: How thick the surface is that the fan is being placed into.
    """

    def __init__(
        self,
        width: float,
        surface: SheetMetal,
        x: float,
        y: float,
        internal: bool = True,
        depth: float = 2.0,
        hole_diameter: float = 3.0
    ) -> None:
        self.width = width
        self.border=1
        self.diameter=width-2*self.border
        self.surface = surface
        self.internal = internal
        self.x = x
        self.y = y
        self.depth = depth
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
        start_x = self.x - self.width / 2 + self.hole_diameter+self.border
        start_y = self.y - self.width / 2 + self.hole_diameter+self.border
        end_x = self.x + self.width / 2 - self.hole_diameter+self.border
        end_y = self.y + self.width / 2 - self.hole_diameter+self.border
        for working_x in [start_x, end_x]:
            for working_y in [start_y, end_y]:
                self.surface.make_hole(x=working_x, y=working_y, side="TOP", diameter=self.hole_diameter, depth=2)

    def externa(self):
        """
        This method will cut a large hole in the SheetMetal for the fan.
        """
        self.surface.make_hole(x=self.x, y=self.y, side="TOP", diameter=self.diameter, depth=2)

    def interna(self):
        """
        This method will cut multiple slots into the SheetMetal surface to make gaps that will allow the internal fan to circulate the air.
        """
        slot_area = self.diameter - 16
        slots = int((slot_area)/8)
        spaces=(slot_area -slots*4)/(slots-1)
        start_x = self.x -self.diameter / 2
        # finish_y = self.y + counter
        start_y = self.y - (self.diameter - 16)/2
        while start_y < self.diameter/2 + self.y -counter:
            self.surface.make_slot(x=start_x, y=start_y, side="TOP", x_size=self.diameter -2, y_size=counter, z_size=self.depth)
            # self.surface.make_slot(x=start_x, y=finish_y, side="TOP", x_size=self.diameter-2, y_size=counter, z_size=self.depth)
            start_y = start_y + 2*counter
            # finish_y = finish_y - 2*counter
        self.surface.make_slot(x=self.x - self.width/2 + self.hole_diameter+self.border+1, y=self.y - self.width / 2 + self.hole_diameter+self.border, side="TOP", x_size=self.width - 2*self.hole_diameter - 2*self.border  - 4, y_size=4, z_size=self.depth)
        self.surface.make_slot(x=self.x - self.width/2 + self.hole_diameter+self.border+1, y=self.y + self.width / 2 - self.hole_diameter+self.border, side="TOP", x_size=self.width - 2*self.hole_diameter - 2*self.border  - 4, y_size=4, z_size=self.depth)
