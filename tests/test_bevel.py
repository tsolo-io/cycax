# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from itertools import combinations
from pathlib import Path

import pytest

from cycax.cycad import SheetMetal
from tests.shared import check_json_reference, check_stl_reference, hex_code_check, stl_compare


def fancy_edge(tmp_path: Path, edge_type: str, part_no: str):
    sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no=part_no)

    edges = combinations(("LEFT", "RIGHT", "FRONT", "BACK", "TOP", "BOTTOM"), 2)
    for edge in edges:
        if edge in (("LEFT", "RIGHT"), ("TOP", "BOTTOM"), ("FRONT", "BACK")):
            with pytest.raises(Exception):  # noqa: B017 cat the base exception in the test we have not decided on custom exceptions.
                sheet.beveled_edge(edge_type=edge_type, side1=edge[0], side2=edge[1], size=3)
        else:
            sheet.beveled_edge(edge_type=edge_type, side1=edge[0], side2=edge[1], size=3)

    sheet.save(path=tmp_path)
    sheet.render("preview3d")
    sheet.render("freecad")


def test_edge_round(tmp_path: Path):
    # This test checks that the two designs of beveled edges are being produced as they should.

    fancy_edge(tmp_path, edge_type="round", part_no="sheet_round")
    assert stl_compare(tmp_path / "sheet_round" / "sheet_round.stl", Path("./tests/references/sheet_round.stl"))
    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_round",
        ext=".scad",
        hex_code="18a554a0aae5b37ec09fcf68ce3ae153cb19ebf261f4be092636e5ddacc28fd0",
    )
    check_json_reference(tmp_path / "sheet_round" / "sheet_round.json", "sheet_round.json")


def test_edge_chamfer(tmp_path: Path):
    fancy_edge(tmp_path, edge_type="chamfer", part_no="sheet_chamfer")
    check_stl_reference(tmp_path / "sheet_chamfer" / "sheet_chamfer.stl", "sheet_chamfer.stl")
    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_chamfer",
        ext=".scad",
        hex_code="d7c03ff389ae4fef7776d92c36c5db48e162714b60e94d3334415bfdb7a6d94b",
    )
    check_json_reference(tmp_path / "sheet_chamfer" / "sheet_chamfer.json", "sheet_chamfer.json")
