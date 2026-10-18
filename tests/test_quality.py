# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from cycax import quality


def test_artifact_names_round_trip():
    name = quality.artifact_name("bracket", "freecad", "fine", "stl")
    assert name == "bracket-freecad-fine.stl"
    artifact = quality.parse_artifact_name(name)
    assert (artifact.name, artifact.engine, artifact.profile, artifact.ext) == ("bracket", "freecad", "fine", "stl")


def test_legacy_names_count_as_standard():
    artifact = quality.parse_artifact_name("bracket-freecad.FCStd")
    assert (artifact.engine, artifact.profile, artifact.ext) == ("freecad", "standard", "fcstd")


def test_non_artifacts_are_ignored():
    for filename in ("spec.json", "bracket-freecad.log", "bracket-import.step"):
        assert quality.parse_artifact_name(filename) is None


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError, match="Unknown profile"):
        quality.artifact_name("a", "freecad", "ultra", "stl")


def test_highest_profile_wins():
    files = ["p-freecad-draft.stl", "p-freecad-fine.stl", "p-build123d-standard.stl"]
    assert quality.select_best(files, "stl") == "p-freecad-fine.stl"


def test_tie_goes_to_engine_order():
    files = ["p-openscad-standard.stl", "p-build123d-standard.stl", "p-freecad-standard.stl"]
    table = {"build123d.stl.standard": 50, "freecad.stl.standard": 50}
    assert quality.select_best(files, "stl", table=table) == "p-freecad-standard.stl"


def test_openscad_fine_is_below_freecad_standard():
    files = ["p-openscad-fine.stl", "p-freecad-standard.stl"]
    assert quality.select_best(files, "stl") == "p-freecad-standard.stl"


def test_table_override_changes_the_choice_without_renaming():
    files = ["p-openscad-fine.stl", "p-freecad-standard.stl"]
    assert quality.select_best(files, "stl", table={"openscad.stl.fine": 99}) == "p-openscad-fine.stl"


def test_min_profile_filters_candidates():
    files = ["p-freecad-draft.stl", "p-freecad-standard.stl"]
    assert quality.select_best(files, "stl", min_profile="fine") is None
    assert quality.select_best(files, "stl", min_profile="standard") == "p-freecad-standard.stl"


def test_blender_render_is_the_best_png():
    files = ["p-freecad-fine.png", "p-blender-fine.png", "p-python-fine.png"]
    assert quality.select_best(files, "png") == "p-blender-fine.png"


def test_summary_format_uses_json_files():
    from cycax import quality

    assert quality.artifact_name("plate", "python", "standard", "summary") == "plate-python-standard.json"
    files = ["plate-python-standard.json", "plate-python-standard.step", "spec.json"]
    assert quality.select_best(files, "summary") == "plate-python-standard.json"


def test_unfold_is_only_the_dxf():
    from cycax import quality

    files = ["tray_unfold-freecad-standard.step", "tray-freecad-standard.step", "tray_unfold-freecad-standard.dxf"]
    assert quality.select_best(files, "step") == "tray-freecad-standard.step"
    assert quality.select_best(files, "dxf") == "tray_unfold-freecad-standard.dxf"
    assert quality.select_best(["tray_unfold-freecad-standard.step"], "step") is None
