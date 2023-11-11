from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class CycadSide:
    name = ""

    def __init__(self, parent):
        self._parent = parent

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Side: " + self.name

    def _location_calc(self, pos: tuple[float, float], sink: float = 0.0) -> tuple[float, float, float]:
        """Location is calculated for the (x, y) plane using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket.

        Returns:
            The (x, y, z) location of an object.
        """
        raise ValueError("_location_calc is Not implemented on" + self.name)

    def _depth_check(self, val: float | None = None) -> float:
        """Determine the depth of a feature.

        Args:
            val: Depth of object.

        Raises:
            ValueError: The side specidfied does not have a depth check method.
        """
        raise ValueError("_depth_check is Not implemented on" + self.name)

    def _rotate(self):
        """Rotate the part by 90 degrees by keeping selected side on the same plain."""
        msg = "_rotate should be defined for each side."
        raise NotImplementedError(msg)

    def rotate(self, angle: float = 90):
        """Rotate the part by keeping the selected side on the same plain.

        Rotation is counter clock wise. Negative angles are converted to positive.

        Args:
            angle: The angle in degrees that the part will be rotates on.

        """
        if self._parent.assembly is None:
            # TODO: Think about which exception should be raised, maybe even a custom one.
            msg = "Not part of an assembly"
            raise ValueError(msg)

        if angle % 90 != 0:
            # TODO: Think about which exception should be raised, maybe even a custom one.
            msg = "Can only rotate in multiples of 90 degrees"
            raise ValueError(msg)

        while angle < 0:
            # Change the angle to a positive number.
            angle = 360 + angle

        for _n in range(int(angle / 90)):
            self._rotate()

    @property
    def opposite(self):
        return {
            TOP: self._parent.bottom,
            BOTTOM: self._parent.top,
            LEFT: self._parent.right,
            RIGHT: self._parent.left,
            FRONT: self._parent.back,
            BACK: self._parent.front,
        }[self.name]

    def hole(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
        depth: float | None = None,
        *,
        external_subtract: bool = False,
    ):
        """This will insert a whole given the relatice details, into the correct side.

        Args:
            pos: this is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            depth: How deep to drill the hole, if not specified will drill the hole all the way through.
            sink: The hole can be sunk bellow the surface of the specified side to make a pocket.
            external_subtract: This is specified that the hole will only be transferred onto other surfaces.
                When set to True the hole will not be drilled into the main object.
        """
        _depth = self._depth_check(depth)
        _location_tuple = self._location_calc(pos=pos, sink=sink)
        self._parent.make_hole(
            x=_location_tuple[0],
            y=_location_tuple[1],
            z=_location_tuple[2],
            side=self.name,
            diameter=diameter,
            depth=_depth,
            external_subtract=external_subtract,
        )

    def box(
        self,
        pos: tuple[float, float],
        length: float,
        width: float,
        depth: float | None = None,
        sink: float = 0,
        *,
        center: bool = False,
    ):
        """This box will insert a rectangle shape cut out into the object.

        Args:
            pos: The (x, y) coordinates of the box.
            length: The length of the box as viewed from the specified side.
            width: The width of the box as viewed from the specified side.
            depth: The depth of the box, if not specified will drill all the way through the box.
            sink: The box can be sunk bellow the surface of the specified side to make a pocket.
            center: The box can be specified from the center of the box.
        """
        _depth = self._depth_check(depth)
        if center is True:
            _location_tuple = self._location_calc(pos=pos, sink=sink, length=0.0, width=0.0)
        else:
            _location_tuple = self._location_calc(pos=pos, sink=sink, length=length, width=width)

        _box_dimensions = self._box_size_calc(width=width, length=length, depth=_depth)
        self._parent.make_rectangle(
            side=self.name,
            x=_location_tuple[0],
            y=_location_tuple[1],
            z=_location_tuple[2],
            x_size=_box_dimensions[0],
            y_size=_box_dimensions[1],
            z_size=_box_dimensions[2],
            center=center,
        )

    def nut(
        self,
        pos: tuple[float, float],
        nut_type: str = "M3",
        depth: float | None = None,
        sink: float = 0.0,
        *,
        vertical: bool = True,
    ):
        """
        This method allows a nut cut out to be cut into a specified side.
        Args:
            pos: The (x,y) coordinates of the nut cut out.
            nut_type: The type of nut to be cut.
                This is used to create the diameter of the nut but will be developed in later versions.
            depth: How deep to make the nut cut out.
                If it is not specified the nut cut out will be assumed the thickness of the nut.
            sink: The nut cut out can be sunk bellow the surface of the specified side to make a pocket.
            vertical: This will be set to False if you want the flat side rather than the point side down.
        """
        # _depth = self._depth_check(depth)
        _location_tuple = self._location_calc(pos=pos, sink=sink)
        self._parent.make_nut(
            side=self.name,
            x=_location_tuple[0],
            y=_location_tuple[1],
            z=_location_tuple[2],
            nut_type=nut_type,
            depth=depth,
            vertical=vertical,
        )

    def sphere(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere cut out to be cut into a specified side.
        Args:
            pos: The (x,y) coordinates of the  cut out.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        _location_tuple = self._location_calc(pos=pos, sink=sink)
        self._parent.make_sphere(
            side=self.name,
            x=_location_tuple[0],
            y=_location_tuple[1],
            z=_location_tuple[2],
            diameter=diameter,
        )

    def slot(
        self,
        pos: tuple[float, float],
        length: float,
        width: float,
        depth: float | None = None,
        *,
        horizontal: bool = True,
        external_subtract: bool = False,
    ):
        """
        This allows a slot cut out to be cut into the specified side.
        Args:
            pos: The (x,y) coordinates of the slot cut out.
            length: The length of the slot as viewed from the specified side.
            width: The width of the slot as viewed from the specified side.
            depth: The depth of the slot as viewed from the specified side.
                If not specified it will cut the slot all the way through the surface.
            horizontal: Slots can either run vertical or horizontally.
            external_subtract: This is specified that the slot will only be transferred onto other surfaces.
                When set to True the slot will not be drilled into the main object.
        """
        _depth = self._depth_check(depth)
        _location_tuple = self._location_calc(pos=pos, sink=0.0)
        if horizontal is False:
            length, width = width, length
        _box_dimensions = self._box_size_calc(width=width, length=length, depth=_depth)
        self._parent.make_slot(
            x=_location_tuple[0],
            y=_location_tuple[1],
            z=_location_tuple[2],
            side=self.name,
            x_size=_box_dimensions[0],
            y_size=_box_dimensions[1],
            z_size=_box_dimensions[2],
            horizontal=horizontal,
            external_subtract=external_subtract,
        )


class LeftSide(CycadSide):
    name = LEFT

    def _location_calc(
        self, pos: tuple[float, float], sink: float = 0.0, length: float = 0.0, width: float = 0.0
    ) -> tuple[float, float, float]:
        temp_x = self._parent.x_min + sink
        temp_y = self._parent.y_max - pos[0] - length
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = depth
        y_size = length
        z_size = width
        return x_size, y_size, z_size

    def _depth_check(self, val: float | None = None) -> float:
        if val is None:
            return self._parent.x_size
        else:
            return val

    def _rotate(self):
        self._parent.assembly.rotate_freeze_left(self._parent)


class RightSide(CycadSide):
    name = RIGHT

    def _location_calc(
        self, pos: tuple[float, float], sink: float = 0.0, length: float = 0.0, width: float = 0.0
    ) -> tuple[float, float, float]:
        temp_x = self._parent.x_max - sink
        temp_y = pos[0]
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        if val is None:
            return self._parent.x_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = depth
        y_size = length
        z_size = width
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.assembly.rotate_freeze_left(self._parent)


class TopSide(CycadSide):
    name = TOP

    def _location_calc(
        self, pos: tuple[float, float], sink: float = 0.0, length: float = 0.0, width: float = 0.0
    ) -> tuple[float, float, float]:
        temp_x = pos[0]
        temp_y = pos[1]
        temp_z = self._parent.z_max - sink
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        if val is None:
            return self._parent.z_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = width
        z_size = depth
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.assembly.rotate_freeze_top(self._parent)


class BottomSide(CycadSide):
    name = BOTTOM

    def _location_calc(
        self, pos: tuple[float, float], sink: float = 0.0, length: float = 0.0, width: float = 0.0
    ) -> tuple[float, float, float]:
        temp_x = pos[0]
        temp_y = self._parent.y_max - pos[1] - width
        temp_z = self._parent.z_min + sink
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        if val is None:
            return self._parent.z_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = width
        z_size = depth
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.assembly.rotate_freeze_top(self._parent)


class FrontSide(CycadSide):
    name = FRONT

    def _location_calc(
        self, pos: tuple[float, float], sink: float = 0.0, length: float = 0.0, width: float = 0.0
    ) -> tuple[float, float, float]:
        temp_x = pos[0]
        temp_y = self._parent.y_min + sink
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float | None = None) -> float:
        if val is None:
            return self._parent.y_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = depth
        z_size = width
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.assembly.rotate_freeze_front(self._parent)


class BackSide(CycadSide):
    name = BACK

    def _location_calc(
        self, pos: tuple[float, float], sink: float = 0.0, length: float = 0.0, width: float = 0.0
    ) -> tuple[float, float, float]:
        temp_x = self._parent.x_max - pos[0] - length
        temp_y = self._parent.y_max - sink
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float | None = None) -> float:
        if val is None:
            return self._parent.y_size
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = depth
        z_size = width
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.assembly.rotate_freeze_front(self._parent)
