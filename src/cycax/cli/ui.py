# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The terminal UI, `cycax ui` (task cycax/42; layout: docs cycax-cli-design.html section 8).

A thin layer on the service layer (cycax.app), like the CLI: the project tree with a status per
target, the details of the selected target, the activity log, and keys for the everyday
actions. Every action is also a CLI command. Not flashy: the terminal's own colours (an
ANSI theme); colour only for status, always with a symbol too.
"""

import json
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Input, RichLog, Static, Tree

from cycax.app.events import Event, TargetDone, TargetFailed, TargetProgress, TargetStarted
from cycax.app.project import Project
from cycax.app.results import editor_command, open_path, pick_result, result_files

# Status symbol, word and style (colour is never the only signal).
STATUS = {
    "built": ("✓", "built", "green"),
    "cached": ("↻", "cached", "green"),
    "failed": ("✗", "failed", "red"),
    "building": ("•", "building", "yellow"),
    "new": ("·", "not built", "dim"),
}
BACKENDS = ("auto", "local", "server")
ACTIVITY_LINES = 50

HELP = """\
Keys

  b        Build the selected target
  a        Build all targets
  o        Open the native result (FCStd in FreeCAD, else STEP, ...)
  v        View the selected target in 3D in the web browser
  r        Make the report of the selected target and open it
  w        Watch on/off: build again when a file is saved
  l        Change between auto, local and server
  e        Open the source file in the editor, at the target's line
  /        Filter the targets by name (Esc clears)
  Enter    On a result: open it. On a failed activity line: the full error.
  ?        This help
  q        Quit (server builds go on)

Every action is also a command: cycax build, open, view, report, watch.
Press Esc or q to close this help."""


def _line(obj) -> int:
    import inspect  # noqa: PLC0415

    try:
        return inspect.getsourcelines(obj)[1]
    except (OSError, TypeError):
        return 0


class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape,q,question_mark", "app.pop_screen", "Close")]  # noqa: RUF012

    def compose(self) -> ComposeResult:
        yield Static(HELP, id="help")


class ErrorScreen(ModalScreen):
    BINDINGS = [Binding("escape,q,enter", "app.pop_screen", "Close")]  # noqa: RUF012

    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield Static(self.text, id="help")


class Activity(RichLog):
    """The activity log; Enter shows the full text of the newest failure."""

    BINDINGS = [Binding("enter", "app.show_error", "Full error")]  # noqa: RUF012
    can_focus = True


class CycaxUI(App):
    """`cycax ui`."""

    TITLE = "CyCAx"
    CSS = """
    Screen { layout: vertical; }
    #header { height: 1; padding: 0 1; }
    #main { height: 1fr; }
    #left { width: 36; border: round $foreground 50%; border-title-align: left; }
    #filter { display: none; border: none; height: 1; padding: 0 1; }
    #filter.visible { display: block; }
    #tree { height: 1fr; }
    #right { border: round $foreground 50%; border-title-align: left; padding: 0 1; }
    #details { height: auto; }
    #results { height: auto; max-height: 12; margin-top: 1; }
    #activity { height: 8; border: round $foreground 50%; border-title-align: left; }
    #help { width: 76; height: auto; border: round $foreground; padding: 1 2; background: $background; }
    HelpScreen, ErrorScreen { align: center middle; }
    """
    BINDINGS = [  # noqa: RUF012
        Binding("b", "build", "Build"),
        Binding("a", "build_all", "Build all"),
        Binding("o", "open", "Open"),
        Binding("v", "view", "View 3D"),
        Binding("r", "report", "Report"),
        Binding("w", "watch", "Watch: off"),
        Binding("l", "backend", "Local/server"),
        Binding("e", "edit", "Editor", show=False),
        Binding("slash", "filter", "Filter", show=False),
        Binding("escape", "clear_filter", "Clear filter", show=False),
        Binding("question_mark", "help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, project: Project, *, backend: str | None = None, check_server: bool = True):
        super().__init__(ansi_color=True)
        self.project = project
        self.backend = backend or project.settings.backend
        self.check_server = check_server
        self.status: dict[str, str] = {}
        self.last_build: dict[str, str] = {}
        self.errors: dict[int, str] = {}  # activity line -> full error
        self.selected: str | None = None
        self.filter_text = ""
        self.server_state = "server: checking" if check_server else ""
        self._watch_stop: threading.Event | None = None
        self._busy = threading.Lock()  # one build at a time
        self._children: list[subprocess.Popen] = []

    # -- layout ---------------------------------------------------------------------------
    def compose(self) -> ComposeResult:
        yield Static(id="header")
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield Input(placeholder="Filter targets", id="filter")
                yield Tree("Project", id="tree")
            with VerticalScroll(id="right"):
                yield Static(id="details")
                yield DataTable(id="results", cursor_type="row", show_header=False)
        yield Activity(id="activity", max_lines=ACTIVITY_LINES, wrap=False, markup=False)
        yield Footer()

    def on_mount(self):
        # The terminal's own colours (Textual >= 2: "ansi-dark"; older: "textual-ansi").
        for theme in ("ansi-dark", "textual-ansi"):
            if theme in self.available_themes:
                self.theme = theme
                break
        self.query_one("#left").border_title = "Project"
        self.query_one("#activity").border_title = "Activity"
        tree = self.query_one("#tree", Tree)
        tree.show_root = False
        tree.guide_depth = 2
        self.query_one("#results", DataTable).add_columns("Format", "File", "")
        for name in self._targets():
            self.status[name] = "built" if result_files(self.project, name) else "new"
        self._fill_tree()
        self._header()
        if self.check_server:
            self._probe_server()

    def _targets(self) -> dict:
        try:
            return self.project.targets()
        except Exception as error:  # noqa: BLE001 - shown, the UI stays open
            self._log("failed", f"Cannot load the project: {error}", full=str(error))
            return {}

    def _header(self):
        name = self.project.settings.name or self.project.root.name
        left = f"CyCAx · {name} · {self.backend}"
        watching = " · watching" if self._watch_stop else ""
        self.query_one("#header", Static).update(Text(f"{left}{watching}   {self.server_state}"))

    def _fill_tree(self):
        tree = self.query_one("#tree", Tree)
        tree.clear()
        by_file: dict[Path, list] = {}
        for ref in self._targets().values():
            if self.filter_text and self.filter_text.lower() not in ref.name.lower():
                continue
            by_file.setdefault(ref.file, []).append(ref)
        first = None
        for file, refs in by_file.items():
            branch = tree.root.add(self._relative(file), expand=True)
            for ref in refs:
                node = branch.add_leaf(self._label(ref.name, ref.kind), data=ref.name)
                if ref.name == self.selected or first is None:
                    first = node
        if first is not None and self.selected not in {ref.name for refs in by_file.values() for ref in refs}:
            self.selected = first.data
        self._show_details()

    def _label(self, name: str, kind: str) -> Text:
        symbol, _word, style = STATUS[self.status.get(name, "new")]
        label = Text()
        label.append(symbol, style=style)
        label.append(f" {name}")
        label.append(f"  {kind}", style="dim")
        return label

    def _refresh_labels(self):
        targets = self._targets()
        for node in self._leaves(self.query_one("#tree", Tree).root):
            ref = targets.get(node.data)
            if ref:
                node.set_label(self._label(ref.name, ref.kind))

    def _leaves(self, node):
        for child in node.children:
            if child.data is not None:
                yield child
            yield from self._leaves(child)

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.project.root))
        except ValueError:
            return str(path)

    # -- details --------------------------------------------------------------------------
    def _show_details(self):
        details = self.query_one("#details", Static)
        table = self.query_one("#results", DataTable)
        table.clear()
        right = self.query_one("#right")
        name = self.selected
        ref = self._targets().get(name) if name else None
        if ref is None:
            right.border_title = ""
            details.update("No target selected." if self._targets() else "No targets. Add one: cycax new part bracket")
            return
        right.border_title = name
        details.update(self._details_text(ref))
        for fmt, path in result_files(self.project, name).items():
            table.add_row(fmt.upper(), path.name, "Open", key=str(path))
        report = self.project.build_folder / name / "report"
        if report.is_dir():
            table.add_row("REPORT", f"{self._relative(report)}/", "Open", key=str(report))

    def _details_text(self, ref) -> Text:
        line = _line(ref.target.obj)
        text = Text()
        location = f"{self._relative(ref.file)}, line {line}" if line else self._relative(ref.file)
        text.append(f"{ref.kind.capitalize()} · {location}\n")
        symbol, word, style = STATUS[self.status.get(ref.name, "new")]
        text.append(symbol, style=style)
        text.append(f" {word}\n\n")
        for key, value in self._facts(ref.name):
            text.append(f"{key:<12}{value}\n")
        if ref.target.description:
            text.append(f"\n{ref.target.description.strip().splitlines()[0]}\n", style="dim")
        return text

    def _facts(self, name: str) -> list[tuple[str, str]]:
        """Size, material, mass and features from the last build's files (when there)."""
        folder = self.project.build_folder / name
        facts = []
        summary = _read_json(next(iter(sorted(folder.glob("*_summary.json"))), None)) if folder.is_dir() else None
        specs = [p for p in sorted(folder.glob("*.json")) if not p.name.endswith("_summary.json")] if folder.is_dir() else []
        spec = _read_json(specs[0]) if specs else None
        if summary and summary.get("bbox"):
            size = summary["bbox"].get("size") or []
            if size:
                facts.append(("Size", " × ".join(f"{v:.1f}" for v in size) + " mm"))
        material = (spec or {}).get("meta", {}).get("material") or (summary or {}).get("material")
        if isinstance(material, dict):
            facts.append(("Material", " ".join(str(material[k]) for k in ("name", "code") if material.get(k))))
        if summary and summary.get("mass_g"):
            facts.append(("Mass", f"{summary['mass_g']:.1f} g"))
        if spec:
            if spec.get("kind") == "assembly":
                facts.append(("Parts", str(len(spec.get("parts", [])))))
            else:
                features = spec.get("features", [])
                counts: dict[str, int] = {}
                for feature in features:
                    counts[feature.get("type", "?")] = counts.get(feature.get("type", "?"), 0) + 1
                detail = ", ".join(f"{count} {kind}" for kind, count in sorted(counts.items()))
                facts.append(("Features", f"{len(features)} ({detail})" if detail else str(len(features))))
        if name in self.last_build:
            facts.append(("Last build", self.last_build[name]))
        else:
            log = folder / "build.log"
            if log.is_file():
                facts.append(("Last build", time.strftime("%Y-%m-%d %H:%M", time.localtime(log.stat().st_mtime))))
        return facts

    @on(Tree.NodeHighlighted, "#tree")
    def _highlighted(self, event: Tree.NodeHighlighted):
        if event.node.data is not None:
            self.selected = event.node.data
            self._show_details()

    @on(DataTable.RowSelected, "#results")
    def _open_row(self, event: DataTable.RowSelected):
        self._open(Path(event.row_key.value))

    # -- activity -------------------------------------------------------------------------
    def _log(self, status: str, message: str, *, full: str | None = None):
        symbol, _word, style = STATUS.get(status, ("·", "", ""))
        line = Text(time.strftime("%H:%M:%S  "))
        line.append(symbol, style=style)
        line.append(f" {message}")
        log = self.query_one("#activity", RichLog)
        log.write(line)
        if full:
            self.errors[len(log.lines) - 1] = full

    def on_build_event(self, event: Event):
        """Builder events (from the build thread through call_from_thread)."""
        name = event.target
        if isinstance(event, TargetStarted):
            self.status[name] = "building"
            self._log("building", f"{name} building ({self.backend})")
        elif isinstance(event, TargetProgress):
            self._log("building", f"{name}: {event.message}")
        elif isinstance(event, TargetDone):
            self.status[name] = "cached" if event.cached else "built"
            word = "from the cache" if event.cached else "built"
            self.last_build[name] = f"{time.strftime('%H:%M')} · {event.seconds:.1f} s · {self.backend}"
            self._log(self.status[name], f"{name} {word} {event.seconds:.1f} s")
        elif isinstance(event, TargetFailed):
            self.status[name] = "failed"
            full = event.error + (f"\n\nTo fix: {event.fix}" if event.fix else "")
            self._log("failed", f"{name} failed: {event.error.splitlines()[0] if event.error else ''}", full=full)
        self._refresh_labels()
        if name == self.selected:
            self._show_details()

    def action_show_error(self):
        if self.errors:
            self.push_screen(ErrorScreen(self.errors[max(self.errors)]))  # the newest failure

    # -- actions --------------------------------------------------------------------------
    def action_build(self):
        if self.selected:
            self._build([self.selected])

    def action_build_all(self):
        self._build(list(self._targets()))

    @work(thread=True, exclusive=False)
    def _build(self, names: list[str]):
        if not self._busy.acquire(blocking=False):
            self.call_from_thread(self._log, "building", "A build is running; wait for it to end.")
            return
        try:
            self._run_build(names)
        finally:
            self._busy.release()

    def _run_build(self, names: list[str]):
        from cycax.api import collect_items  # noqa: PLC0415
        from cycax.app.builder import Builder  # noqa: PLC0415
        from cycax.app.watch import forget_project_modules  # noqa: PLC0415

        forget_project_modules(self.project)  # build the code as it is saved now

        def emit(event):
            self.call_from_thread(self.on_build_event, event)

        try:
            items, _failed = collect_items(self.project, names, on_event=emit)
        except Exception as error:  # noqa: BLE001 - shown in the activity log
            self.call_from_thread(self._log, "failed", f"Cannot load the project: {error}", full=str(error))
            return
        Builder(self.project, backend=self.backend, on_event=emit).build(items)
        self.call_from_thread(self._show_details)

    def action_open(self):
        if not self.selected:
            return
        try:
            path = pick_result(self.project, self.selected)
        except Exception as error:  # noqa: BLE001 - CycaxError with a fix
            self._log("failed", f"{error} {getattr(error, 'fix', '') or ''}".strip())
            return
        self._open(path)

    def _open(self, path: Path):
        try:
            open_path(path)
            self._log("built", f"Opened {self._relative(path)}")
        except Exception as error:  # noqa: BLE001 - e.g. no xdg-open
            self._log("failed", f"{error} {getattr(error, 'fix', '') or ''}".strip())

    def action_view(self):
        if self.selected:
            self._cli(["view", self.selected], f"3D view of {self.selected} in the web browser")

    def action_report(self):
        if self.selected:
            self._cli(["report", self.selected, "--open"], f"Report of {self.selected}")

    def _cli(self, args: list[str], message: str):
        """Run a CLI command in the background (its output goes to the build folder)."""
        command = [sys.executable, "-m", "cycax.cli.main", "-C", str(self.project.root), *args]
        if self.backend != self.project.settings.backend:
            command.append(f"--{self.backend}")
        folder = self.project.build_folder
        folder.mkdir(parents=True, exist_ok=True)
        with (folder / "cycax-ui.log").open("a") as out:
            self._children.append(subprocess.Popen(command, stdout=out, stderr=out, stdin=subprocess.DEVNULL))  # noqa: S603
        self._log("building", f"{message}: cycax {' '.join(args)}")

    def action_watch(self):
        if self._watch_stop:
            self._watch_stop.set()
            self._watch_stop = None
            self._log("new", "Watch off")
        else:
            self._watch_stop = threading.Event()
            self._watch(self._watch_stop)
            self._log("new", "Watch on: save a file to build again")
        self._set_watch_label()
        self._header()

    def _set_watch_label(self):
        state = "on" if self._watch_stop else "off"
        self.bind("w", "watch", description=f"Watch: {state}")
        self.refresh_bindings()

    @work(thread=True)
    def _watch(self, stop: threading.Event):
        from cycax.app.watch import watch  # noqa: PLC0415

        def changed(names):
            with self._busy:
                self._run_build(names)

        watch(self.project, on_change=changed, stop=stop)

    def action_backend(self):
        self.backend = BACKENDS[(BACKENDS.index(self.backend) + 1) % len(BACKENDS)]
        self._log("new", f"Builds now: {self.backend}")
        self._header()

    def action_edit(self):
        if not self.selected:
            return
        ref = self._targets().get(self.selected)
        if ref is None:
            return
        command = editor_command(self.project, ref.file, _line(ref.target.obj) or 1)
        try:
            with self.suspend():
                subprocess.run(command, check=False)  # noqa: S603
        except Exception as error:  # noqa: BLE001 - e.g. the editor is not installed
            self._log("failed", f"Cannot start the editor {command[0]}: {error}")

    def action_filter(self):
        box = self.query_one("#filter", Input)
        box.add_class("visible")
        box.focus()

    def action_clear_filter(self):
        box = self.query_one("#filter", Input)
        if box.has_class("visible"):
            box.value = ""
            box.remove_class("visible")
            self.filter_text = ""
            self._fill_tree()
            self.query_one("#tree").focus()

    @on(Input.Changed, "#filter")
    def _filter_changed(self, event: Input.Changed):
        self.filter_text = event.value
        self._fill_tree()

    @on(Input.Submitted, "#filter")
    def _filter_done(self, _event: Input.Submitted):
        self.query_one("#tree").focus()

    def action_help(self):
        self.push_screen(HelpScreen())

    @work(thread=True)
    def _probe_server(self):
        from cycax.app.server import ServerClient  # noqa: PLC0415

        online = ServerClient(self.project.settings.server_url).available()
        self.server_state = "● server online" if online else "○ server offline"
        self.call_from_thread(self._header)

    def on_unmount(self):
        if self._watch_stop:
            self._watch_stop.set()


def _read_json(path: Path | None) -> dict | None:
    if path is None:
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def run_ui(project: Project, *, backend: str | None = None):
    """Run the UI; log records go to `<build folder>/cycax-ui.log`, not over the screen."""
    folder = project.build_folder
    folder.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    saved = root.handlers[:]
    handler = logging.FileHandler(folder / "cycax-ui.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.handlers = [handler]
    try:
        CycaxUI(project, backend=backend).run()
    finally:
        root.handlers = saved
        handler.close()
