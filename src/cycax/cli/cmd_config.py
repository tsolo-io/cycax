# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""`cycax config show | get | set | edit`: the settings in cycax.toml and the user config file.

Keys have the TOML form `<section>.<key>`, e.g. `build.backend`. `set` changes one line and
keeps the comments in the file.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

from cycax.app.errors import ProjectError, UsageError

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)

# TOML key -> Settings attribute
KEYS = {
    "project.name": "name",
    "project.sources": "sources",
    "build.backend": "backend",
    "build.outputs": "outputs",
    "build.folder": "build_folder",
    "build.engine": "engine",
    "build.profile": "profile",
    "server.url": "server_url",
    "editor.command": "editor",
    "cache.folder": "cache_folder",
}
DICT_SECTIONS = {"tools": "tools", "quality": "quality", "report": "report"}


def _guarded(func):
    from cycax.cli.main import guarded  # noqa: PLC0415 - main imports this module

    return guarded(func)()


def _state():
    from cycax.cli.main import state  # noqa: PLC0415

    return state()


def values(settings) -> dict:
    data = {key: getattr(settings, attribute) for key, attribute in KEYS.items()}
    for section, attribute in DICT_SECTIONS.items():
        for key, value in getattr(settings, attribute).items():
            data[f"{section}.{key}"] = value
    return data


def _check_key(key: str):
    section = key.partition(".")[0]
    if key not in KEYS and section not in DICT_SECTIONS:
        msg = f"Unknown setting {key!r}."
        raise UsageError(msg, fix=f"Use one of: {', '.join(KEYS)}, or tools.*, quality.*, report.*")


def toml_value(text: str) -> str:
    """The TOML form of a value from the command line: TOML as it is, else a string."""
    try:
        tomllib.loads(f"v = {text}")
    except tomllib.TOMLDecodeError:
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def set_in_text(text: str, key: str, value: str) -> str:
    """Set `section.key = value` in TOML text; keep all other lines and comments."""
    section, _, name = key.partition(".")
    lines = text.splitlines()
    header = re.compile(r"^\s*\[([^\]]+)\]\s*(#.*)?$")
    current, insert_at = None, None
    for index, line in enumerate(lines):
        match = header.match(line)
        if match:
            if current == section:
                break
            current = match.group(1).strip()
            if current == section:
                insert_at = index + 1
            continue
        if current == section:
            if re.match(rf"^\s*{re.escape(name)}\s*=", line):
                comment = re.search(r"\s+#.*$", line)
                lines[index] = f"{name} = {value}" + (comment.group(0) if comment else "")
                return "\n".join(lines) + "\n"
            if line.strip():
                insert_at = index + 1
    if insert_at is None:
        lines.extend(["", f"[{section}]", f"{name} = {value}"] if lines else [f"[{section}]", f"{name} = {value}"])
    else:
        lines.insert(insert_at, f"{name} = {value}")
    return "\n".join(lines) + "\n"


def _config_file(*, user: bool) -> Path:
    from cycax.app.project import PROJECT_FILE, user_config_file  # noqa: PLC0415

    if user:
        return user_config_file()
    project = _state().project
    if not project.has_project_file or not (project.root / PROJECT_FILE).is_file():
        msg = "There is no cycax.toml here or in a parent folder."
        raise ProjectError(msg, fix="Run: cycax init   (or use --user for the user config)")
    return project.root / PROJECT_FILE


UserOpt = Annotated[bool, typer.Option("--user", help="The user config file (personal settings), not cycax.toml.")]


@app.command()
def show():
    """Show all settings (cycax.toml and the user config together)."""

    def run():
        from cycax.app.project import user_config_file  # noqa: PLC0415

        st = _state()
        project = st.project
        data = values(project.settings)
        if st.out.json_mode:
            st.out.print_json({"project": str(project.root), "user_config": str(user_config_file()), **data})
            return
        st.out.table([{"key": k, "value": v} for k, v in data.items()], ["key", "value"])
        st.out.print(f"\nProject: {project.root}   User config: {user_config_file()}")

    _guarded(run)


@app.command("get")
def get_value(key: str):
    """Show one setting, e.g. build.backend."""

    def run():
        _check_key(key)
        st = _state()
        value = values(st.project.settings).get(key)
        if st.out.json_mode:
            st.out.print_json({key: value})
        else:
            st.out.print(str(value) if value is not None else "")

    _guarded(run)


@app.command("set")
def set_value(key: str, value: str, *, user: UserOpt = False):
    """Change one setting, e.g. `cycax config set build.backend server`."""

    def run():
        from cycax.app.project import Project  # noqa: PLC0415

        _check_key(key)
        st = _state()
        file = _config_file(user=user)
        old = file.read_text() if file.exists() else ""
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(set_in_text(old, key, toml_value(value)))
        try:
            Project.load(st.project.root)
        except ProjectError:
            file.write_text(old)
            raise
        st.out.print(f"{st.out.sym('ok')} {key} = {toml_value(value)}   ({file})")

    _guarded(run)


@app.command()
def edit(*, user: UserOpt = False):
    """Open cycax.toml (or the user config) in the editor."""

    def run():
        from cycax.app.results import editor_command  # noqa: PLC0415

        file = _config_file(user=user)
        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text('# CyCAx user settings, e.g.\n# [editor]\n# command = "zed {file}:{line}"\n')
        subprocess.run(editor_command(_state().project, file), check=False)  # noqa: S603

    _guarded(run)
