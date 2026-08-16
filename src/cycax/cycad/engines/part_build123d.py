# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import math
from pathlib import Path

import build123d

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


class PartEngineBuild123d(PartEngine):
    """
    Decode a JSON and render with Build123d.
    """

    def __init__(self, name: str | None = None, path: Path | None = None, config: dict | None = None):
        self.jobs = {}
        super().__init__(name, path, config)

    def _decode_cylinder(self, feature_spec: dict) -> build123d.objects_part.Box:
        """
        This method creates a Cylinder object in Build123d.

        Args:
            feature_spec: The details about the cylinder.

        """
        radius = feature_spec["x_size"] / 2
        height = feature_spec["z_size"]
        feature = build123d.Cylinder(radius=radius, height=height)
        # TODO: Support the different orientations
        feature = build123d.Pos(radius, radius, height / 2) * feature
        return feature

    def _decode_cube(self, feature_spec: dict) -> build123d.objects_part.Box:
        """
        This method will return the string that will have the Build123d for a cube.

        Args:
            feature: this will be the dictionary that contains the details about the cube.

        """
        feature = build123d.Box(feature_spec["x_size"], feature_spec["y_size"], feature_spec["z_size"])
        if not feature_spec.get("center"):
            feature = (
                build123d.Pos(
                    feature_spec["x"] + feature_spec["x_size"] / 2,
                    feature_spec["y"] + feature_spec["y_size"] / 2,
                    feature_spec["z"] + feature_spec["z_size"] / 2,
                )
                * feature
            )
            if feature_spec.get("side") == BOTTOM:
                pass  # No feature transform needed.
            elif feature_spec.get("side") == TOP:
                feature = build123d.Pos(0, 0, -feature_spec["z_size"]) * feature
            elif feature_spec.get("side") == BACK:
                feature = build123d.Pos(0, -feature_spec["y_size"], 0) * feature
            elif feature_spec.get("side") == RIGHT:
                feature = build123d.Pos(-feature_spec["x_size"], 0, 0) * feature
            # TODO: The rest of the sides needs to be checked
        else:
            feature = (
                build123d.Pos(
                    feature_spec["x"],
                    feature_spec["y"],
                    feature_spec["z"],
                )
                * feature
            )
        return feature

    def _decode_cylinder_feature(self, feature_spec: dict) -> build123d.objects_part.Cylinder:
        """
        This method will return the string that will have the scad for a hole.

        Args:
            feature_spec: This will be a dictionary containing the necessary information about the hole.

        """
        feature = build123d.Cylinder(feature_spec["diameter"] / 2, height=feature_spec["depth"])
        x = feature_spec["x"]
        y = feature_spec["y"]
        z = feature_spec["z"]
        depth = feature_spec["depth"]
        side = feature_spec["side"]
        if feature_spec["action"] == "subtract":
            pos = {
                FRONT: build123d.Pos(x, y + depth / 2, z) * build123d.Rotation(X=270),
                BACK: build123d.Pos(x, y - depth / 2, z) * build123d.Rotation(X=90),
                TOP: build123d.Pos(x, y, z - depth / 2) * build123d.Rotation(Y=180),
                BOTTOM: build123d.Pos(x, y, z + depth / 2) * build123d.Rotation(Y=0),
                LEFT: build123d.Pos(x + depth / 2, y, z) * build123d.Rotation(Y=90),
                RIGHT: build123d.Pos(x - depth / 2, y, z) * build123d.Rotation(Y=270),
            }[side]
        else:
            pos = {
                FRONT: build123d.Pos(x, y - depth / 2, z) * build123d.Rotation(X=270),
                BACK: build123d.Pos(x, y + depth / 2, z) * build123d.Rotation(X=90),
                TOP: build123d.Pos(x, y, z + depth / 2) * build123d.Rotation(Y=180),
                BOTTOM: build123d.Pos(x, y, z - depth / 2) * build123d.Rotation(Y=0),
                LEFT: build123d.Pos(x - depth / 2, y, z) * build123d.Rotation(Y=90),
                RIGHT: build123d.Pos(x + depth / 2, y, z) * build123d.Rotation(Y=270),
            }[side]
        feature = pos * feature
        return feature

    def _decode_nut(self, feature_spec: dict) -> str:
        """
        This method will return the string that will have the Build123d for a nut cut out.

        Example feature_spec:
          {
            'name': 'nut',
             'type': 'nut_cutout',
             'action': 'subtract',
             'x': 10,
             'y': 7,
             'z': 7,
             'side': 'RIGHT',
             'nut_type': 'M3',
             'diameter': 6.2,
             'thickness': 2.5,
             'side_to_side': 5.5,
             'depth': 2.5,
             'vertical': True
           }

        Args:
            feature: This will be a dictionary containing the necessary information about the nut.
        """

        rot = 0 if feature_spec["vertical"] else 90
        hex2d = build123d.RegularPolygon(radius=feature_spec["diameter"] / 2, side_count=6, rotation=rot)
        feature = build123d.extrude(hex2d, amount=feature_spec["depth"])
        if feature_spec["side"] == FRONT:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(X=270) * feature
        elif feature_spec["side"] == BACK:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(X=90) * feature
        elif feature_spec["side"] == TOP:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=180) * feature
        elif feature_spec["side"] == BOTTOM:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=0) * feature
        elif feature_spec["side"] == LEFT:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=90) * feature
        elif feature_spec["side"] == RIGHT:
            pos = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"])
            feature = pos * build123d.Rotation(Y=270) * feature
        return feature

    def _decode_sphere(self, feature_spec: dict) -> build123d.objects_part.Sphere:
        """
        This method will return the string that will have the Build123d for a sphere cut out.

        Args:
            feature: This will be a dictionary containing the necessary information about the sphere.

        """
        feature = build123d.Sphere(feature_spec["diameter"] / 2)
        feature = build123d.Pos(feature_spec["x"], feature_spec["y"], feature_spec["z"]) * feature
        return feature

    def _oriented_plane(self, feature_spec: dict) -> tuple[build123d.Plane, "build123d.Align"]:
        """The plane a bend-related feature's `u_dir`/`v_dir`/`n_dir` describe.

        Returns `(plane, thickness_align)`. `build123d.Plane` derives its own `y_dir` as
        `z_dir.cross(x_dir)` -- so `x_dir=u_dir` alone doesn't pin down `z_dir`; it has to
        be picked so that derived `y_dir` comes out equal to `v_dir`, which is `u_dir
        cross v_dir` (a fixed identity: if `z = x cross y` then `z cross x = y`, always).
        That's *not* reliably `n_dir` or `-n_dir` -- `cycax.cycad.bend`'s `u`/`v`/`n` triad
        doesn't keep a consistent handedness across all four base sides (verified: it
        matches `-n_dir` for two of LEFT/RIGHT/FRONT/BACK and `+n_dir` for the other two).
        So which way `z_dir` actually points relative to `n_dir` (material is at `-n_dir`,
        see `_grow_part_bounds`) has to be checked per feature, and the box's thickness
        axis aligned (`Align.MIN` vs `Align.MAX`) accordingly, rather than assuming.
        """
        u_dir, v_dir, n_dir = feature_spec["u_dir"], feature_spec["v_dir"], feature_spec["n_dir"]
        z_dir = (
            u_dir[1] * v_dir[2] - u_dir[2] * v_dir[1],
            u_dir[2] * v_dir[0] - u_dir[0] * v_dir[2],
            u_dir[0] * v_dir[1] - u_dir[1] * v_dir[0],
        )
        plane = build123d.Plane(
            origin=build123d.Vector(feature_spec["x"], feature_spec["y"], feature_spec["z"]),
            x_dir=build123d.Vector(*u_dir),
            z_dir=build123d.Vector(*z_dir),
        )
        points_outward = sum(z_dir[i] * n_dir[i] for i in range(3)) > 0
        thickness_align = build123d.Align.MAX if points_outward else build123d.Align.MIN
        return plane, thickness_align

    def _decode_bend(self, feature_spec: dict) -> build123d.Part:
        """Render a `bend` feature as an oriented box.

        cycax has already resolved the bend's angle/direction into exact `u_dir`/`v_dir`/
        `n_dir` orientation vectors (`cycax.cycad.bend.BendSide`) -- this is a "fake"
        render for visualisation (see docs/content/bending-design.md §7), a sharp-cornered
        box rather than a true filleted bend, but it needs no separate angle/rotation math
        of its own, unlike a from-scratch approach would.
        """
        plane, thickness_align = self._oriented_plane(feature_spec)
        box = build123d.Box(
            feature_spec["width"],
            feature_spec["height"],
            feature_spec["thickness"],
            align=(build123d.Align.MIN, build123d.Align.MIN, thickness_align),
        )
        return plane * box

    def _decode_flange_corner_round(self, feature_spec: dict) -> build123d.Part:
        """Render a `flange_corner_round` feature: round the flange's two far corners.

        Deliberately not routed through `_decode_beveled_edge` -- see `FlangeCornerRound`
        and docs/content/bending-design.md §11. Cuts a quarter-cylinder fillet at each of
        the two corners on the feature's `far` edge (`x`/`y`/`z`, spanning `width` along
        `u_dir`), the same "box minus cylinder" shape `_decode_beveled_edge` already uses
        for a different kind of edge, just anchored to this feature's own oriented plane.
        """
        plane, thickness_align = self._oriented_plane(feature_spec)
        radius = feature_spec["radius"]
        thickness = feature_spec["thickness"]
        width = feature_spec["width"]

        def corner_cut(*, at_max_u: bool) -> build123d.Part:
            # The box sits at u in [0, radius] (min corner) or [width-radius, width] (max
            # corner), v in [-radius, 0] (back from the far edge, into the flange). The
            # fillet cylinder is tangent to the box's two inner edges, at whichever u its
            # own corner (the one *not* at 0 or width) sits.
            box_u = width - radius if at_max_u else 0.0
            fillet_u = width - radius if at_max_u else radius
            box = build123d.Box(
                radius, radius, thickness, align=(build123d.Align.MIN, build123d.Align.MAX, thickness_align)
            )
            box = build123d.Pos(box_u, 0, 0) * box
            cylinder = build123d.Cylinder(
                radius, thickness, align=(build123d.Align.CENTER, build123d.Align.CENTER, thickness_align)
            )
            cylinder = build123d.Pos(fillet_u, -radius, 0) * cylinder
            return box - cylinder

        return plane * (corner_cut(at_max_u=False) + corner_cut(at_max_u=True))

    def _decode_flange_hole_cut(self, feature_spec: dict) -> build123d.Part:
        """Render a `flange_hole_cut` feature: a straight-through circular hole, centred
        at `x`/`y`/`z` (see `cycax.cycad.features.FlangeHoleCut`)."""
        plane, thickness_align = self._oriented_plane(feature_spec)
        cylinder = build123d.Cylinder(
            feature_spec["diameter"] / 2,
            feature_spec["thickness"],
            align=(build123d.Align.CENTER, build123d.Align.CENTER, thickness_align),
        )
        return plane * cylinder

    def _decode_flat_rectangle_cut(self, feature_spec: dict) -> build123d.Part:
        """Render a `flat_rectangle_cut` feature: a straight-through rectangular cutout,
        centred at `x`/`y`/`z` (see `cycax.cycad.features.FlatRectangleCut`)."""
        plane, thickness_align = self._oriented_plane(feature_spec)
        box = build123d.Box(
            feature_spec["width"],
            feature_spec["height"],
            feature_spec["thickness"],
            align=(build123d.Align.CENTER, build123d.Align.CENTER, thickness_align),
        )
        return plane * box

    def _decode_flat_polygon_cut(self, feature_spec: dict) -> build123d.Part:
        """Render a `flat_polygon_cut` feature: a straight-through regular-polygon cutout,
        centred at `x`/`y`/`z`, with one vertex at the minimum-`v_dir` point before the
        plane's own orientation is applied (see `cycax.cycad.features.FlatPolygonCut`) --
        built from explicit vertices (not `build123d.RegularPolygon`) so that convention is
        followed exactly, matching the FreeCAD engine's own construction.
        """
        plane, thickness_align = self._oriented_plane(feature_spec)
        sides = feature_spec["sides"]
        radius = feature_spec["diameter"] / 2
        points = [
            (
                radius * math.cos(math.radians(-90 + k * 360.0 / sides)),
                radius * math.sin(math.radians(-90 + k * 360.0 / sides)),
            )
            for k in range(sides)
        ]
        thickness = feature_spec["thickness"]
        extrude_amount = thickness if thickness_align == build123d.Align.MIN else -thickness
        face = build123d.Polygon(*points, align=None)
        prism = build123d.extrude(face, amount=extrude_amount)
        return plane * prism

    def _bend_chains(self, bend_features: list[dict]) -> list[list[dict]]:
        """Group `bend` features into chains -- a root bend (`parent` is `None`) followed
        by its descendants, in order. Only far-edge chaining is authored (see
        `cycax.cycad.bend`'s module docstring), so each bend has at most one child; this
        just walks that linked list back into an ordered list per chain.
        """
        children_by_parent: dict[str | None, list[dict]] = {}
        for feature in bend_features:
            children_by_parent.setdefault(feature.get("parent"), []).append(feature)

        chains = []
        for root in children_by_parent.get(None, []):
            chain = [root]
            current = root
            while True:
                kids = children_by_parent.get(current["id"], [])
                if not kids:
                    break
                current = kids[0]
                chain.append(current)
            chains.append(chain)
        return chains

    def _decode_bend_chains_brake_formed(self, bend_features: list[dict]) -> tuple[list[build123d.Part], list[dict]]:
        """Render every bend chain with `build123d.make_brake_formed()` -- a real
        press-brake primitive that gives each bend a rounded transition "for free",
        instead of `_decode_bend`'s sharp-cornered oriented box.

        Opt in via `config={"bend_style": "brake_formed"}`; the default stays the
        oriented-box render, which is kept available deliberately -- it's an accurate
        (if sharp-cornered) placeholder already relied on for real part-variant testing
        (see docs/content/sheetmetal-bend-design.md), not something this replaces.

        Returns `(parts, fallback_features)`: `parts` are the successfully brake-formed
        chains (ready to add); `fallback_features` are individual `bend` feature dicts
        whose chain couldn't be verified as sound and should be rendered the old way
        instead (see below) -- the caller is expected to run those back through
        `_decode_bend` one at a time, same as when this render mode is off entirely.

        Known limitations, accepted rather than worked around:
        - Uses the chain's own *first* bend's `width` throughout, so a `gap1`/`gap2`
          narrowed flange partway down a chain won't visually narrow -- `make_brake_formed`
          takes a width per vertex, but a narrower flange is also off-centre (asymmetric
          gap), which a straight swept profile can't represent without an extra lateral
          shift this doesn't attempt.
        - The corner fillet radius is tied to `thickness` by `make_brake_formed` itself, not
          to the bend's own `radius` field (a build123d limitation, not a cycax one).
        - For a chain with a genuine corner (bend-on-bend, not just a single flange), no
          combination of `side` and wire direction found so far gives both the correct
          width direction *and* the full corner fillet at once (one always drops the outer
          corner's material; verified by volume, not just bounding box, since the
          dropped-material case still "looked" plausible from its bounding box alone).
          Rather than ship a rounded-looking but silently-incomplete part, a chain that
          fails verification falls back to the oriented-box render, chain by chain -- so
          today this mode mainly benefits single-bend (non-nested) chains; see
          docs/content/sheetmetal-bend-design.md.

        Even a single, un-nested flange isn't safe with just one `side` value, either:
        `make_brake_formed`'s in-plane thickness-offset direction and its out-of-plane
        width-sweep direction both derive from the same `side` choice (via an
        internally-offset wire's auto-derived face normal), but aren't a matched pair --
        confirmed on the tray's plain back wall, where one `side` gave the correct width
        direction with the thickness offset on the *wrong* face (the whole wall shifted
        inward by one thickness, silently -- same "looks plausible, isn't" trap as the
        corner case), and the other gave the reverse. Building the wire in both point
        orders as well as both `side` values (4 combinations total) recovers a correct
        pairing for a plain flange; verified via `_thickness_ok` below, not assumed.
        """
        parts = []
        fallback_features = []
        for chain in self._bend_chains(bend_features):
            first = chain[0]
            vertices = [build123d.Vector(first["x"], first["y"], first["z"])]
            for bend in chain:
                end = tuple(bend[c] + bend["v_dir"][i] * bend["height"] for i, c in enumerate("xyz"))
                vertices.append(build123d.Vector(*end))

            thickness, width, u_dir = first["thickness"], first["width"], first["u_dir"]
            origin = (first["x"], first["y"], first["z"])
            total_length = sum(bend["height"] for bend in chain)
            expected_volume = thickness * width * total_length

            def u_reach(candidate: build123d.Part, u_dir=u_dir, origin=origin) -> float:
                bbox = candidate.bounding_box()
                mins, maxs = (bbox.min.X, bbox.min.Y, bbox.min.Z), (bbox.max.X, bbox.max.Y, bbox.max.Z)
                support = tuple(maxs[i] if u_dir[i] >= 0 else mins[i] for i in range(3))
                return sum((support[i] - origin[i]) * u_dir[i] for i in range(3))

            def thickness_ok(candidate: build123d.Part, chain=chain, thickness=thickness, width=width) -> bool:
                # Check *every* bend in the chain, not just the first -- confirmed
                # necessary: on the tray's front+lip chain, the first bend (the plain
                # wall) had exactly the right thickness while the second (the 180-degree
                # return lip) came out a uniform ~75% of `thickness` throughout its own
                # length -- consistent (not tapering), but still wrong, and invisible to a
                # check that only ever probed the first segment.
                #
                # Material should be on the `-n_dir` side only (see
                # `cycax.cycad.bend._grow_part_bounds`'s own convention), and should
                # actually reach *close to* `thickness`, not just "some" -- a probe just
                # inside the correct face isn't enough to catch a too-thin result, so this
                # checks near the far (`0.85x`) and just past the expected (`1.15x`) faces.
                for bend in chain:
                    n_dir, u_dir, v_dir = bend["n_dir"], bend["u_dir"], bend["v_dir"]
                    base = tuple(
                        bend[c] + u_dir[i] * (width / 2) + v_dir[i] * (bend["height"] / 2) for i, c in enumerate("xyz")
                    )
                    near_pt = build123d.Vector(*(base[i] - n_dir[i] * thickness * 0.85 for i in range(3)))
                    past_pt = build123d.Vector(*(base[i] - n_dir[i] * thickness * 1.15 for i in range(3)))
                    if not candidate.is_inside(near_pt) or candidate.is_inside(past_pt):
                        return False
                return True

            candidates = []
            for point_order in (vertices, list(reversed(vertices))):
                edges = [
                    build123d.Edge.make_line(point_order[i], point_order[i + 1]) for i in range(len(point_order) - 1)
                ]
                wire = build123d.Wire(edges)
                for side in (build123d.Side.RIGHT, build123d.Side.LEFT):
                    try:
                        candidates.append(build123d.make_brake_formed(thickness, width, wire, side=side))
                    except Exception as exc:
                        logging.debug("make_brake_formed failed for side=%s: %s", side, exc)
                        continue

            # A candidate is only trusted if it extends in the right direction (matching u
            # in [0, width], the flange's real extent from `origin`), has the material on
            # the correct face (not shifted by a whole thickness), *and* has approximately
            # the expected amount of material -- each check caught a real, confirmed-bad
            # case the others missed (see the docstring above).
            sound = [
                candidate
                for candidate in candidates
                if u_reach(candidate) >= width * 0.9
                and candidate.volume >= expected_volume * 0.9
                and thickness_ok(candidate)
            ]
            if sound:
                parts.append(max(sound, key=lambda candidate: candidate.volume))
            else:
                fallback_features.extend(chain)
        return parts, fallback_features

    def _decode_beveled_edge(self, feature_spec: dict):
        """
        Return the solid to subtract off the edge.

        Args:
            feature: This will be a dictionary containing the necessary information about the beveled edge.

        Example:
        feature_spec = {
            'name': 'beveled_edge',
            'type': 'beveled_edge',
            'action': 'subtract',
            'edge_type': 'round',
            'axis1': 'y', 'bound1': 0.0,
            'axis2': 'x', 'bound2': 0.0,
            'size': 3, 'side': 'BOTTOM', 'depth': 2
            }
        """
        action_cube = {
            "side": feature_spec["side"],
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "x_size": feature_spec["depth"],
            "y_size": feature_spec["depth"],
            "z_size": feature_spec["depth"],
        }
        b1_cube = max(0.0, feature_spec["bound1"] - feature_spec["size"])
        b2_cube = max(0.0, feature_spec["bound2"] - feature_spec["size"])
        action_cube[feature_spec["axis1"]] = b1_cube
        action_cube[f"{feature_spec['axis1']}_size"] = feature_spec["size"]
        action_cube[feature_spec["axis2"]] = b2_cube
        action_cube[f"{feature_spec['axis2']}_size"] = feature_spec["size"]
        feature_cube = self._decode_cube(action_cube)
        action_cylinder = {
            "side": feature_spec["side"],
            "action": "subtract",
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "diameter": feature_spec["size"] * 2.0,
            "depth": feature_spec["depth"],
        }
        b1_cylinder = max(feature_spec["size"], feature_spec["bound1"] - feature_spec["size"])
        b2_cylinder = max(feature_spec["size"], feature_spec["bound2"] - feature_spec["size"])
        action_cylinder[feature_spec["axis1"]] = b1_cylinder
        action_cylinder[feature_spec["axis2"]] = b2_cylinder
        feature_cylinder = self._decode_cylinder_feature(action_cylinder)
        return feature_cube - feature_cylinder

    def build(self, part) -> list:
        """Create the output files for the part."""

        self.name = name = part.part_no
        files = []
        files = self.jobs.get(name, [])
        if not files:
            logging.info("Building part %s", name)
            self.set_path(part._base_path)
            file_no_ext = self._base_path / name / f"{name}"
            data = json.loads(self._json_file.read_text())
            files = self._build(data, file_no_ext)
            self.jobs[name] = files
        return self.file_list(files=files, engine="Build123d", score=3)

    def get_plane(self, part, side: str) -> build123d.Plane:
        if side is None:
            side = BOTTOM
        elif side not in SIDES:
            raise ValueError()

        ref_plane = getattr(build123d.Plane, side.lower())
        for face in part.faces().filter_by(ref_plane):
            plane = build123d.Plane(face)
            if plane.z_dir == ref_plane.z_dir:
                return plane

    def _build(self, definition: dict, file_no_ext: Path) -> list[Path]:
        """
        This is the main working class for decoding the scad. It is necessary for it to be refactored.

        Raises:
            ValueError: if incorrect part_name is provided.
        """

        part = None
        add_features = []
        subtract_features = []
        brake_formed = self.config.get("bend_style") == "brake_formed"
        fallback_bend_ids: set[str] = set()
        if brake_formed:
            bend_features = [f for f in definition["features"] if f["type"] == "bend"]
            chain_parts, fallback_features = self._decode_bend_chains_brake_formed(bend_features)
            add_features.extend(chain_parts)
            fallback_bend_ids = {f["id"] for f in fallback_features}

        for action in definition["features"]:
            match action["type"]:
                case "cuboid":
                    feature = self._decode_cube(action)
                case "cylinder":
                    # Base-shape cylinders (x_size/z_size) and cylinder features/holes
                    # (diameter/depth/side) share the "cylinder" type but need different
                    # decoders.
                    if "diameter" in action:
                        feature = self._decode_cylinder_feature(action)
                    else:
                        feature = self._decode_cylinder(action)
                case "sphere":
                    feature = self._decode_sphere(action)
                case "nut_cutout":
                    feature = self._decode_nut(action)
                case "beveled_edge":
                    feature = self._decode_beveled_edge(action)
                case "bend":
                    if brake_formed and action["id"] not in fallback_bend_ids:
                        continue  # Already rendered as part of a brake-formed chain, above.
                    feature = self._decode_bend(action)
                case "flange_corner_round":
                    feature = self._decode_flange_corner_round(action)
                case "flange_hole_cut":
                    feature = self._decode_flange_hole_cut(action)
                case "flat_rectangle_cut":
                    feature = self._decode_flat_rectangle_cut(action)
                case "flat_polygon_cut":
                    feature = self._decode_flat_polygon_cut(action)
                case _:
                    msg = f"Unknown feature type: {action['type']}"
                    raise ValueError(msg)

            feature = (
                build123d.Plane.XY * feature
            )  # The position and direction in the JSON is all relevant to the XY Plane.
            if action["action"] in ("add", "bend"):
                add_features.append(feature)
            elif action["action"] == "subtract":
                subtract_features.append(feature)
            else:
                msg = f"Unknown action type: {action['action']}"
                raise ValueError(msg)

        for feature in add_features:
            if part is None:
                part = feature
            else:
                part += feature
            if isinstance(part, build123d.ShapeList):
                # A boolean union between shapes that only touch along an edge/line (not a
                # face) -- common once a bend is at a non-90-degree angle -- can come back
                # as a bare ShapeList rather than a Compound/Solid. Both represent the same
                # valid, connected geometry; ShapeList just isn't itself an exportable OCCT
                # shape (no .wrapped), so re-wrap it as a Compound, which is.
                part = build123d.Compound(children=list(part))
        for feature in subtract_features:
            part -= feature
            if isinstance(part, build123d.ShapeList):
                part = build123d.Compound(children=list(part))

        files = []
        build123d.export_stl(to_export=part, file_path=file_no_ext.with_suffix(".stl"))
        files.append({"file": file_no_ext.with_suffix(".stl"), "type": "stl"})
        build123d.export_gltf(to_export=part, file_path=file_no_ext.with_suffix(".gltf"))
        files.append({"file": file_no_ext.with_suffix(".gltf"), "type": "gltf"})
        build123d.export_step(to_export=part, file_path=file_no_ext.with_suffix(".step"))
        files.append({"file": file_no_ext.with_suffix(".step"), "type": "step"})
        return files
