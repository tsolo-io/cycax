# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The light report: SVG side views from the spec only (task cycax/26).

No CAD tool, no build: the views are computed from the feature data in plain Python, so the
report is ready in well under a second (for `cycax watch` and the server UI). The CLI runs it
locally; the python worker runs the same code for the cache.

Each of the six views shows the outline of the base shape and every feature that reaches that
side: cuts red and dashed, adds green, bend lines blue. Each feature has a label (C1, A1, B1,
...) that is the same in all views and in `features.csv`.

The views look at the part from outside (third-angle style): TOP looks down, FRONT looks from
-y, RIGHT from +x, and so on. Sizes are in mm; 1 SVG unit = 1 mm.
"""

import csv
import io
import math
from dataclasses import dataclass, field
from pathlib import Path

SIDES = ("TOP", "FRONT", "RIGHT", "BACK", "LEFT", "BOTTOM")
# Per view: (u axis, v axis) as signed world axes, the axis that points to the viewer, and
# which end of the part the viewer sees.
VIEWS = {
    "TOP": ((0, 1), (1, 1), 2, +1),
    "BOTTOM": ((0, -1), (1, 1), 2, -1),
    "FRONT": ((0, 1), (2, 1), 1, -1),
    "BACK": ((0, -1), (2, 1), 1, +1),
    "LEFT": ((1, -1), (2, 1), 0, -1),
    "RIGHT": ((1, 1), (2, 1), 0, +1),
}
# Into-the-part direction of a feature made from a side (subtract) as (axis, sign).
INTO = {"TOP": (2, -1), "BOTTOM": (2, 1), "FRONT": (1, 1), "BACK": (1, -1), "LEFT": (0, 1), "RIGHT": (0, -1)}
COLOURS = {"cut": "#d62728", "add": "#2ca02c", "bend": "#1f77b4", "base": "#222222", "other": "#7f7f7f"}
TOUCH = 1e-6


@dataclass
class Shape:
    """A feature as a simple solid: a box (lo/hi), a cylinder (centre, axis, radius, length,
    from the start point along +axis*sign) or a sphere."""

    kind: str  # box | cylinder | sphere | line
    lo: tuple = (0.0, 0.0, 0.0)
    hi: tuple = (0.0, 0.0, 0.0)
    start: tuple = (0.0, 0.0, 0.0)
    axis: int = 2
    sign: int = 1
    radius: float = 0.0
    length: float = 0.0
    sides: int = 0  # 6 = hexagon (nut), 0 = circle
    end: tuple = (0.0, 0.0, 0.0)  # line end

    def bounds(self) -> tuple[tuple, tuple]:
        if self.kind == "box":
            return self.lo, self.hi
        if self.kind == "line":
            return tuple(map(min, self.start, self.end)), tuple(map(max, self.start, self.end))
        if self.kind == "sphere":
            return tuple(c - self.radius for c in self.start), tuple(c + self.radius for c in self.start)
        lo, hi = list(self.start), list(self.start)
        for axis in range(3):
            if axis == self.axis:
                other = self.start[axis] + self.sign * self.length
                lo[axis], hi[axis] = min(self.start[axis], other), max(self.start[axis], other)
            else:
                lo[axis], hi[axis] = self.start[axis] - self.radius, self.start[axis] + self.radius
        return tuple(lo), tuple(hi)


@dataclass
class Item:
    label: str
    role: str  # cut | add | bend | base | other
    feature: dict
    shape: Shape | None
    views: list[str] = field(default_factory=list)


def _box(feature: dict) -> Shape:
    x, y, z = feature["x"], feature["y"], feature["z"]
    xs, ys, zs = feature["x_size"], feature["y_size"], feature["z_size"]
    if feature.get("center"):
        return Shape("box", lo=(x - xs / 2, y - ys / 2, z - zs / 2), hi=(x + xs / 2, y + ys / 2, z + zs / 2))
    # Same placement as the engines: the box grows away from the side it is made from.
    shift = {"TOP": (0, 0, -zs), "BACK": (0, -ys, 0), "RIGHT": (-xs, 0, 0)}.get(feature.get("side"), (0, 0, 0))
    lo = (x + shift[0], y + shift[1], z + shift[2])
    return Shape("box", lo=lo, hi=(lo[0] + xs, lo[1] + ys, lo[2] + zs))


def feature_shape(feature: dict) -> Shape | None:
    """The simple solid of a feature, or None for a feature type that is not drawn."""
    kind = feature.get("type")
    action = feature.get("action")
    if kind == "import":  # an imported model: its bounding box (cycax/35)
        return Shape("box", lo=(0.0, 0.0, 0.0), hi=(feature["x_size"], feature["y_size"], feature["z_size"]))
    if kind == "cuboid":
        return _box(feature)
    if kind == "cylinder" and "diameter" in feature:
        axis, sign = INTO[feature["side"]]
        if action != "subtract":
            sign = -sign
        return Shape(
            "cylinder",
            start=(feature["x"], feature["y"], feature["z"]),
            axis=axis,
            sign=sign,
            radius=feature["diameter"] / 2,
            length=feature["depth"],
        )
    if kind == "cylinder":  # base shape: x_size = diameter, z_size = height
        radius = feature["x_size"] / 2
        start = (feature.get("x", 0.0) + radius, feature.get("y", 0.0) + radius, feature.get("z", 0.0))
        return Shape("cylinder", start=start, axis=2, sign=1, radius=radius, length=feature["z_size"])
    if kind == "cone":  # a countersink: drawn as its surface circle
        axis, sign = INTO[feature["side"]]
        return Shape(
            "cylinder",
            start=(feature["x"], feature["y"], feature["z"]),
            axis=axis,
            sign=sign,
            radius=feature["diameter"] / 2,
            length=feature["depth"],
        )
    if kind == "sphere":
        return Shape("sphere", start=(feature["x"], feature["y"], feature["z"]), radius=feature["diameter"] / 2)
    if kind == "nut_cutout":
        axis, sign = INTO[feature["side"]]
        return Shape(
            "cylinder",
            start=(feature["x"], feature["y"], feature["z"]),
            axis=axis,
            sign=sign,
            radius=feature["diameter"] / 2,
            length=feature["depth"],
            sides=6,
        )
    if kind == "bend" and "u_dir" in feature:
        start = (feature["x"], feature["y"], feature["z"])
        end = tuple(s + d * feature.get("width", 0.0) for s, d in zip(start, feature["u_dir"], strict=True))
        return Shape("line", start=start, end=end)
    return None


def items_of(spec: dict) -> list[Item]:
    """The base shape and the labelled features (C = cut, A = add, B = bend, F = other)."""
    counters = {"cut": 0, "add": 0, "bend": 0, "other": 0}
    prefix = {"cut": "C", "add": "A", "bend": "B", "other": "F"}
    features = spec["features"]
    items = [Item("base", "base", features[0], feature_shape(features[0]))]
    for feature in features[1:]:
        action = feature.get("action")
        role = {"subtract": "cut", "add": "add", "bend": "bend"}.get(action, "other")
        if feature.get("type") == "bend":
            role = "bend"
        counters[role] += 1
        items.append(Item(f"{prefix[role]}{counters[role]}", role, feature, feature_shape(feature)))
    return items


def _project(point, view: str) -> tuple[float, float]:
    (ua, us), (va, vs), _, _ = VIEWS[view]
    return point[ua] * us, point[va] * vs


def _overlap_2d(a: Shape, b: Shape, view: str) -> bool:
    (alo, ahi), (blo, bhi) = a.bounds(), b.bounds()
    axes = [VIEWS[view][0][0], VIEWS[view][1][0]]
    return all(alo[i] <= bhi[i] + TOUCH and blo[i] <= ahi[i] + TOUCH for i in axes)


def _visible(item: Item, view: str, solids: list[Item]) -> bool:
    """Adds and bends are always drawn (they are outside the base). A cut is drawn when it
    reaches the face of the base, or of an add it overlaps, on the side that the view shows."""
    if item.role != "cut":
        return True
    _, _, axis, end = VIEWS[view]
    lo, hi = item.shape.bounds()
    for solid in solids:
        if solid.role != "base" and not _overlap_2d(item.shape, solid.shape, view):
            continue
        slo, shi = solid.shape.bounds()
        if end > 0 and hi[axis] >= shi[axis] - TOUCH:
            return True
        if end < 0 and lo[axis] <= slo[axis] + TOUCH:
            return True
    return False


def _svg_shape(shape: Shape, view: str, style: str) -> str:
    _, _, axis, _ = VIEWS[view]
    if shape.kind in ("cylinder", "sphere") and (shape.kind == "sphere" or shape.axis == axis):
        cu, cv = _project(shape.start, view)
        if shape.sides:
            corners = [(math.cos(math.pi / 3 * k), math.sin(math.pi / 3 * k)) for k in range(6)]
            points = " ".join(f"{cu + shape.radius * c:.3f},{-(cv + shape.radius * s):.3f}" for c, s in corners)
            return f'<polygon points="{points}" {style}/>'
        return f'<circle cx="{cu:.3f}" cy="{-cv:.3f}" r="{shape.radius:.3f}" {style}/>'
    if shape.kind == "line":
        (u1, v1), (u2, v2) = _project(shape.start, view), _project(shape.end, view)
        return f'<line x1="{u1:.3f}" y1="{-v1:.3f}" x2="{u2:.3f}" y2="{-v2:.3f}" {style}/>'
    lo, hi = shape.bounds()
    corners = [_project((x, y, z), view) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    us = [c[0] for c in corners]
    vs = [c[1] for c in corners]
    return (
        f'<rect x="{min(us):.3f}" y="{-max(vs):.3f}" width="{max(us) - min(us):.3f}" '
        f'height="{max(vs) - min(vs):.3f}" {style}/>'
    )


def _is_point(shape: Shape, view: str) -> bool:
    """A line seen end-on (a bend line along the view direction)."""
    if shape.kind != "line":
        return False
    (u1, v1), (u2, v2) = _project(shape.start, view), _project(shape.end, view)
    return abs(u1 - u2) < TOUCH and abs(v1 - v2) < TOUCH


def _centre(shape: Shape, view: str) -> tuple[float, float]:
    lo, hi = shape.bounds()
    return _project(tuple((a + b) / 2 for a, b in zip(lo, hi, strict=True)), view)


def side_view_svg(spec: dict, view: str, items: list[Item] | None = None, *, px_per_mm: float | None = None) -> str:
    """One side view as an SVG document. `px_per_mm` sets the display size (the same value for
    several pictures gives the same scale); default: real size in mm."""
    items = items if items is not None else items_of(spec)
    base = items[0]
    solids = [base] + [item for item in items[1:] if item.role == "add" and item.shape is not None]
    drawn = [base] + [
        item
        for item in items[1:]
        if item.shape is not None and _visible(item, view, solids) and not _is_point(item.shape, view)
    ]
    # The drawing area: everything drawn, plus a margin.
    us, vs = [], []
    for item in drawn:
        lo, hi = item.shape.bounds()
        for corner in ((lo[0], lo[1], lo[2]), (hi[0], hi[1], hi[2])):
            u, v = _project(corner, view)
            us.append(u)
            vs.append(v)
    width, height = max(us) - min(us), max(vs) - min(vs)
    # Text and line sizes from the whole part (not this view), so all views of a part match.
    part_lo, part_hi = zip(*(item.shape.bounds() for item in items if item.shape is not None), strict=True)
    size = max(max(hi) - min(lo) for lo, hi in zip(zip(*part_lo, strict=True), zip(*part_hi, strict=True), strict=True))
    size = max(size, width, height, 1.0)
    margin = size * 0.12
    stroke = size / 400
    font = max(size / 40, 1.5)
    x0, y0 = min(us) - margin, -max(vs) - margin - font * 2
    box_w, box_h = width + 2 * margin, height + 2 * margin + font * 2
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.3f} {y0:.3f} {box_w:.3f} {box_h:.3f}" '
        + (
            f'width="{box_w * px_per_mm:.1f}" height="{box_h * px_per_mm:.1f}">'
            if px_per_mm
            else f'width="{box_w:.3f}mm" height="{box_h:.3f}mm">'
        ),
        f'<rect x="{x0:.3f}" y="{y0:.3f}" width="{box_w:.3f}" height="{box_h:.3f}" fill="#ffffff"/>',
        f'<text x="{x0 + margin / 2:.3f}" y="{y0 + font * 1.5:.3f}" font-family="sans-serif" '
        f'font-size="{font:.3f}" fill="#222">{spec["name"]} - {view.lower()} ({width:.1f} x {height:.1f} mm)</text>',
    ]
    for item in drawn:
        colour = COLOURS[item.role]
        if item.role == "base":
            style = f'fill="#f4f4f4" stroke="{colour}" stroke-width="{stroke * 2:.3f}"'
        elif item.role == "cut":
            style = (
                f'fill="none" stroke="{colour}" stroke-width="{stroke * 1.5:.3f}" '
                f'stroke-dasharray="{stroke * 6:.3f} {stroke * 4:.3f}"'
            )
        elif item.role == "bend":
            style = f'fill="none" stroke="{colour}" stroke-width="{stroke * 2:.3f}"'
        else:
            style = f'fill="none" stroke="{colour}" stroke-width="{stroke * 1.5:.3f}"'
        lines.append(f'<g data-label="{item.label}">' + _svg_shape(item.shape, view, style))
        if item.role != "base" and not _is_point(item.shape, view):
            cu, cv = _centre(item.shape, view)
            lines.append(
                f'<text x="{cu:.3f}" y="{-cv - font * 0.3:.3f}" font-family="sans-serif" font-size="{font * 0.8:.3f}" '
                f'text-anchor="middle" fill="{colour}">{item.label}</text>'
            )
        lines.append("</g>")
        if view not in item.views:
            item.views.append(view)
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def features_csv(items: list[Item]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["label", "role", "type", "name", "side", "x", "y", "z", "size", "views"])
    for item in items:
        feature = item.feature
        if "diameter" in feature:
            size = f"d{feature['diameter']:g}" + (f" x {feature['depth']:g}" if "depth" in feature else "")
        elif "x_size" in feature:
            size = f"{feature['x_size']:g} x {feature['y_size']:g} x {feature['z_size']:g}"
        elif feature.get("type") == "bend":
            size = f"{feature.get('angle', 0):g} deg, r{feature.get('radius', 0):g}, {feature.get('width', 0):g} long"
        else:
            size = ""
        views = " ".join(v.lower() for v in item.views) if item.shape is not None else "not drawn"
        writer.writerow(
            [
                item.label,
                item.role,
                feature.get("type"),
                feature.get("name"),
                feature.get("side", ""),
                feature.get("x", ""),
                feature.get("y", ""),
                feature.get("z", ""),
                size,
                views,
            ]
        )
    return out.getvalue()


def write_light_report(spec: dict, folder: Path) -> dict[str, Path]:
    """Write `<side>.svg` for the six sides and `features.csv` into `folder`."""
    if spec.get("kind") != "part":
        msg = "The light report is for parts; for an assembly, make it for each part."
        raise ValueError(msg)
    folder.mkdir(parents=True, exist_ok=True)
    items = items_of(spec)
    files = {}
    for view in SIDES:
        path = folder / f"{view.lower()}.svg"
        path.write_text(side_view_svg(spec, view, items))
        files[view.lower()] = path
    csv_path = folder / "features.csv"
    csv_path.write_text(features_csv(items))
    files["features"] = csv_path
    return files


def sheet_svg(spec: dict) -> str:
    """The six views on one sheet (3 x 2): TOP, FRONT, RIGHT / BACK, LEFT, BOTTOM.

    One file for the cache and the server UI (`<name>-<engine>-standard.svg`)."""
    items = items_of(spec)
    cells = []
    for view in SIDES:
        svg = side_view_svg(spec, view, items)
        root_open, _, body = svg.partition(">")
        view_box = root_open.split('viewBox="', 1)[1].split('"', 1)[0]
        cells.append((view_box, body.rsplit("</svg>", 1)[0]))
    cell_w, cell_h = 400, 300
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cell_w * 3} {cell_h * 2}" '
        f'width="{cell_w * 3}" height="{cell_h * 2}">',
        f'<rect width="{cell_w * 3}" height="{cell_h * 2}" fill="#ffffff"/>',
    ]
    boxes = [tuple(float(v) for v in view_box.split()) for view_box, _ in cells]
    # One scale for all views: the same mm look the same size in every view.
    scale = min(min(cell_w / vw, cell_h / vh) for _, _, vw, vh in boxes)
    for index, ((vx, vy, vw, vh), (_, body)) in enumerate(zip(boxes, cells, strict=True)):
        # A plain transform (not a nested <svg>): every SVG renderer handles it.
        x = (index % 3) * cell_w + (cell_w - vw * scale) / 2
        y = (index // 3) * cell_h + (cell_h - vh * scale) / 2
        out.append(f'<g transform="translate({x:.3f} {y:.3f}) scale({scale:.6f}) translate({-vx:.3f} {-vy:.3f})">')
        out.append(body)
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"
