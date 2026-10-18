# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The light report (task cycax/26)."""

import csv
import time
import xml.etree.ElementTree as ET

from cycax.cycad import Print3D
from cycax.report.light import SIDES, items_of, side_view_svg, write_light_report

SVG = "{http://www.w3.org/2000/svg}"


def plate():
    part = Print3D(part_no="plate", x_size=40, y_size=20, z_size=5)
    part.top.hole(pos=(10, 10), diameter=4.2, depth=2)  # a blind hole from the top
    part.front.hole(pos=(30, 2.5), diameter=2)  # through, from the front
    return part.export()


def labels(svg: str) -> set[str]:
    root = ET.fromstring(svg)  # noqa: S314 - our own output
    return {g.get("data-label") for g in root.iter(f"{SVG}g")} - {"base"}


def test_six_views_and_features_csv(tmp_path):
    start = time.monotonic()
    files = write_light_report(plate(), tmp_path)
    assert time.monotonic() - start < 1.0
    assert {path.name for path in files.values()} == {f"{s.lower()}.svg" for s in SIDES} | {"features.csv"}
    rows = list(csv.DictReader(files["features"].open()))
    assert [row["label"] for row in rows] == ["base", "C1", "C2"]
    assert rows[1]["views"] == "top"  # blind hole: only seen from the top


def test_a_cut_is_shown_only_where_it_reaches_the_surface():
    spec = plate()
    items = items_of(spec)
    assert labels(side_view_svg(spec, "TOP", items)) == {"C1"}
    assert labels(side_view_svg(spec, "BOTTOM", items)) == set()
    assert labels(side_view_svg(spec, "FRONT", items)) == {"C2"}
    assert labels(side_view_svg(spec, "BACK", items)) == {"C2"}  # a through hole


def test_cut_style_is_red_and_dashed():
    svg = side_view_svg(plate(), "TOP")
    circle = next(ET.fromstring(svg).iter(f"{SVG}circle"))  # noqa: S314
    assert circle.get("stroke") == "#d62728"
    assert circle.get("stroke-dasharray")
    assert float(circle.get("r")) == 2.1


def test_adds_are_always_drawn():
    part = Print3D(part_no="post", x_size=20, y_size=20, z_size=2)
    part.top.box_add(pos=(5, 5), width=4, length=4, depth=10)
    spec = part.export()
    for side in SIDES:
        if side != "BOTTOM":
            assert any(label.startswith(("A", "C")) for label in labels(side_view_svg(spec, side))), side


def test_cli_report_light(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from cycax.cli.main import app

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    runner = CliRunner()
    project = tmp_path / "proj"
    assert runner.invoke(app, ["--yes", "init", str(project), "--backend", "local"]).exit_code == 0
    result = runner.invoke(app, ["-C", str(project), "report", "--light"])
    assert result.exit_code == 0, result.output
    assert (project / "build" / "example_part" / "report" / "light" / "top.svg").is_file()


def test_sheet_has_six_views():
    from cycax.report.light import sheet_svg

    root = ET.fromstring(sheet_svg(plate()))  # noqa: S314
    assert len([child for child in root if child.tag == f"{SVG}g"]) == 6
