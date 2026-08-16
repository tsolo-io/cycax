# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# This file is called directly from FreeCAD, exactly like cycax_part_freecad.py, but is a
# dedicated script for `SheetMetalBend` parts only -- see docs/content/sheetmetal-bend-design.md.
# CyCAx launches the FreeCAD binary and passes in:
# 1. The fullpath to this file.
# 2. The path to the part JSON file; as environmental variable ("CYCAX_JSON")
# 3. The path to where the output files should be stored; as environmental variable ("CYCAX_CWD")
#
# Unlike cycax_part_freecad.py, this engine only ever builds one part at a time (no BULK
# mode yet -- SheetMetalBend parts are built one at a time in every worked example so far;
# add it the same way part_freecad.py's bulk_build() does, if/when it's actually needed).
#
# Deliberately keeps the *entire* FreeCAD object tree alive in the saved .FCStd -- every
# bend (`SMBendWall`) and every cutout is a real, named document object, chained via
# Part::Cut, so the part can be re-opened in FreeCAD and hand-adjusted (e.g. an earlier
# bend's angle) with everything downstream recomputing. An earlier prototype of this engine
# deleted the intermediate bend objects after building, on the assumption STEP export
# needed a single flattened shape -- confirmed unnecessary (STEP export just reads whatever
# object is currently the end of the chain), so that cleanup step doesn't exist here.

import logging
import math
import os
from pathlib import Path

import FreeCAD as App
import FreeCADGui
import importDXF
import Part
from FreeCAD import Matrix, Vector

try:
    import SheetMetalTools

    if not hasattr(SheetMetalTools, "taskRestoreDefaults"):
        # SheetMetalTools' task-panel defaults-restore only exists in GUI mode; this file
        # runs the FreeCAD GUI binary but never opens that specific task panel, so a stub
        # is enough (matches the FreeCAD SheetMetal proof-of-concept this was verified
        # against, see docs/content/sheetmetal-bend-design.md).
        def _sm_task_restore_defaults(obj, var_list):
            pass

        SheetMetalTools.taskRestoreDefaults = _sm_task_restore_defaults

    import SheetMetalCmd
    import SheetMetalUnfoldCmd

    SHEETMETAL_AVAILABLE = True
except ImportError:
    SHEETMETAL_AVAILABLE = False
    logging.warning("SheetMetal workbench not found -- this engine cannot build SheetMetalBend parts.")

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"
REAR = "BACK"

_HOLE_CUT_ROTATIONS = {
    FRONT: App.Rotation(Vector(1, 0, 0), 270),
    BACK: App.Rotation(Vector(1, 0, 0), 90),
    TOP: App.Rotation(Vector(0, 1, 0), 180),
    BOTTOM: App.Rotation(Vector(0, 1, 0), 0),
    LEFT: App.Rotation(Vector(0, 1, 0), 90),
    RIGHT: App.Rotation(Vector(0, 1, 0), 270),
}


class EngineFreecadBend:
    """Builds a `SheetMetalBend` part's JSON into a real, live FreeCAD SheetMetal document.

    Args:
        base_path: the path where the outputs need to be stored.
    """

    def __init__(self, base_path: Path):
        self._base_path = base_path
        self.filepath = ""

    # -- Bends ---------------------------------------------------------------------------

    def _find_edge(
        self,
        shape,
        origin: tuple,
        u_dir: tuple,
        v_dir: tuple,
        width: float,
        length_tolerance: float = 0.5,
        direction_tolerance: float = 1e-3,
        position_tolerance: float = 20.0,
    ) -> str:
        """Find the just-created flange's own leading edge, to bend the next segment from.

        cycax's own geometry (`cycax.cycad.bend`) models bends as sharp, zero-radius
        corners, so its predicted fold-line coordinates don't exactly match FreeCAD
        SheetMetal's *real*, rounded-bend-radius geometry -- verified empirically: for a
        90 mm bend at `radius=2`, cycax's predicted far-edge position was off by exactly
        one `radius` once the real bend was built. Exact coordinate matching (what an
        idealised model would suggest) therefore doesn't work here.

        Instead this matches by shape: among edges parallel to `u_dir` with length
        matching `width` *and* sitting close to `origin` in every direction except
        `v_dir` (`position_tolerance`), pick whichever sits furthest along `v_dir` from
        `origin` -- i.e. the flange's own leading edge, wherever the real bend geometry
        actually put it.

        The `position_tolerance` filter is required, not a nicety: without it, a nested
        bend elsewhere in the same part that happens to be a similar length, orientation,
        *and* height can otherwise out-rank the real target edge.

        Raises:
            ValueError: If no matching edge is found.
        """
        u_vec, v_vec, origin_vec = Vector(*u_dir), Vector(*v_dir), Vector(*origin)
        best_edge, best_projection = None, None
        for i, edge in enumerate(shape.Edges):
            verts = [v.Point for v in edge.Vertexes]
            if len(verts) != 2:  # noqa: PLR2004 two-endpoint edge
                continue
            a, b = verts
            edge_vector = b - a
            if abs(edge_vector.Length - width) > length_tolerance:
                continue
            edge_direction = edge_vector.normalize()
            if abs(abs(edge_direction.dot(u_vec)) - 1.0) > direction_tolerance:
                continue
            offset = (a + b) * 0.5 - origin_vec
            projection = offset.dot(v_vec)
            off_axis = offset - u_vec * offset.dot(u_vec) - v_vec * projection
            if off_axis.Length > position_tolerance:
                continue
            if best_projection is None or projection > best_projection:
                best_projection, best_edge = projection, f"Edge{i + 1}"
        if best_edge is None:
            msg = f"No edge parallel to {u_dir} with length {width} found near {origin}."
            raise ValueError(msg)
        return best_edge

    def _v_dir_extent(self, shape, origin: tuple, direction: tuple) -> float:
        """How far `shape`'s bounding box reaches beyond `origin`, projected onto `direction`."""
        bbox = shape.BoundBox
        support_point = (
            bbox.XMax if direction[0] >= 0 else bbox.XMin,
            bbox.YMax if direction[1] >= 0 else bbox.YMin,
            bbox.ZMax if direction[2] >= 0 else bbox.ZMin,
        )
        return sum((s - o) * c for s, o, c in zip(support_point, origin, direction, strict=True))

    def decode_bend(self, feature: dict, current_obj, doc: App.Document):
        """Add one real bend/flange via the FreeCAD SheetMetal workbench.

        Args:
            feature: The `bend` feature dict (see `cycax.cycad.features.Bend`).
            current_obj: The document object to bend -- the whole part built so far.
            doc: The active FreeCAD document.

        Returns:
            The new bend's document object -- becomes `current_obj` for the next bend, and
            is *kept* in the document (not removed) so it stays editable.
        """
        if not SHEETMETAL_AVAILABLE:
            msg = "The FreeCAD SheetMetal workbench is required to build a `bend` feature."
            raise RuntimeError(msg)

        full_width = feature["width"] + feature["gap1"] + feature["gap2"]
        origin = (
            feature["x"] - feature["u_dir"][0] * feature["gap1"],
            feature["y"] - feature["u_dir"][1] * feature["gap1"],
            feature["z"] - feature["u_dir"][2] * feature["gap1"],
        )
        edge_name = self._find_edge(current_obj.Shape, origin, feature["u_dir"], feature["fold_dir"], full_width)

        def build_bend(*, invert: bool):
            obj = doc.addObject("Part::FeaturePython", f"Bend_{feature['id']}_{invert}")
            SheetMetalCmd.SMBendWall(obj, current_obj, [edge_name])
            obj.radius = feature["radius"]
            obj.angle = feature["angle"]
            obj.length = feature["height"]
            obj.gap1 = feature["gap1"]
            obj.gap2 = feature["gap2"]
            obj.kfactor = feature["k_factor"]
            obj.BendType = {
                "outer": "Material Outside",
                "inner": "Material Inside",
                "thickness_outer": "Thickness Outside",
                "offset": "Offset",
            }[feature["corner_reference"]]
            obj.LengthSpec = {
                "leg": "Leg",
                "outer_sharp": "Outer Sharp",
                "inner_sharp": "Inner Sharp",
                "tangential": "Tangential",
            }[feature["length_spec"]]
            obj.invert = invert
            doc.recompute()
            return obj

        # `invert`'s "natural" (False) direction depends on the target edge's own
        # orientation within the shape, not on `direction` alone (verified empirically).
        # Score each candidate by isolating the material *this specific bend* actually
        # added (`candidate.cut(current_obj)`), then checking that isolated material
        # reaches forward (`+v_dir`) and not backward (`-v_dir`) from `origin`.
        #
        # An earlier version scored the *whole* candidate shape's bounding box against the
        # *whole* parent's -- which broke on `bend2.py`'s bracket: by the time the second
        # grip's second bend is decoded, `current_obj` already contains the *first* grip's
        # far reach in the same `v_dir` axis (both grips fold along X), which dominates the
        # global bounding box and drowns out this bend's own, much smaller, local signal.
        # Isolating the newly-added material first makes the measurement local to this
        # bend, immune to whatever unrelated geometry already exists elsewhere in the part.
        v_dir = feature["v_dir"]
        neg_v_dir = tuple(-c for c in v_dir)

        def score(shape) -> float:
            added = shape.cut(current_obj.Shape)
            if added.Volume < 1e-6:  # noqa: PLR2004 near-zero-volume guard
                return float("-inf")
            forward = self._v_dir_extent(added, origin, v_dir)
            backward = self._v_dir_extent(added, origin, neg_v_dir)
            return forward - backward

        candidate_true = build_bend(invert=True)
        candidate_false = build_bend(invert=False)
        if score(candidate_true.Shape) >= score(candidate_false.Shape):
            doc.removeObject(candidate_false.Name)
            return candidate_true
        doc.removeObject(candidate_true.Name)
        return candidate_false

    # -- Cutouts ---------------------------------------------------------------------------

    def _hole_tool(self, feature: dict, doc: App.Document, name: str):
        """A native, independently-editable `Part::Cylinder` for a `hole`/`Holes` feature."""
        obj = doc.addObject("Part::Cylinder", name)
        obj.Radius = feature["diameter"] / 2
        obj.Height = feature["depth"]
        obj.Placement = App.Placement(
            Vector(feature["x"], feature["y"], feature["z"]), _HOLE_CUT_ROTATIONS[feature["side"]]
        )
        doc.recompute()
        return obj

    def _flange_face_offset(self, solid, center: tuple, n_dir: tuple, position_tolerance: float = 5.0) -> float:
        """How far (signed, along `n_dir`) the real geometry's own outer face sits from
        `center`, by finding it directly rather than assuming a fixed relationship.

        A fixed "offset by the bend's own radius" formula was tried first and confirmed
        *not* to generalise: it matched two same-direction ("up") test bends exactly, but
        failed outright on a "down"-direction, gap-narrowed flange (`bend2.py`'s
        `front_flange`/`back_flange`) -- the real offset there wasn't `radius` at all in
        that flange's own current `n_dir`, because the curved bend region's own footprint
        is anchored to the *parent* surface's normal at the fold, not necessarily this
        flange's own (rotated) `n_dir`. Rather than re-derive which reference normal
        applies in which case, find the real face directly: among planar faces whose
        normal matches `n_dir` (the *outward* direction specifically, not just parallel --
        see `Bend`'s "origin sits on the outer face" convention) and whose footprint
        plausibly contains `center` in the two axes perpendicular to `n_dir`
        (`position_tolerance`), keep whichever is closest to `center` along `n_dir`.
        """
        axes = [i for i in range(3) if abs(n_dir[i]) < 0.5]  # noqa: PLR2004 near-zero component
        best_offset = None
        for face in solid.Faces:
            if face.Surface.TypeId != "Part::GeomPlane":
                continue
            normal = face.normalAt(0, 0)
            dot = normal.x * n_dir[0] + normal.y * n_dir[1] + normal.z * n_dir[2]
            if dot < 0.95:  # noqa: PLR2004 near-zero tolerance -- same direction as n_dir, not antiparallel
                continue
            bbox = face.BoundBox
            mins, maxs = (bbox.XMin, bbox.YMin, bbox.ZMin), (bbox.XMax, bbox.YMax, bbox.ZMax)
            if not all(mins[i] - position_tolerance <= center[i] <= maxs[i] + position_tolerance for i in axes):
                continue
            point = face.CenterOfMass
            offset = (
                (point.x - center[0]) * n_dir[0] + (point.y - center[1]) * n_dir[1] + (point.z - center[2]) * n_dir[2]
            )
            if best_offset is None or abs(offset) < abs(best_offset):
                best_offset = offset
        return best_offset if best_offset is not None else 0.0

    def _corrected_center(self, feature: dict, solid) -> tuple:
        """Correct a flange cutout's centre for the real, rounded-bend-radius geometry.

        `feature["x"/"y"/"z"]` is cycax's *idealised* position, computed as if this
        flange's own bend were a sharp, zero-radius fold -- fine for a cut on the *base*
        sheet (`parent` is `None`, no bend involved), but not for a cut on a flange: the
        real flange's own outer face doesn't sit flush with that idealised position (see
        `_flange_face_offset`).
        """
        center = (feature["x"], feature["y"], feature["z"])
        if feature.get("parent") is None:
            return center
        n_dir = feature["n_dir"]
        offset = self._flange_face_offset(solid, center, n_dir)
        return tuple(center[i] + n_dir[i] * offset for i in range(3))

    def _flange_hole_tool(self, feature: dict, center: tuple, doc: App.Document, name: str, solid):
        """A native `Part::Cylinder` for a `flange_hole_cut` feature, oriented via its own
        `u_dir`/`v_dir`/`n_dir` frame (unlike `_hole_tool`, which only handles the base
        sheet's 6 fixed, axis-aligned side rotations).

        Same "try both, keep whichever overlaps" fix as `_extruded_flat_cut` -- confirmed
        needed here too on the bracket example's `front_flange`/`back_flange` (bent
        "down", unlike the tray's tips): `points_outward` alone picked the wrong side for
        both M12 holes, landing them entirely outside the real solid.
        """
        u_dir, v_dir, n_dir = feature["u_dir"], feature["v_dir"], feature["n_dir"]
        z_dir, points_outward = self._oriented_frame(u_dir, v_dir, n_dir)
        thickness = feature["thickness"]
        radius = feature["diameter"] / 2
        matrix = Matrix(
            u_dir[0], v_dir[0], z_dir[0], 0,
            u_dir[1], v_dir[1], z_dir[1], 0,
            u_dir[2], v_dir[2], z_dir[2], 0,
            0, 0, 0, 1,
        )  # fmt: skip

        def placement_for(z_start: float) -> App.Placement:
            base = Vector(*(center[i] + z_dir[i] * z_start for i in range(3)))
            return App.Placement(base, App.Rotation(matrix))

        preferred_z_start = -thickness if points_outward else 0.0
        other_z_start = 0.0 if points_outward else -thickness
        preferred_shape = Part.makeCylinder(radius, thickness)
        preferred_shape.Placement = placement_for(preferred_z_start)
        z_start = preferred_z_start if self._overlap_volume(preferred_shape, solid) > 1e-6 else other_z_start  # noqa: PLR2004

        obj = doc.addObject("Part::Cylinder", name)
        obj.Radius = radius
        obj.Height = thickness
        obj.Placement = placement_for(z_start)
        doc.recompute()
        return obj

    def _oriented_frame(self, u_dir: tuple, v_dir: tuple, n_dir: tuple) -> tuple:
        """Derive `(z_dir, points_outward)` for a cutout's own oriented in-plane axes.

        `z_dir` can't just be `n_dir`: `u_dir`/`v_dir` here are a cutout's own, possibly
        rotated, local axes (see `FlatRectangleCut`/`FlatPolygonCut`), not necessarily
        forming a right-handed triple with `n_dir` directly -- same issue already fixed for
        `decode_flange_corner_round`. Deriving the 3rd axis as `u_dir cross v_dir` is
        always a valid basis; `points_outward` then says whether that happens to point the
        same way as `n_dir` or not, which is what decides which face the material
        (thickness) extends from.
        """
        z_dir = (
            u_dir[1] * v_dir[2] - u_dir[2] * v_dir[1],
            u_dir[2] * v_dir[0] - u_dir[0] * v_dir[2],
            u_dir[0] * v_dir[1] - u_dir[1] * v_dir[0],
        )
        points_outward = sum(z_dir[i] * n_dir[i] for i in range(3)) > 0
        return z_dir, points_outward

    def _overlap_volume(self, shape, solid) -> float:
        """How much of `shape` actually overlaps `solid`, or 0 if none/invalid."""
        try:
            common = shape.common(solid)
        except Exception:
            return 0.0
        return common.Volume if common and common.Volume else 0.0

    def _extruded_flat_cut(
        self, center: tuple, u_dir: tuple, v_dir: tuple, n_dir: tuple, local_vertices, thickness: float, solid
    ):
        """Build a straight-through cut shape by extruding a 2D polygon (in the cutout's
        own local `(u, v)` plane, given as `local_vertices` pairs) through `thickness`.

        Shared by `FlatRectangleCut` (4 corners) and `FlatPolygonCut` (`sides` corners) --
        a rectangle is just a 4-gon here, so one routine covers both.

        Which side of the cutout's own plane (`z_dir`, `-z_dir`) the material actually
        extends into isn't reliably predictable from `points_outward` alone for a *nested*
        bend -- confirmed on the tray's `right_tip` (a bend off `right_wall`, itself a
        bend): the cut computed on the wrong side sat entirely outside the real solid
        ("under the flange", not overlapping it at all), the same class of orientation
        ambiguity already worked around for `SMBendWall`'s own `invert`. Build both
        candidates and keep whichever actually overlaps `solid`, rather than trusting the
        sign convention on its own.
        """
        z_dir, points_outward = self._oriented_frame(u_dir, v_dir, n_dir)

        def build(z_start: float):
            base_point = tuple(center[i] + z_dir[i] * z_start for i in range(3))
            vectors = [
                Vector(
                    base_point[0] + u_dir[0] * lu + v_dir[0] * lv,
                    base_point[1] + u_dir[1] * lu + v_dir[1] * lv,
                    base_point[2] + u_dir[2] * lu + v_dir[2] * lv,
                )
                for lu, lv in local_vertices
            ]
            vectors.append(vectors[0])
            face = Part.Face(Part.Shape(Part.makePolygon(vectors)))
            extrude_vec = Vector(z_dir[0] * thickness, z_dir[1] * thickness, z_dir[2] * thickness)
            return face.extrude(extrude_vec)

        preferred_z_start = -thickness if points_outward else 0.0
        other_z_start = 0.0 if points_outward else -thickness
        preferred = build(preferred_z_start)
        if self._overlap_volume(preferred, solid) > 1e-6:  # noqa: PLR2004 near-zero overlap tolerance
            return preferred
        return build(other_z_start)

    def _flat_rectangle_cut_shape(self, feature: dict, center: tuple, solid):
        half_w, half_h = feature["width"] / 2, feature["height"] / 2
        local_vertices = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
        return self._extruded_flat_cut(
            center,
            feature["u_dir"],
            feature["v_dir"],
            feature["n_dir"],
            local_vertices,
            feature["thickness"],
            solid,
        )

    def _flat_polygon_cut_shape(self, feature: dict, center: tuple, solid):
        sides, radius = feature["sides"], feature["diameter"] / 2
        # One vertex at the minimum-v point (angle -90 deg), matching the same convention
        # documented for the (aspirational) `regular_polygon` JSON feature.
        local_vertices = [
            (
                radius * math.cos(math.radians(-90 + k * 360.0 / sides)),
                radius * math.sin(math.radians(-90 + k * 360.0 / sides)),
            )
            for k in range(sides)
        ]
        return self._extruded_flat_cut(
            center,
            feature["u_dir"],
            feature["v_dir"],
            feature["n_dir"],
            local_vertices,
            feature["thickness"],
            solid,
        )

    def decode_flange_corner_round(self, feature: dict, solid):
        """Cut the two far corners of a flange (`FlangeCornerRound`) -- returns the shape
        to subtract, a "box minus cylinder" shape built from this feature's own oriented
        `u_dir`/`v_dir`/`n_dir` frame.

        Args:
            feature: The `flange_corner_round` feature dict.
            solid: The part's current `Part.Shape` -- needed because `feature["x"/"y"/"z"]`
                is cycax's *idealised*, zero-radius-corner position for this flange's far
                edge, which doesn't exactly match where the real, rounded-bend-radius
                geometry actually put it (same root cause as `_find_edge`). Re-finds the
                real far edge instead of trusting the idealised position.
        """
        u_dir, v_dir, n_dir = feature["u_dir"], feature["v_dir"], feature["n_dir"]
        z_dir, points_outward = self._oriented_frame(u_dir, v_dir, n_dir)
        thickness = feature["thickness"]

        width, radius = feature["width"], feature["radius"]
        ideal_origin = (feature["x"], feature["y"], feature["z"])
        edge_name = self._find_edge(solid, ideal_origin, u_dir, v_dir, width)
        edge_idx = int(edge_name.replace("Edge", "")) - 1
        verts = [v.Point for v in solid.Edges[edge_idx].Vertexes]
        ideal_origin_vec = Vector(*ideal_origin)
        origin = min(verts, key=lambda v: (v - ideal_origin_vec).Length)
        matrix = Matrix(
            u_dir[0], v_dir[0], z_dir[0], 0,
            u_dir[1], v_dir[1], z_dir[1], 0,
            u_dir[2], v_dir[2], z_dir[2], 0,
            0, 0, 0, 1,
        )  # fmt: skip
        placement = App.Placement(App.Vector(0, 0, 0), App.Rotation(matrix))
        placement.Base = origin

        def corner_cut(*, at_max_u: bool, z_start: float):
            box_u = width - radius if at_max_u else 0.0
            fillet_u = width - radius if at_max_u else radius
            box = Part.makeBox(radius, radius, thickness, Vector(box_u, -radius, z_start))
            cylinder = Part.makeCylinder(radius, thickness, Vector(fillet_u, -radius, z_start))
            return box.cut(cylinder)

        def build_cut(z_start: float):
            cut = corner_cut(at_max_u=False, z_start=z_start).fuse(corner_cut(at_max_u=True, z_start=z_start))
            cut.Placement = placement
            return cut

        # Which side of the origin's own plane (`z_start=0` vs `-thickness`) the material
        # actually sits on isn't reliably predictable from `points_outward` alone for a
        # *nested* bend -- confirmed on the tray's `right_tip` (a bend off `right_wall`,
        # itself a bend): the cut computed on the wrong side sat entirely under the real
        # flange, not overlapping it at all, even though its own shape/size was correct.
        # Build both and keep whichever actually overlaps `solid` (see `_extruded_flat_cut`
        # for the same fix applied to rectangle/polygon cuts).
        preferred_z_start = -thickness if points_outward else 0.0
        other_z_start = 0.0 if points_outward else -thickness
        preferred = build_cut(preferred_z_start)
        if self._overlap_volume(preferred, solid) > 1e-6:  # noqa: PLR2004 near-zero overlap tolerance
            return preferred
        return build_cut(other_z_start)

    def _shape_tool(self, shape, doc: App.Document, name: str):
        """Wrap a computed `Part.Shape` (polygon/corner-round cuts) as a live document
        object, so it participates correctly in the kept `Part::Cut` chain -- recomputes
        if anything upstream of it changes, though (unlike `_hole_tool`) its own
        size/position aren't independently editable via the property panel.
        """
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        doc.recompute()
        return obj

    # -- Unfold / DXF ------------------------------------------------------------------------

    def _find_base_face(self, shape, thickness: float, tolerance: float = 0.1) -> str:
        """Find the base sheet's own top face (flat, normal up, at `Z=thickness`), to
        anchor the unfold from. Validated against a working FreeCAD SheetMetal
        proof-of-concept (`~/src/cycax-playpen/sheetmetal-bend/sheetmetal_part.py`).
        """
        for i, face in enumerate(shape.Faces):
            if face.Surface.TypeId != "Part::GeomPlane":
                continue
            normal = face.normalAt(0, 0)
            if abs(normal.z) < 0.9:  # noqa: PLR2004 near-vertical normal
                continue
            bbox = face.BoundBox
            if abs(bbox.ZMin - thickness) < tolerance and abs(bbox.ZMax - thickness) < tolerance:
                return f"Face{i + 1}"
        msg = "Could not find the base sheet's top face for unfolding."
        raise ValueError(msg)

    def _export_unfold(self, final_obj, thickness: float, k_factor: float, doc: App.Document):
        """Unfold the flat pattern and export it as STEP and (layered) DXF.

        Sketch generation for unfold requires GUI mode -- true here, since this script
        always runs the FreeCAD GUI binary (not `--console`), same as
        `cycax_part_freecad.py`.
        """
        if not SHEETMETAL_AVAILABLE:
            msg = "The FreeCAD SheetMetal workbench is required to unfold a SheetMetalBend part."
            raise RuntimeError(msg)

        face_name = self._find_base_face(final_obj.Shape, thickness)
        unfold_obj = doc.addObject("Part::FeaturePython", "Unfold")
        SheetMetalUnfoldCmd.SMUnfold(unfold_obj, final_obj, [face_name])
        unfold_obj.KFactor = k_factor
        unfold_obj.GenerateSketch = True
        unfold_obj.SeparateSketchLayers = True
        if hasattr(unfold_obj, "ViewObject"):
            SheetMetalTools.SMViewProvider(unfold_obj.ViewObject)
        doc.recompute()

        if not unfold_obj.Shape or not unfold_obj.Shape.isValid():
            msg = "Unfold produced an invalid shape."
            raise ValueError(msg)
        unfold_obj.Shape.exportStep(f"{self.filepath}-unfold.step")

        sketch_names = getattr(unfold_obj, "UnfoldSketches", [])
        sketches = [doc.getObject(sketch_name) for sketch_name in sketch_names]
        sketches = [sketch for sketch in sketches if sketch is not None]
        if not sketches:
            msg = "Unfold produced no sketches -- cannot export DXF."
            raise ValueError(msg)
        importDXF.export(sketches, f"{self.filepath}-unfold.dxf")

    # -- Build ---------------------------------------------------------------------------

    def build(self, definition: dict):
        """Build a `SheetMetalBend` part's JSON into a live FreeCAD document, and export
        STEP (folded), FCStd (live tree), STEP (unfolded), and DXF (unfolded).

        Args:
            definition: The part's JSON definition.
        """
        name = definition["name"]
        if App.ActiveDocument:
            App.closeDocument(name)
        doc = App.newDocument(name)

        base_feature = definition["features"][0]
        if base_feature["action"] != "add" or base_feature["type"] != "cuboid":
            msg = "First feature must be the SheetMetalBend's base cuboid."
            raise ValueError(msg)

        base_obj = doc.addObject("Part::Box", "BaseSheet")
        base_obj.Length = base_feature["x_size"]
        base_obj.Width = base_feature["y_size"]
        base_obj.Height = base_feature["z_size"]
        doc.recompute()
        current_obj = base_obj

        bend_features = [f for f in definition["features"][1:] if f["type"] == "bend"]
        for bend_feature in bend_features:
            current_obj = self.decode_bend(bend_feature, current_obj, doc)

        cut_index = 0
        for feature in definition["features"][1:]:
            if feature["type"] == "bend":
                continue
            cut_index += 1
            if feature["type"] == "cylinder" and feature["action"] == "subtract":
                tool_obj = self._hole_tool(feature, doc, f"Hole_{cut_index}")
            elif feature["type"] == "flange_hole_cut":
                center = self._corrected_center(feature, current_obj.Shape)
                tool_obj = self._flange_hole_tool(feature, center, doc, f"Hole_{cut_index}", current_obj.Shape)
            elif feature["type"] == "flat_rectangle_cut":
                center = self._corrected_center(feature, current_obj.Shape)
                shape = self._flat_rectangle_cut_shape(feature, center, current_obj.Shape)
                tool_obj = self._shape_tool(shape, doc, f"RectCut_{cut_index}")
            elif feature["type"] == "flat_polygon_cut":
                center = self._corrected_center(feature, current_obj.Shape)
                shape = self._flat_polygon_cut_shape(feature, center, current_obj.Shape)
                tool_obj = self._shape_tool(shape, doc, f"PolyCut_{cut_index}")
            elif feature["type"] == "flange_corner_round":
                cut_shape = self.decode_flange_corner_round(feature, current_obj.Shape)
                tool_obj = self._shape_tool(cut_shape, doc, f"CornerRound_{cut_index}")
            else:
                logging.error("Feature type %s is not supported by SheetMetalBend.", feature["type"])
                continue

            cut_obj = doc.addObject("Part::Cut", f"Cut_{cut_index}")
            cut_obj.Base = current_obj
            cut_obj.Tool = tool_obj
            doc.recompute()
            current_obj = cut_obj

        final_obj = current_obj
        self.filepath = self._base_path / name / name

        k_factor = bend_features[0]["k_factor"] if bend_features else 0.44
        self._export_unfold(final_obj, base_feature["z_size"], k_factor, doc)

        FreeCADGui.activeDocument().activeView().viewTop()
        FreeCADGui.SendMsgToActiveView("ViewFit")
        doc.saveCopy(f"{self.filepath}.FCStd")
        final_obj.Shape.exportStep(f"{self.filepath}.step")

        App.closeDocument(name)


try:
    json_file = os.getenv("CYCAX_JSON")
    out_dir = os.getenv("CYCAX_CWD")
    engine = EngineFreecadBend(Path(out_dir))

    import json

    definition = json.loads(Path(json_file).read_text())
    logging.info("SheetMetalBend json file %s out dir = %s", json_file, out_dir)
    engine.build(definition)
finally:
    # QtGui.QApplication.quit() reliably segfaults here (Gui::PythonConsole teardown,
    # inside Qt's MDI/view-widget destruction) -- and an unclean-looking exit is what
    # triggers FreeCAD's crash-recovery prompt on the *next* launch. Everything this
    # process needs to produce is already written to disk by this point, so skip Qt's
    # graceful widget teardown entirely and terminate immediately instead.
    os._exit(0)
