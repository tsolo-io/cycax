# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The project: `cycax.toml`, settings, and the build targets in it (task cycax/17).

A project is a folder with a `cycax.toml` (or a `[tool.cycax]` table in `pyproject.toml`).
CyCAx finds it like git finds a repository: in the current folder or a parent folder.
Personal settings (tool paths, the editor) are in the user config file:
`~/.config/cycax/config.toml` on Linux, `%APPDATA%\\cycax\\config.toml` on Windows.
"""

import difflib
import logging
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path

from cycax.app.errors import ProjectError, TargetNotFoundError

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

PROJECT_FILE = "cycax.toml"
SKIP_FOLDERS = {".git", ".hatch", ".venv", "venv", "build", "dist", "__pycache__", "node_modules", "site"}


def default_backend() -> str:
    """`auto` on Linux and macOS, `server` on Windows (no local FreeCAD needed there)."""
    return "server" if platform.system() == "Windows" else "auto"


def user_config_file() -> Path:
    import platformdirs  # noqa: PLC0415 - small, but only needed here

    return Path(platformdirs.user_config_dir("cycax", appauthor=False)) / "config.toml"


def default_cache_folder() -> str:
    """~/.cache/cycax on Linux, the normal cache folder on macOS and Windows."""
    import platformdirs  # noqa: PLC0415

    return platformdirs.user_cache_dir("cycax", appauthor=False)


@dataclass
class Settings:
    name: str = ""
    sources: list[str] = field(default_factory=lambda: ["."])
    backend: str = field(default_factory=default_backend)  # local | server | auto
    outputs: list[str] = field(default_factory=lambda: ["step"])
    build_folder: str = "build"
    engine: str = "build123d"  # project default engine (engine-selection.md rule 4)
    profile: str = "standard"
    server_url: str = "nats://127.0.0.1:4222"
    tools: dict[str, str] = field(default_factory=dict)  # freecad/openscad: path or "auto"
    report: dict = field(default_factory=dict)
    quality: dict[str, int] = field(default_factory=dict)  # score overrides
    editor: str = ""  # e.g. "zed {file}:{line}"; empty = $VISUAL / $EDITOR / vi
    cache_folder: str = field(default_factory=default_cache_folder)
    jobs: int | None = None  # parallel local builds; None = all cores, 1 = one at a time

    def apply(self, data: dict):
        """Merge a parsed TOML document (cycax.toml, [tool.cycax] or the user config)."""
        project = data.get("project", {})
        build = data.get("build", {})
        server = data.get("server", {})
        self.name = project.get("name", self.name)
        self.sources = list(project.get("sources", self.sources))
        self.backend = build.get("backend", self.backend)
        self.outputs = list(build.get("outputs", self.outputs))
        self.build_folder = build.get("folder", self.build_folder)
        self.engine = build.get("engine", self.engine)
        self.profile = build.get("profile", self.profile)
        self.jobs = build.get("jobs", self.jobs)
        self.server_url = server.get("url", self.server_url)
        self.tools.update(data.get("tools", {}))
        self.report.update(data.get("report", {}))
        self.quality.update({key: int(value) for key, value in data.get("quality", {}).items()})
        self.editor = data.get("editor", {}).get("command", self.editor)
        self.cache_folder = data.get("cache", {}).get("folder", self.cache_folder)
        if self.backend not in ("local", "server", "auto"):
            msg = f"Unknown backend {self.backend!r} in the settings."
            raise ProjectError(msg, fix="Use local, server or auto.")


def find_project_root(start: Path | None = None) -> Path | None:
    """The nearest folder (start or a parent) with cycax.toml, or with [tool.cycax] in pyproject.toml."""
    folder = (start or Path.cwd()).resolve()
    for candidate in (folder, *folder.parents):
        if (candidate / PROJECT_FILE).is_file():
            return candidate
        pyproject = candidate / "pyproject.toml"
        if pyproject.is_file() and "tool" in (doc := _read_toml(pyproject)) and "cycax" in doc["tool"]:
            return candidate
    return None


def _read_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        msg = f"Cannot read {path}: {error}"
        raise ProjectError(msg, fix=f"Correct the TOML in {path}.") from error


@dataclass
class TargetRef:
    name: str
    kind: str
    file: Path
    target: object  # cycax.targets.Target


class Project:
    """A CyCAx project (or the current folder, when there is no cycax.toml)."""

    def __init__(self, root: Path | None = None, settings: Settings | None = None):
        self.root = (root or Path.cwd()).resolve()
        self.settings = settings or Settings()
        self._targets: dict[str, TargetRef] | None = None

    @classmethod
    def load(cls, start: Path | None = None, *, user_config: bool = True) -> "Project":
        """Find and load the project around `start` (default: the current folder)."""
        settings = Settings()
        root = find_project_root(start)
        if root is not None:
            if (root / PROJECT_FILE).is_file():
                settings.apply(_read_toml(root / PROJECT_FILE))
            else:
                settings.apply(_read_toml(root / "pyproject.toml")["tool"]["cycax"])
        if user_config:
            config = user_config_file()
            if config.is_file():
                settings.apply(_read_toml(config))
        return cls(root or (start or Path.cwd()), settings)

    @property
    def has_project_file(self) -> bool:
        return find_project_root(self.root) == self.root

    @property
    def build_folder(self) -> Path:
        folder = Path(self.settings.build_folder).expanduser()
        return folder if folder.is_absolute() else self.root / folder

    def source_files(self) -> list[Path]:
        files = []
        for source in self.settings.sources:
            path = (self.root / source).resolve()
            if path.is_file() and path.suffix == ".py":
                files.append(path)
            elif path.is_dir():
                for file in sorted(path.rglob("*.py")):
                    relative = file.relative_to(path).parts
                    if any(part in SKIP_FOLDERS or part.startswith(".") for part in relative[:-1]):
                        continue
                    if not file.name.startswith("_"):
                        files.append(file)
        return files

    def targets(self) -> dict[str, TargetRef]:
        """All targets in the project sources. Target names must be unique."""
        if self._targets is not None:
            return self._targets
        from cycax.targets import load_targets  # noqa: PLC0415 - imports user code

        found: dict[str, TargetRef] = {}
        for file in self.source_files():
            try:
                file_targets = load_targets(file)
            except Exception as error:  # noqa: BLE001 - one broken file must not hide the rest
                logging.warning("Skipping %s: %s", file, error)
                continue
            for target in file_targets:
                if target.name in found:
                    other = found[target.name].file
                    msg = f"Two targets have the name {target.name!r}: {other} and {file}."
                    raise ProjectError(msg, fix="Target names must be unique in a project; rename one.")
                found[target.name] = TargetRef(target.name, target.kind, file, target)
        self._targets = found
        return found

    def find_target(self, name: str) -> TargetRef:
        """A target by its name, or by a unique part of the name."""
        targets = self.targets()
        if name in targets:
            return targets[name]
        matches = [key for key in targets if name.lower() in key.lower()]
        if len(matches) == 1:
            return targets[matches[0]]
        if len(matches) > 1:
            msg = f"The name {name!r} matches more than one target: {', '.join(sorted(matches))}."
            raise TargetNotFoundError(msg, fix="Type more of the name.")
        close = difflib.get_close_matches(name, list(targets), n=3, cutoff=0.5)
        hint = f"Did you mean: {', '.join(close)}?" if close else None
        msg = f"No target with the name {name!r}."
        raise TargetNotFoundError(msg, fix=hint or "To see all targets: cycax list")
