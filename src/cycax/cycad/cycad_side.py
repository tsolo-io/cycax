# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging

from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP
from cycax.cycad.vents import Vent


class CycadSide:
    name = ""

    def __init__(self, parent):
        self._parent = parent

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Side: " + self.name

    def _location_calc(
        self, pos: tuple[float, float], sink: float = 0.0, length: float = 0.0, width: float = 0.0
    ) -> tuple[float, float, float]:
        """Location is calculated for the (x, y) plain using two values and a side.

        Args:
            pos: (x, y) location of an object which is used to find the location with the side.
            sink: The object can be sunk bellow the surface of the specified side to make a pocket.

        Returns:
            The (x, y, z) location of an object.
        """
        logging.debug("Call _location_calc(pos=%s, sink=%s, length=%s, width=%s)", pos, sink, length, width)
        msg = f"_location_calc is Not implemented on {self.name}"
        raise ValueError(msg)

    def _depth_check(self, val: float | None = None) -> float:  # noqa: ARG002 Unused argument
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

    def vent(
        self, x_min: float, y_min: float, x_max: float, y_max: float, border: float = 0, separation: float | None = None
    ):
        """Define the constraints for the vent and create a vent object.

        Args:
            x_min: The minimum x-coordinate of the vent.
            y_min: The minimum y-coordinate of the vent.
            x_max: The maximum x-coordinate of the vent.
            y_max: The maximum y-coordinate of the vent.
            border: The border size around the vent.
            separation: The separation between the vent features, only applicable if the vent is not a single feature.

        Returns:
            A Vent object representing the vent. The different vent types are methods on the Vent class.
        """
        return Vent(
            x_min=x_min + border,
            y_min=y_min + border,
            x_max=x_max - border,
            y_max=y_max - border,
            side=self,
            separation=separation,
        )

    def cylinder(
        self,
        pos: tuple[float, float],
        diameter: float,
        height: float,
        sink: float = 0.0,
    ):
        """This will put a cylinder of the relevant details onto the side.

        Args:
            pos: This is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            height: How tall to make the cylinder.
        """
        _location_tuple = self._location_calc(pos=pos, sink=sink)
        self._parent.make_cylinder(
            x=_location_tuple[0],
            y=_location_tuple[1],
            z=_location_tuple[2],
            side=self.name,
            diameter=diameter,
            height=height,
        )

    def hole(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
        depth: float | None = None,
        *,
        external_subtract: bool = False,
    ):
        """This will insert a hole given the relative details, into the correct side.

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
        external_subtract: bool = False,
        calculate: bool = False,
    ):
        """This box will insert a rectangle shape cut out into the object.

        Args:
            pos: The (x, y) coordinates of the box.
            length: The length of the box as viewed from the specified side.
            width: The width of the box as viewed from the specified side.
            depth: The depth of the box, if not specified will drill all the way through the box.
            sink: The box can be sunk bellow the surface of the specified side to make a pocket.
            center: The box can be specified from the center of the box.
            external_subtract: The box will only be transferred onto other surfaces.
                When set to True the box will not be cut from the main object.
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
            external_subtract=external_subtract,
            calculate=calculate,
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

    def sphere_add(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere to be added onto a specified side.
        Args:
            pos: The (x,y) coordinates of the  cut out.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        sink = sink - diameter / 2
        _location_tuple = self._location_calc(pos=pos, sink=sink)
        self._parent.make_sphere_add(
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

    def subtract(self, part2):  # referencing CycadPart results in a circular import
        """
        This method adds the features of part2 to the part1 on the side where they touch.
        This method will be used for moving around conn-cube and harddive screw holes.

        Args:
            partside1: The part side that will receive the features.
            part2: The part that is used as the template when transferring features.

        Raises:
            ValueError: When the side present in CycadSide does not match one of the expected sides.
        """
        part1 = self._parent
        side = self.name
        part1.make_bounding_box()

        for feature in part2._final_place():
            if feature.name == "cube":
                if side == TOP:
                    if (feature.z - feature.z_size / 2) == part1.bounding_box[TOP]:
                        feature.side = TOP
                        part1.insert_feature(feature)
                elif side == BOTTOM:
                    if (feature.z + feature.z_size / 2) == part1.bounding_box[BOTTOM]:
                        feature.side = BOTTOM
                        part1.insert_feature(feature)
                elif side == LEFT:
                    if (feature.x + feature.x_size / 2) == part1.bounding_box[LEFT]:
                        feature.side = LEFT
                        part1.insert_feature(feature)
                elif side == RIGHT:
                    if (feature.x - feature.x_size / 2) == part1.bounding_box[RIGHT]:
                        feature.side = RIGHT
                        part1.insert_feature(feature)
                elif side == FRONT:
                    if (feature.y + feature.y_size / 2) == part1.bounding_box[FRONT]:
                        feature.side = FRONT
                        part1.insert_feature(feature)
                elif side == BACK:
                    if (feature.y - feature.y_size / 2) == part1.bounding_box[BACK]:
                        feature.side = BACK
                        part1.insert_feature(feature)
                else:
                    msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
                    raise ValueError(msg)
            elif side == TOP:
                if feature.z == part1.bounding_box[TOP]:
                    feature.side = TOP
                    part1.insert_feature(feature)
            elif side == BOTTOM:
                if feature.z == part1.bounding_box[BOTTOM]:
                    feature.side = BOTTOM
                    part1.insert_feature(feature)
            elif side == LEFT:
                if feature.x == part1.bounding_box[LEFT]:
                    feature.side = LEFT
                    part1.insert_feature(feature)
            elif side == RIGHT:
                if feature.x == part1.bounding_box[RIGHT]:
                    feature.side = RIGHT
                    part1.insert_feature(feature)
            elif side == FRONT:
                if feature.y == part1.bounding_box[FRONT]:
                    feature.side = FRONT
                    part1.insert_feature(feature)
            elif side == BACK:
                if feature.y == part1.bounding_box[BACK]:
                    feature.side = BACK
                    part1.insert_feature(feature)
            else:
                msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
                raise ValueError(msg)

    def level(self, partside2):  # reference to CycadSide results in error
        """
        Align the two sides onto the same plain.

        Moves part1 so that its given side is on the same plain as the given
        side of parts2. e.g. `level(part1.front part2.back)` will move part1
        so that its front is on the same plain as the back of part2.

        Args:
            partside1: The CycadSide to be moved to match the plain of the other part.
            partside2: The CycadSide used as reference when moving part1.
        Raises:
            ValueError: When the side present in CycadSide does not match one of the expected sides.
        """
        part1 = self._parent
        part2 = partside2._parent
        part1side = self.name
        part2side = partside2.name
        part2.make_bounding_box()
        part1.make_bounding_box()
        to_here = part2.bounding_box[part2side]

        if part1side == BOTTOM:
            part1.at(z=to_here)
        elif part1side == TOP:
            z_size = part1.z_max - part1.z_min
            part1.at(z=to_here - z_size)
        elif part1side == LEFT:
            part1.at(x=to_here)
        elif part1side == RIGHT:
            x_size = part1.x_max - part1.x_min
            part1.at(x=to_here - x_size)
        elif part1side == FRONT:
            part1.at(y=to_here)
        elif part1side == BACK:
            y_size = part1.y_max - part1.y_min
            part1.at(y=to_here - y_size)
        else:
            msg = f"Side: {part1side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
            raise ValueError(msg)

        part1.make_bounding_box()


class LeftSide(CycadSide):
    name = LEFT

    def _location_calc(
        self,
        pos: tuple[float, float],
        sink: float = 0.0,
        length: float = 0.0,
        width: float = 0.0,  # noqa: ARG002 Unused argument
    ) -> tuple[float, float, float]:
        temp_x = self._parent.x_min + sink
        temp_y = self._parent.y_size - pos[0] - length
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = depth
        y_size = length
        z_size = width
        return x_size, y_size, z_size

    def _depth_check(self, val: float | None = None) -> float:
        if val is None:
            return self._parent.x_max - self._parent.x_min
        else:
            return val

    def _rotate(self):
        self._parent.rotate_freeze_left()

    def cylinder(
        self,
        pos: tuple[float, float],
        diameter: float,
        height: float,
        sink: float = 0.0,
    ):
        """This will put a cylinder of the relevant details onto the side.

        Args:
            pos: This is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            height: How tall to make the cylinder.
        """
        super().cylinder(pos=pos, diameter=diameter, height=height, sink=sink)
        self._parent.x_min = self._parent.x_min - height + sink

    def sphere_add(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere to be added onto a specified side.
        Args:
            pos: The (x,y) coordinates of the sphere.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        super().sphere_add(pos=pos, diameter=diameter, sink=sink)
        self._parent.x_min = self._parent.x_min - diameter + sink


class RightSide(CycadSide):
    name = RIGHT

    def _location_calc(
        self,
        pos: tuple[float, float],
        sink: float = 0.0,
        length: float = 0.0,  # noqa: ARG002 Unused argument
        width: float = 0.0,  # noqa: ARG002 Unused argument
    ) -> tuple[float, float, float]:
        temp_x = self._parent.x_max - sink
        temp_y = pos[0]
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float | None = None) -> float:
        if val is None:
            return self._parent.x_max - self._parent.x_min
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = depth
        y_size = length
        z_size = width
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.rotate_freeze_left()

    def cylinder(
        self,
        pos: tuple[float, float],
        diameter: float,
        height: float,
        sink: float = 0.0,
    ):
        """This will put a cylinder of the relevant details onto the side.

        Args:
            pos: This is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            height: How tall to make the cylinder.
        """
        super().cylinder(pos=pos, diameter=diameter, height=height, sink=sink)
        self._parent.x_max = self._parent.x_max + height - sink

    def sphere_add(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere to be added onto a specified side.
        Args:
            pos: The (x,y) coordinates of the sphere.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        super().sphere_add(pos=pos, diameter=diameter, sink=sink)
        self._parent.x_max = self._parent.x_max + diameter - sink


class TopSide(CycadSide):
    name = TOP

    def _location_calc(
        self,
        pos: tuple[float, float],
        sink: float = 0.0,
        length: float = 0.0,  # noqa: ARG002 Unused argument
        width: float = 1.0,  # noqa: ARG002 Unused argument
    ) -> tuple[float, float, float]:
        temp_x = pos[0]
        temp_y = pos[1]
        temp_z = self._parent.z_max - sink
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        if val is None:
            return self._parent.z_max - self._parent.z_min
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = width
        z_size = depth
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.rotate_freeze_top()

    def cylinder(
        self,
        pos: tuple[float, float],
        diameter: float,
        height: float,
        sink: float = 0.0,
    ):
        """This will put a cylinder of the relevant details onto the side.

        Args:
            pos: This is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            height: How tall to make the cylinder.
        """
        super().cylinder(pos=pos, diameter=diameter, height=height, sink=sink)
        self._parent.z_max = self._parent.z_max + height - sink

    def sphere_add(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere to be added onto a specified side.
        Args:
            pos: The (x,y) coordinates of the sphere.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        super().sphere_add(pos=pos, diameter=diameter, sink=sink)
        self._parent.z_max = self._parent.z_max + diameter - sink


class BottomSide(CycadSide):
    name = BOTTOM

    def _location_calc(
        self,
        pos: tuple[float, float],
        sink: float = 0.0,
        length: float = 0.0,  # noqa: ARG002 Unused argument
        width: float = 0.0,
    ) -> tuple[float, float, float]:
        temp_x = pos[0]
        temp_y = self._parent.y_size - pos[1] - width
        temp_z = self._parent.z_min + sink
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float) -> float:
        if val is None:
            return self._parent.z_max - self._parent.z_min
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = width
        z_size = depth
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.rotate_freeze_top()

    def cylinder(
        self,
        pos: tuple[float, float],
        diameter: float,
        height: float,
        sink: float = 0.0,
    ):
        """This will put a cylinder of the relevant details onto the side.

        Args:
            pos: This is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            height: How tall to make the cylinder.
        """
        super().cylinder(pos=pos, diameter=diameter, height=height, sink=sink)
        self._parent.z_min = self._parent.z_min - height + sink

    def sphere_add(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere to be added onto a specified side.
        Args:
            pos: The (x,y) coordinates of the sphere.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        super().sphere_add(pos=pos, diameter=diameter, sink=sink)
        self._parent.z_min = self._parent.z_min - diameter + sink


class FrontSide(CycadSide):
    name = FRONT

    def _location_calc(
        self,
        pos: tuple[float, float],
        sink: float = 0.0,
        length: float = 0.0,  # noqa: ARG002 Unused argument
        width: float = 0.0,  # noqa: ARG002 Unused argument
    ) -> tuple[float, float, float]:
        temp_x = pos[0]
        temp_y = self._parent.y_min + sink
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float | None = None) -> float:
        if val is None:
            return self._parent.y_max - self._parent.y_min
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = depth
        z_size = width
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.rotate_freeze_front()

    def cylinder(
        self,
        pos: tuple[float, float],
        diameter: float,
        height: float,
        sink: float = 0.0,
    ):
        """This will put a cylinder of the relevant details onto the side.

        Args:
            pos: This is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            height: How tall to make the cylinder.
        """
        super().cylinder(pos=pos, diameter=diameter, height=height, sink=sink)
        self._parent.y_min = self._parent.y_min - height + sink

    def sphere_add(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere to be added onto a specified side.
        Args:
            pos: The (x,y) coordinates of the sphere.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        super().sphere_add(pos=pos, diameter=diameter, sink=sink)
        self._parent.y_min = self._parent.y_min - diameter + sink


class BackSide(CycadSide):
    name = BACK

    def _location_calc(
        self,
        pos: tuple[float, float],
        sink: float = 0.0,
        length: float = 0.0,
        width: float = 0.0,  # noqa: ARG002 Unused argument
    ) -> tuple[float, float, float]:
        temp_x = self._parent.x_size - pos[0] - length
        temp_y = self._parent.y_max - sink
        temp_z = pos[1]
        return temp_x, temp_y, temp_z

    def _depth_check(self, val: float | None = None) -> float:
        if val is None:
            return self._parent.y_max - self._parent.y_min
        else:
            return val

    def _box_size_calc(self, width: float, length: float, depth: float) -> tuple[float, float, float]:
        x_size = length
        y_size = depth
        z_size = width
        return x_size, y_size, z_size

    def _rotate(self):
        self._parent.rotate_freeze_front()

    def cylinder(
        self,
        pos: tuple[float, float],
        diameter: float,
        height: float,
        sink: float = 0.0,
    ):
        """This will put a cylinder of the relevant details onto the side.

        Args:
            pos: This is a tuple that contains the (x, y) coordinates of the object.
            diameter: The diameter of the hole.
            height: How tall to make the cylinder.
        """
        super().cylinder(pos=pos, diameter=diameter, height=height, sink=sink)
        self._parent.y_max = self._parent.y_max + height - sink

    def sphere_add(
        self,
        pos: tuple[float, float],
        diameter: float,
        sink: float = 0.0,
    ):
        """
        This method allows a sphere to be added onto a specified side.
        Args:
            pos: The (x,y) coordinates of the sphere.
            diameter: The diameter of the sphere.
            sink: How far into or out of the plastic the sphere should be extruded.
        """
        super().sphere_add(pos=pos, diameter=diameter, sink=sink)
        self._parent.y_max = self._parent.y_max + diameter - sink
