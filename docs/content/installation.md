<!--
SPDX-FileCopyrightText: 2025, 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Installation

CyCAx is a dependency of each CAD project, as other Python libraries are. There is no global
install. Each project has its own CyCAx version, and you run the `cycax` command with
`hatch run cycax ...`.

## Requirements

- Python 3.10 to 3.14.
- [Hatch](https://hatch.pypa.io/) (it uses [uv](https://docs.astral.sh/uv/) to install quickly).
- Linux, macOS or Windows.
- Optional: FreeCAD 1.1 (FCStd files and sheet-metal parts), OpenSCAD (SCAD files). Without
  them, the CyCAx server can build these files (`backend = "server"` or `"auto"`).

## A new project (recommended)

1. Make the project folder and its `pyproject.toml`:

    ```toml
    [project]
    name = "gusset"
    version = "0.1.0"
    requires-python = ">=3.10"
    dependencies = ["cycax"]

    [tool.hatch.envs.default]
    installer = "uv"

    [tool.hatch.envs.default.env-vars]
    # The Tsolo package index on Gitea. CI publishes each new cycax version there.
    UV_EXTRA_INDEX_URL = "https://gitea.tu.tsolo.net/api/packages/Kuat/pypi/simple/"
    PIP_EXTRA_INDEX_URL = "https://gitea.tu.tsolo.net/api/packages/Kuat/pypi/simple/"
    ```

    Use `"cycax>=0.3.0rc5"` (or a newer version) to get a release candidate, because pip and
    uv do not select pre-release versions by default.

2. Make the CyCAx project and check the tools:

    ```bash
    hatch run cycax init       # cycax.toml, parts/example_part.py, .gitignore
    hatch run cycax doctor     # build123d, FreeCAD, OpenSCAD, the server
    hatch run cycax build
    ```

The first `hatch run` makes the environment and installs CyCAx. Then continue with
[Getting Started](getting-started.md) and [The cycax command](cli.md).

### Without the Gitea index

CyCAx is open source. You can also install it from GitHub:

```toml
dependencies = ["cycax @ git+https://github.com/tsolo-io/cycax"]

[tool.hatch.metadata]
allow-direct-references = true
```

## Work on CyCAx itself

```bash
git clone https://github.com/tsolo-io/cycax.git
cd cycax
hatch run cycax --help          # the development version
hatch run testing:test          # the tests
```

To use your working copy of CyCAx in a CAD project, add it as an editable dependency in
that project: `dependencies = ["cycax @ file:///home/<you>/src/cycax"]` (with
`allow-direct-references = true`), or `hatch run pip install -e ~/src/cycax`.

## CAD tools

| Tool | Needed for | Install |
|---|---|---|
| build123d | STEP, STL, GLB of parts and assemblies (the default engine) | Installed with CyCAx. |
| FreeCAD 1.1 + SheetMetal workbench | FCStd files, sheet-metal parts (bends, unfold DXF) | Linux: the AppImage from [freecad.org](https://www.freecad.org/downloads.php). Then in FreeCAD: Tools > Addon manager > SheetMetal. |
| OpenSCAD | SCAD files | Linux: `sudo apt install openscad` or the AppImage. macOS: `brew install openscad`. |

CyCAx finds FreeCAD and OpenSCAD in the `PATH` and in `~/Applications/`. To use a different
file, set the path in the user config file (`~/.config/cycax/config.toml`):

```toml
[tools]
freecad = "~/Applications/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage"
openscad = "/usr/bin/openscad"
```

`hatch run cycax doctor` shows what CyCAx found, and how to fix each problem.

## Windows

- Use Windows Terminal or the VS Code terminal. They show the colours and the symbols. In an
  old console, use `--plain`.
- `cycax init` selects `backend = "server"` on Windows. Then FreeCAD and OpenSCAD are not
  necessary on the Windows computer: the CyCAx server builds FCStd, sheet-metal parts and
  SCAD files. build123d still builds locally.
- Set the server in `cycax.toml`: `[server] url = "nats://<server>:4222"`.
- `cycax open` uses the default application of each file type.
- For the editor, set `[editor] command = "code -g {file}:{line}"` in
  `%APPDATA%\cycax\config.toml`.

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'cycax'` | Use `hatch run ...` in the project folder, or `hatch shell`. |
| `cycax` installs an old version | Add the version, e.g. `"cycax>=0.3.0rc5"`, then `hatch env prune`. |
| No matching distribution for cycax | Check the `UV_EXTRA_INDEX_URL` in `pyproject.toml`, and that you can open the index URL. |
| FreeCAD or OpenSCAD not found | Run `hatch run cycax doctor`; set the path in `[tools]`. |
| Server not reachable | Check `[server] url`; build with `--local`. |

If you find a problem, open an issue at <https://github.com/tsolo-io/cycax/issues> with the
output of `hatch run cycax doctor`.
