# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# Tests for the utilities of from CyCAD engines.
from cycax.cycad.engines.utils import check_source_hash, find_appimage


def test_check_source_hash(tmp_path):
    source_test_file = tmp_path / "mypart.json"
    target_test_file = tmp_path / "mypart.3d"
    hash_test_file = tmp_path / ".mypart.json.hash"
    assert not source_test_file.exists(), "There should be no source file."
    assert not target_test_file.exists(), "There should be no target file."
    assert not hash_test_file.exists(), "There should be no hash file."
    source_test_file.write_text("bla bla")
    # No hash file and no target file, expect True.
    assert check_source_hash(source_test_file, target_test_file), (
        "Should create the target since it is not there and there is no source hash file."
    )
    assert hash_test_file.exists(), "The hash file should be there."
    # No target file, expect True.
    assert check_source_hash(source_test_file, target_test_file), "Should create the target since it is not there."
    target_test_file.write_text("yes")
    # Target exists file and no update to source, expect False.
    assert not check_source_hash(source_test_file, target_test_file), "Should NOT create the target."
    hash_test_file.write_text("1")
    assert check_source_hash(source_test_file, target_test_file), "Should create the target since hash is different."


def test_find_appimage_picks_newest(tmp_path):
    apps = tmp_path / "Applications"
    apps.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    for name in ("FreeCAD_1.1.3-Linux-x86_64.AppImage", "FreeCAD_1.10.0-Linux-x86_64.AppImage", "OpenSCAD.AppImage"):
        (apps / name).touch()
    (other / "FreeCAD_26.3.0-Linux-x86_64-py311.AppImage").touch()

    assert find_appimage("FreeCAD", [tmp_path / "missing", apps]).name == "FreeCAD_1.10.0-Linux-x86_64.AppImage"
    assert find_appimage("FreeCAD", [apps, other]).name == "FreeCAD_26.3.0-Linux-x86_64-py311.AppImage"
    assert find_appimage("Blender", [apps, other]) is None
