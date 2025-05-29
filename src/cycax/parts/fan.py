# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.cuboid import Cuboid


class Fan(Cuboid):
    """This class will initialize a fan cut out in the sheet metal specified.

    Args:
        size: Width of the fan. This will be used to create the fan's square bounding box.
        thickness: The thickness of the fan.
        part_no: The specific part number of the fan.
        internal: This is a boolean to establish whether the fan is external or internal.
            If the fan is external slots will be cut out and if it is internal a big hole will be cut.
        hole_depth: The depth of the material the fan will be set to cut out.
        hole_diameter: The diameter of the securing holes of the fan.
        side_pad: Add extra material on the sides to ensure the structure is sound. Lessens air flow.
    """

    def __init__(
        self,
        size: float,
        thickness: float,
        part_no: str,
        *,
        internal: bool = True,
        hole_depth: float = 2.0,
        hole_diameter: float = 4.5,
        side_pad: float = 0,
    ):
        self.size = size
        self.border = 1
        self.diameter = size - 2 * self.border
        self.internal = internal
        self.center = size / 2
        self.hole_depth = hole_depth
        self.hole_diameter = hole_diameter
        # hole_from_edge - The distance the center of mounting holes is from the edge.
        # Normally 4mm but we can be more specific for fan sizes we know.
        self.hole_from_edge = {80: 4.25}.get(size, 4)
        self.side_pad = side_pad

        super().__init__(part_no=part_no, x_size=size, y_size=size, z_size=thickness)

        self.definition()

    def definition(self):
        """
        This method will be called within the init method.
        Based on whether the specified fan is external or internal it will call the relevant method.
        """
        self.top.hole(pos=(self.center, self.center), diameter=self.diameter, depth=2)
        self.bottom.hole(pos=(self.center, self.center), diameter=self.diameter, depth=2)
        if self.internal:
            self._internal()
        else:
            self._external()

        self._mounting_holes()

    def _mounting_holes(self):
        """
        This method will cut the mounting holes of the fan into the sheet_metal.
        """

        start = self.hole_from_edge
        end = self.size - self.hole_from_edge
        for working_x in [start, end]:
            for working_y in [start, end]:
                self.top.hole(
                    pos=(working_x, working_y),
                    diameter=self.hole_diameter,
                    depth=self.hole_depth,
                    external_subtract=True,
                )
                self.top.hole(pos=(working_x, working_y), diameter=4.5, depth=None)

    def _internal(self):
        """
        This method will cut a large hole in the SheetMetal for the fan.
        """
        self.top.hole(
            pos=(self.size / 2, self.size / 2), diameter=self.size - 2, depth=self.hole_depth, external_subtract=True
        )

    def _external(self):
        """
        This method will cut multiple slots into the SheetMetal surface.
        The gaps will allow the internal fan to circulate the air.
        """

        slot_width = 5  # Size/width of the slot
        wall_width = 4  # Minimal material left between slots.
        start = self.hole_from_edge
        end = self.size - self.hole_from_edge
        length = end - start
        slot_count = int(length / (slot_width + wall_width))
        step = length / slot_count
        slot_x = start - slot_width / 2 + self.side_pad
        # Correct length for slot use.
        length = end - start - 2 * self.side_pad + slot_width

        for n in range(slot_count + 1):
            if n in [0, slot_count]:
                _length = length - 20
                x = slot_x + 10
            else:
                _length = length
                x = slot_x

            self.top.slot(
                pos=(x, start + n * step),
                length=_length,
                width=slot_width,
                depth=self.hole_depth,
                external_subtract=True,
            )


class Fan80x80(Fan):
    def __init__(self, *, thickness: int, side_pad: int = 0, internal: bool = False):
        super().__init__(
            size=80,
            thickness=thickness,
            part_no=f"fan_80x80x{thickness}",
            internal=internal,
            side_pad=side_pad,
            hole_depth=None,
            hole_diameter=3.2,
        )


class Fan80x80x15(Fan80x80):
    def __init__(self, *, internal: bool = False):
        super().__init__(thickness=15, internal=internal)


class Fan80x80x25(Fan80x80):
    def __init__(self, side_pad: int = 0, *, internal: bool = False):
        super().__init__(thickness=25, side_pad=side_pad, internal=internal)
