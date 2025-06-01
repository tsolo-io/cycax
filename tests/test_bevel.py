# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from itertools import combinations
from pathlib import Path

import pytest

from cycax.cycad import SheetMetal
from tests.shared import hex_code_check


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


def test_edge(tmp_path: Path):
    # This test checks that the two designs of beveled edges are being produced as they should.

    fancy_edge(tmp_path, edge_type="round", part_no="sheet_round")
    fancy_edge(tmp_path, edge_type="chamfer", part_no="sheet_chamfer")

    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_round",
        ext=".scad",
        hex_code="18a554a0aae5b37ec09fcf68ce3ae153cb19ebf261f4be092636e5ddacc28fd0",
    )

    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_round",
        ext=".stl",
        hex_codes=[
            "cf0f9c6a51c52f13977b6338c809a8ccd37643b5b937367cf0f329a5a02705cd",
            "31e8b431facaf2b32a2a130a086d5d44cfecf14da531b7488f8c5c2d6484a4fb",
        ],
    )

    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_round",
        ext=".json",
        hex_code="b224c64efdd0f82f092af986a21f20c9a67c2b0c99cbda2955e69a018715d26c",
    )

    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_chamfer",
        ext=".scad",
        hex_code="d7c03ff389ae4fef7776d92c36c5db48e162714b60e94d3334415bfdb7a6d94b",
    )

    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_chamfer",
        ext=".stl",
        hex_code="4bbcee334a5b95c759574e47b8960ecba076584ba1343ba839aa9f15745fbf8d",
    )

    hex_code_check(
        tmp_path=tmp_path,
        filename="sheet_chamfer",
        ext=".json",
        hex_code="57e6bbe2ce79d236b6d361d3fdfaad7ffc308d16025a0123ae0a0b8325e78d9c",
    )
