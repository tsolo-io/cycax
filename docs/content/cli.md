<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# The cycax command

The `cycax` command builds the parts and assemblies in a project. The usual work is three
commands:

```bash
hatch run cycax init        # make a project in this folder
hatch run cycax build       # build all targets
hatch run cycax open bracket
```

CyCAx is a dependency of each project, so use `hatch run cycax ...` (or activate the project
environment). The examples below write `cycax ...` for short.

## A project

A project is a folder with a `cycax.toml` file. CyCAx also reads a `[tool.cycax]` table in
`pyproject.toml`. CyCAx finds the project in the current folder or in a parent folder, as git
does. `-C <folder>` selects a different project.

```toml
[project]
name = "ironhive"
sources = ["parts", "assemblies"]   # folders (or files) with targets

[build]
backend = "auto"       # auto: this computer first, then the server | local | server
outputs = ["step"]     # FCStd, SCAD and the unfold DXF are added when the engine makes them
folder = "build"       # results: build/<target>/
engine = "build123d"   # default engine
profile = "standard"   # draft | standard | fine
# jobs = 4             # local build123d parts built at the same time; default: all cores

[server]
url = "nats://cycax.example.lan:4222"

[tools]
freecad = "~/Applications/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage"   # or "auto"

[quality]              # score overrides, see engine-selection.md
"openscad.stl.standard" = 5
```

Personal settings (tool paths, the editor) go in the user config file. It has the same
sections. It is `~/.config/cycax/config.toml` on Linux and `%APPDATA%\cycax\config.toml` on
Windows. `cycax config show` shows both paths.

### Targets

A target is a function or class with `@cycax_part` or `@cycax_assembly` (see
[Getting Started](getting-started.md#compiling-with-the-cli)). The target name is the function or
class name. Target names must be unique in a project, because the name is also the result folder
`build/<name>/`. `cycax list` shows an error when two targets have the same name.

You can type a part of a name when it is unique: `cycax open brack`. When a name does not
exist, CyCAx shows the names that are near it. `file.py:name` works for targets outside the
project.

## Commands

| Command | What it does |
|---|---|
| `cycax` | Shows the help screen. |
| `cycax init [folder]` | Makes `cycax.toml`, `parts/example_part.py` and `.gitignore`, then checks the tools. Asks where to build (auto, local, server). |
| `cycax new part <name>` | Adds `parts/<name>.py` from the most basic part template. `cycax new assembly <name>` adds `assemblies/<name>.py`. |
| `cycax list` | Shows the targets: name, kind, file and line, description (the docstring). |
| `cycax build [targets...]` | Builds the targets. No targets = all targets. Uses the cache. Builds parts before assemblies. |
| `cycax plan [targets...]` | Shows what a build will do, with no build: for each output the engine, local or server, the profile, and if it is in the cache. |
| `cycax open [target]` | Opens a result with the default application: FCStd, else STEP, STL, GLB, DXF, SCAD. `--step`, `--stl`, `--fcstd`, `--dxf`, `--scad`, `--glb` select one. `--folder` opens the result folder. |
| `cycax report [targets...]` | HTML quick view in `build/<target>/report/` (`index.html`, `summary.json`, `views.svg`, `render.png`, model, `features.csv`, `holes.csv`, `bom.csv` for assemblies). `--open` opens it; `--no-png` skips the render (it needs FreeCAD); `--out <folder>`. `--light`: only the six SVG side views and `features.csv` from the spec (no build, < 1 s). `--format markdown --out <parent>`: pages for the project documentation, one folder per part and assembly (`<parent>/<name>/index.md`, replaced each time; an assembly links to its parts with `../<part>/index.md`); default parent: `[report] markdown_out` in cycax.toml. |
| `cycax watch [targets...]` | Builds again each time you save a Python file of the project (only the targets in the saved files; all when a helper module changes) and makes the light report. `--draft` for speed. Ctrl+C stops. |
| `cycax view <target>` | Builds a GLB (assemblies: STL) and shows it in 3D in the browser (a local page). `--watch`: builds again on save and the page updates by itself (draft profile by default). |
| `cycax doctor` | Checks Python, build123d, FreeCAD, the SheetMetal workbench, OpenSCAD, the server and the cache. Each problem has a fix. |
| `cycax help advanced` | Shows the advanced commands. |

### Build options

| Option | What it does |
|---|---|
| `--output step,stl` (`-o`) | The formats. Default: `[build] outputs`. |
| `--draft`, `--fine` | The quality profile of meshes (STL, GLB). Default: `standard`. |
| `--force` | Builds again, also when the result is in the cache. |
| `--local`, `--server`, `--auto` | Where to build. Default: `[build] backend`. |
| `--editable` | FreeCAD: keeps the full feature tree in the FCStd file (slow). |
| `--jobs N` (`-j`) | Local build123d parts built at the same time (process pool). Default: `[build] jobs`, else all cores; `-j 1` builds one after another. |
| `--tool <engine>` | Advanced: uses this engine (build123d, freecad, openscad). Normally the planner selects it ([engine-selection.md](engine-selection.md)). |

### Advanced commands

| Command | What it does |
|---|---|
| `cycax compile [targets...]` | Writes the JSON spec of each target to `build/<target>/`. No build. |
| `cycax cache list` | Shows the local cache entries. `--sort size\|used\|name`. |
| `cycax cache open <hash>` | Opens a cache entry folder. |
| `cycax cache clean <hash>...` | Removes entries. `--older-than <days>` or `--all`. Asks first, unless `--yes`. |
| `cycax config show` | Shows all settings. |
| `cycax config get build.backend` | Shows one setting. |
| `cycax config set build.backend server` | Changes one line in `cycax.toml` (`--user`: in the user config). Comments stay. |
| `cycax config edit` | Opens `cycax.toml` (`--user`: the user config) in the editor. |

## Options for all commands

| Option | What it does |
|---|---|
| `-v`, `-vv` | More log messages (info, debug). The default shows only warnings. |
| `--debug` | Shows the full traceback of an error, and the debug log. |
| `--json` | Shows data as JSON (`list`, `build`, `plan`, `doctor`, `compile`, `cache list`, `config`). |
| `--plain` | No colour, symbols or spinner. Also when `NO_COLOR` is set or the terminal has no Unicode. |
| `-y`, `--yes` | Does not ask questions; uses the defaults. CyCAx never asks when there is no terminal. |
| `-C <folder>` | Uses the project in this folder. |

These options also work after the command name: `cycax list --json`.

## Results and errors

`cycax build` shows one line for each target: `✓` built, `↻` from the cache, `✗` failed. At
the end it shows the totals and the results folder. The full log of each build is in
`build/<target>/build.log`.

An error in your Python code shows your file and line, not the CyCAx internals:

```text
✗ broken: ZeroDivisionError: division by zero
parts/broken.py, line 8
    width = part.x_size / 0
  To fix: Correct the code at this line. Or, for the full traceback: cycax build broken --debug
```

Exit codes:

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | A build failed |
| 2 | Usage error (unknown target, unknown option, bad setting) |
| 3 | A tool or the server is not available (also `doctor` with a problem) |

## Editor

Commands that open a source file use the `[editor] command` from the user config. `{file}`
and `{line}` are replaced. Without a setting, CyCAx uses `$VISUAL`, then `$EDITOR`, then `vi`,
with `+{line}`.

```toml
[editor]
command = "zed {file}:{line}"          # Zed
# command = "code -g {file}:{line}"    # VS Code
# command = "nvim +{line} {file}"      # Neovim / Vim
```
