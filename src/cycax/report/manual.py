# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Manual pages from example files (task cycax/29, `cycax report <file> --format markdown-manual`).

One page per file: `<out>/<file stem>/index.md`. The module docstring is the title (first line)
and the introduction. Each target, in file order, is one section: its docstring, a code example
that can be copied (the imports and the module-level helpers it uses, the decorator and the
function or class), then one picture.

The picture: the side view from `@cycax_part(doc_view="top")`, else a render (PNG) when an
engine can make one, else the top view. Assemblies get a top view of the parts' outlines from
the assembly STEP. All side views of one page have the same scale.
"""

import ast
import inspect
import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path

from cycax.report.light import side_view_svg

MAX_PICTURE_PX = 640


@dataclass
class Section:
    name: str
    kind: str
    line: int
    description: str
    code: str
    picture: str = ""  # file name in the page folder
    caption: str = ""


def _used_names(node: ast.AST) -> set[str]:
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
        elif isinstance(child, ast.Attribute):
            root = child
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name):
                names.add(root.id)
    return names


def _defined_names(node: ast.stmt) -> set[str]:
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return {node.name}
    if isinstance(node, ast.Assign):
        return {t.id for t in node.targets if isinstance(t, ast.Name)}
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return {node.target.id}
    return set()


def example_code(source: str, name: str) -> str:
    """The code of one top-level function or class with the imports and the module-level
    definitions it needs (recursively), in file order. No `if __name__ == "__main__"` block."""
    tree = ast.parse(source)
    lines = source.splitlines()
    definitions = {n: stmt for stmt in tree.body for n in _defined_names(stmt)}
    if name not in definitions:
        msg = f"No top-level definition {name!r}."
        raise ValueError(msg)
    needed: set[str] = set()
    todo = [name]
    while todo:
        current = todo.pop()
        if current in needed:
            continue
        needed.add(current)
        stmt = definitions[current]
        todo += [n for n in _used_names(stmt) if n in definitions and n not in needed]
    used = set()
    for current in needed:
        used |= _used_names(definitions[current])

    def text(stmt: ast.stmt) -> str:
        start = min([stmt.lineno] + [d.lineno for d in getattr(stmt, "decorator_list", [])])
        return "\n".join(lines[start - 1 : stmt.end_lineno])

    imports = []
    for stmt in tree.body:
        if isinstance(stmt, ast.Import | ast.ImportFrom):
            keep = [a for a in stmt.names if (a.asname or a.name.split(".")[0]) in used]
            if not keep:
                continue
            names = ", ".join(f"{a.name} as {a.asname}" if a.asname else a.name for a in keep)
            if isinstance(stmt, ast.Import):
                imports.append(f"import {names}")
            else:
                imports.append(f"from {'.' * stmt.level}{stmt.module or ''} import {names}")
    blocks = [text(stmt) for stmt in tree.body if _defined_names(stmt) & needed]
    return "\n".join(imports) + "\n\n\n" + "\n\n\n".join(blocks) + "\n"


def _title(module, path: Path) -> tuple[str, str]:
    doc = inspect.getdoc(module) or ""
    if doc:
        first, _, rest = doc.partition("\n")
        return first.strip().rstrip("."), rest.strip()
    return path.stem.replace("_", " ").capitalize(), ""


def _assembly_top_svg(step_file: Path, px_per_mm: float | None) -> str:
    """A top view of the outlines of the parts of an assembly (from its STEP)."""
    from cycax.testing import assembly_instances  # noqa: PLC0415 - loads build123d

    instances = assembly_instances(step_file)
    xs = [v for i in instances for v in (i.bbox_min[0], i.bbox_max[0])]
    ys = [v for i in instances for v in (i.bbox_min[1], i.bbox_max[1])]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    margin = max(width, height) * 0.05
    stroke = max(width, height) / 500
    x0, y0 = min(xs) - margin, -max(ys) - margin
    box_w, box_h = width + 2 * margin, height + 2 * margin
    size = f'width="{box_w * px_per_mm:.1f}" height="{box_h * px_per_mm:.1f}"' if px_per_mm else ""
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.3f} {y0:.3f} {box_w:.3f} {box_h:.3f}" {size}>',
        f'<rect x="{x0:.3f}" y="{y0:.3f}" width="{box_w:.3f}" height="{box_h:.3f}" fill="#ffffff"/>',
    ]
    for instance in sorted(instances, key=lambda i: i.bbox_max[2]):
        (x1, y1, _), (x2, y2, _) = instance.bbox_min, instance.bbox_max
        out.append(
            f'<rect x="{x1:.3f}" y="{-y2:.3f}" width="{x2 - x1:.3f}" height="{y2 - y1:.3f}" '
            f'fill="#f4f4f4" fill-opacity="0.7" stroke="#222" stroke-width="{stroke:.3f}"/>'
        )
    out.append("</svg>")
    return "\n".join(out) + "\n"


def write_manual_page(source: Path, out_parent: Path, *, picture_for=None) -> Path:
    """Write `<out_parent>/<stem>/index.md` for one example file.

    `picture_for(target, obj)` returns a dict with "png" and/or "step" files (from the cache or
    a build), or {} — the caller decides how to get them (the CLI uses the Builder)."""
    from cycax.targets import collect_targets, import_source  # noqa: PLC0415

    source = Path(source).resolve()
    module = import_source(source)
    text = source.read_text()
    targets = sorted(collect_targets(module).values(), key=lambda t: inspect.getsourcelines(t.obj)[1])
    folder = out_parent / source.stem
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)

    made = []
    for target in targets:
        objects = target.make()
        obj = objects[0]
        spec = obj.export()
        made.append((target, obj, spec))
    # One scale for all side views in the file: the largest part fits MAX_PICTURE_PX.
    sizes = []
    for _, _, spec in made:
        if spec["kind"] == "part":
            base = spec["features"][0]
            sizes.append(max(base.get("x_size", 1), base.get("y_size", 1), base.get("z_size", 1)))
    px_per_mm = MAX_PICTURE_PX / (max(sizes) * 1.3) if sizes else None

    sections = []
    for target, obj, spec in made:
        section = Section(
            name=target.name,
            kind=target.kind,
            line=inspect.getsourcelines(target.obj)[1],
            description=target.description,
            code=example_code(text, target.obj.__name__),
        )
        files = picture_for(target, obj) if picture_for else {}
        if spec["kind"] == "part" and target.doc_view:
            view = target.doc_view.upper()
            section.picture = f"{target.name}_{target.doc_view.lower()}.svg"
            (folder / section.picture).write_text(side_view_svg(spec, view, px_per_mm=px_per_mm))
            section.caption = f"{target.doc_view.lower()} view"
        elif "png" in files:
            section.picture = f"{target.name}.png"
            shutil.copyfile(files["png"], folder / section.picture)
            section.caption = "render"
        elif spec["kind"] == "part":
            section.picture = f"{target.name}_top.svg"
            (folder / section.picture).write_text(side_view_svg(spec, "TOP", px_per_mm=px_per_mm))
            section.caption = "top view"
        elif "step" in files:
            section.picture = f"{target.name}_top.svg"
            (folder / section.picture).write_text(_assembly_top_svg(files["step"], None))
            section.caption = "top view of the parts"
        sections.append(section)

    title, intro = _title(module, source)
    lines = [f"# {title}", ""]
    if intro:
        lines += [intro, ""]
    for section in sections:
        lines += [f"## {section.name}", ""]
        if section.description:
            lines += [section.description, ""]
        lines += ["```python", textwrap.dedent(section.code).rstrip(), "```", ""]
        if section.picture:
            lines += [f"![{section.name}: {section.caption}]({section.picture})", ""]
    lines += [f"<small>Made by `cycax report {source.name} --format markdown-manual`.</small>", ""]
    index = folder / "index.md"
    index.write_text("\n".join(lines))
    return index
