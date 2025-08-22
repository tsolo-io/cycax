# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from struct import calcsize

from cycax.cycad import Assembly, Cuboid, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


class Socket(Cuboid):
    """A simple part with a rectangle cutout and a matching rectangle external subtract.

    A small holes and external subtract of the holes are made to check alignment.
    The one hole has a diameter of 1mm and the other a diameter of 2mm.
    The socket is rotated so that the 1mm hole should be the origin of the cut square.
    """

    def __init__(self):
        super().__init__(part_no="socket", x_size=34.0, y_size=24.0, z_size=20.0)

    def definition(self):
        """Calculate the connect cube."""
        pos = (2, 2)
        length = self.x_size - 4
        width = self.z_size - 4
        self.back.box(pos=pos, length=length, width=width, depth=15)
        self.back.box(
            pos=pos,
            length=length,
            width=width,
            external_subtract=True,
            calculate=True,
        )
        # For the test, rotate the part so that the 1mm hole is the origin of the cut square.
        self.back.hole(pos=pos, diameter=1)
        self.back.hole(pos=pos, diameter=1, external_subtract=True)
        # The 2mm hole is for visual reference only, when debugging the test.
        self.back.hole(pos=(pos[0] + length, pos[1] + width), diameter=2)
        self.back.hole(pos=(pos[0] + length, pos[1] + width), diameter=2, external_subtract=True)
        # The 3mm hole is to check the center of the cutout. This will all us to determine the orientation.
        self.back.hole(pos=(pos[0] + length / 2, pos[1] + width / 2), diameter=3)
        self.back.hole(pos=(pos[0] + length / 2, pos[1] + width / 2), diameter=3, external_subtract=True)


def make_plate_with_socket(side: str) -> Assembly:
    """Makes a plate with a socket that has a rectangle cutout.

    Returns:
        The assembly that was created with plate and socket.
    """
    assembly = Assembly("test")
    base = SheetMetal(z_size=2.0, x_size=100, y_size=200, part_no="base")
    assembly.add(base)
    psocket = Socket()
    assembly.add(psocket)

    if side == BACK:
        base.rotate("yz")
        psocket.rotate("xx")
        psocket.level(front=base.back, top=base.top, left=base.left)
        psocket.move(z=-5, x=5)
        psocket.level(front=base.back, subtract=True)
    elif side == FRONT:
        base.rotate("yz")
        psocket.level(back=base.front, top=base.top, right=base.right)
        psocket.move(z=-5, x=-5)
        psocket.level(back=base.front, subtract=True)
    elif side == TOP:
        psocket.rotate("xxxzz")
        psocket.level(bottom=base.top, front=base.front, right=base.right)
        psocket.move(y=5, x=-5)
        psocket.level(bottom=base.top, subtract=True)

    return assembly


def test_subtract_side(tmp_path):
    """This test creates a plate with a socket that has a rectangle cutout and a hole.

    A check is made to ensure that the hole and the rectangle cutout are at the same locations.
    This test is a simplification of a real life problem.
    """

    assembled_side = {}
    for side in TOP, BACK, FRONT:
        assembly = make_plate_with_socket(side=side)
        # Help with debugging
        assembly.save(tmp_path)
        assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d()])
        assembled_side[side] = assembly

    for _side, assembly in assembled_side.items():
        base = assembly.get_part("base_1").export()
        compare = {}
        for feature in base["features"]:
            print(_side, feature)
            if feature["type"] == "cut":
                if feature["name"] == "hole":
                    name = f"{feature['name']}{feature['diameter']}"
                else:
                    name = feature["name"]
                compare[name] = feature
        assert compare["hole3"]["x"] == compare["cube"]["x"]
        assert compare["hole3"]["y"] == compare["cube"]["y"]
