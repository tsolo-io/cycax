# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import itertools
import json
from pathlib import Path

import pytest

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
    mypart1.rotate_freeze_front()
    mypart1.rotate_freeze_top()

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
    conn_front_bottom_left = Connect()

    assembly.add(conn_front_top_left)
    assembly.add(conn_front_bottom_left)
    assembly.add(side_left)
    assembly.add(side_right)
    assembly.add(side_top)
    assembly.add(side_front)
    assembly.add(side_bottom)

    side_front.rotate_freeze_left()
    side_bottom.rotate_freeze_top()
    side_top.rotate_freeze_top()
    side_left.rotate_freeze_top()
    side_left.rotate_freeze_front()
    side_right.rotate_freeze_top()
    side_right.rotate_freeze_front()

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
        conn_front_bottom_left,
    )


def get_cycax_json_hash(filename: Path) -> str:
    """
    Return a consistent string representation of the JSON object.

    Name is removed.
    Features are sorted.
    Data is UnJSON.
    """
    data = json.loads(filename.read_text())
    data["name"] = ""
    features = []
    for feature in data.get("features", []):
        # Make each feature a string (JSON) so we can sort them.
        features.append(json.dumps(feature))
    parts = []
    for part in data.get("parts", []):
        part["part_no"] = ""
        parts.append(json.dumps(part))
    new_data = data
    features.sort()
    new_data["features"] = features
    new_data["parts"] = parts
    # UnJSON the string so it is shorter, human readable.
    # Not parseable but it helps to spot the issue.
    # Alternative would be to use the smart dict compare in pytest
    # and not return string here.
    content = json.dumps(new_data).replace("\\", "").replace('"', "").replace(": ", ":")
    return content


def get_hashes(name: str, tmp_path: Path, assembly, *, slow: bool = False) -> list:
    assemb_path = tmp_path / name
    assemb_path.mkdir()
    assembly.save(path=assemb_path)
    hash_map = {}
    if slow:
        assembly.render(part_engine="freecad")

        for filename in assemb_path.glob("*/*.stl"):
            pname = filename.name.split("_")[-1]
            file_hash = get_file_hash(filename)
            hash_map[pname] = file_hash
    else:
        for filename in assemb_path.glob("*/*.json"):
            pname = filename.name.split("_")[-1]
            file_hash = get_cycax_json_hash(filename)
            hash_map[pname] = file_hash

    hash_list = []
    for key in sorted(hash_map.keys()):
        hash_list.append((key, hash_map[key]))
    return hash_list


@pytest.mark.slow
def x_test_level_subtract_order_slow(tmp_path: Path):
    build_test_case(tmp_path=tmp_path, slow=True)


def x_test_level_subtract_order(tmp_path: Path):
    build_test_case(tmp_path=tmp_path, slow=False)


def json_compare(filename1: Path, filename2: Path):
    with open(filename1) as f1, open(filename2) as f2:
        json1 = json.load(f1)
        json2 = json.load(f2)
    return json1 == json2


def build_test_case(*, tmp_path, slow: bool):
    name = "case_ref"
    (
        assembly,
        side_left,
        side_right,
        side_top,
        side_bottom,
        side_front,
        conn_front_top_left,
        conn_front_bottom_left,
    ) = sides(name)

    conn_front_top_left.level(
        front=side_front.back,
        top=side_top.bottom,
        left=side_left.right,
        subtract=True,
    )
    conn_front_bottom_left.level(
        front=side_front.back,
        bottom=side_bottom.top,
        left=side_left.right,
        subtract=True,
    )

    hashes_ref = get_hashes(name, tmp_path, assembly, slow=slow)

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
            conn_front_bottom_left,
        ) = sides(name)
        for side in order_test:
            if side == FRONT:
                assembly.level(conn_front_top_left.front, side_front.back)
                assembly.level(conn_front_bottom_left.front, side_front.back)
            if side == TOP:
                assembly.level(conn_front_top_left.top, side_top.bottom)
                assembly.level(conn_front_bottom_left.bottom, side_bottom.top)
            if side == LEFT:
                assembly.level(conn_front_top_left.left, side_left.right)
                assembly.level(conn_front_bottom_left.left, side_left.right)

        for side in order_test:
            if side == FRONT:
                assembly.subtract(side_front.back, conn_front_top_left)
                assembly.subtract(side_front.back, conn_front_bottom_left)
            if side == TOP:
                assembly.subtract(side_top.bottom, conn_front_top_left)
                assembly.subtract(side_bottom.top, conn_front_bottom_left)
            if side == LEFT:
                assembly.subtract(side_left.right, conn_front_top_left)
                assembly.subtract(side_left.right, conn_front_bottom_left)

        hashes_test = get_hashes(name, tmp_path, assembly, slow=slow)
        # Path("/tmp/hashes_ref").write_text("\n".join(str(hashes_ref).split(",")))
        # Path("/tmp/hashes_test").write_text("\n".join(str(hashes_test).split(",")))
        assert hashes_ref == hashes_test, (
            f"Compare the hashes for the two assemblies: REF({hashes_ref}) != TEST({hashes_test})"
        )
