<!--
SPDX-FileCopyrightText: 2025, 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# CyCAx Data File Specification (version 2)

CyCAx writes two kinds of JSON file: a **part** file (a base shape plus features) and an
**assembly** file (a flat list of placed parts). The files are the contract between the Python
DSL, the CLI and every engine and worker.

- The Pydantic models are in `cycax.spec` (`PartSpec`, `AssemblySpec`, `validate_spec`).
- JSON Schemas for tools that do not use Python: `src/cycax/spec/schemas/part.schema.json`
  and `assembly.schema.json` (regenerate with `python -m cycax.spec`).
- Version 2 is a hard cut-over: tools reject other versions with a clear error.

## Rules

1. Every file has `spec_version` (`2`), `kind` (`"part"` or `"assembly"`) and `name`.
2. All lengths are millimetres (float). All angles are degrees (float). There is no unit setting.
3. **`meta` objects hold everything that does not change the shape**: description, notes,
   `doc_view`, material, colour, manufacturing. They can appear on the file and on assembly
   part entries.
4. **The cache hash** is xxh64 of the orjson-serialised file **with every `meta` key removed,
   at any depth** (`cycax.spec.spec_hash`). So a change to a description, a material or a
   colour does not cause a rebuild. The name is part of the hash.
5. The files are verbose by design: no loops, variables or templates. Repetition and
   parameters live in the Python code that writes the file.

## Part file

```json
{
  "spec_version": 2,
  "kind": "part",
  "name": "aluminium_bracket",
  "features": [
    {"name": "cube", "type": "cuboid", "action": "add", "side": "BOTTOM",
     "x": 0.0, "y": 0.0, "z": 0.0, "x_size": 80.0, "y_size": 50.0, "z_size": 3.0, "center": false},
    {"name": "hole", "type": "cylinder", "action": "subtract", "side": "TOP",
     "x": 40.0, "y": 25.0, "z": 3.0, "diameter": 30.0, "depth": 3.0}
  ],
  "subtract": [],
  "meta": {
    "description": "A bracket that holds the shaft.",
    "notes": "Longer **Markdown** text for the reports.",
    "doc_view": "top",
    "material": {"name": "aluminium", "code": "5052-H32", "standard": "AISI"},
    "colour": [0.75, 0.75, 0.75]
  }
}
```

- `features`: `features[0]` is the base shape (`cuboid`, `cylinder` or `sphere`, action
  `add`). Every feature has `type` and `action` (`add`, `subtract`, `bend`, ...) plus fields of
  its own type; see [Part features](data-file-part-spec-features.md).
- `subtract`: features that are not cut into this part but into the parts it is placed against
  (`external_subtract=True` in the DSL).
- `meta` (not hashed): `description` (the docstring of the `@cycax_part` target), `notes`
  (Markdown), `doc_view` (picture view for the manual), `material` (`name`, `code`, optional
  `standard`, optional `density` in g/cm³; see [Materials](materials.md)), `colour` (`[r, g, b]`
  or `[r, g, b, a]`, each 0.0-1.0; from the material when the part has no colour), `manufacture`
  (later).

## Assembly file

```json
{
  "spec_version": 2,
  "kind": "assembly",
  "name": "ironhive5ur",
  "parts": [
    {"name": "rack_cover_side_plate", "instance": "rack_cover_side_plate_1",
     "hash": "28294d32bd0816cc",
     "x": 0.0, "y": 0.0, "z": 0.0, "x_size": 440.0, "y_size": 89.0, "z_size": 2.0,
     "center": false, "rotate": [{"axis": "x", "angle": 90.0}],
     "meta": {"colour": [0.5, 0.5, 0.5]}}
  ],
  "meta": {"description": "The 5U rack."}
}
```

- `parts` is flat: nested assemblies in the DSL are unpacked before the file is written.
- `name` is the part number, `instance` the unique name of this copy in the assembly, `hash`
  the cache key of that part's file (workers find the exact part by it; two parts with the same
  name can differ in size).
- `x`/`y`/`z`: position of the placed part (the minimum corner); `x_size`/`y_size`/`z_size`: its
  size; `rotate`: rotations in the order applied (axis and degrees); `transform`: the placement
  as a 4 x 4 row-major matrix (part coordinates to world, mm). Engines use `transform`; `x`/`y`/`z`
  and `rotate` stay for readers and older specs.
- `meta.colour` (not hashed): the display colour of this instance. `meta.material` (not hashed,
  only when the part has a material): the part's material, the same object as in the part file;
  renderers use it for the look of the part.
- `meta` on the file (not hashed): `description`, `notes`.

## Kind detection

Tools use `kind`. (Version 1 files had no `kind`; tools told parts from assemblies by a
`features` or `parts` list. Version 1 is no longer supported.)
