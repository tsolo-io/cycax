# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The HTML report (task cycax/27)."""

import csv
import json

import cycax
from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.app.reports import html_report
from cycax.cycad import Assembly, Print3D, SheetMetal
from cycax.materials import ALUMINIUM_5052_H32, PLA
from cycax.report.html_report import bom_rows, holes_csv


def plate():
    part = SheetMetal(part_no="plate", x_size=100, y_size=50, z_size=2, material=ALUMINIUM_5052_H32)
    part.top.hole(pos=(10, 10), diameter=4.2)
    return part


def project(tmp_path) -> Project:
    settings = Settings()
    settings.cache_folder = str(tmp_path / "cache")
    settings.backend = "local"
    return Project(tmp_path, settings)


def test_holes_csv():
    rows = list(csv.DictReader(holes_csv(plate().export()).splitlines()))
    assert rows == [{"label": "C1", "side": "TOP", "x": "10", "y": "10", "z": "2", "diameter": "4.2", "depth": "2"}]


def test_part_report(tmp_path):
    proj = project(tmp_path)
    index = html_report(Builder(proj), BuildItem("plate", plate()), tmp_path / "report", with_png=False)
    folder = index.parent
    assert {p.name for p in folder.iterdir()} >= {
        "index.html",
        "summary.json",
        "views.svg",
        "features.csv",
        "holes.csv",
        "model.glb",
        "plate.step",
    }
    page = index.read_text()
    assert "26.7 g" in page  # (100 x 50 x 2 - pi x 2.1² x 2) mm³ x 2.68 g/cm³
    assert "Laser cut from aluminium 5052-H32 sheet." in page
    assert "data:application/octet-stream;base64," in page  # the model works from file://
    summary = json.loads((folder / "summary.json").read_text())
    assert summary["material"]["name"] == "aluminium"


def test_assembly_bom(tmp_path):
    assembly = Assembly("pair")
    a = Print3D(part_no="block", x_size=10, y_size=10, z_size=10, material=PLA)
    b = Print3D(part_no="block", x_size=10, y_size=10, z_size=10, material=PLA)
    assembly.add(a)
    assembly.add(b)
    b.level(left=a.right)
    proj = project(tmp_path)
    index = html_report(Builder(proj), BuildItem("pair", assembly), tmp_path / "report")
    rows = list(csv.DictReader((index.parent / "bom.csv").open()))
    assert len(rows) == 1
    assert rows[0]["quantity"] == "2"
    assert float(rows[0]["total_mass_g"]) == 2 * 1.24
    assert "Bill of materials" in index.read_text()


def test_bom_rows_without_summaries():
    spec = {"parts": [{"name": "x", "hash": "h1"}, {"name": "x", "hash": "h1"}, {"name": "y", "hash": "h2"}]}
    rows = bom_rows(spec, {}, {})
    assert [(r["part"], r["quantity"], r["mass_g"]) for r in rows] == [("x", 2, ""), ("y", 1, "")]


def test_cli_report_html(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from cycax.cli.main import app

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    runner = CliRunner()
    proj = tmp_path / "proj"
    assert runner.invoke(app, ["--yes", "init", str(proj), "--backend", "local"]).exit_code == 0
    toml = proj / "cycax.toml"
    toml.write_text(toml.read_text() + f'\n[cache]\nfolder = "{tmp_path / "cache"}"\n')
    result = runner.invoke(app, ["-C", str(proj), "report", "example_part", "--no-png"])
    assert result.exit_code == 0, result.output
    assert (proj / "build" / "example_part" / "report" / "index.html").is_file()
    assert runner.invoke(app, ["-C", str(proj), "report", "--format", "pdf"]).exit_code == 2
    assert cycax  # imported for the lazy build entry point
