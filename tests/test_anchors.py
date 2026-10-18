# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Anchors (task cycax/37)."""

import build123d
import pytest

from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.cycad import Assembly, Print3D


def plate():
    part = Print3D(part_no="anchored", x_size=40, y_size=20, z_size=5)
    part.top.hole(pos=(10, 10), diameter=4, name="m4")
    return part


def test_face_and_hole_anchors_in_part_coordinates():
    part = plate()
    assert part.anchor("top").origin == (20.0, 10.0, 5.0)
    assert part.anchor("left").normal == (-1.0, 0.0, 0.0)
    assert part.anchor("m4").origin == (10.0, 10.0, 5.0)
    assert part.export()["meta"]["anchors"]["m4"]["normal"] == [0.0, 0.0, 1.0]
    with pytest.raises(KeyError, match="has: back, bottom"):
        part.anchor("nope")


def test_custom_anchor():
    part = plate()
    mount = part.anchor("mount", pos=(0, 0, 0), normal=(0, 0, -1))
    assert mount.normal == (0.0, 0.0, -1.0)
    assert abs(sum(a * b for a, b in zip(mount.normal, mount.x_dir, strict=True))) < 1e-9


def test_anchors_follow_a_30_degree_rotation(tmp_path):
    part = plate()
    part.move(x=50, y=30)
    part.rotate(z=30)
    hole = part.anchor("m4")
    right = part.anchor("right")
    assert right.normal == pytest.approx((0.866025404, 0.5, 0.0))
    # The real hole in the built assembly: its cylinder axis is where the anchor says.
    assembly = Assembly("anchored_assembly")
    assembly.add(part)
    settings = Settings()
    settings.cache_folder = str(tmp_path / "cache")
    result = Builder(Project(tmp_path, settings), outputs=["step"], backend="local").build(
        [BuildItem("anchored_assembly", assembly)]
    )
    target = next(iter(result.targets.values()))
    assert target.error is None, target.error
    shape = build123d.import_step(target.files["step"])
    cylinders = [f for f in shape.faces() if f.geom_type == build123d.GeomType.CYLINDER]
    assert cylinders
    centre = cylinders[0].center(build123d.CenterOf.BOUNDING_BOX)
    assert (centre.X, centre.Y) == pytest.approx(hole.origin[:2], abs=1e-6)
    assert centre.Z + 2.5 == pytest.approx(hole.origin[2], abs=1e-6)  # the hole goes down from the top
