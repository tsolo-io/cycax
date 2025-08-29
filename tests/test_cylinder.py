# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Cylinder
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from tests.shared import stl_compare, stl_compare_models


def sphere_cube(tmp_path: Path):
    cylinder = Cylinder(diameter=10, height=10, part_no="test_cylinder")

    cylinder.save(tmp_path)
    cylinder.build(PartEngineBuild123d())
    stl = tmp_path / "test_cylinder" / "test_cylinder.stl"
    build123d_stl = stl.with_name("test_cylinder_build123d.stl")
    stl.rename(build123d_stl)
    cylinder.build(PartEngineFreeCAD(name=cylinder.part_no, path=tmp_path))
    # Read Build123d Mesh
    stl_compare_models(build123d_stl, stl)


def test_sphere(tmp_path: Path):
    print(tmp_path)
    sphere_cube(tmp_path)
