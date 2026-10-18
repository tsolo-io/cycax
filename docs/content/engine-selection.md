<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Engine Selection

How `cycax.build()` and `cycax build` decide which engine (tool) makes each requested output,
and where it runs (local or server). `cycax plan <target>` shows the result of these rules
without building anything.

Status: design for upgrade-plan work package P1.5 (task cycax/13). The four start rules were
decided on 2026-10-17; the details below are proposals until the open questions are answered.

## Terms

- **Output**: a requested file format: `step`, `stl`, `glb`, `fcstd`, `scad`, `png`, `dxf`
  (sheet-metal unfold), `blend`.
- **Engine**: what makes the file, and the name in the artifact name
  (`<name>-<engine>-<profile>.<ext>`): `build123d`, `freecad`, `openscad`, `blender`,
  `python` (build123d on the Python worker).
- **Backend**: `local`, `server` or `auto` (local first, then server).

## Which engines can make what

| Output | Part | Assembly |
|---|---|---|
| step | build123d, freecad, python | build123d, freecad |
| stl | build123d, freecad, openscad, python | build123d, freecad |
| glb | build123d, freecad, python, blender | blender |
| fcstd | freecad | freecad |
| scad | openscad | openscad |
| png | freecad, python, blender | blender |
| dxf (unfold) | freecad (sheet metal only) | — |
| blend | blender | blender |

Where each engine can run: build123d and OpenSCAD locally; FreeCAD locally (AppImage) or on
the server (FreeCAD worker, parts only for now); Blender and Python only on the server.
Blender renders a part from the part's STL: the builder makes that STL first (by the normal
rules) and hands it over, like the parts of an assembly. For a part's `png` Blender is chosen
only with `--tool blender` (or `engine="blender"`); for an assembly it is the only engine.

## Rules, in order

1. **An output that only one engine can make picks that engine**: `fcstd` and `dxf` →
   FreeCAD, `scad` → OpenSCAD, `blend` → Blender.
2. **A per-target engine** wins next: `@cycax_part(engine="freecad")`.
3. **A part-class default** comes next: `SheetMetalBend` (any part with bend or flange
   features) → FreeCAD. FreeCAD is the reference for sheet metal; build123d bends are a
   draft preview only.
4. **The project default** (`cycax.toml` `[build] engine`, default `build123d`) is used for
   everything else, if it can make the output; otherwise the first engine in the table order
   that can.
5. **Where it runs** (`backend`):
   - `local`: run locally; stop with an error if the engine is not installed locally.
   - `server`: send to the worker for that engine; stop with an error if NATS is not
     reachable or the engine has no worker.
   - `auto`: local if the engine is installed locally, else the server, else stop with an
     error that names the missing tool.
6. **Cache first**: before running anything, look for an artifact of that format at or above
   the requested profile in the cache (local cache, then the NATS cache when it is
   reachable). A hit means no build.

Assemblies: each part is planned with the rules above for the formats the assembly engine
needs (`stl` for Blender, `step` for build123d and FreeCAD), then the assembly itself.

## Defaults

- Outputs of `cycax build`: `step`; plus `fcstd` when FreeCAD builds the part, `scad` when
  OpenSCAD builds it, and the unfold `dxf` for sheet metal. `stl`/`glb` only when a command
  needs them (`view` → glb; reports and Blender → stl).
- Profile: `standard`.

## Open Questions

1. Rule 3 makes FreeCAD the engine for every sheet-metal part. With `backend = "auto"` and no
   local FreeCAD, these go to the server. Should `--draft` use build123d for sheet metal
   instead (fast preview, box bends), and only `standard`/`fine` use FreeCAD?
> Answer:

2. When the project default engine cannot make an output (e.g. default `build123d`, output
   `fcstd`), rule 1 picks FreeCAD for that output only. The same part can then come from two
   engines (STEP from build123d, FCStd from FreeCAD). Is that acceptable, or should one engine
   make all outputs of a part when it can (here: FreeCAD makes STEP and FCStd)?
> Answer:

3. Assemblies: which assembly engine is the default for `cycax build` of an assembly:
   build123d (local, STEP) or Blender (server, .blend/GLB)?
> Answer:

4. Should a per-target engine also be possible from the CLI (`--engine freecad`) for one run,
   or only in code?
> Answer:
