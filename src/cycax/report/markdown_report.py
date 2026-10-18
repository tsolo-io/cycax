# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: E501 - Markdown table lines
"""The Markdown engineering report (task cycax/28, `cycax report --format markdown`).

Pages for the project documentation (Zensical builds them on CI). One folder per part and per
assembly, all siblings under one parent folder (`--out`): `<parent>/<name>/index.md` plus its
pictures. A part has exactly one folder; an assembly page links to its parts with
`../<part>/index.md`. Each folder is replaced each time. Relative links only, no code.
"""

import shutil
from pathlib import Path

from cycax.report import units
from cycax.report.html_report import bom_rows, holes_csv
from cycax.report.light import SIDES, features_csv, items_of, side_view_svg
from cycax.spec import spec_hash


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _csv_table(text: str, columns: list[str] | None = None) -> str:
    import csv  # noqa: PLC0415
    import io  # noqa: PLC0415

    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return ""
    columns = columns or list(rows[0])
    return _table(columns, [[row[c] for c in columns] for row in rows])


def _fresh(folder: Path):
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)


def _head(spec: dict, target: str) -> list[str]:
    meta = spec.get("meta", {})
    lines = [f"# {target}", ""]
    if meta.get("description"):
        lines += [meta["description"], ""]
    if meta.get("notes"):
        lines += [meta["notes"], ""]
    return lines


def _facts(summary: dict | None, meta: dict) -> list[list[str]]:
    facts = []
    if summary:
        facts.append(["Size", " x ".join(f"{v:g}" for v in summary["bbox_mm"]["size"]) + " mm"])
        facts.append(["Volume", units.volume(summary["volume_mm3"])])
        facts.append(["Surface area", units.area(summary["area_mm2"])])
        if "mass_g" in summary:
            facts.append(["Mass", units.mass(summary["mass_g"])])
        sheet = summary.get("sheet_metal")
        if sheet:
            facts.append(["Sheet thickness", units.length(sheet["thickness_mm"])])
            facts.append(["Flat area", units.area(sheet["flat_area_mm2"])])
    material = meta.get("material")
    if material:
        facts.append(
            [
                "Material",
                " ".join(v for v in (material.get("name"), material.get("code"), material.get("standard")) if v),
            ]
        )
    return facts


def _manufacture(meta: dict) -> list[str]:
    manufacture = meta.get("manufacture")
    if not manufacture:
        return []
    lines = [
        "## How to make it",
        "",
        f"Process: **{manufacture.get('process', '')}**, quantity {manufacture.get('quantity', 1)}.",
        "",
    ]
    lines += [f"{index}. {line}" for index, line in enumerate(manufacture.get("instructions", []), start=1)]
    return [*lines, ""]


def write_markdown_part(folder: Path, spec: dict, *, target: str, artifacts: dict[str, Path]) -> Path:
    """`<folder>/index.md` and its pictures for one part."""
    import json  # noqa: PLC0415

    _fresh(folder)
    meta = spec.get("meta", {})
    summary = json.loads(Path(artifacts["summary"]).read_text()) if "summary" in artifacts else None
    lines = _head(spec, target)

    pictures = []
    if "png" in artifacts:
        shutil.copyfile(artifacts["png"], folder / "render.png")
        pictures.append(f"![{target}](render.png)")
    items = items_of(spec)
    for view in SIDES:
        (folder / f"{view.lower()}.svg").write_text(side_view_svg(spec, view, items))
    if "drawing" in artifacts:
        shutil.copyfile(artifacts["drawing"], folder / "drawing.svg")
        pictures.append(f"![{target} drawing](drawing.svg)")
    if pictures:
        lines += [*pictures, ""]

    facts = _facts(summary, meta)
    if facts:
        lines += [_table(["Property", "Value"], facts), ""]
    lines += _manufacture(meta)

    lines += ["## Side views", "", "Cuts are red and dashed, adds green, bend lines blue.", ""]
    lines += [f"![{view.lower()}]({view.lower()}.svg)" for view in ("TOP", "FRONT", "RIGHT")]
    lines += [""]

    sheet = (summary or {}).get("sheet_metal")
    if sheet:
        rows = [
            [b["id"], b["label"], f"{b['angle_deg']:g}°", b["direction"], f"{b['radius_mm']:g} mm", b["k_factor"]]
            for b in sheet["bends"]
        ]
        lines += ["## Bends", "", _table(["Bend", "Label", "Angle", "Direction", "Radius", "K-factor"], rows), ""]
    holes = _csv_table(holes_csv(spec))
    if holes:
        lines += ["## Holes", "", holes, ""]
    lines += [
        "## Features",
        "",
        _csv_table(features_csv(items), ["label", "role", "type", "side", "x", "y", "z", "size", "views"]),
        "",
    ]

    downloads = []
    if "step" in artifacts:
        shutil.copyfile(artifacts["step"], folder / f"{spec['name']}.step")
        downloads.append(f"[{spec['name']}.step]({spec['name']}.step)")
    if summary:
        (folder / "summary.json").write_text(json.dumps(summary, indent=2))
        downloads.append("[summary.json](summary.json)")
    if downloads:
        lines += ["## Files", "", " · ".join(downloads), ""]
    lines += [f"<small>CyCAx · hash `{spec_hash(spec)}`</small>", ""]
    index = folder / "index.md"
    index.write_text("\n".join(lines))
    return index


def write_markdown_assembly(
    folder: Path,
    spec: dict,
    *,
    target: str,
    artifacts: dict[str, Path],
    part_specs: dict[str, dict],
    part_summaries: dict[str, dict],
    part_folders: dict[str, str],
) -> Path:
    """`<folder>/index.md` of an assembly, with a BOM that links to the sibling part folders."""
    _fresh(folder)
    meta = spec.get("meta", {})
    lines = _head(spec, target)
    if "png" in artifacts:
        shutil.copyfile(artifacts["png"], folder / "render.png")
        lines += [f"![{target}](render.png)", ""]
    bom = bom_rows(spec, part_specs, part_summaries)
    masses = [row["total_mass_g"] for row in bom if row["total_mass_g"] != ""]
    facts = [["Parts", f"{sum(row['quantity'] for row in bom)} ({len(bom)} different)"]]
    if masses:
        facts.append(["Mass of the known parts", units.mass(sum(masses))])
    lines += [_table(["Property", "Value"], facts), ""]
    lines += _manufacture(meta)
    rows = [
        [
            f"[{row['part']}](../{part_folders[row['hash']]}/index.md)" if row["hash"] in part_folders else row["part"],
            row["quantity"],
            row["material"],
            row["process"],
            units.mass(row["mass_g"]) if row["mass_g"] != "" else "",
            units.mass(row["total_mass_g"]) if row["total_mass_g"] != "" else "",
        ]
        for row in bom
    ]
    lines += ["## Bill of materials", "", _table(["Part", "Qty", "Material", "Process", "Mass", "Total"], rows), ""]
    if "step" in artifacts:
        shutil.copyfile(artifacts["step"], folder / f"{spec['name']}.step")
        lines += ["## Files", "", f"[{spec['name']}.step]({spec['name']}.step)", ""]
    lines += [f"<small>CyCAx · hash `{spec_hash(spec)}`</small>", ""]
    index = folder / "index.md"
    index.write_text("\n".join(lines))
    return index
