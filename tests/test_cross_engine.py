# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Cross-engine part tests (task cycax/23): every part of the test set is built with every
engine that can build it, and all pairs must give the same model.

The matrix is slow (FreeCAD starts for each part), so it runs only when asked:
`hatch run testing:cross-engine` (or `pytest -m cross_engine`, or CYCAX_CROSS_ENGINE=1).
Engines: build123d always; FreeCAD and OpenSCAD when they are installed; the server FreeCAD
worker when CYCAX_TEST_SERVER_URL is set (e.g. nats://127.0.0.1:4222).
The planted-fault test always runs: it proves that the matrix finds a difference.
"""

import os
from pathlib import Path

import pytest

from cycax import testing
from cycax.app.tools import FreeCADLocalTool, OpenSCADTool
from cycax.cycad import Print3D
from cycax.targets import load_targets

ROOT = Path(__file__).resolve().parents[1]
TEST_SET = [*sorted((ROOT / "src" / "examples").glob("*.py")), ROOT / "bend.py", ROOT / "bend2.py"]
# More folders, e.g. CYCAX_CROSS_ENGINE_EXTRA=~/src/kuat/IronHive/src/ironhive (martin: IronHive
# belongs in the test set). Separate several folders with ":".
for _extra in filter(None, os.environ.get("CYCAX_CROSS_ENGINE_EXTRA", "").split(":")):
    TEST_SET += sorted(p for p in Path(_extra).expanduser().rglob("*.py") if not p.name.startswith("_"))
SHEET_METAL_BEND = "SheetMetalBend"
# Known differences of the server FreeCAD worker (only when CYCAX_TEST_SERVER_URL is set).
KNOWN_SERVER: dict[str, str] = {}
# Differences that are known and wait for a decision (they still run; a fix makes them XPASS).
KNOWN: dict[str, str] = {}


def local_engines() -> list[str]:
    engines = ["build123d"]
    if FreeCADLocalTool().available():
        engines.append("freecad")
    if OpenSCADTool().available():
        engines.append("openscad")
    return engines


def part_cases() -> list:
    cases = []
    for file in TEST_SET:
        if not file.exists():
            continue
        try:
            targets = load_targets(file)
        except Exception as error:  # noqa: BLE001 - shown as a failing case
            cases.append(
                pytest.param(file, None, id=f"{file.stem}-load-error", marks=pytest.mark.xfail(reason=str(error)))
            )
            continue
        for t in targets:
            if t.kind != "part":
                continue
            case_id = f"{file.stem}:{t.name}"
            marks = [pytest.mark.xfail(reason=KNOWN[case_id], strict=False)] if case_id in KNOWN else []
            cases.append(pytest.param(file, t.name, id=case_id, marks=marks))
    return cases


@pytest.fixture
def matrix_enabled(request):
    markexpr = request.config.option.markexpr or ""
    if "cross_engine" not in markexpr and os.environ.get("CYCAX_CROSS_ENGINE") != "1":
        pytest.skip("cross-engine matrix: run with -m cross_engine or CYCAX_CROSS_ENGINE=1")


@pytest.mark.cross_engine
@pytest.mark.slow
@pytest.mark.parametrize(("file", "target"), part_cases())
def test_part_matrix(matrix_enabled, tmp_path, file, target):  # noqa: ARG001 - fixture skips
    (selected,) = load_targets(file, target)
    for index, obj in enumerate(selected.make()):
        engines = local_engines()
        if type(obj).__name__ == SHEET_METAL_BEND or any(c.__name__ == SHEET_METAL_BEND for c in type(obj).__mro__):
            engines = [e for e in engines if e == "freecad"]  # FreeCAD is the reference for bends
        server_url = os.environ.get("CYCAX_TEST_SERVER_URL")
        result = testing.cross_engine(obj, engines, tmp_path / f"local_{index}")
        if server_url:
            server = testing.cross_engine(
                obj, ["freecad"], tmp_path / f"server_{index}", backend="server", server_url=server_url
            )
            for engine, measured in server.measures.items():
                result.measures[f"{engine}@server"] = measured
            result.errors.update({f"{e}@server": err for e, err in server.errors.items()})
            reference = next(iter(result.measures))
            for engine in server.measures:
                ma, mb = result.measures[reference], result.measures[f"{engine}@server"]
                result.pairs[(reference, f"{engine}@server")] = testing.compare(ma, mb)
        print(result.report())  # noqa: T201 - the matrix in the CI log
        if len(result.measures) + len(result.errors) < 2:  # noqa: PLR2004
            pytest.skip(f"{result.name}: only {engines} can build it here")
        if not result.ok and result.name in KNOWN_SERVER:
            local_ok = all(not problems for (a, b), problems in result.pairs.items() if "@server" not in a + b)
            if local_ok and not result.errors:
                pytest.xfail(KNOWN_SERVER[result.name])
        assert result.ok, result.report()


def test_a_planted_fault_fails_the_matrix(tmp_path):
    """Test of the test: one engine gets a hole 1 mm to the side; the matrix must see it."""
    part = Print3D(part_no="planted", x_size=40, y_size=20, z_size=5)
    part.top.hole(pos=(10, 10), diameter=4.2)

    def move_hole(engine: str, spec: dict) -> dict:
        if engine == "build123d":
            return spec
        for feature in spec["features"]:
            if feature.get("name") == "hole":
                feature["x"] += 1.0
        return spec

    # Two builds with the same engine: the second gets the fault.
    good = testing.cross_engine(part, ["build123d"], tmp_path / "good")
    bad = testing.cross_engine(part, ["build123d"], tmp_path / "bad", spec_hook=lambda _e, s: move_hole("x", s))
    problems = testing.compare(good.measures["build123d"], bad.measures["build123d"])
    assert any(problem.startswith("centre x") for problem in problems), problems
    same = testing.cross_engine(part, ["build123d"], tmp_path / "same")
    assert testing.compare(good.measures["build123d"], same.measures["build123d"]) == []
