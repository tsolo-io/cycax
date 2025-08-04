# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
from itertools import combinations, product

# from pathlib import Path
from cycax.cycad import Assembly, Cuboid, SheetMetal

# from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
# from cycax.cycad.engines.part_build123d import PartEngineBuild123d
# from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


class Connect(Cuboid):
    def __init__(self, *, holes: bool = True):
        self.holes = holes
        super().__init__(part_no="connect", x_size=20.0, y_size=20.0, z_size=20.0)

    def definition(self):
        """Calculate the connect cube."""
        for side_name in SIDES:
            pos = (10, 10)
            side = self.get_side(side_name)
            side.hole(pos=pos, diameter=3.0, depth=3)
            if self.holes:
                side.hole(pos=pos, diameter=3.2, external_subtract=True)
            else:
                side.box(pos=(pos[0] - 2, pos[1] - 2), length=4, width=4, external_subtract=True)


def make_plate_with_connect_cubes(side: str, name: str | None = None, *, holes: bool = True) -> Assembly:
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
    bp_side = getattr(base_plate, side.lower())
    cc_side = bp_side.opposite.name.lower()
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
        conn = Connect(holes=holes)
        assembly.add(conn)
        for ref_side in sides:
            conn.level(**{ref_side.lower(): getattr(base_plate, ref_side.lower())})
        conn.level(**{cc_side: bp_side, "subtract": True})
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
        side_plate.top.hole(pos=(length / 2, length / 2), diameter=3)
        side_plate.top.hole(pos=(length / 2, length / 2), diameter=6, depth=1)

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
            side_plate.rotate("zzz")  # Rotate the left and right sides
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

    for sides in product((TOP, BOTTOM), (LEFT, RIGHT), (FRONT, BACK)):
        conn = Connect()
        assembly.add(conn)
        for side in sides:
            side_lower = side.lower()
            conn.level(**{side_lower: level_dict[side_lower]})
        for side in sides:
            side_lower = side.lower()
            conn.level(**{side_lower: level_dict[side_lower], "subtract": True})


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
        assert features1[n] == features2[n]


def test_level_subtract_side():
    """Test adding connect cubes to different sides of a plate.

    Each orientation of the plate is tested separately.
    This test is a simplified version of the next test, where a box is built from plates and connectors cubes.
    """
    assembly_tests = {}
    for holes in (True, False):
        for side in SIDES:
            assembly = make_plate_with_connect_cubes(side, name=side, holes=holes)

            # Help with debugging
            # save_path = Path(f"/tmp/test-side/{side.lower()}")
            # save_path.mkdir(parents=True, exist_ok=True)
            # assembly.save(save_path)
            # assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d()])
            # assembly_tests[side] = assembly

        # Test the assembly list
        for _side, assembly in assembly_tests.items():
            for part_name, part in assembly.parts.items():
                if "connect" in part_name:
                    continue
                if holes:
                    pos_vals = (10, part.x_size - 10, part.y_size - 10)
                else:
                    pos_vals = (8, part.x_size - 12, part.y_size - 12)
                features = part.export().get("features", [])
                assert len(features) == 5
                features_set = set()
                for feature in features:
                    if feature["type"] == "cut":
                        features_set.add(json.dumps(feature, sort_keys=True))
                        assert feature["side"] in (TOP, BOTTOM)
                        assert feature["x"] in pos_vals
                        assert feature["y"] in pos_vals
                        if holes:
                            assert feature["diameter"] == 3.2
                        else:
                            assert feature["x_size"] == 4.0
                            assert feature["y_size"] == 4.0
                assert len(features_set) == 4


def test_level_subtract_box():
    """Test the creation of a box with six sides held together by eight connection cubes on the corners.

    This test checks that the level and rotate of the sides work correctly when the cubes subtrcat holes from the sides.
    """
    assembly = make_sides()
    add_corner(assembly)
    # Help with debugging
    # assembly.save("/tmp/test")
    # assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d(), PartEngineFreeCAD()])

    parts = [p for p in assembly.parts.keys() if "connect" not in p]
    for part1name, part2name in combinations(parts, 2):
        part1 = assembly.get_part(part1name)
        part2 = assembly.get_part(part2name)
        compare_parts(part1, part2)
