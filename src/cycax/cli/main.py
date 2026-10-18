# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The `cycax` command (tasks cycax/15, 17, 18, 19; design: docs/cycax-cli-design.html).

The commands use the service layer (`cycax.app`); this module only reads the arguments and
shows the results. Keep the imports at the top light: `cycax --help` must start fast.

Exit codes: 0 ok, 1 build failed, 2 usage error, 3 tool or server not available.
"""

import functools
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import typer

from cycax.app.errors import CycaxError, UsageError, user_code_error
from cycax.app.project import Project
from cycax.cli import cmd_cache, cmd_config
from cycax.cli.output import BuildView, Output

KNOWN_FORMATS = ("step", "stl", "fcstd", "dxf", "scad", "glb", "png", "blend", "summary", "svg", "views", "drawing")

HELP = """\
CyCAx makes CAD files from Python.

Start
  init      Make a new CyCAx project in this folder
  new       Add a new part or assembly file to the project

Work
  build     Build the parts and assemblies
  open      Open a result in FreeCAD or the file manager
  watch     Build again each time you save a file
  view      Show a part in 3D in your web browser
  plan      Show what a build will do (engine, local or server, cache)
  report    Make a report: HTML quick view, or --light (side views)

Look
  list      Show the parts and assemblies in this project

Help
  doctor    Check that FreeCAD, OpenSCAD and the server are ready
  ui        Open the interactive screen

Example:   cycax build bracket
More help: cycax build --help    Advanced commands: cycax help advanced
"""

HELP_ADVANCED = """\
Advanced commands

  compile                   Write the JSON spec only. No build.
  cache list | open | clean Show and clean the local cache. clean asks first, unless --yes.
  config show | get | set | edit
                            Show or change the settings. edit opens cycax.toml in the editor.
  build --tool <engine>     Use this engine (build123d, freecad, openscad). Normally the
                            planner selects it.

Options for all commands (put them before the command: cycax -v build)
  -v, -vv     More log messages (info, debug)
  --debug     Full tracebacks and debug log
  --json      Data as JSON
  --plain     No colour, symbols or spinner (also when NO_COLOR is set)
  -y, --yes   Do not ask questions; use the defaults
  -C <folder> Use the project in this folder
"""


@dataclass
class State:
    out: Output
    yes: bool = False
    debug: bool = False
    project_dir: Path | None = None
    _project: Project | None = field(default=None, repr=False)

    @property
    def project(self) -> Project:
        if self._project is None:
            self._project = Project.load(self.project_dir)
        return self._project

    @property
    def can_ask(self) -> bool:
        return not self.yes and sys.stdin.isatty() and sys.stdout.isatty() and not self.out.json_mode


_STATE: State | None = None


def state() -> State:
    """The state of this run (set by the main callback)."""
    global _STATE  # noqa: PLW0603
    if _STATE is None:  # pragma: no cover - only when a command runs without the callback
        _STATE = State(out=Output())
    return _STATE


def guarded(func):
    """Show known errors with their fix, user-code errors with file and line; set the exit code."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (typer.Exit, typer.Abort, typer.TyperException, KeyboardInterrupt):
            raise
        except Exception as error:
            st = state()
            if st.debug:
                st.out.err.print_exception(show_locals=False)
            known = user_code_error(error, context=f"cycax {func.__name__.removesuffix('_cmd').replace('_', ' ')}")
            st.out.error(known)
            raise typer.Exit(known.exit_code) from None

    return wrapper


def ask_choice(question: str, options: list[tuple[str, str]], default: int = 1) -> int:
    """A numbered question. Returns the 0-based index. Asks only on a terminal, never with --yes."""
    st = state()
    if not st.can_ask:
        return default - 1
    st.out.print(question)
    width = max(len(label) for label, _ in options)
    for number, (label, detail) in enumerate(options, start=1):
        st.out.print(f"  {number}  {label:<{width}}   {detail}".rstrip())
    while True:
        answer = typer.prompt("Type a number", default=str(default), show_default=True)
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        st.out.print(f"Type a number from 1 to {len(options)}.")


def setup_logging(verbose: int, *, debug: bool, plain: bool):
    """Warning by default, -v info, -vv debug. The root logger takes all records, so that each
    `build/<target>/build.log` gets the full log; the terminal shows only the selected level."""
    level = logging.DEBUG if debug or verbose >= 2 else logging.INFO if verbose == 1 else logging.WARNING  # noqa: PLR2004
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    if plain:
        handler: logging.Handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    else:
        from rich.console import Console  # noqa: PLC0415
        from rich.logging import RichHandler  # noqa: PLC0415

        handler = RichHandler(console=Console(stderr=True), show_time=False, show_path=debug)
    handler.setLevel(level)
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    for noisy in ("asyncio", "nats", "matplotlib", "PIL", "OCP", "build123d", "trimesh"):
        logging.getLogger(noisy).setLevel(max(level, logging.INFO))


app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
    add_completion=False,
    help="CyCAx makes CAD files from Python.",
)
app.add_typer(cmd_cache.app, name="cache", help="Show and clean the local cache.", rich_help_panel="Advanced")
app.add_typer(cmd_config.app, name="config", help="Show or change the settings.", rich_help_panel="Advanced")


@app.callback()
def main(
    ctx: typer.Context,
    *,
    verbose: Annotated[
        int, typer.Option("--verbose", "-v", count=True, help="More log messages: -v info, -vv debug.")
    ] = 0,
    debug: Annotated[bool, typer.Option("--debug", help="Show full tracebacks and the debug log.")] = False,
    json_mode: Annotated[bool, typer.Option("--json", help="Show data as JSON.")] = False,
    plain: Annotated[bool, typer.Option("--plain", help="No colour, symbols or spinner.")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Do not ask questions; use the defaults.")] = False,
    project_dir: Annotated[
        Path | None, typer.Option("--project", "-C", help="Use the project in this folder.", show_default=False)
    ] = None,
):
    out = Output(plain=plain, json_mode=json_mode)
    setup_logging(verbose, debug=debug, plain=out.plain)
    global _STATE  # noqa: PLW0603
    _STATE = ctx.obj = State(out=out, yes=yes, debug=debug, project_dir=project_dir)
    if ctx.invoked_subcommand is None:
        typer.echo(HELP)


@app.command("help", rich_help_panel="Help")
def help_cmd(topic: Annotated[str | None, typer.Argument(help="advanced")] = None):
    """Show the help screen, or the advanced commands."""
    typer.echo(HELP_ADVANCED if topic == "advanced" else HELP)


# -- Start --------------------------------------------------------------------------------------
BACKENDS = [
    ("auto", "Auto: this computer first, then the CyCAx server"),
    ("local", "Only on this computer (local)"),
    ("server", "Only on the CyCAx server"),
]


@app.command(rich_help_panel="Start")
@guarded
def init(
    folder: Annotated[Path, typer.Argument(help="The project folder.")] = Path(),
    name: Annotated[str | None, typer.Option(help="The project name. Default: the folder name.")] = None,
    backend: Annotated[str | None, typer.Option(help="auto, local or server.")] = None,
):
    """Make a new CyCAx project in this folder."""
    from cycax.app import templates  # noqa: PLC0415
    from cycax.app.project import PROJECT_FILE, default_backend  # noqa: PLC0415

    st = state()
    root = folder.expanduser().resolve()
    if (root / PROJECT_FILE).exists():
        msg = f"{root} is already a CyCAx project."
        raise UsageError(msg, fix=f"Edit {root / PROJECT_FILE}, or use: cycax new part <name>")
    st.out.print(f"Make a new CyCAx project in {root}\n")
    if name is None:
        name = typer.prompt("  Project name", default=root.name) if st.can_ask else root.name
    if backend is None:
        names = [b for b, _ in BACKENDS]
        backend = BACKENDS[
            ask_choice(
                "  Where do you want to build?",
                [("", t) for _, t in BACKENDS],
                default=names.index(default_backend()) + 1,
            )
        ][0]
    if backend not in ("auto", "local", "server"):
        msg = f"Unknown backend {backend!r}."
        raise UsageError(msg, fix="Use auto, local or server.")

    root.mkdir(parents=True, exist_ok=True)
    made = []
    (root / PROJECT_FILE).write_text(templates.CYCAX_TOML.format(name=name, backend=backend))
    made.append(PROJECT_FILE)
    part_folder, content = templates.render("part", "example_part")
    part_file = root / part_folder / "example_part.py"
    if not part_file.exists():
        part_file.parent.mkdir(parents=True, exist_ok=True)
        part_file.write_text(content)
        made.append(f"{part_folder}/example_part.py")
    gitignore = root / ".gitignore"
    lines = gitignore.read_text().splitlines() if gitignore.exists() else []
    missing = [line for line in templates.GITIGNORE.splitlines() if line not in lines]
    if missing:
        gitignore.write_text("\n".join([*lines, *missing]) + "\n")
        made.append(".gitignore")
    if st.out.json_mode:
        st.out.print_json({"project": str(root), "files": made, "backend": backend})
        return
    for file in made:
        st.out.print(f"  {st.out.sym('ok')} Made {file}")
    _short_doctor(Project.load(root, user_config=True), check_server=backend != "local")
    st.out.print(f"\nNext:\n  1. Open {part_folder}/example_part.py and change it.\n  2. Run: cycax build")


def _short_doctor(project: Project, *, check_server: bool):
    from cycax.app.doctor import run_checks  # noqa: PLC0415

    st = state()
    checks = run_checks(project, check_server=check_server)
    words = {"ok": "ready", "warning": "not found", "problem": "problem"}
    tools = [c for c in checks if c.name in ("build123d", "FreeCAD", "OpenSCAD", "Server")]
    summary = ", ".join(f"{c.name} {words[c.status]}" for c in tools)
    st.out.print(f"  {st.out.sym('ok')} Checked tools: {summary}")


@app.command(rich_help_panel="Start")
@guarded
def new(
    kind: Annotated[str, typer.Argument(help="part or assembly")],
    name: Annotated[str, typer.Argument(help="The name of the new target, e.g. bracket")],
):
    """Add a new part or assembly file to the project."""
    from cycax.app import templates  # noqa: PLC0415

    st = state()
    if kind not in templates.TEMPLATES:
        msg = f"Unknown template {kind!r}."
        raise UsageError(msg, fix=f"Use one of: {', '.join(templates.TEMPLATES)}")
    project = st.project
    folder, content = templates.render(kind, name)
    file = project.root / folder / f"{templates.slug(name)}.py"
    if file.exists():
        msg = f"{file} exists."
        raise UsageError(msg, fix="Use another name.")
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content)
    if st.out.json_mode:
        st.out.print_json({"file": str(file), "target": templates.slug(name), "kind": kind})
        return
    st.out.print(f"{st.out.sym('ok')} Made {file.relative_to(project.root)}")
    if file not in project.source_files():
        st.out.print(f"{st.out.sym('warn')} {folder}/ is not in [project] sources in cycax.toml; add it.")
    st.out.print(f"Next: cycax build {templates.slug(name)}")


# -- Look ---------------------------------------------------------------------------------------
def _line(obj) -> int:
    import inspect  # noqa: PLC0415

    try:
        return inspect.getsourcelines(obj)[1]
    except (OSError, TypeError):
        return 0


def _relative(project: Project, path: Path) -> str:
    try:
        return str(path.relative_to(project.root))
    except ValueError:
        return str(path)


@app.command("list", rich_help_panel="Look")
@guarded
def list_cmd(
    source: Annotated[
        str | None, typer.Argument(help="A Python file or module outside the project. Default: the project.")
    ] = None,
):
    """Show the parts and assemblies in this project."""
    st = state()
    project = st.project
    if source:
        from cycax.targets import load_targets  # noqa: PLC0415

        file, _, name = source.partition(":")
        folder = Path(file)
        files = sorted(p for p in folder.rglob("*.py") if not p.name.startswith("_")) if folder.is_dir() else [file]
        rows = [
            {"name": t.name, "kind": t.kind, "file": str(f), "line": _line(t.obj), "description": t.description}
            for f in files
            for t in load_targets(f, name or None)
        ]
    else:
        rows = [
            {
                "name": ref.name,
                "kind": ref.kind,
                "file": _relative(project, ref.file),
                "line": _line(ref.target.obj),
                "description": ref.target.description,
            }
            for ref in project.targets().values()
        ]
    if st.out.json_mode:
        st.out.print_json(rows)
        return
    if not rows:
        st.out.print("No targets found.")
        st.out.print("To add one: cycax new part bracket")
        return
    for row in rows:
        row["file"] = f"{row['file']}:{row['line']}" if row["line"] else row["file"]
        row["description"] = (row["description"] or "").splitlines()[0] if row["description"] else ""
    st.out.table(rows, ["name", "kind", "file", "description"])


# -- Work ---------------------------------------------------------------------------------------
def _outputs(output: list[str] | None) -> list[str] | None:
    if not output:
        return None
    formats = [f.strip().lower().lstrip(".") for entry in output for f in entry.split(",") if f.strip()]
    unknown = [f for f in formats if f not in KNOWN_FORMATS]
    if unknown:
        msg = f"Unknown output format: {', '.join(unknown)}."
        raise UsageError(msg, fix=f"Use: {', '.join(KNOWN_FORMATS)}")
    return list(dict.fromkeys(formats))


def _choose(flags: dict[str, bool], what: str) -> str | None:
    chosen = [name for name, on in flags.items() if on]
    if len(chosen) > 1:
        msg = f"Use only one of {', '.join('--' + c for c in chosen)}."
        raise UsageError(msg, fix=f"Select one {what}.")
    return chosen[0] if chosen else None


OutputOpt = Annotated[
    list[str] | None, typer.Option("--output", "-o", help="Formats, e.g. step,stl. Default: cycax.toml.")
]
DraftOpt = Annotated[bool, typer.Option("--draft", help="Fast, coarse STL/GLB.")]
FineOpt = Annotated[bool, typer.Option("--fine", help="Slow, fine STL/GLB.")]
LocalOpt = Annotated[bool, typer.Option("--local", help="Build only on this computer.")]
ServerOpt = Annotated[bool, typer.Option("--server", help="Build only on the CyCAx server.")]
AutoOpt = Annotated[bool, typer.Option("--auto", help="This computer first, then the server.")]
ToolOpt = Annotated[
    str | None, typer.Option("--tool", help="Advanced: use this engine (build123d, freecad, openscad).")
]
TargetsArg = Annotated[
    list[str] | None, typer.Argument(help="Target names (or a unique part of a name), or file.py:name. Default: all.")
]


def _targets(project: Project, targets: list[str] | None) -> list[str]:
    """The target names to build; unknown names stop here (usage error, exit code 2)."""
    if targets:
        return [t if ":" in t or t.endswith(".py") else project.find_target(t).name for t in targets]
    names = list(project.targets())
    if not names:
        msg = f"No targets in {project.root}."
        raise UsageError(msg, fix="Add one: cycax new part bracket")
    return names


def _check_tool(tool: str | None):
    from cycax.app.planner import ENGINE_ORDER  # noqa: PLC0415

    if tool and tool not in ENGINE_ORDER:
        msg = f"Unknown engine {tool!r}."
        raise UsageError(msg, fix=f"Use one of: {', '.join(ENGINE_ORDER)}")


@app.command(rich_help_panel="Work")
@guarded
def build(
    targets: TargetsArg = None,
    *,
    output: OutputOpt = None,
    draft: DraftOpt = False,
    fine: FineOpt = False,
    force: Annotated[bool, typer.Option("--force", help="Build again, also when the result is in the cache.")] = False,
    local: LocalOpt = False,
    server: ServerOpt = False,
    auto: AutoOpt = False,
    editable: Annotated[bool, typer.Option("--editable", help="FreeCAD: keep the full feature tree (slow).")] = False,
    tool: ToolOpt = None,
    jobs: Annotated[
        int | None,
        typer.Option("--jobs", "-j", min=1, help="Local parts built at the same time. Default: all cores."),
    ] = None,
):
    """Build the parts and assemblies. No targets = all targets in the project."""
    from cycax.api import collect_items  # noqa: PLC0415
    from cycax.app.builder import Builder  # noqa: PLC0415

    st = state()
    project = st.project
    outputs = _outputs(output)
    profile = _choose({"draft": draft, "fine": fine}, "profile")
    backend = _choose({"local": local, "server": server, "auto": auto}, "backend")
    _check_tool(tool)
    names = _targets(project, targets)
    where = backend or project.settings.backend
    count = f"{len(names)} target{'s' if len(names) != 1 else ''}"
    header = f"Project {project.settings.name or project.root.name}   · {where}   · {count}"
    with BuildView(st.out, header) as view:
        items, failed = collect_items(project, names, on_event=view.on_event)
        if tool:
            for item in items:
                item.engine = tool
        builder = Builder(
            project,
            backend=backend,
            profile=profile,
            outputs=outputs,
            force=force,
            editable=editable,
            on_event=view.on_event,
            jobs=jobs,
        )
        result = builder.build(items)
        result.targets = {**failed, **result.targets}
    view.summary(result, project.build_folder)
    if result.ok:
        if not st.out.json_mode and result.targets:
            st.out.print(f"\nNext: cycax open {next(iter(result.targets))}")
        return
    raise typer.Exit(max(t.exit_code or 1 for t in result.targets.values() if t.error))


@app.command(rich_help_panel="Work")
@guarded
def plan(
    targets: TargetsArg = None,
    *,
    output: OutputOpt = None,
    draft: DraftOpt = False,
    fine: FineOpt = False,
    force: Annotated[bool, typer.Option("--force", help="Plan as if the cache is empty.")] = False,
    local: LocalOpt = False,
    server: ServerOpt = False,
    auto: AutoOpt = False,
    tool: ToolOpt = None,
):
    """Show what a build will do: for each output the engine, local or server, and the cache. No build."""
    from cycax.api import collect_items  # noqa: PLC0415
    from cycax.app.builder import Builder  # noqa: PLC0415

    st = state()
    project = st.project
    _check_tool(tool)
    builder = Builder(
        project,
        backend=_choose({"local": local, "server": server, "auto": auto}, "backend"),
        profile=_choose({"draft": draft, "fine": fine}, "profile"),
        outputs=_outputs(output),
        force=force,
    )
    items, failed = collect_items(project, _targets(project, targets))
    rows = [
        {"target": name, "error": result.error, "fix": result.fix, "exit_code": result.exit_code}
        for name, result in failed.items()
    ]
    for item in items:
        engine = tool or item.engine
        try:
            planned = builder.plan_object(item.obj, engine=engine)
        except Exception as error:  # noqa: BLE001 - shown per target
            known = user_code_error(error)
            rows.append({"target": item.target, "error": known.message, "fix": known.fix, "exit_code": known.exit_code})
            continue
        rows.extend(_plan_rows(item.target, planned, builder))
        all_cached = len(planned.cached) == sum(len(step.formats) for step in planned.steps)
        if planned.kind == "assembly" and not all_cached:
            try:
                for _part, part_plan in builder.plan_parts(item.obj, planned):
                    rows.extend(_plan_rows(item.target, part_plan, builder, note="input"))
            except Exception as error:  # noqa: BLE001
                known = user_code_error(error)
                rows.append(
                    {"target": item.target, "error": known.message, "fix": known.fix, "exit_code": known.exit_code}
                )
    if st.out.json_mode:
        st.out.print_json(rows)
        return
    st.out.print(
        f"Project {project.settings.name or project.root.name}   · {builder.backend}   · profile {builder.profile}\n"
    )
    st.out.table(
        [r for r in rows if not r.get("error")], ["target", "name", "kind", "format", "engine", "where", "cache"]
    )
    errors = [r for r in rows if r.get("error")]
    for row in errors:
        st.out.error(CycaxError(f"{row['target']}: {row['error']}", row.get("fix")))
    if errors:
        raise typer.Exit(max(row.get("exit_code") or 1 for row in errors))


def _plan_rows(target: str, planned, builder, note: str = "") -> list[dict]:
    rows = []
    for step in planned.steps:
        for fmt in step.formats:
            cached = planned.cached.get(fmt)
            rows.append(
                {
                    "target": target,
                    "name": planned.name,
                    "kind": f"{planned.kind} ({note})" if note else planned.kind,
                    "format": fmt,
                    "engine": step.engine,
                    "where": step.where,
                    "profile": builder.profile,
                    "cache": "yes" if cached else "no",
                    "cached_file": str(cached) if cached else None,
                    "hash": planned.cache_hash,
                }
            )
    return rows


OPEN_FORMATS = ("fcstd", "step", "stl", "dxf", "scad", "glb")


@app.command("open", rich_help_panel="Work")
@guarded
def open_cmd(
    target: Annotated[str | None, typer.Argument(help="The target name, or a unique part of it.")] = None,
    *,
    fcstd: Annotated[bool, typer.Option("--fcstd", help="The FreeCAD file.")] = False,
    step: Annotated[bool, typer.Option("--step", help="The STEP file.")] = False,
    stl: Annotated[bool, typer.Option("--stl", help="The STL file.")] = False,
    dxf: Annotated[bool, typer.Option("--dxf", help="The unfold DXF (sheet metal).")] = False,
    scad: Annotated[bool, typer.Option("--scad", help="The OpenSCAD file.")] = False,
    glb: Annotated[bool, typer.Option("--glb", help="The GLB file.")] = False,
    folder: Annotated[bool, typer.Option("--folder", help="The result folder, in the file manager.")] = False,
):
    """Open a result with the default application (FCStd in FreeCAD), or the result folder."""
    from cycax.app import results  # noqa: PLC0415

    st = state()
    project = st.project
    if target is None:
        refs = list(project.targets().values())
        if not refs:
            msg = "There are no targets in this project."
            raise UsageError(msg, fix="Add one: cycax new part bracket")
        if not st.can_ask:
            msg = "Which target? Give a target name."
            raise UsageError(msg, fix="cycax open <target>   (cycax list shows the names)")
        options = [(ref.name, f"{ref.kind:<9} {_relative(project, ref.file)}") for ref in refs]
        target = refs[ask_choice("Which target do you want to open?", options)].name
    else:
        target = project.find_target(target).name if ":" not in target else target.rpartition(":")[2]
    flags = {"fcstd": fcstd, "step": step, "stl": stl, "dxf": dxf, "scad": scad, "glb": glb, "folder": folder}
    choice = _choose(flags, "result")
    if choice == "folder":
        path = project.build_folder / target
        if not path.is_dir():
            msg = f"{target} is not built yet."
            raise UsageError(msg, fix=f"cycax build {target}")
    else:
        path = results.pick_result(project, target, choice)
    results.open_path(path)
    if st.out.json_mode:
        st.out.print_json({"opened": str(path)})
    else:
        st.out.print(f"{st.out.sym('ok')} Opened {_relative(project, path)}")


@app.command(rich_help_panel="Work")
@guarded
def report(
    targets: TargetsArg = None,
    *,
    light: Annotated[
        bool, typer.Option("--light", help="SVG side views from the spec only (no build, < 1 s).")
    ] = False,
    fmt: Annotated[str, typer.Option("--format", "-f", help="html or markdown.")] = "html",
    out: Annotated[
        Path | None,
        typer.Option(
            "--out", help="The parent folder. html default: build/<target>/report/; markdown: [report] markdown_out."
        ),
    ] = None,
    open_page: Annotated[bool, typer.Option("--open", help="Open the HTML report in the browser.")] = False,
    no_png: Annotated[bool, typer.Option("--no-png", help="No render (a render needs FreeCAD).")] = False,
    draft: DraftOpt = False,
    fine: FineOpt = False,
    local: LocalOpt = False,
    server: ServerOpt = False,
    auto: AutoOpt = False,
):
    """Make a report: HTML quick view (default), Markdown pages for the docs, or --light (side views only)."""
    import time  # noqa: PLC0415

    from cycax.api import build_items  # noqa: PLC0415

    st = state()
    project = st.project
    start = time.monotonic()
    names = _targets(project, targets)
    if light:
        from cycax.report.light import write_light_report  # noqa: PLC0415

        written = []
        for name in names:
            for item in build_items(project, name):
                spec = item.obj.export()
                parts = [spec] if spec["kind"] == "part" else [p.export() for p in _assembly_parts(item.obj)]
                for part_spec in parts:
                    sub = part_spec["name"] if spec["kind"] != "part" else ""
                    base = (out / item.target) if out else (project.build_folder / item.target / "report")
                    folder = base / "light" / sub
                    files = write_light_report(part_spec, folder)
                    written.append(
                        {
                            "target": item.target,
                            "part": part_spec["name"],
                            "folder": str(folder),
                            "files": sorted(p.name for p in files.values()),
                        }
                    )
        if st.out.json_mode:
            st.out.print_json(written)
            return
        for row in written:
            st.out.print(f"  {st.out.sym('ok')} {row['part']}  {_relative(project, Path(row['folder']))}/")
        st.out.print(f"\n  {len(written)} light report(s) in {time.monotonic() - start:.2f} s")
        return

    if fmt not in ("html", "markdown", "markdown-manual"):
        msg = f"The report format {fmt!r} does not exist yet."
        raise UsageError(msg, fix="Use --format html, markdown or markdown-manual, or --light.")
    if fmt == "markdown-manual":
        _manual_pages(
            st,
            project,
            targets,
            out,
            with_png=not no_png,
            backend=_choose({"local": local, "server": server, "auto": auto}, "backend"),
        )
        return
    if fmt == "markdown" and out is None:
        markdown_out = project.settings.report.get("markdown_out")
        if not markdown_out:
            msg = "A Markdown report needs a parent folder."
            raise UsageError(msg, fix="Use --out <folder>, or set [report] markdown_out in cycax.toml.")
        out = project.root / markdown_out
    from cycax.app.builder import Builder  # noqa: PLC0415
    from cycax.app.reports import html_report, markdown_report  # noqa: PLC0415
    from cycax.app.results import open_path  # noqa: PLC0415

    builder = Builder(
        project,
        backend=_choose({"local": local, "server": server, "auto": auto}, "backend"),
        profile=_choose({"draft": draft, "fine": fine}, "profile"),
    )
    pages = []
    for name in names:
        for item in build_items(project, name):
            if not st.out.json_mode:
                st.out.print(f"  {st.out.sym('busy')} {item.target}: making the report ...")
            if fmt == "markdown":
                indexes = markdown_report(builder, item, out, with_png=not no_png)
            else:
                folder = (out / item.target) if out else (project.build_folder / item.target / "report")
                indexes = [html_report(builder, item, folder, with_png=not no_png)]
            for index in indexes:
                pages.append({"target": item.target, "index": str(index)})
                if not st.out.json_mode:
                    st.out.print(f"  {st.out.sym('ok')} {item.target}  {_relative(project, index)}")
    if st.out.json_mode:
        st.out.print_json(pages)
    else:
        st.out.print(f"\n  {len(pages)} report(s) in {time.monotonic() - start:.1f} s")
    if open_page and pages:
        open_path(Path(pages[0]["index"]))


def _manual_pages(st, project, files, out, *, with_png: bool, backend: str | None):
    """`--format markdown-manual`: one page per example file (task cycax/29)."""
    from cycax.app.builder import Builder, BuildItem  # noqa: PLC0415
    from cycax.app.reports import _try  # noqa: PLC0415
    from cycax.report.manual import write_manual_page  # noqa: PLC0415

    if not files or not all(f.endswith(".py") for f in files):
        msg = "A manual page is made from example files."
        raise UsageError(msg, fix="cycax report examples/slots.py --format markdown-manual --out docs/content/examples")
    if out is None:
        markdown_out = project.settings.report.get("markdown_out")
        if not markdown_out:
            msg = "A manual page needs a parent folder."
            raise UsageError(msg, fix="Use --out <folder>, or set [report] markdown_out in cycax.toml.")
        out = project.root / markdown_out
    builder = Builder(project, backend=backend)

    def picture_for(target, obj):
        item = BuildItem(target.name, obj, target.engine)
        if target.kind == "assembly":
            return _try(builder, item, ["step"])
        return _try(builder, item, ["png"]) if with_png and not target.doc_view else {}

    pages = []
    for file in files:
        index = write_manual_page(Path(file), out, picture_for=picture_for)
        pages.append({"file": file, "index": str(index)})
        if not st.out.json_mode:
            st.out.print(f"  {st.out.sym('ok')} {file}  {_relative(project, index)}")
    if st.out.json_mode:
        st.out.print_json(pages)


def _assembly_parts(assembly) -> list:
    flat = assembly.combine_all_assemblies() if assembly.assemblies else assembly
    unique = {}
    for part in flat.parts.values():
        unique.setdefault(part.part_no, part)
    return list(unique.values())


@app.command(rich_help_panel="Work")
@guarded
def watch(
    targets: TargetsArg = None,
    *,
    output: OutputOpt = None,
    draft: DraftOpt = False,
    fine: FineOpt = False,
    local: LocalOpt = False,
    server: ServerOpt = False,
    auto: AutoOpt = False,
):
    """Build again each time you save a file (and make the light report). Ctrl+C stops."""
    from cycax.api import collect_items  # noqa: PLC0415
    from cycax.app.builder import Builder  # noqa: PLC0415
    from cycax.app.watch import watch as watch_files  # noqa: PLC0415
    from cycax.report.light import write_light_report  # noqa: PLC0415

    st = state()
    project = st.project
    names = _targets(project, targets)
    builder = Builder(
        project,
        backend=_choose({"local": local, "server": server, "auto": auto}, "backend"),
        profile=_choose({"draft": draft, "fine": fine}, "profile"),
        outputs=_outputs(output),
    )

    def cycle(changed: list[str]):
        from cycax.app.builder import BuildResult  # noqa: PLC0415

        with BuildView(st.out, f"{time.strftime('%H:%M:%S')}  {', '.join(changed)}") as view:
            builder.on_event = view.on_event
            items, failed = collect_items(project, changed, on_event=view.on_event)
            result = BuildResult(targets=dict(failed))
            for item in items:
                result.targets[item.target] = builder.build_item(item)
                spec = item.obj.export()
                if spec["kind"] == "part":
                    write_light_report(spec, project.build_folder / item.target / "report" / "light")
        view.summary(result, project.build_folder)

    import time  # noqa: PLC0415

    cycle(names)
    st.out.print(f"\nWatching {', '.join(project.settings.sources)} - save a file to build again. Ctrl+C stops.")
    try:
        watch_files(project, on_change=cycle, wanted=targets and names)
    except KeyboardInterrupt:
        st.out.print("Stopped.")


@app.command(rich_help_panel="Work")
@guarded
def view(
    target: Annotated[str, typer.Argument(help="The target name, or a unique part of it.")],
    *,
    watch_files: Annotated[bool, typer.Option("--watch", help="Build again on save; the browser updates.")] = False,
    draft: DraftOpt = False,
    fine: FineOpt = False,
    local: LocalOpt = False,
    server: ServerOpt = False,
    auto: AutoOpt = False,
    port: Annotated[int, typer.Option(help="The local port (0 = any free port).")] = 0,
    no_browser: Annotated[bool, typer.Option("--no-browser", help="Do not open the browser.")] = False,
):
    """Show a part or assembly in 3D in your web browser (builds a GLB first if necessary)."""
    import webbrowser  # noqa: PLC0415

    from cycax.api import build_items  # noqa: PLC0415
    from cycax.app.builder import Builder  # noqa: PLC0415
    from cycax.app.watch import LiveModel, serve, wait_forever  # noqa: PLC0415
    from cycax.app.watch import watch as watch_project  # noqa: PLC0415

    st = state()
    project = st.project
    (name,) = _targets(project, [target])
    builder = Builder(
        project,
        backend=_choose({"local": local, "server": server, "auto": auto}, "backend"),
        profile=_choose({"draft": draft, "fine": fine}, "profile") or ("draft" if watch_files else None),
    )
    model = LiveModel()

    def build_model(_changed=None):
        try:
            items = build_items(project, name)
        except Exception as error:  # noqa: BLE001 - shown in the browser and here
            known = user_code_error(error)
            model.update(None, known.message)
            st.out.error(known)
            return
        item = items[0]
        kind = "assembly" if hasattr(item.obj, "parts") else "part"
        builder.outputs = ["glb"] if kind == "part" else ["stl"]
        result = builder.build_item(item)
        if result.error:
            model.update(None, result.error)
            st.out.error(CycaxError(f"{name}: {result.error}", result.fix))
            return
        path = result.files.get("glb") or result.files.get("stl")
        model.update(path)
        word = "from cache" if result.cached else f"built in {result.seconds:.1f} s"
        st.out.print(f"  {st.out.sym('cache' if result.cached else 'ok')} {name}  {word}")

    build_model()
    server_ = serve(model, name, port)
    url = f"http://127.0.0.1:{server_.server_address[1]}/"
    st.out.print(f"\nViewer: {url}   (Ctrl+C stops)")
    if not no_browser:
        webbrowser.open(url)
    try:
        if watch_files:
            watch_project(project, on_change=build_model, wanted=[name])
        else:
            wait_forever()
    except KeyboardInterrupt:
        st.out.print("Stopped.")
    finally:
        server_.shutdown()


# -- Help ---------------------------------------------------------------------------------------
@app.command(rich_help_panel="Help")
@guarded
def ui(local: LocalOpt = False, server: ServerOpt = False, auto: AutoOpt = False):
    """Open the interactive screen: targets, details, build, open, view, report, watch."""
    from cycax.cli.ui import run_ui  # noqa: PLC0415 - Textual only for this command

    st = state()
    run_ui(st.project, backend=_choose({"local": local, "server": server, "auto": auto}, "backend"))


@app.command(rich_help_panel="Help")
@guarded
def doctor(
    *,
    no_server: Annotated[bool, typer.Option("--no-server", help="Do not check the server.")] = False,
):
    """Check that build123d, FreeCAD, OpenSCAD and the server are ready. Tells how to fix each problem."""
    from dataclasses import asdict  # noqa: PLC0415

    from cycax.app.doctor import run_checks  # noqa: PLC0415

    st = state()
    checks = run_checks(st.project, check_server=not no_server)
    problems = [c for c in checks if c.status == "problem"]
    warnings = [c for c in checks if c.status == "warning"]
    if st.out.json_mode:
        st.out.print_json([asdict(c) for c in checks])
    else:
        symbols = {"ok": "ok", "problem": "fail", "warning": "warn"}
        width = max(len(c.name) for c in checks)
        for check in checks:
            st.out.print(f"  {st.out.sym(symbols[check.status])} {check.name:<{width}}   {check.detail}")
            if check.fix and check.status != "ok":
                st.out.print(f"      To fix: {check.fix}")
        word = "Ready." if not problems else "Not ready."
        st.out.print(f"\n  {word} {len(problems)} problem(s), {len(warnings)} warning(s).")
    if problems:
        raise typer.Exit(3)


# -- Advanced -----------------------------------------------------------------------------------
@app.command("compile", rich_help_panel="Advanced")
@guarded
def compile_cmd(targets: TargetsArg = None):
    """Write the JSON spec of each target into the build folder. No build."""
    import json  # noqa: PLC0415

    from cycax.api import build_items  # noqa: PLC0415
    from cycax.spec import spec_hash  # noqa: PLC0415

    st = state()
    project = st.project
    written = []
    for name in _targets(project, targets):
        for item in build_items(project, name):
            spec = item.obj.export()
            folder = project.build_folder / item.target
            folder.mkdir(parents=True, exist_ok=True)
            file = folder / f"{spec['name']}.json"
            file.write_text(json.dumps(spec, indent=2))
            written.append({"target": item.target, "name": spec["name"], "hash": spec_hash(spec), "file": str(file)})
    if st.out.json_mode:
        st.out.print_json(written)
        return
    for row in written:
        st.out.print(f"  {st.out.sym('ok')} {row['target']}  {_relative(project, Path(row['file']))}  {row['hash']}")


GLOBAL_FLAGS = {"--json", "--plain", "--debug", "--yes", "-y", "--verbose", "-v", "-vv", "-vvv"}
GLOBAL_WITH_VALUE = {"--project", "-C"}


def global_options_first(argv: list[str]) -> list[str]:
    """Allow global options after the command too: `cycax list --json` = `cycax --json list`."""
    front, rest = [], []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--":
            rest.extend(argv[index:])
            break
        if arg in GLOBAL_FLAGS:
            front.append(arg)
        elif arg in GLOBAL_WITH_VALUE and index + 1 < len(argv):
            front.extend(argv[index : index + 2])
            index += 1
        elif arg.split("=", 1)[0] in GLOBAL_WITH_VALUE:
            front.append(arg)
        else:
            rest.append(arg)
        index += 1
    return front + rest


def run():
    """The `cycax` console script."""
    app(args=global_options_first(sys.argv[1:]), prog_name="cycax")


if __name__ == "__main__":
    run()
