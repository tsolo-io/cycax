import itertools
import pytest
from pathlib import Path

from cycax.cycad import Assembly, Cuboid, SheetMetal
from cycax.cycad.location import FRONT, LEFT, SIDES, TOP

from .shared import get_file_hash

# Test the rotation method of the part.


def test_level():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")
    mypart2 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test2")

    assembly.add(mypart1)
    assembly.add(mypart2)

    assembly.level(mypart1.bottom, mypart2.bottom)

    assert mypart1.position == mypart2.position

    assembly.level(mypart1.right, mypart2.right)

    assert mypart1.position == mypart2.position

    assembly.level(mypart1.front, mypart2.front)

    assert mypart1.position == mypart2.position

    assembly.level(mypart1.bottom, mypart2.top)

    assert mypart1.position == [0, 0, 2]

    assembly.level(mypart1.left, mypart2.right)

    assert mypart1.position == [1000, 0, 2]

    assembly.level(mypart1.front, mypart2.back)

    assert mypart1.position == [1000, 100, 2]

    assembly.level(mypart1.top, mypart2.bottom)

    assert mypart1.position == [1000, 100, -2]

    assembly.level(mypart1.right, mypart2.left)

    assert mypart1.position == [-1000, 100, -2]

    assembly.level(mypart1.back, mypart2.front)
    assembly.rotate_freeze_front(mypart1)
    assembly.rotate_freeze_top(mypart1)

    assert mypart1.position == [-1000, -100, -2]


class Connect(Cuboid):
    def __init__(self):
        super().__init__(part_no="connect", x_size=20, y_size=20, z_size=20)

    def definition(self):
        """Calculate the connect cube."""
        for side_name in SIDES:
            pos = (10, 10)
            side = self.get_side(side_name)
            side.hole(pos=pos, diameter=3.2, external_subtract=True)
            side.hole(pos=pos, diameter=3.0, depth=3)
            side.hole(pos=pos, diameter=2.9)  # Through everything


def sides(name: str) -> tuple:
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly(name)
    side_left = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no=f"part-{name}_side_left")
    side_right = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no=f"part-{name}_side_right")
    side_top = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no=f"part-{name}_side_top")
    side_bottom = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no=f"part-{name}_side_bottom")
    side_front = SheetMetal(
        x_size=width + 2 * thickness,
        y_size=width,
        z_size=thickness,
        part_no="part-test_side_front",
    )

    conn_front_top_left = Connect()

    assembly.add(conn_front_top_left)
    assembly.add(side_left)
    assembly.add(side_right)
    assembly.add(side_top)
    assembly.add(side_front)
    assembly.add(side_bottom)

    assembly.rotate_freeze_left(side_front)
    assembly.rotate_freeze_top(side_bottom)
    assembly.rotate_freeze_top(side_top)
    assembly.rotate_freeze_top(side_left)
    assembly.rotate_freeze_front(side_left)
    assembly.rotate_freeze_top(side_right)
    assembly.rotate_freeze_front(side_right)

    assembly.level(side_top.front, side_front.back)
    assembly.level(side_left.front, side_front.back)
    assembly.level(side_right.front, side_front.back)
    assembly.level(side_bottom.front, side_front.back)
    assembly.level(side_top.top, side_front.top)
    assembly.level(side_left.left, side_front.left)
    assembly.level(side_right.right, side_front.right)
    assembly.level(side_bottom.bottom, side_front.bottom)

    assembly.level(side_top.right, side_right.left)
    assembly.level(side_bottom.right, side_right.left)

    return (
        assembly,
        side_left,
        side_right,
        side_top,
        side_bottom,
        side_front,
        conn_front_top_left,
    )


def get_hashes(name, tmp_path, assembly) -> list:
    assemb_path = tmp_path / name
    assemb_path.mkdir()
    assembly.save(path=assemb_path)
    assembly.render()

    hash_map = {}
    for filename in assemb_path.glob("*/*.stl"):
        file_hash = get_file_hash(filename)
        pname = filename.name.split("_")[-1]
        hash_map[pname] = file_hash

    hash_list = []
    for key in sorted(hash_map.keys()):
        hash_list.append((key, hash_map[key]))

    print(assemb_path, hash_list)
    return hash_list


@pytest.mark.slow
def test_level_subtract_order(tmp_path: Path):
    name = "case_ref"
    (
        assembly,
        side_left,
        side_right,
        side_top,
        side_bottom,
        side_front,
        conn_front_top_left,
    ) = sides(name)

    conn_front_top_left.level(
        front=side_front.back,
        top=side_top.bottom,
        left=side_left.right,
        subtract=True,
    )

    hashes_ref = get_hashes(name, tmp_path, assembly)

    for order_test in itertools.permutations([FRONT, TOP, LEFT]):
        name = "case_{}-{}-{}".format(*order_test)
        (
            assembly,
            side_left,
            side_right,
            side_top,
            side_bottom,
            side_front,
            conn_front_top_left,
        ) = sides(name)
        for side in order_test:
            if side == FRONT:
                assembly.level(conn_front_top_left.front, side_front.back)
            if side == TOP:
                assembly.level(conn_front_top_left.top, side_top.bottom)
            if side == LEFT:
                assembly.level(conn_front_top_left.left, side_left.right)

        for side in order_test:
            if side == FRONT:
                assembly.subtract(side_front.back, conn_front_top_left)
            if side == TOP:
                assembly.subtract(side_top.bottom, conn_front_top_left)
            if side == LEFT:
                assembly.subtract(side_left.right, conn_front_top_left)

        hashes_test = get_hashes(name, tmp_path, assembly)
        print("Compare  REF:", hashes_ref)
        print("Compare TEST:", hashes_test)
        assert hashes_ref == hashes_test, "Compare the hashes for the two assemblies."

    assert False
