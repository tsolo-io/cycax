# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# Assembly JSON must carry the real part hashes (the cache key the workers look parts up by).
import json

from cycax.cycad import Assembly, SheetMetal
from cycax.spec import spec_hash


def test_parts_with_the_same_name_get_different_hashes():
    assembly = Assembly("pair")
    small = SheetMetal(part_no="plate", x_size=10, y_size=10, z_size=2)
    big = SheetMetal(part_no="plate", x_size=40, y_size=10, z_size=2)
    assembly.add(small)
    assembly.add(big)
    hashes = [part["hash"] for part in assembly.export()["parts"]]
    assert all(hashes)
    assert len(set(hashes)) == 2  # noqa: PLR2004


def test_assembly_hash_matches_the_saved_part_json(tmp_path):
    assembly = Assembly("single")
    part = SheetMetal(part_no="plate", x_size=10, y_size=20, z_size=2)
    part.top.hole(pos=(5, 5), diameter=3)
    assembly.add(part)
    part_file = part.save(tmp_path)
    # Hash of the data in the saved file, computed the way the CLI and cycax-send do it.
    expected = spec_hash(json.loads(part_file.read_text()))
    assert assembly.export()["parts"][0]["hash"] == expected


def test_an_explicit_hash_is_kept():
    assembly = Assembly("explicit")
    part = SheetMetal(part_no="plate", x_size=10, y_size=20, z_size=2)
    part.hash = "abc123"
    assembly.add(part)
    assert assembly.export()["parts"][0]["hash"] == "abc123"
