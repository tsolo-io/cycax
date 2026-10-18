# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# Parallel local builds (task cycax/41): uncached build123d parts are built in a process pool
# before the serial pass; the serial pass uses those results and reports pool failures.
from typing import ClassVar

from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.app.tools import Build123dTool
from cycax.cycad import SheetMetal


def _project(tmp_path, **settings):
    return Project(tmp_path, Settings(cache_folder=str(tmp_path / "cache"), backend="local", **settings))


def _plates(count):
    items = []
    for number in range(count):
        plate = SheetMetal(part_no=f"plate{number}", x_size=20 + number, y_size=10, z_size=2)
        plate.top.hole(pos=(5, 5), diameter=3)
        items.append(BuildItem(target=plate.part_no, obj=plate))
    return items


class _BadPart:
    """A target whose spec no engine can build (unknown feature type)."""

    source_files: ClassVar[dict] = {}

    def export(self):
        return {
            "spec_version": 2,
            "kind": "part",
            "name": "bad",
            "features": [{"name": "x", "type": "no_such_feature", "action": "add", "side": "BOTTOM"}],
            "subtract": [],
            "meta": {},
        }


def _no_serial_build(monkeypatch):
    """Fail if the main process builds a part itself (pool workers import a fresh cycax)."""
    calls = []

    def build(_self, **kwargs):
        calls.append(kwargs["spec"]["name"])
        msg = "built in the main process"
        raise AssertionError(msg)

    monkeypatch.setattr(Build123dTool, "build", build)
    return calls


def test_parts_build_in_the_pool(tmp_path, monkeypatch):
    calls = _no_serial_build(monkeypatch)
    result = Builder(_project(tmp_path), outputs=["step", "stl"], jobs=2).build(_plates(3))
    assert result.ok, {name: target.error for name, target in result.targets.items()}
    assert calls == []
    for name, target in result.targets.items():
        assert target.files["step"].exists(), name
        assert target.files["stl"].stat().st_size > 0


def test_force_also_builds_in_the_pool(tmp_path, monkeypatch):
    project = _project(tmp_path)
    assert Builder(project, outputs=["step"], jobs=2).build(_plates(2)).ok
    calls = _no_serial_build(monkeypatch)
    result = Builder(project, outputs=["step"], jobs=2, force=True).build(_plates(2))
    assert result.ok, {name: target.error for name, target in result.targets.items()}
    assert calls == []


def test_a_pool_failure_is_reported_without_a_second_build(tmp_path, monkeypatch):
    calls = _no_serial_build(monkeypatch)
    items = [*_plates(2), BuildItem(target="bad", obj=_BadPart())]
    result = Builder(_project(tmp_path), outputs=["step"], jobs=2).build(items)
    assert not result.ok
    assert "no_such_feature" in result.targets["bad"].error
    assert result.targets["plate0"].files and result.targets["plate1"].files
    assert calls == []


def test_one_job_builds_one_after_another(tmp_path, monkeypatch):
    calls = []
    original = Build123dTool.build

    def build(self, **kwargs):
        calls.append(kwargs["spec"]["name"])
        return original(self, **kwargs)

    monkeypatch.setattr(Build123dTool, "build", build)
    result = Builder(_project(tmp_path), outputs=["step"], jobs=1).build(_plates(2))
    assert result.ok
    assert calls == ["plate0", "plate1"]
