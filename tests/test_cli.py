# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The `cycax` command (tasks cycax/15, 17, 18, 19)."""

import json

import pytest
from typer.testing import CliRunner

from cycax.cli.main import app, global_options_first

BROKEN = """\
from cycax import cycax_part
from cycax.cycad import Print3D


@cycax_part
def broken() -> Print3D:
    part = Print3D(part_no="broken", x_size=10, y_size=10, z_size=2)
    width = part.x_size / 0
    return part
"""


@pytest.fixture
def cli(tmp_path, monkeypatch):
    """Run cycax in a new project; the user config and the cache are in tmp_path."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("NO_COLOR", "1")
    project = tmp_path / "proj"
    runner = CliRunner()

    def run(*args, check_code: int | None = 0):
        result = runner.invoke(app, ["--yes", "-C", str(project), *args])
        if check_code is not None:
            assert result.exit_code == check_code, result.output
        return result

    run("init", str(project), "--backend", "local")
    toml = project / "cycax.toml"
    toml.write_text(toml.read_text() + f'\n[cache]\nfolder = "{tmp_path / "cache"}"\n')
    run.project = project
    return run


def test_no_arguments_show_the_help_screen():
    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0
    assert "Start" in result.output
    assert "cycax help advanced" in result.output


def test_global_options_after_the_command():
    assert global_options_first(["list", "--json", "-C", "x"]) == ["--json", "-C", "x", "list"]
    assert global_options_first(["build", "-vv", "a", "--", "--json"]) == ["-vv", "build", "a", "--", "--json"]


def test_init_makes_a_project(cli):
    project = cli.project
    assert (project / "cycax.toml").is_file()
    assert (project / "parts" / "example_part.py").is_file()
    assert "build/" in (project / ".gitignore").read_text()
    result = cli("init", str(project), check_code=2)
    assert "already a CyCAx project" in result.output


def test_new_and_list(cli):
    cli("new", "assembly", "Two Plates")
    assert (cli.project / "assemblies" / "two_plates.py").is_file()
    rows = json.loads(cli("--json", "list").output)
    assert {(r["name"], r["kind"]) for r in rows} == {("example_part", "part"), ("two_plates", "assembly")}
    assert rows[0]["description"]


def test_list_from_a_sub_folder(cli, monkeypatch):
    sub = cli.project / "parts"
    monkeypatch.chdir(sub)
    result = CliRunner().invoke(app, ["--json", "list"])
    assert result.exit_code == 0, result.output
    assert "example_part" in result.output


def test_duplicate_target_names_are_an_error(cli):
    (cli.project / "parts" / "copy.py").write_text((cli.project / "parts" / "example_part.py").read_text())
    result = cli("list", check_code=2)
    assert "Two targets have the name 'example_part'" in result.output


def test_unknown_target_suggests_names(cli):
    result = cli("build", "exampel_part", check_code=2)
    assert "Did you mean: example_part" in result.output


def test_unknown_output_format(cli):
    result = cli("build", "--output", "step,xyz", check_code=2)
    assert "Unknown output format: xyz" in result.output


def test_two_backends_is_a_usage_error(cli):
    cli("build", "--local", "--server", check_code=2)


def test_error_in_user_code_shows_file_and_line(cli):
    (cli.project / "parts" / "broken.py").write_text(BROKEN)
    result = cli("build", "broken", check_code=1)
    assert "ZeroDivisionError: division by zero" in result.output
    assert "parts/broken.py, line 8" in result.output
    assert "width = part.x_size / 0" in result.output
    assert "To fix:" in result.output


def test_compile_writes_the_spec(cli):
    rows = json.loads(cli("--json", "compile", "example_part").output)
    spec = json.loads((cli.project / "build" / "example_part" / "example_part.json").read_text())
    assert spec["spec_version"] == 2
    assert rows[0]["hash"]


def test_plan_shows_engine_and_cache(cli):
    rows = json.loads(cli("--json", "plan", "example_part").output)
    assert [(r["format"], r["engine"], r["where"], r["cache"]) for r in rows] == [("step", "build123d", "local", "no")]
    rows = json.loads(cli("--json", "plan", "example_part", "--output", "scad").output)
    assert rows[0]["engine"] == "openscad"


def test_build_then_cache(cli):
    result = cli("build", "example_part")
    assert "1 built" in result.output
    assert (cli.project / "build" / "example_part" / "example_part.step").is_file()
    assert (cli.project / "build" / "example_part" / "build.log").is_file()
    result = cli("build", "example_part")
    assert "1 from cache" in result.output
    rows = json.loads(cli("--json", "plan", "example_part").output)
    assert rows[0]["cache"] == "yes"
    rows = json.loads(cli("--json", "cache", "list").output)
    assert any(r["name"] == "example_part" for r in rows)


def test_open_without_a_target_and_no_terminal(cli):
    result = cli("open", check_code=2)
    assert "Give a target name" in result.output


def test_open_not_built(cli):
    result = cli("open", "example_part", check_code=2)
    assert "not built yet" in result.output


def test_config_set_and_get(cli):
    cli("config", "set", "build.profile", "draft")
    assert cli("config", "get", "build.profile").output.strip() == "draft"
    assert 'profile = "draft"' in (cli.project / "cycax.toml").read_text()
    cli("config", "set", "build.backend", "bogus", check_code=2)
    assert 'backend = "local"' in (cli.project / "cycax.toml").read_text()
    cli("config", "get", "nothing.here", check_code=2)


def test_cache_clean_asks_first(cli):
    runner = CliRunner()
    result = runner.invoke(app, ["-C", str(cli.project), "cache", "clean", "--all"])
    # No entries: nothing to ask.
    assert result.exit_code == 0, result.output


def test_doctor_json(cli):
    result = cli("--json", "doctor", "--no-server", check_code=None)
    assert result.exit_code in (0, 3)
    names = {c["name"] for c in json.loads(result.output)}
    assert {"Python", "build123d", "FreeCAD", "Project"} <= names
