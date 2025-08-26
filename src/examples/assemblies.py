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
            for x in (12, 30, 60):
                side.hole(pos=(x, 10), diameter=4.2, depth=2)
                side.hole(pos=(x, 10), diameter=3.9, depth=10)
                side.hole(pos=(x, 10), diameter=4.2, external_subtract=True)  # Through everything


class DriveStack(Assembly):
    def definition(self):
        """Define the drive stack."""
        bracket_l = Bracket()
        bracket_r = Bracket()
        self.add(bracket_l, "bracket_left")
        self.add(bracket_r, "bracket_right")

        dev1 = Device()
        dev2 = Device()
        self.add(dev1, "device1")
        self.add(dev2, "device2")

        bracket_l.rotate("xz")
        bracket_r.rotate("xz")

        dev2.level(bottom=dev1.top, left=dev1.left, front=dev1.front)
        dev2.move(z=10)

        bracket_l.level(top=dev2.top, right=dev2.left, front=dev2.front)
        bracket_r.level(top=dev2.top, left=dev2.right, front=dev2.front)
        dev1.level(right=bracket_r.left, subtract=True)
        dev1.level(left=bracket_l.right, subtract=True)
        dev2.level(right=bracket_r.left, subtract=True)
        dev2.level(left=bracket_l.right, subtract=True)


def assemble() -> Assembly:
    base = Assembly("base")
    bottom = SheetMetal(x_size=200, y_size=200, z_size=2, part_no="bottom")
    base.add(bottom)

    box = Assembly("box")
    box.add_assembly(base)

    # Below will be moved to an assembly.

    drive_stack = DriveStack(name="DriveStack")
    drive_stack.definition()  # TODO: Assembly should call this automatically.
    box.add_assembly(drive_stack)

    # TODO: Change to: drive_stack.level(bottom=base.top, left=base.left, front=base.front)
    drive_stack.bottom.level(base.top)
    drive_stack.front.level(base.front)
    drive_stack.left.level(base.left)

    return box.combine_all_assemblies()


if __name__ == "__main__":
    box = assemble()
    box.save("./build/assemblies")
    box.build(engine=AssemblyBuild123d(box.name), part_engines=[PartEngineBuild123d()])
