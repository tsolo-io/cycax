# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Assembly, Cuboid, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


class Socket(Cuboid):
    """A simple part with a rectangle cutout and a matching rectangle external subtract.

    A small hole and external subtract of this hole is also made to check alignment.
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
        )
        self.back.hole(pos=pos, diameter=1)
        self.back.hole(pos=pos, diameter=1, external_subtract=True)


def make_plate_with_connect_cubes(back: bool = True) -> Assembly:
    """Makes a plate with a socket that has a rectangle cutout.

    Returns:
        The assembly that was created with plate and socket.
    """
    assembly = Assembly("test")
    base = SheetMetal(z_size=2.0, x_size=100, y_size=200, part_no="base")
    assembly.add(base)
    base.rotate("yz")

    psocket = Socket()
    assembly.add(psocket)
    if back:
        psocket.rotate("xx")
        psocket.level(front=base.back, top=base.top, left=base.left)
        psocket.move(z=-5, x=5)
        psocket.level(front=base.back, subtract=True)
    else:
        psocket.level(back=base.front, top=base.top, right=base.right)
        psocket.move(z=-5, x=-5)
        psocket.level(back=base.front, subtract=True)

    return assembly


def test_subtract_side():
    """This test creates a plate with a socket that has a rectangle cutout and a hole.

    A check is made to ensure that the hole and the rectangle cutout are at the same locations.
    This test is a simplification of a real life problem.
    """

    for flip in (True, False):
        assembly = make_plate_with_connect_cubes(back=flip)
        # Help with debugging
        save_path = Path("/tmp/test-subtract/")
        save_path.mkdir(parents=True, exist_ok=True)
        assembly.save(save_path)
        assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d()])

        base = assembly.get_part("base_1").export()
        compare = {}
        print(base)
        for feature in base["features"]:
            if feature["type"] == "cut":
                compare[feature["name"]] = feature
        assert compare["hole"]["x"] == compare["cube"]["x"]
        assert compare["hole"]["y"] == compare["cube"]["y"]
        assert compare["hole"]["z"] == compare["cube"]["z"]
