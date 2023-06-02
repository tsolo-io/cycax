from cycax.cycad.features import Holes, NutCutOut, RectangleCutOut
from cycax.cycad.location import TOP, Location
from cycax.cycad.slot import Slot


class CycadPart(Location):
    """This will be the class that specifies certain details with regards to the CycadPart."""
    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        side: str,
        part_no: str,
        x_size: float,
        y_size: float,
        z_size: float,
    ):
        
        """
        This method will initialize a CycadPart at the desired location.

        Args:
            x : The location of x along the x axis.
            y : The location of y along the y axis.
            z : The location of z along the z axis.
            x_size : The size of x.
            y_size : The size of y.
            z_size : The siez of z.
            part_no : The unique name that will be given to a type of parts. 
        
        """  
        super().__init__(x, y, z, side)
        self.part_no = part_no
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.features = []  # Stores all the holes to be cut
        self.move_holes = []
        self.x_max: float = self.x_size  # Location.Right
        self.x_min: float = 0  # Location.Left
        self.y_min: float = 0  # Location.Front
        self.y_max: float = self.y_size  # Location.Back
        self.z_min: float = 0  # Location.Bottom
        self.z_max: float = self.z_size  # Location.Top
        self.bounding_box = {}
        self.rotmax = [self.x_size, self.y_size, self.z_size]
        self.moves = [0, 0, 0]
        self.rotate = [0, 0, 0]
        self.final_location = False

    def make_hole(
        self,
        x: float,
        y: float,
        side: str,
        diameter: float,
        depth: float,
        inner: bool = True,
    ):
        """!!!!!THIS METHOD WILL ONLY WORK IF WE ARE MAKING HOLES IN THE CENTRE OF A CUBIC OBJECT, NEED TO RETHINK LOGIC!!!!!!
        If instead of Location.top and Location.bottom it were possible to think rather (x, y, z_max)
        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            side: The side of the part the hole will be made in.
            diameter: The diameter of the hole.
            depth: The depth of the hole. If Null the hole is through the part.
            inner: If this is an internal or an external hole.
        """
        location_output = self.side_location_calculator(side=side, x=x, y=y)
        temp_hole = Holes(
            side=side, x=location_output[0], y=location_output[1], z=location_output[2], diameter=diameter, depth=depth
        )
        if inner:
            self.features.append(temp_hole)
        else:
            self.features.append(temp_hole)
            self.move_holes.append(temp_hole)

    def make_slot(
        self,
        x: float,
        y: float,
        side: str,
        x_size: float,
        y_size: float,
        z_size: float,
        horizontal: bool = True,
        inner=True,
    ):
        """This method will insert a slot into a CycadPart.
        
        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            side: The side of the part the hole will be made in.
            x_size : The size of x of slot.
            y_size : The size of y of slot.
            z_size : The siez of z of slot.
            horizontal : This can be overridden if it is preferred to have a verticle slot.
            inner: If this is an internal or an external hole.
        """

        location_output = self.side_location_calculator(side=side, x=x, y=y)
        temp_slot = Slot(
            side=side,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
            x=location_output[0],
            y=location_output[1],
            z=location_output[2],
            Horizontal=horizontal,
        )
        # This will add it to the relevnt array
        if inner:
            self.features.append(temp_slot)
        else:
            self.features.append(temp_slot)
            self.move_holes.append(temp_slot)

    def make_nut(self, side: str, x: float, y: float, type: float, depth: float, sink=0):
        """This method will insert a nut into a CycadPart.
        
        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            side: The side of the part the hole will be made in.
            type: This is the type of nut specified as a float. This method will be updated in version 2.
            depth: This is how deep the nut cut out must be.
            sink: This can be specified if you would like an embedded nut. One that is not a vissible cut from the outside but rather deeper in the 3D print.
        """

        location_output = self.side_location_calculator(side=side, x=x, y=y, sink=sink)
        temp_nut = NutCutOut(
            side=side, x=location_output[0], y=location_output[1], z=location_output[2], type=type, depth=depth
        )
        self.features.append(temp_nut)

    def make_rectangle(
        self,
        side: str,
        x: float,
        y: float,
        x_size: float,
        y_size: float,
        z_size: float,
        sink=0,
        center=False,
    ):
        """This method will cut a block out of the CycadPart.
        
        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            side: The side of the part the hole will be made in.
            x_size : The size of x of rectangle.
            y_size : The size of y of rectangle.
            z_size : The size of z of rectangle.
            sink : This can be changed if you would like an embedded cut out.
            center : This can be overridden if you would like to have the location of the cut out specified from its center.
        """

        location_output = self.side_location_calculator(side=side, x=x, y=y, sink=sink)
        temp_rect = RectangleCutOut(
            side=side,
            x=location_output[0],
            y=location_output[1],
            z=location_output[2],
            x_size=x_size, 
            y_size=y_size,
            z_size=z_size,
            center=center,
        )
        self.features.append(temp_rect)

    def make_bounding_box(self):
        """This bounding box will be used to help keep track of and update the bounds."""

        self.bounding_box = {
            "TOP": self.z_max,
            "BOTTOM": self.z_min,
            "LEFT": self.x_min,
            "RIGHT": self.x_max,
            "FRONT": self.y_min,
            "BACK": self.y_max,
        }

    def move(self, x=0, y=0, z=0):
        """This method will be used for moving the part.
        
        Args:
            x: the amount the object should be moved along the x axis.
            y: the amount the object should be moved along the y axis.
            z: the amound the object should be moved along the z axis
            
            
        """

        x_size = self.x_max - self.x_min
        y_size = self.y_max - self.y_min
        z_size = self.z_max - self.z_min

        if x != 0:
            self.x_min = x
            self.x_max = x + x_size
            self.moves[0] = x
        if y != 0:
            self.y_min = y
            self.y_max = y + y_size
            self.moves[1] = y
        if z != 0:
            self.z_min = z
            self.z_max = z + z_size
            self.moves[2] = z

        self.make_bounding_box()

    def insert_hole(self, hole):
        """This method will be used for inserting the hole into an object.
        
        Args:
            hole: hole to be inserted.

            
        """

        if self.moves[0] != 0:
            hole.move(x=-self.moves[0])
        if self.moves[1] != 0:
            hole.move(y=-self.moves[1])
        if self.moves[2] != 0:
            hole.move(z=-self.moves[2])

        if self.rotate[0] != 0:
            hole.swap_yz(((360 - self.rotate[0]) / 90), self.rotmax[1])
        if self.rotate[1] != 0:
            hole.swap_xz(((360 - self.rotate[1]) / 90), self.rotmax[2])
        if self.rotate[2] != 0:
            hole.swap_xy(((360 - self.rotate[2]) / 90), self.rotmax[0])

        self.features.append(hole)
        self.move_holes.append(hole)

    def side_location_calculator(self, side: str, x: float, y: float, sink=0):
        
        """
        Calculate given the side of and object and the relative x and y location on that side where the definite location is.
            Args:
                x: x location
                y: y location
                side: side of object
            
            Raises: 
                ValueError: if the side is not one of the available and expected sides.
                
            Returns:
                tupel: tupel containing floats of the x, y and z values.

            
        """

        if side == super.TOP:
            temp_x = x
            temp_y = y
            temp_z = self.z_max - sink  # Where is self.z_max defined??
        elif side == super.BOTTOM:
            temp_x = x
            temp_y = y
            temp_z = self.z_min + sink
        elif side == super.LEFT:
            temp_x = self.x_min + sink
            temp_y = x
            temp_z = y
        elif side == super.RIGHT:
            temp_x = self.x_max - sink
            temp_y = x
            temp_z = y
        elif side == super.FRONT:
            temp_x = x
            temp_y = self.y_min + sink
            temp_z = y
        elif side == super.BACK:
            temp_x = x
            temp_y = self.y_max - sink
            temp_z = y
        else:
            msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
            raise ValueError(msg)

        return temp_x, temp_y, temp_z
