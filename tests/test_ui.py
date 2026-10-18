# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# The terminal UI, `cycax ui` (task cycax/42), driven headless at 100 x 30 with Textual's pilot.
import contextlib

import pytest
from typer.testing import CliRunner

pytest.importorskip("textual")

from cycax.app.project import Project  # noqa: E402
from cycax.cli import ui  # noqa: E402
from cycax.cli.main import app  # noqa: E402

from .test_cli import BROKEN  # noqa: E402

SIZE = (100, 30)
pytestmark = pytest.mark.asyncio


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    folder = tmp_path / "proj"
    result = CliRunner().invoke(app, ["--yes", "init", str(folder), "--backend", "local"])
    assert result.exit_code == 0, result.output
    toml = folder / "cycax.toml"
    toml.write_text(toml.read_text() + f'\n[cache]\nfolder = "{tmp_path / "cache"}"\n')
    (folder / "parts" / "broken.py").write_text(BROKEN)
    return Project.load(folder, user_config=False)


def _ui(project):
    return ui.CycaxUI(project, check_server=False)


def _activity(app_) -> str:
    return "\n".join(line.text for line in app_.query_one("#activity").lines)


async def test_tree_header_and_details(project):
    app_ = _ui(project)
    async with app_.run_test(size=SIZE) as pilot:
        await pilot.pause()
        leaves = {node.data for node in app_._leaves(app_.query_one("#tree").root)}
        assert leaves == {"example_part", "broken"}
        assert "local" in str(app_.query_one("#header").render())
        assert app_.selected in leaves
        assert "parts/" in str(app_.query_one("#details").render())


async def test_build_the_selected_target(project):
    app_ = _ui(project)
    async with app_.run_test(size=SIZE) as pilot:
        app_.selected = "example_part"
        await pilot.press("b")
        await app_.workers.wait_for_complete()
        await pilot.pause()
        assert app_.status["example_part"] == "built"
        assert "example_part built" in _activity(app_)
        formats = [row[0] for row in (app_.query_one("#results").get_row_at(i) for i in range(app_.query_one("#results").row_count))]
        assert "STEP" in formats
        assert "Last build" in str(app_.query_one("#details").render())


async def test_a_failed_build_shows_the_error(project):
    app_ = _ui(project)
    async with app_.run_test(size=SIZE) as pilot:
        app_.selected = "broken"
        await pilot.press("b")
        await app_.workers.wait_for_complete()
        await pilot.pause()
        assert app_.status["broken"] == "failed"
        assert "broken failed" in _activity(app_)
        full = next(iter(app_.errors.values()))
        assert "broken.py" in full
        app_.query_one("#activity").focus()
        await pilot.press("enter")
        assert isinstance(app_.screen, ui.ErrorScreen)
        await pilot.press("escape")
        assert not isinstance(app_.screen, ui.ErrorScreen)


async def test_filter_backend_help(project):
    app_ = _ui(project)
    async with app_.run_test(size=SIZE) as pilot:
        await pilot.press("slash", "b", "r", "o")
        await pilot.pause()
        assert {node.data for node in app_._leaves(app_.query_one("#tree").root)} == {"broken"}
        await pilot.press("enter", "escape")
        await pilot.pause()
        assert len(list(app_._leaves(app_.query_one("#tree").root))) == 2  # noqa: PLR2004
        await pilot.press("l")
        assert app_.backend == "server"
        await pilot.press("l")
        assert app_.backend == "auto"
        await pilot.press("question_mark")
        assert isinstance(app_.screen, ui.HelpScreen)
        await pilot.press("escape")
        assert not isinstance(app_.screen, ui.HelpScreen)


async def test_open_view_report_and_editor(project, monkeypatch):
    opened, started, edited = [], [], []
    monkeypatch.setattr(ui, "open_path", opened.append)
    monkeypatch.setattr(ui.subprocess, "Popen", lambda command, **_: started.append(command))
    monkeypatch.setattr(ui.subprocess, "run", lambda command, **_: edited.append(command))
    monkeypatch.setattr(ui.CycaxUI, "suspend", lambda _self: contextlib.nullcontext())
    app_ = _ui(project)
    async with app_.run_test(size=SIZE) as pilot:
        app_.selected = "example_part"
        await pilot.press("o")  # not built yet: a message, nothing opened
        assert opened == []
        assert "not built" in _activity(app_)
        await pilot.press("b")
        await app_.workers.wait_for_complete()
        await pilot.press("o")
        assert opened and opened[0].suffix == ".step"
        await pilot.press("v", "r")
        # python -m cycax.cli.main -C <project> <command ...>
        assert [command[5:] for command in started] == [["view", "example_part"], ["report", "example_part", "--open"]]
        await pilot.press("e")
        assert edited and str(project.root / "parts" / "example_part.py") in edited[0]


async def test_watch_toggles(project):
    app_ = _ui(project)
    async with app_.run_test(size=SIZE) as pilot:
        await pilot.press("w")
        assert app_._watch_stop is not None
        assert "watching" in str(app_.query_one("#header").render())
        await pilot.press("w")
        assert app_._watch_stop is None
