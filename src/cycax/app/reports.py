# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Make reports (task cycax/27): get the artifacts (cache first, else build), then write the
report files. The engines and workers make the artifacts; the report code only writes files."""

import json
import logging
from collections.abc import Callable
from pathlib import Path

from cycax.app.builder import Builder, BuildItem
from cycax.app.errors import CycaxError
from cycax.report.html_report import write_html_report

PART_OUTPUTS = ["step", "glb", "summary", "svg"]
ASSEMBLY_OUTPUTS = ["step", "stl"]


def _try(builder: Builder, item: BuildItem, outputs: list[str]) -> dict[str, Path]:
    """Build (or take from the cache) some outputs; an output no engine can make is skipped."""
    saved = builder.outputs
    builder.outputs = outputs
    try:
        result = builder.build_item(item)
    finally:
        builder.outputs = saved
    if result.error:
        logging.info("Report: %s not made for %s: %s", ", ".join(outputs), item.target, result.error)
        return {}
    return result.files


def part_artifacts(builder: Builder, item: BuildItem, *, with_png: bool, say=None) -> dict[str, Path]:
    say = say or (lambda _message: None)
    say("models, summary and side views")
    artifacts = _try(builder, item, PART_OUTPUTS)
    if not artifacts:
        artifacts = _try(builder, item, ["step", "summary", "svg"])  # e.g. no GLB engine
    if not artifacts:
        msg = f"Cannot make the report of {item.target}: the build failed."
        raise CycaxError(msg, fix=f"cycax build {item.target}")
    if with_png:
        say("render and drawing")
        artifacts |= _try(builder, item, ["png"])
        artifacts |= _try(builder, item, ["drawing"])  # a TechDraw drawing, when FreeCAD can make it
    return artifacts


def assembly_parts(builder: Builder, item: BuildItem, spec: dict, *, say=None):
    """(part hash -> (part object, spec), part hash -> summary) of an assembly."""
    say = say or (lambda _message: None)
    flat = item.obj.combine_all_assemblies() if item.obj.assemblies else item.obj
    hashes = {p["name"]: p["hash"] for p in spec["parts"]}
    parts, summaries = {}, {}
    for part in flat.parts.values():
        part_spec = part.export()
        part_hash = hashes[part_spec["name"]]
        if part_hash in parts:
            continue
        parts[part_hash] = (part, part_spec)
        say(f"summary of {part_spec['name']}")
        files = _try(builder, BuildItem(f"{item.target}/{part_spec['name']}", part, item.engine), ["summary"])
        if "summary" in files:
            summaries[part_hash] = json.loads(files["summary"].read_text())
    return parts, summaries


def html_report(
    builder: Builder, item: BuildItem, folder: Path, *, with_png: bool = True, on_progress: Callable | None = None
) -> Path:
    spec = item.obj.export()
    if spec["kind"] == "part":
        artifacts = part_artifacts(builder, item, with_png=with_png, say=on_progress)
        return write_html_report(folder, spec, target=item.target, artifacts=artifacts)
    artifacts = _try(builder, item, ASSEMBLY_OUTPUTS)
    parts, summaries = assembly_parts(builder, item, spec, say=on_progress)
    return write_html_report(
        folder,
        spec,
        target=item.target,
        artifacts=artifacts,
        part_specs={h: part_spec for h, (_, part_spec) in parts.items()},
        part_summaries=summaries,
    )


def markdown_report(
    builder: Builder, item: BuildItem, parent: Path, *, with_png: bool = True, on_progress: Callable | None = None
) -> list[Path]:
    """`<parent>/<target>/index.md` (replaced each time); an assembly also writes one sibling
    folder per part, `<parent>/<part>/index.md`, and links to them."""
    from cycax.report.markdown_report import write_markdown_assembly, write_markdown_part  # noqa: PLC0415

    spec = item.obj.export()
    if spec["kind"] == "part":
        artifacts = part_artifacts(builder, item, with_png=with_png, say=on_progress)
        return [write_markdown_part(parent / item.target, spec, target=item.target, artifacts=artifacts)]
    artifacts = _try(builder, item, ASSEMBLY_OUTPUTS)
    parts, summaries = assembly_parts(builder, item, spec, say=on_progress)
    pages = []
    folders = {}
    for part_hash, (part, part_spec) in parts.items():
        part_item = BuildItem(part_spec["name"], part, item.engine)
        part_files = part_artifacts(builder, part_item, with_png=with_png, say=on_progress)
        pages.append(
            write_markdown_part(parent / part_spec["name"], part_spec, target=part_spec["name"], artifacts=part_files)
        )
        folders[part_hash] = part_spec["name"]
    pages.insert(
        0,
        write_markdown_assembly(
            parent / item.target,
            spec,
            target=item.target,
            artifacts=artifacts,
            part_specs={h: part_spec for h, (_, part_spec) in parts.items()},
            part_summaries=summaries,
            part_folders=folders,
        ),
    )
    return pages
