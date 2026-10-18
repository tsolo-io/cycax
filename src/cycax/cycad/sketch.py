# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""2D sketches: pad, pocket, revolve, and DXF import (task cycax/34).

A `Sketch` is a set of closed profiles in 2D (mm): rectangles, circles, polygons, slots and
polylines with arcs. A profile inside another profile is a hole in it (even-odd rule), so a
plate outline with a hole pattern is one sketch.

    from cycax.cycad import Sketch, SketchPart

    outline = Sketch().rectangle(0, 0, 80, 40, radius=5)
    for x in (10, 70):
        outline.circle(x, 20, diameter=4.2)
    plate = SketchPart(part_no="plate", sketch=outline, thickness=3)   # pad
    plate.top.pocket(Sketch().rectangle(30, 10, 20, 20), depth=1)       # a pocket in the top

    bracket = SketchPart(part_no="bracket", sketch=Sketch.from_dxf("bracket.dxf"), thickness=2)

In the spec a sketch operation is ONE feature (`type: "sketch"`) that holds all the profiles,
the plane, the operation and the depth. A DXF is converted to profiles when the part is made, so
the workers need no file; the file name and its SHA-256 are in the feature, so a changed file
gives a new hash.
"""

import hashlib
import math
from pathlib import Path

from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.features import Feature
from cycax.cycad.location import BOTTOM

# DXF $INSUNITS -> mm (0 = no units in the file: `scale=` is necessary).
DXF_UNITS_MM = {1: 25.4, 2: 304.8, 4: 1.0, 5: 10.0, 6: 1000.0, 8: 0.0000254, 9: 0.0254, 10: 914.4}
CLOSE = 1e-6


def _r(value: float) -> float:
    return round(float(value), 9) + 0.0


class Sketch:
    """Closed 2D profiles. Each method returns the sketch, so calls can be chained."""

    def __init__(self):
        self.profiles: list[dict] = []
        self.source: dict | None = None

    # -- profiles ---------------------------------------------------------------------------
    def polyline(self, points: list[tuple[float, float]]) -> "Sketch":
        """A closed polygon through `points` (the last point connects to the first)."""
        if len(points) < 3:  # noqa: PLR2004
            msg = "A closed polyline needs at least 3 points."
            raise ValueError(msg)
        segments = []
        for (x1, y1), (x2, y2) in zip(points, [*points[1:], points[0]], strict=True):
            segments.append({"line": [_r(x1), _r(y1), _r(x2), _r(y2)]})
        self.profiles.append({"segments": segments})
        return self

    def rectangle(self, x: float, y: float, width: float, height: float, *, radius: float = 0.0) -> "Sketch":
        """A rectangle with its lower-left corner at (x, y); `radius` rounds the corners."""
        if radius <= 0:
            return self.polyline([(x, y), (x + width, y), (x + width, y + height), (x, y + height)])
        r = min(radius, width / 2, height / 2)
        x2, y2 = x + width, y + height
        segments = [
            {"line": [_r(x + r), _r(y), _r(x2 - r), _r(y)]},
            {"arc": {"center": [_r(x2 - r), _r(y + r)], "radius": _r(r), "start": 270.0, "end": 360.0}},
            {"line": [_r(x2), _r(y + r), _r(x2), _r(y2 - r)]},
            {"arc": {"center": [_r(x2 - r), _r(y2 - r)], "radius": _r(r), "start": 0.0, "end": 90.0}},
            {"line": [_r(x2 - r), _r(y2), _r(x + r), _r(y2)]},
            {"arc": {"center": [_r(x + r), _r(y2 - r)], "radius": _r(r), "start": 90.0, "end": 180.0}},
            {"line": [_r(x), _r(y2 - r), _r(x), _r(y + r)]},
            {"arc": {"center": [_r(x + r), _r(y + r)], "radius": _r(r), "start": 180.0, "end": 270.0}},
        ]
        self.profiles.append({"segments": segments})
        return self

    def circle(self, x: float, y: float, *, diameter: float) -> "Sketch":
        self.profiles.append({"circle": {"center": [_r(x), _r(y)], "radius": _r(diameter / 2)}})
        return self

    def polygon(self, x: float, y: float, *, sides: int, diameter: float, angle: float = 0.0) -> "Sketch":
        """A regular polygon around (x, y); `diameter` is the circle through its corners."""
        points = [
            (
                x + diameter / 2 * math.cos(math.radians(angle + 360 * k / sides)),
                y + diameter / 2 * math.sin(math.radians(angle + 360 * k / sides)),
            )
            for k in range(sides)
        ]
        return self.polyline(points)

    def slot(self, x: float, y: float, *, length: float, width: float, angle: float = 0.0) -> "Sketch":
        """A slot from the centre of one round end (x, y), `length` to the other end's centre."""
        a = math.radians(angle)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy * width / 2, dx * width / 2
        x2, y2 = x + dx * length, y + dy * length
        r = width / 2
        # Arcs are stored counter-clockwise from start to end; the direction in the loop does
        # not matter. The far cap is at (x2, y2), the near cap at (x, y).
        segments = [
            {"line": [_r(x + nx), _r(y + ny), _r(x2 + nx), _r(y2 + ny)]},
            {"arc": {"center": [_r(x2), _r(y2)], "radius": _r(r), "start": _r(angle - 90), "end": _r(angle + 90)}},
            {"line": [_r(x2 - nx), _r(y2 - ny), _r(x - nx), _r(y - ny)]},
            {"arc": {"center": [_r(x), _r(y)], "radius": _r(r), "start": _r(angle + 90), "end": _r(angle + 270)}},
        ]
        self.profiles.append({"segments": segments})
        return self

    # -- import -----------------------------------------------------------------------------
    @classmethod
    def from_dxf(cls, file: str | Path, *, scale: float | None = None, layer: str | None = None) -> "Sketch":
        """Closed outlines of a DXF file (LWPOLYLINE/POLYLINE with bulges, CIRCLE, and LINE/ARC
        chains). The units come from the file ($INSUNITS); without units, give `scale=` (mm per
        drawing unit), else it is an error."""
        import ezdxf  # noqa: PLC0415 - only for DXF import

        path = Path(file)
        doc = ezdxf.readfile(path)
        units = doc.header.get("$INSUNITS", 0)
        if scale is None:
            if units not in DXF_UNITS_MM:
                msg = (
                    f"{path.name} has no units ($INSUNITS = {units}). Give the scale: "
                    "Sketch.from_dxf(file, scale=1.0) for mm, 25.4 for inches."
                )
                raise ValueError(msg)
            scale = DXF_UNITS_MM[units]
        sketch = cls()
        loose = []
        for entity in doc.modelspace():
            if layer is not None and entity.dxf.layer != layer:
                continue
            kind = entity.dxftype()
            if kind == "CIRCLE":
                c = entity.dxf.center
                sketch.circle(c.x * scale, c.y * scale, diameter=2 * entity.dxf.radius * scale)
            elif kind in ("LWPOLYLINE", "POLYLINE"):
                segments = _polyline_segments(entity, scale)
                if segments:
                    sketch.profiles.append({"segments": segments})
            elif kind == "LINE":
                s, e = entity.dxf.start, entity.dxf.end
                loose.append({"line": [_r(s.x * scale), _r(s.y * scale), _r(e.x * scale), _r(e.y * scale)]})
            elif kind == "ARC":
                c = entity.dxf.center
                loose.append(
                    {
                        "arc": {
                            "center": [_r(c.x * scale), _r(c.y * scale)],
                            "radius": _r(entity.dxf.radius * scale),
                            "start": _r(entity.dxf.start_angle),
                            "end": _r(entity.dxf.end_angle),
                        }
                    }
                )
        for chain in _chains(loose):
            sketch.profiles.append({"segments": chain})
        if not sketch.profiles:
            msg = f"No closed outlines in {path.name}."
            raise ValueError(msg)
        sketch.source = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "scale": scale}
        return sketch

    # -- export -----------------------------------------------------------------------------
    def bounds(self) -> tuple[tuple[float, float], tuple[float, float]]:
        xs, ys = [], []
        for profile in self.profiles:
            if "circle" in profile:
                (cx, cy), r = profile["circle"]["center"], profile["circle"]["radius"]
                xs += [cx - r, cx + r]
                ys += [cy - r, cy + r]
            for seg in profile.get("segments", []):
                if "line" in seg:
                    x1, y1, x2, y2 = seg["line"]
                    xs += [x1, x2]
                    ys += [y1, y2]
                else:
                    arc = seg["arc"]
                    (cx, cy), r = arc["center"], arc["radius"]
                    for a in _arc_angles(arc):
                        xs.append(cx + r * math.cos(math.radians(a)))
                        ys.append(cy + r * math.sin(math.radians(a)))
        return (min(xs), min(ys)), (max(xs), max(ys))

    def export(self) -> list[dict]:
        return [dict(p) for p in self.profiles]


def _arc_angles(arc: dict) -> list[float]:
    """The end angles of an arc plus the 0/90/180/270 angles it passes (for bounds)."""
    start, end = arc["start"], arc["end"]
    while end <= start:
        end += 360
    angles = [start, end]
    k = math.ceil(start / 90) * 90
    while k < end:
        angles.append(k)
        k += 90
    return angles


def _polyline_segments(entity, scale: float) -> list[dict]:
    if entity.dxftype() == "LWPOLYLINE":
        points = [(p[0], p[1], p[4]) for p in entity.get_points("xyseb")]
        closed = entity.closed
    else:
        points = [(v.dxf.location.x, v.dxf.location.y, v.dxf.bulge) for v in entity.vertices]
        closed = entity.is_closed
    if not closed and len(points) > 2 and math.dist(points[0][:2], points[-1][:2]) < CLOSE:  # noqa: PLR2004
        points = points[:-1]
        closed = True
    if not closed:
        return []
    segments = []
    for (x1, y1, bulge), (x2, y2, _) in zip(points, [*points[1:], points[0]], strict=True):
        if abs(bulge) < CLOSE:
            segments.append({"line": [_r(x1 * scale), _r(y1 * scale), _r(x2 * scale), _r(y2 * scale)]})
            continue
        # A bulge is tan(angle / 4) of the arc from (x1, y1) to (x2, y2), positive = counter-clockwise.
        angle = 4 * math.atan(bulge)
        chord = math.dist((x1, y1), (x2, y2))
        radius = chord / (2 * math.sin(abs(angle) / 2))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        distance = math.sqrt(max(radius**2 - (chord / 2) ** 2, 0.0))
        nx, ny = -(y2 - y1) / chord, (x2 - x1) / chord
        sign = 1 if (bulge > 0) == (abs(angle) < math.pi) else -1
        cx, cy = mx + sign * nx * distance, my + sign * ny * distance
        a1 = math.degrees(math.atan2(y1 - cy, x1 - cx))
        a2 = math.degrees(math.atan2(y2 - cy, x2 - cx))
        start, end = (a1, a2) if bulge > 0 else (a2, a1)
        segments.append(
            {
                "arc": {
                    "center": [_r(cx * scale), _r(cy * scale)],
                    "radius": _r(radius * scale),
                    "start": _r(start),
                    "end": _r(end),
                }
            }
        )
    return segments


def _ends(seg: dict) -> tuple[tuple[float, float], tuple[float, float]]:
    if "line" in seg:
        x1, y1, x2, y2 = seg["line"]
        return (x1, y1), (x2, y2)
    arc = seg["arc"]
    (cx, cy), r = arc["center"], arc["radius"]
    start = (cx + r * math.cos(math.radians(arc["start"])), cy + r * math.sin(math.radians(arc["start"])))
    end = (cx + r * math.cos(math.radians(arc["end"])), cy + r * math.sin(math.radians(arc["end"])))
    return start, end


def _chains(segments: list[dict], tolerance: float = 1e-3) -> list[list[dict]]:
    """Closed loops from loose LINE/ARC entities (the direction of a segment does not matter)."""
    left = list(segments)
    loops = []
    while left:
        chain = [left.pop(0)]
        start, end = _ends(chain[0])
        while math.dist(start, end) > tolerance:
            for index, seg in enumerate(left):
                a, b = _ends(seg)
                if math.dist(a, end) <= tolerance or math.dist(b, end) <= tolerance:
                    chain.append(left.pop(index))
                    end = b if math.dist(a, end) <= tolerance else a
                    break
            else:
                break  # an open chain: not a profile
        if math.dist(start, end) <= tolerance:
            loops.append(chain)
    return loops


class SketchFeature(Feature):
    """One sketch operation: the profiles, the plane, the operation and the depth."""

    def __init__(
        self,
        *,
        sketch: Sketch,
        action: str,
        operation: str,
        origin: tuple[float, float, float],
        x_dir: tuple[float, float, float],
        y_dir: tuple[float, float, float],
        normal: tuple[float, float, float],
        depth: float = 0.0,
        revolve: dict | None = None,
        side: str | None = None,
    ):
        super().__init__(side=side, x=origin[0], y=origin[1], z=origin[2])
        self.name = "sketch"
        self.type = "sketch"
        self.action = action
        self.operation = operation
        self.plane = {
            "origin": [_r(v) for v in origin],
            "x_dir": [_r(v) for v in x_dir],
            "y_dir": [_r(v) for v in y_dir],
            "normal": [_r(v) for v in normal],
        }
        self.depth = float(depth)
        self.revolve = revolve
        self.sketch = sketch

    def export(self) -> dict:
        data = {
            "name": "sketch",
            "type": "sketch",
            "action": self.action,
            "operation": self.operation,
            "side": self.side,
            "plane": self.plane,
            "profiles": self.sketch.export(),
        }
        if self.operation == "pad":
            data["depth"] = self.depth
        if self.revolve:
            data["revolve"] = self.revolve
        if self.sketch.source:
            data["source"] = dict(self.sketch.source)
        return data

    def move(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        origin = self.plane["origin"]
        self.plane["origin"] = [_r(origin[0] + (x or 0)), _r(origin[1] + (y or 0)), _r(origin[2] + (z or 0))]


class SketchPart(CycadPart):
    """A part made from a sketch on the XY plane: padded `thickness` up (+z), or revolved.

    Args:
        part_no: The part number.
        sketch: The outline (and its holes).
        thickness: Pad height (mm). Not used with `revolve`.
        revolve: `{"axis": [[x1, y1], [x2, y2]], "angle": 360}`: revolve the sketch about the
            axis through the two sketch points instead of padding it.
    """

    def __init__(
        self,
        part_no: str,
        sketch: Sketch,
        thickness: float = 0.0,
        *,
        revolve: dict | None = None,
        assembly=None,
        colour: str | None = None,
        material=None,
        manufacture=None,
    ):
        (x1, y1), (x2, y2) = sketch.bounds()
        if revolve is None and thickness <= 0:
            msg = "A sketch part needs a thickness (pad) or revolve=."
            raise ValueError(msg)
        self.sketch = sketch
        self.revolve_spec = revolve
        self.thickness = thickness
        if revolve:
            # Bounds of a full revolution about the axis: the sketch swept around it.
            (ax1, ay1), (ax2, ay2) = revolve["axis"]
            reach = max(
                abs((px - ax1) * (ay2 - ay1) - (py - ay1) * (ax2 - ax1)) / math.dist((ax1, ay1), (ax2, ay2))
                for px, py in ((x1, y1), (x1, y2), (x2, y1), (x2, y2))
            )
            size = (x2 - x1, y2 - y1, 2 * reach)
        else:
            size = (x2 - x1, y2 - y1, thickness)
        self._sketch_offset = (x1, y1)
        super().__init__(
            x=0.0,
            y=0.0,
            z=0.0,
            side=BOTTOM,
            part_no=part_no,
            x_size=size[0],
            y_size=size[1],
            z_size=size[2],
            polygon="sketch",
            assembly=assembly,
            colour=colour,
            material=material,
            manufacture=manufacture,
            default_colour="orange",
        )
        if revolve:
            self.z_min, self.z_max = -size[2] / 2, size[2] / 2
        self.x_min, self.y_min = x1, y1
        self.x_max, self.y_max = x2, y2
        self.make_bounding_box()

    def base_feature(self) -> dict:
        feature = SketchFeature(
            sketch=self.sketch,
            action="add",
            operation="revolve" if self.revolve_spec else "pad",
            origin=(0.0, 0.0, 0.0),
            x_dir=(1.0, 0.0, 0.0),
            y_dir=(0.0, 1.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            depth=self.thickness,
            revolve=self.revolve_spec,
            side=BOTTOM,
        )
        return feature.export()


def side_frame(cycad_side) -> tuple[tuple, tuple, tuple, tuple]:
    """(origin, x_dir, y_dir, into_part) of a part side, in the same `pos` coordinates as
    `side.hole(pos=...)`: the sketch point (u, v) is at origin + u * x_dir + v * y_dir."""
    o = cycad_side._location_calc(pos=(0.0, 0.0))  # noqa: SLF001 - same package
    px = cycad_side._location_calc(pos=(1.0, 0.0))  # noqa: SLF001
    py = cycad_side._location_calc(pos=(0.0, 1.0))  # noqa: SLF001
    x_dir = tuple(b - a for a, b in zip(o, px, strict=True))
    y_dir = tuple(b - a for a, b in zip(o, py, strict=True))
    into = {
        "TOP": (0, 0, -1),
        "BOTTOM": (0, 0, 1),
        "FRONT": (0, 1, 0),
        "BACK": (0, -1, 0),
        "LEFT": (1, 0, 0),
        "RIGHT": (-1, 0, 0),
    }[cycad_side.name]
    return o, x_dir, y_dir, into
