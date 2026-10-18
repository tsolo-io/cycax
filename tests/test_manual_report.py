# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Manual pages from example files (task cycax/29)."""

from cycax.report.manual import example_code, write_manual_page

EXAMPLE = '''"""Brackets.

Two small examples.
"""

import math

from cycax import cycax_part
from cycax.cycad import Print3D, SheetMetal

WIDTH = 40


def helper(part):
    part.top.hole(pos=(10, 10), diameter=4)


@cycax_part(doc_view="top")
def plate() -> Print3D:
    """A plate with one hole."""
    part = Print3D(part_no="plate", x_size=WIDTH, y_size=20, z_size=5)
    helper(part)
    return part


@cycax_part
class Big(SheetMetal):
    """A big sheet."""

    def __init__(self):
        super().__init__(part_no="big", x_size=WIDTH * 2, y_size=40)


if __name__ == "__main__":
    print(math.pi)
'''


def test_example_code_has_its_own_imports_and_helpers():
    code = example_code(EXAMPLE, "plate")
    assert "from cycax import cycax_part" in code
    assert "from cycax.cycad import Print3D" in code
    assert "SheetMetal" not in code  # not used by plate
    assert "import math" not in code
    assert "WIDTH = 40" in code
    assert "def helper(part):" in code
    assert '@cycax_part(doc_view="top")' in code
    assert "__main__" not in code
    compile(code, "example", "exec")


def test_manual_page(tmp_path):
    source = tmp_path / "brackets.py"
    source.write_text(EXAMPLE)
    index = write_manual_page(source, tmp_path / "docs")
    page = index.read_text()
    assert page.startswith("# Brackets\n\nTwo small examples.")
    assert page.index("## plate") < page.index("## Big")  # file order
    assert "A plate with one hole." in page
    assert "![plate: top view](plate_top.svg)" in page
    assert (index.parent / "plate_top.svg").is_file()
    assert (index.parent / "Big_top.svg").is_file()
    # Same scale: the same px per mm in both pictures.
    svg_plate = (index.parent / "plate_top.svg").read_text()
    svg_big = (index.parent / "Big_top.svg").read_text()

    def px_per_mm(svg):
        view_w = float(svg.split('viewBox="', 1)[1].split()[2])
        width = float(svg.split('width="', 1)[1].split('"', 1)[0])
        return width / view_w

    assert abs(px_per_mm(svg_plate) - px_per_mm(svg_big)) < 0.01  # sizes are rounded to 0.1 px
