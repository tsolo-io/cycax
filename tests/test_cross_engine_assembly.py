# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Cross-engine assembly tests (task cycax/40): build123d, FreeCAD and Blender must give the same
assembly, instance by instance. The matrix runs with -m cross_engine and CYCAX_TEST_SERVER_URL
(FreeCAD and Blender run on the server); the planted-error and interference tests always run."""

import os
from pathlib import Path

import pytest

from cycax import testing
from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.cycad import Assembly, Print3D
from cycax.targets import load_targets

ROOT = Path(__file__).resolve().parents[1]
TEST_SET = sorted((ROOT / "src" / "examples").glob("*.py"))
for _extra in filter(None, os.environ.get("CYCAX_CROSS_ENGINE_EXTRA", "").split(":")):
    TEST_SET += sorted(p for p in Path(_extra).expanduser().rglob("*.py") if not p.name.startswith("_"))


def assembly_cases() -> list:
    cases = []
    for file in TEST_SET:
        try:
            targets = load_targets(file)
        except Exception as error:  # noqa: BLE001
            cases.append(
                pytest.param(file, None, id=f"{file.stem}-load-error", marks=pytest.mark.xfail(reason=str(error)))
            )
            continue
        cases.extend(pytest.param(file, t.name, id=f"{file.stem}:{t.name}") for t in targets if t.kind == "assembly")
    return cases


@pytest.mark.cross_engine
@pytest.mark.slow
@pytest.mark.parametrize(("file", "target"), assembly_cases())
def test_assembly_matrix(request, tmp_path, file, target):
    if "cross_engine" not in (request.config.option.markexpr or "") and os.environ.get("CYCAX_CROSS_ENGINE") != "1":
        pytest.skip("cross-engine matrix: run with -m cross_engine")
    server_url = os.environ.get("CYCAX_TEST_SERVER_URL")
    engines = ["build123d", "freecad", "blender"] if server_url else ["build123d"]
    (selected,) = load_targets(file, target)
    for index, assembly in enumerate(selected.make()):
        result = testing.cross_engine_assembly(assembly, engines, tmp_path / str(index), server_url=server_url)
        print(result.report())  # noqa: T201
        assert result.ok, result.report()


def two_blocks(gap: float) -> Assembly:
    assembly = Assembly(f"blocks_{int(gap * 10)}")
    a = Print3D(part_no="block_a", x_size=20, y_size=10, z_size=10)
    b = Print3D(part_no="block_b", x_size=20, y_size=10, z_size=10)
    assembly.add(a)
    assembly.add(b)
    b.level(left=a.right)
    b.move(x=gap)
    return assembly


def step_of(assembly, tmp_path) -> Path:
    settings = Settings()
    settings.cache_folder = str(tmp_path / "cache")
    built = Builder(Project(tmp_path, settings), outputs=["step"], backend="local").build_item(
        BuildItem(assembly.name, assembly)
    )
    assert built.error is None, built.error
    return built.files["step"]


def test_a_misplaced_part_fails(tmp_path):
    good = testing.assembly_instances(step_of(two_blocks(0), tmp_path / "good"))
    moved = testing.assembly_instances(step_of(two_blocks(0.5), tmp_path / "moved"))
    problems = testing.compare_instances(good, moved)
    assert any(problem.startswith("block_b_1: bbox min x") for problem in problems), problems
    assert testing.compare_instances(good, testing.assembly_instances(step_of(two_blocks(0), tmp_path / "again"))) == []


def test_interference(tmp_path):
    assert testing.interference(step_of(two_blocks(0), tmp_path / "touch")) == []  # touching is fine
    clashes = testing.interference(step_of(two_blocks(-2), tmp_path / "overlap"))
    assert [(a, b) for a, b, _ in clashes] == [("block_a_1", "block_b_1")]
    assert clashes[0][2] == pytest.approx(2 * 10 * 10)
