#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, Cuboid, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d

LENGTH = 100


class Bracket(Print3D):
    """This class represents a special bracket to hold a device in place."""

    def __init__(self):
        super().__init__(part_no="bracket", x_size=LENGTH, y_size=50, z_size=15)

    def definition(self):
        """Define the bracket."""
        side = self.front
        x = 10
        while x < LENGTH:
            pos = (x, self.z_size / 2)
            side.hole(pos=pos, diameter=3.2, depth=2)
            side.hole(pos=pos, diameter=2.9, depth=10)
            side.hole(pos=pos, diameter=3.2, external_subtract=True)  # Through everything
            x += 10


class Device(Cuboid):
    """Create the device."""

    def __init__(self):
        super().__init__(part_no="sxdevice", x_size=LENGTH, y_size=80, z_size=20)

    def definition(self):
        """Define the device."""
        for side in (self.left, self.right):
            for x in range(10, 50, 90):
                side.hole(pos=(x, 10), diameter=4.2, depth=2)
                side.hole(pos=(x, 10), diameter=3.9, depth=10)
                side.hole(pos=(x, 10), diameter=4.2, external_subtract=True)  # Through everything


def assemble() -> Assembly:
    box = Assembly("box")

    bottom = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="bottom")
    box.add(bottom)

    # Below will be moved to an assembly.
    bracket_l = Bracket()
    bracket_r = Bracket()
    box.add(bracket_l)
    box.add(bracket_r)

    dev1 = Device()
    dev2 = Device()
    box.add(dev1)
    box.add(dev2)

    bracket_l.rotate("xz")
    bracket_r.rotate("xzzz")

    dev2.level(bottom=dev1.top, left=dev1.left, front=dev1.front)
    dev2.move(z=10)

    bracket_l.level(top=dev2.top, right=dev2.left, front=dev2.front)
    bracket_r.level(top=dev2.top, left=dev2.right, front=dev2.front)
    dev1.level(right=bracket_r.left, subtract=True)
    dev1.level(left=bracket_l.right, subtract=True)
    dev2.level(right=bracket_r.left, subtract=True)
    dev2.level(left=bracket_l.right, subtract=True)

    return box


if __name__ == "__main__":
    box = assemble()
    box.save("./build/assemblies")
    box.build(engine=AssemblyBuild123d(box.name), part_engines=[PartEngineBuild123d()])
