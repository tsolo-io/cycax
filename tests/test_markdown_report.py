# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The Markdown engineering report (task cycax/28)."""

import re

from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.app.reports import markdown_report
from cycax.cycad import Assembly, Print3D, SheetMetal
from cycax.materials import ALUMINIUM_5052_H32, PLA


def project(tmp_path) -> Project:
    settings = Settings()
    settings.cache_folder = str(tmp_path / "cache")
    settings.backend = "local"
    return Project(tmp_path, settings)


def links(page: str) -> list[str]:
    return re.findall(r"\]\(([^)]+)\)", page)


def test_part_page(tmp_path):
    plate = SheetMetal(part_no="plate", x_size=100, y_size=50, z_size=2, material=ALUMINIUM_5052_H32)
    plate.top.hole(pos=(10, 10), diameter=4.2)
    plate.description = "A test plate."
    (index,) = markdown_report(Builder(project(tmp_path)), BuildItem("plate", plate), tmp_path / "docs", with_png=False)
    page = index.read_text()
    assert index == tmp_path / "docs" / "plate" / "index.md"
    assert page.startswith("# plate\n\nA test plate.")
    assert "| Mass | 26.7 g |" in page
    assert "## Holes" in page
    assert "```" not in page  # no code on report pages
    for link in links(page):
        assert not link.startswith(("/", "http")), link
        assert (index.parent / link).is_file(), link


def test_assembly_has_sibling_part_folders(tmp_path):
    assembly = Assembly("pair")
    a = Print3D(part_no="block", x_size=10, y_size=10, z_size=10, material=PLA)
    b = Print3D(part_no="lid", x_size=10, y_size=10, z_size=2, material=PLA)
    assembly.add(a)
    assembly.add(b)
    b.level(bottom=a.top)
    docs = tmp_path / "docs"
    (docs / "pair").mkdir(parents=True)
    (docs / "pair" / "old.md").write_text("old")  # the folder is replaced
    pages = markdown_report(Builder(project(tmp_path)), BuildItem("pair", assembly), docs, with_png=False)
    assert [p.parent.name for p in pages] == ["pair", "block", "lid"]
    page = pages[0].read_text()
    assert "[block](../block/index.md)" in page
    assert "[lid](../lid/index.md)" in page
    assert not (docs / "pair" / "old.md").exists()
    for link in links(page):
        assert (pages[0].parent / link).is_file(), link
