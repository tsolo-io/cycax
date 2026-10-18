# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Mates: join parts exactly through anchors, solved in the order written (task cycax/38).

No global constraint solver (decided 2026-10-17). Each mate moves ONE part (the first argument)
to an already-placed part (the second). A part that was used as a reference, or that a mate has
placed, is fixed: moving it with a later mate is an error.

    assembly.mate(lid.bottom, box.top)                       # faces touch, normals opposite
    assembly.align(bolt.ref("axis"), plate.ref("m4"))        # coaxial (contact=True: points meet)
    assembly.place(psu.ref("mount"), on=rack.ref("slot"))    # frame to frame (6 DOF)

The resolved placement is in each part's transform; the mates themselves are in the assembly
spec (`mates`), for FreeCAD joints. Every mate is checked again at export.
"""

import math
from dataclasses import dataclass

from cycax.cycad import placement

TOLERANCE = 1e-6


@dataclass(frozen=True)
class AnchorRef:
    """A part and the name of one of its anchors."""

    part: object
    name: str

    def world(self):
        return self.part.anchor(self.name)


def as_ref(value) -> AnchorRef:
    """An AnchorRef from an AnchorRef, a part side (`part.top`) or a (part, name) pair."""
    if isinstance(value, AnchorRef):
        return value
    if isinstance(value, tuple) and len(value) == 2:  # noqa: PLR2004
        return AnchorRef(*value)
    parent = getattr(value, "_parent", None)
    name = getattr(value, "name", None)
    if parent is not None and isinstance(name, str):
        return AnchorRef(parent, name.lower())
    msg = f"Not an anchor: {value!r}. Use part.top (a face) or part.ref('name')."
    raise TypeError(msg)


# -- vector helpers ------------------------------------------------------------------------------
def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b, strict=True))


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b, strict=True))


def _mul(a, k):
    return tuple(x * k for x in a)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    length = math.sqrt(_dot(a, a))
    return _mul(a, 1 / length) if length else a


def rotation_between(a, b) -> placement.Matrix:
    """The rotation that turns direction a onto direction b (the smallest one)."""
    a, b = _norm(a), _norm(b)
    cos = max(-1.0, min(1.0, _dot(a, b)))
    axis = _cross(a, b)
    if math.sqrt(_dot(axis, axis)) < TOLERANCE:
        if cos > 0:
            return placement.identity()
        # 180 degrees: about any axis perpendicular to a
        helper = (1.0, 0.0, 0.0) if abs(a[0]) < 0.9 else (0.0, 1.0, 0.0)  # noqa: PLR2004
        axis = _cross(a, helper)
    return axis_angle(_norm(axis), math.degrees(math.acos(cos)))


def axis_angle(axis, degrees: float) -> placement.Matrix:
    """Rotation about a unit axis through the origin (Rodrigues)."""
    x, y, z = axis
    a = math.radians(degrees)
    c, s, t = math.cos(a), math.sin(a), 1 - math.cos(a)
    m = placement.identity()
    m[0][:3] = [t * x * x + c, t * x * y - s * z, t * x * z + s * y]
    m[1][:3] = [t * x * y + s * z, t * y * y + c, t * y * z - s * x]
    m[2][:3] = [t * x * z - s * y, t * y * z + s * x, t * z * z + c]
    return m


def _rotate_about(point, rotation: placement.Matrix) -> placement.Matrix:
    return placement.about(point, rotation)


# -- the mates ------------------------------------------------------------------------------------
@dataclass
class Mate:
    kind: str  # mate | align | place
    moving: AnchorRef
    target: AnchorRef
    offset: float = 0.0
    contact: bool = False
    flip: bool = True

    def solve(self):
        """Move the moving part so the mate holds."""
        a, b = self.moving.world(), self.target.world()
        part = self.moving.part
        if self.kind == "mate":
            turn = rotation_between(a.normal, _mul(b.normal, -1))
            part._apply_world(_rotate_about(a.origin, turn))  # noqa: SLF001
            a = self.moving.world()
            distance = _dot(_sub(b.origin, a.origin), b.normal) + self.offset
            part._apply_world(placement.translation(*_mul(b.normal, distance)))  # noqa: SLF001
        elif self.kind == "align":
            target_dir = b.normal if _dot(a.normal, b.normal) >= 0 else _mul(b.normal, -1)
            part._apply_world(_rotate_about(a.origin, rotation_between(a.normal, target_dir)))  # noqa: SLF001
            a = self.moving.world()
            delta = _sub(b.origin, a.origin)
            if not self.contact:  # only across the axis
                delta = _sub(delta, _mul(b.normal, _dot(delta, b.normal)))
            part._apply_world(placement.translation(*delta))  # noqa: SLF001
        else:  # place
            want_normal = _mul(b.normal, -1) if self.flip else b.normal
            part._apply_world(_rotate_about(a.origin, rotation_between(a.normal, want_normal)))  # noqa: SLF001
            a = self.moving.world()
            # Turn about the normal so the x directions agree.
            x_now = _norm(_sub(a.x_dir, _mul(a.normal, _dot(a.x_dir, a.normal))))
            x_want = _norm(_sub(b.x_dir, _mul(a.normal, _dot(b.x_dir, a.normal))))
            angle = math.degrees(math.atan2(_dot(_cross(x_now, x_want), a.normal), _dot(x_now, x_want)))
            part._apply_world(_rotate_about(a.origin, axis_angle(a.normal, angle)))  # noqa: SLF001
            a = self.moving.world()
            part._apply_world(placement.translation(*_sub(b.origin, a.origin)))  # noqa: SLF001

    def problems(self) -> list[str]:
        """What is not true any more (empty = the mate holds)."""
        a, b = self.moving.world(), self.target.world()
        out = []
        if self.kind == "mate":
            if _dot(a.normal, b.normal) > -1 + TOLERANCE:
                out.append("the faces do not face each other")
            gap = _dot(_sub(a.origin, b.origin), b.normal)
            if abs(gap - self.offset) > TOLERANCE:
                out.append(f"the gap is {gap:.6g} mm, not {self.offset:g} mm")
        elif self.kind == "align":
            if abs(abs(_dot(a.normal, b.normal)) - 1) > TOLERANCE:
                out.append("the axes are not parallel")
            delta = _sub(a.origin, b.origin)
            across = _sub(delta, _mul(b.normal, _dot(delta, b.normal)))
            if math.sqrt(_dot(across, across)) > TOLERANCE:
                out.append("the axes are not on one line")
            if self.contact and math.sqrt(_dot(delta, delta)) > TOLERANCE:
                out.append("the points do not meet")
        else:
            want = _mul(b.normal, -1) if self.flip else b.normal
            if _dot(a.normal, want) < 1 - TOLERANCE or _dot(a.x_dir, b.x_dir) < 1 - TOLERANCE:
                out.append("the frames do not agree")
            if math.dist(a.origin, b.origin) > TOLERANCE:
                out.append("the origins do not meet")
        return out

    def to_spec(self, instance_of) -> dict:
        data = {
            "type": self.kind,
            "moving": {"instance": instance_of(self.moving.part), "anchor": self.moving.name},
            "target": {"instance": instance_of(self.target.part), "anchor": self.target.name},
        }
        if self.kind == "mate":
            data["offset"] = self.offset
        if self.kind == "align":
            data["contact"] = self.contact
        if self.kind == "place":
            data["flip"] = self.flip
        return data
