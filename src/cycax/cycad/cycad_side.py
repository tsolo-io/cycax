class CycadSide:
    def __init__(self, parent):
        self._parent = parent

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Side: " + self.name

    def hole(
        self,
        pos: tuple[float, float],
        diameter: float,
        depth: float = None,
        inner: bool = True,
        external_only: bool = False,
    ):
        """
        This will insert a whole given the relatice details, into the correct side.

        Args:
            pos : this is a tupple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            depth: How deep to drill the hole, if not specified will drill the hole all the way through.
            inner: This is specified that the hole is internal and will not be coppied onto other surface. Defaults to True.
            external_only: This is specified that the hole will only be tranferred onto other surfaces and will not be drilled into main object. Defaults to False.
        """
        _depth = self._depth_check(depth)
        _location_tupple = self._location_calc(pos=pos, sink=0)
        self._parent.make_hole(
            x=_location_tupple[0],
            y=_location_tupple[1],
            z=_location_tupple[2],
            side=self.name,
            diameter=diameter,
            depth=_depth,
            inner=inner,
            external_only=external_only,
        )

    def box(
        self,
        pos: tuple[float, float],
        length: float,
        width: float,
        depth: float = None,
        sink: float = 0,
        center: bool = False,
    ):
        """
        This box will insert a rectangle shape cut out into the object.

        Args:
            pos: The (x, y) coordinates of the box.
            length: The length of the box as viewed from the specified side.
            width: The width of the box as viewed from the specified side.
            depth: The depth of the box, if not specified will drill all the way through th box. Defaults to None.
            sink: The box can be sunk bellow the surface of the specified side to make a plocket. Defaults to 0.
            center: The box can be specified from the ceter of the box. Defaults to False.
        """
        _depth = self._depth_check(depth)
        _location_tupple = self._location_calc(pos=pos, sink=sink)
        _box_dimentions = self._box_size_calc(width=width, length=length, depth=_depth)
        self._parent.make_rectangle(
            side=self.name,
            x=_location_tupple[0],
            y=_location_tupple[1],
            z=_location_tupple[2],
            x_size=_box_dimentions[0],
            y_size=_box_dimentions[1],
            z_size=_box_dimentions[2],
            center=center,
        )

    def nut(self, pos: tuple[float, float], nut_type: float = 3.0, depth: float = None, sink: float = 0.0):
        """
        This method allows a nut cut out to be cut into a specified side.
        Args:
            pos: The (x,y) coordinates of the nut cut out.
            nut_type: The type of nut to be cut. This is used to create the diameter of the nut but will be developed in later versions. Defaults to 3.0.
            depth: How deep to make the nut cut out. If it is not specified the nut cut out will be drilled all the way through. Defaults to None.
            sink: The nut cut out can be sunk bellow the surface of the specified side to make a pocket. Defaults to 0.0.
        """
        _depth = self._depth_check(depth)
        _location_tupple = self._location_calc(pos=pos, sink=sink)
        self._parent.make_nut(
            side=self.name,
            x=_location_tupple[0],
            y=_location_tupple[1],
            z=_location_tupple[2],
            nut_type=nut_type,
            depth=_depth,
        )

    def slot(
        self,
        pos: tuple[float, float],
        length: float,
        width: float,
        depth: float = None,
        horizontal: bool = True,
        inner: bool = True,
        external_only: bool = False,
    ):
        """
        This allows a slot cut out to be cut into the specified side.
        Args:
            pos: The (x,y) coordinates of the slot cut out.
            length: The length of the slot as viewed from the specified side.
            width: The width of the slot as viewed from the specified side.
            depth: The depth of the slot as viewed from the specified side. If not specified it will cut the slot all the way through the surface. Defaults to None.
            horizontal: Slots can either run verticall or horizontally. Defaults to horizontal.
            inner: This is specified that the slot is internal and will not be coppied onto other surface. Defaults to True.
            external_only: This is specified that the slot will only be tranferred onto other surfaces and will not be drilled into main object. Defaults to False.
        """
        _depth = self._depth_check(depth)
        _location_tupple = self._location_calc(pos=pos, sink=0.0)
        _box_dimentions = self._box_size_calc(width=width, length=length, depth=_depth)
        self._parent.make_slot(
            x=_location_tupple[0],
            y=_location_tupple[1],
            z=_location_tupple[2],
            side=self.name,
            x_size=_box_dimentions[0],
            y_size=_box_dimentions[1],
            z_size=_box_dimentions[2],
            horizontal=horizontal,
            inner=inner,
            external_only=external_only,
        )

    def _depth_check(self, val: float):
        """
        This is used to check the depth of an object. This method is just used for error catching.

        Args:
            val: Depth of object.

        Raises:
            ValueError: The side specidfied does not have a depth check method.
        """
        raise ValueError("_depth_check is Not implimented on" + self.name)


class LeftSide(CycadSide):
    name = "LEFT"

    def _location_calc(self, pos: tuple[float, float], sink: float = 0.0) -> tuple[float, float, float]:
        """
        location is calculated for the (x, y) plane using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket. Defaults to 0.0.

        Returns:
            tuple[float, float, float]: (x, y, z) location of an object.
        """

        temp_x = self._parent.x_min + sink
        temp_y = pos[0]
        temp_z = pos[1]

        return temp_x, temp_y, temp_z

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        """ "This method, given the necessary values, will figure out what the exact dimensions of the box that is being calculated is.
        Args:
            width: This is how wide the box must be.
            length: This is how long the box must be.
            depth: This is the depth of the box.

        Returns:
            tuple: This will be the exact (x_size, y_size, z_size) of the box.
        """
        x_size = depth
        y_size = width
        z_size = length

        return x_size, y_size, z_size

    def _depth_check(self, val: float) -> float:
        """
        This method is used so that objects can penetrate through the entire object.
        Args:
            val: Depth as specified by the user.

        Returns:
            float: Depth of the ocjet or depth specified by the user.
        """
        if val is None:
            return self._parent.x_size
        else:
            return val


class RightSide(CycadSide):
    name = "RIGHT"

    def _location_calc(self, pos: tuple[float, float], sink: float = 0.0) -> tuple[float, float, float]:
        """
        location is calculated for the (x, y) plane using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket. Defaults to 0.0.

        Returns:
            tuple[float, float, float]: (x, y, z) location of an object.
        """

        temp_x = self._parent.x_max - sink
        temp_y = pos[0]
        temp_z = pos[1]

        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        """
        This method is used so that objects can penetrate through the entire object.
        Args:
            val: Depth as specified by the user.

        Returns:
            float: Depth of the ocjet or depth specified by the user.
        """
        if val is None:
            return self._parent.x_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        """This method, given the necessary values, will figure out what the exact dimensions of the box that is being calculated is.
        Args:
            width: This is how wide the box must be.
            length: This is how long the box must be.
            depth: This is the depth of the box.

        Returns:
            tuple: This will be the exact (x_size, y_size, z_size) of the box.
        """
        x_size = depth
        y_size = width
        z_size = length

        return x_size, y_size, z_size


class TopSide(CycadSide):
    name = "TOP"

    def _location_calc(self, pos: tuple[float, float], sink: float = 0.0) -> tuple[float, float, float]:
        """
        location is calculated for the (x, y) plane using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket. Defaults to 0.0.

        Returns:
            tuple[float, float, float]: (x, y, z) location of an object.
        """

        temp_x = pos[0]
        temp_y = pos[1]
        temp_z = self._parent.z_max - sink

        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        """
        This method is used so that objects can penetrate through the entire object.
        Args:
            val: Depth as specified by the user.

        Returns:
            float: Depth of the ocjet or depth specified by the user.
        """
        if val is None:
            return self._parent.z_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        """This method, given the necessary values, will figure out what the exact dimensions of the box that is being calculated is.
        Args:
            width: This is how wide the box must be.
            length: This is how long the box must be.
            depth: This is the depth of the box.

        Returns:
            tuple: This will be the exact (x_size, y_size, z_size) of the box.
        """
        x_size = width
        y_size = length
        z_size = depth

        return x_size, y_size, z_size


class BottomSide(CycadSide):
    name = "BOTTOM"

    def _location_calc(self, pos: tuple[float, float], sink: float = 0.0) -> tuple[float, float, float]:
        """
        location is calculated for the (x, y) plane using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket. Defaults to 0.0.

        Returns:
            tuple[float, float, float]: (x, y, z) location of an object.
        """

        temp_x = pos[0]
        temp_y = pos[1]
        temp_z = self._parent.z_min + sink

        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        """
        This method is used so that objects can penetrate through the entire object.
        Args:
            val: Depth as specified by the user.

        Returns:
            float: Depth of the ocjet or depth specified by the user.
        """
        if val is None:
            return self._parent.z_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        """This method, given the necessary values, will figure out what the exact dimensions of the box that is being calculated is.
        Args:
            width: This is how wide the box must be.
            length: This is how long the box must be.
            depth: This is the depth of the box.

        Returns:
            tuple: This will be the exact (x_size, y_size, z_size) of the box.
        """
        x_size = width
        y_size = length
        z_size = depth

        return x_size, y_size, z_size


class FrontSide(CycadSide):
    name = "FRONT"

    def _location_calc(self, pos: tuple[float, float], sink: float = 0.0) -> tuple[float, float, float]:
        """
        location is calculated for the (x, y) plane using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket. Defaults to 0.0.

        Returns:
            tuple[float, float, float]: (x, y, z) location of an object.
        """

        temp_x = pos[0]
        temp_y = self._parent.y_min + sink
        temp_z = pos[1]

        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        """
        This method is used so that objects can penetrate through the entire object.
        Args:
            val: Depth as specified by the user.

        Returns:
            float: Depth of the ocjet or depth specified by the user.
        """
        if val is None:
            return self._parent.y_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        """This method, given the necessary values, will figure out what the exact dimensions of the box that is being calculated is.
        Args:
            width: This is how wide the box must be.
            length: This is how long the box must be.
            depth: This is the depth of the box.

        Returns:
            tuple: This will be the exact (x_size, y_size, z_size) of the box.
        """
        x_size = width
        y_size = depth
        z_size = length

        return x_size, y_size, z_size


class BackSide(CycadSide):
    name = "BACK"

    def _location_calc(self, pos: tuple[float, float], sink: float = 0.0) -> tuple[float, float, float]:
        """
        location is calculated for the (x, y) plane using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket. Defaults to 0.0.

        Returns:
            tuple[float, float, float]: (x, y, z) location of an object.
        """

        temp_x = pos[0]
        temp_y = self._parent.y_max - sink
        temp_z = pos[1]

        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        """
        This method is used so that objects can penetrate through the entire object.
        Args:
            val: Depth as specified by the user.

        Returns:
            float: Depth of the ocjet or depth specified by the user.
        """
        if val is None:
            return self._parent.y_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        """This method, given the necessary values, will figure out what the exact dimensions of the box that is being calculated is.

        Args:
            width: This is how wide the box must be.
            length: This is how long the box must be.
            depth: This is the depth of the box.

        Returns:
            tuple: This will be the exact (x_size, y_size, z_size) of the box.
        """

        x_size = width
        y_size = depth
        z_size = length

        return x_size, y_size, z_size
