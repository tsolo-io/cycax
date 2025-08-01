# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
from itertools import combinations, product
from pathlib import Path

from cycax.cycad import Assembly, Cuboid, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


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


def make_plate_with_connect_cubes(side: str, name: str | None = None) -> Assembly:
    """Makes a plate with connector cubes on each corner.

    Args:
        name: The name of the assembly.

    Returns:
        The assembly that was created with plate and four corner cubes.
    """
    if name is None:
        name = "test"

    assembly = Assembly(name)
    base_plate = SheetMetal(x_size=100, y_size=60, z_size=2, part_no=f"{name}_base")
    assembly.add(base_plate)
    bp_side = getattr(base_plate, side.lower()).opposite
    if side in (LEFT, RIGHT):
        base_plate.rotate("xz")
        ref_sides = [(FRONT, BACK), (TOP, BOTTOM)]
    elif side in (FRONT, BACK):
        base_plate.rotate("x")
        ref_sides = [(LEFT, RIGHT), (TOP, BOTTOM)]
    elif side in (TOP, BOTTOM):
        ref_sides = [(LEFT, RIGHT), (FRONT, BACK)]
    else:
        msg = f"Invalid side: {side}"
        raise ValueError(msg)

    for sides in product(*ref_sides):
        conn = Connect()
        assembly.add(conn)
        conn_level_dict = {"subtract": True}
        conn_level_dict[side.lower()] = bp_side
        for ref_side in sides:
            side_lower = ref_side.lower()
            conn_level_dict[side_lower] = getattr(base_plate, side_lower)
        conn.level(**conn_level_dict)
    return assembly


def make_sides(name: str | None = None) -> Assembly:
    """Makes a cube where from flat sides, all the sides are the same.

    No nicely overlapping sides since that will make sides of different sizes.

    Args:
        name: The name of the assembly.

    Returns:
        The assembly that was created with the sides.
    """
    if name is None:
        name = "test"
    length = 100
    thickness = 2

    assembly = Assembly(name)
    for side_name in SIDES:
        side_plate = SheetMetal(x_size=length, y_size=length, z_size=thickness, part_no=f"{name}_{side_name}")
        assembly.add(side_plate)

    bottom_plate = assembly.get_part(f"{name}_{BOTTOM.lower()}_1")
    bottom_plate.rotate("xx")
    top_plate = assembly.get_part(f"{name}_{TOP.lower()}_1")
    for side_name in (FRONT, BACK, LEFT, RIGHT):
        side_plate = assembly.get_part(f"{name}_{side_name.lower()}_1")
        side_plate.rotate("x")  # Make the sides stand up
        if side_name in (FRONT, BACK):
            if side_name == FRONT:
                side_plate.level(back=bottom_plate.front, left=bottom_plate.left, bottom=bottom_plate.top)
            else:
                side_plate.level(front=bottom_plate.back, right=bottom_plate.right, bottom=bottom_plate.top)
                side_plate.rotate("zz")
        elif side_name in (LEFT, RIGHT):
            side_plate.rotate("z")  # Rotate the left and right sides
            if side_name == LEFT:
                side_plate.level(back=bottom_plate.back, right=bottom_plate.left, bottom=bottom_plate.top)
            else:
                side_plate.level(back=bottom_plate.back, left=bottom_plate.right, bottom=bottom_plate.top)
                side_plate.rotate("zz")

    top_plate.level(back=bottom_plate.back, left=bottom_plate.left, bottom=side_plate.top)

    return assembly


def add_corner(assembly: Assembly):
    """Add a corner cube at every place 3 plates join.

    Args:
        assembly: The assembly to add the corner cube to.
    """
    name = assembly.name
    level_dict = {
        "left": assembly.get_part(f"{name}_{LEFT.lower()}_1").right,
        "right": assembly.get_part(f"{name}_{RIGHT.lower()}_1").left,
        "top": assembly.get_part(f"{name}_{TOP.lower()}_1").bottom,
        "bottom": assembly.get_part(f"{name}_{BOTTOM.lower()}_1").top,
        "front": assembly.get_part(f"{name}_{FRONT.lower()}_1").back,
        "back": assembly.get_part(f"{name}_{BACK.lower()}_1").front,
    }

    for sides in product((LEFT, RIGHT), (TOP, BOTTOM), (FRONT, BACK)):
        conn = Connect()
        assembly.add(conn)
        conn_level_dict = {"subtract": True}
        for side in sides:
            side_lower = side.lower()
            conn_level_dict[side_lower] = level_dict[side_lower]
        conn.level(**conn_level_dict)


def compare_parts(part1, part2):
    """Compare two parts by comparing the exported features.

    Features are exported as JSON objects with sorted keys.
    These strings are then sorted per part and then compared.
    """
    exp1 = part1.export()
    exp2 = part2.export()
    features1 = sorted([json.dumps(f, sort_keys=True) for f in exp1["features"]])
    features2 = sorted([json.dumps(f, sort_keys=True) for f in exp2["features"]])
    for n in range(len(features1)):
        # We could comdiameterpare the two strings directly,
        # but doing it an element at a time gives an more informative error message.
        print(features1[n])
        print(features2[n])
        assert features1[n] == features2[n]

    exp1["name"] = ""
    exp2["name"] = ""
    assert exp1 == exp2


def test_level_subtract_side(tmp_path: Path):
    """Test adding connect cubes to different sides."""
    for side in (TOP,):
        assembly1 = make_plate_with_connect_cubes(side)
        # Help with debugging
        save_path = Path(f"/tmp/test/{side.lower()}")
        save_path.mkdir(parents=True, exist_ok=True)
        print(save_path)
        assembly1.save(save_path)
        assembly1.build(
            engine=AssemblyBuild123d(assembly1.name), part_engines=[PartEngineBuild123d(), PartEngineFreeCAD()]
        )

        for part_name, part in assembly1.parts.items():
            if "connect" in part_name:
                continue
            features = part.export().get("features", [])
            features_set = set()
            for feature in features:
                if feature["type"] == "cut":
                    features_set.add(json.dumps(feature, sort_keys=True))
                    assert feature["side"] == side
            assert len(features_set) == 4


def test_level_subtract_box(tmp_path: Path):
    assembly = make_sides()
    add_corner(assembly)
    # Help with debugging
    assembly.save("/tmp/test")
    assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d(), PartEngineFreeCAD()])

    parts = [p for p in assembly.parts.keys() if "connect" not in p]
    for part1name, part2name in combinations(parts, 2):
        part1 = assembly.get_part(part1name)
        part2 = assembly.get_part(part2name)
        compare_parts(part1, part2)
