# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Assembly, SheetMetal


def dial_a_box(length=100, width=50, height=20, thickness=2) -> Assembly:
    """Dial a box delivers custom boxes that is open at the top.

    All boxes are made from unobtainium.
    """
    name = f"box-{thickness}-{length}x{width}x{height}"
    box = Assembly(name)

    bottomside = SheetMetal(
        x_size=length - thickness * 2, y_size=width - thickness * 2, z_size=thickness, part_no="bottom-side"
    )
    leftside = SheetMetal(x_size=width - thickness * 2, y_size=height, z_size=thickness, part_no="left-side")
    rightside = SheetMetal(x_size=width - thickness * 2, y_size=height, z_size=thickness, part_no="right-side")
    frontside = SheetMetal(x_size=length, y_size=height, z_size=thickness, part_no="front-side")
    backside = SheetMetal(x_size=length, y_size=height, z_size=thickness, part_no="back-side")

    box.add(bottomside, "bottom-side")
    box.add(frontside, "front-side")
    box.add(leftside, "left-side")
    box.add(rightside, "back-side")
    box.add(backside, "back-side")

    leftside.rotate("xz")
    rightside.rotate("xz")
    frontside.rotate("x")
    backside.rotate("x")

    bottomside.level(front=frontside.back, bottom=frontside.bottom, left=frontside.left)
    bottomside.move(x=2)
    backside.level(front=bottomside.back, bottom=frontside.bottom)
    leftside.level(front=frontside.back, bottom=frontside.bottom, right=frontside.right)
    rightside.level(front=frontside.back, bottom=frontside.bottom, left=frontside.left)
    # Create the assembly
    return box


if __name__ == "__main__":
    working_directory = Path("./box").parent.resolve()  # Define where we want the artifacts to be stored
    for size in ({"length": 100, "width": 50, "height": 20}, {"length": 50, "width": 150, "height": 30}):
        box = dial_a_box(**size)
        # Save and render the part
        box.save(working_directory / "build" / box.name)
        box.render()
        box.render(engine="openscad")
