# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, SheetMetal

# Tests that with multiple roations the expected outcome is still achieved


def test_rotate():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")
    mypart2 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test2")
    mypart3 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test3")
    mypart4 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test4")
    mypart5 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test5")
    mypart6 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test6")
    mypart7 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test7")
    mypart8 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test8")
    mypart9 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test9")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assembly.add(mypart3)
    assembly.add(mypart4)
    assembly.add(mypart5)
    assembly.add(mypart6)
    assembly.add(mypart7)
    assembly.add(mypart8)
    assembly.add(mypart9)

    # Test that a part is rotated multiple times.
    mypart1.rotate_freeze_left()
    mypart1.rotate_freeze_front()
    mypart1.rotate_freeze_top()
    mypart1.rotate_freeze_left()
    mypart1.rotate_freeze_left()
    
    mypart2.rotate_freeze_left()
    mypart2.rotate_freeze_front()
    mypart2.rotate_freeze_top()

    mypart3.rotate_freeze_left()
    mypart3.rotate_freeze_front()

    mypart4.rotate_freeze_front()
    mypart4.rotate_freeze_left()

    mypart5.rotate_freeze_top()
    mypart5.rotate_freeze_front()

    mypart6.rotate_freeze_front()
    mypart6.rotate_freeze_top()

    mypart7.rotate_freeze_left()
    mypart7.rotate_freeze_top()

    mypart8.rotate_freeze_top()
    mypart8.rotate_freeze_left()

    mypart9.rotate_freeze_left()
    mypart9.rotate_freeze_front()
    mypart9.rotate_freeze_top()
    mypart9.rotate_freeze_left()
    mypart9.rotate_freeze_front()
    mypart9.rotate_freeze_top()

    assembly_def = assembly.export()
    assert assembly_def["parts"][0]["rotate"] == [
        {"axis": "x", "angle": 90},
        {"axis": "y", "angle": 90},
        {"axis": "z", "angle": 90},
        {"axis": "x", "angle": 90},
        {"axis": "x", "angle": 90},
    ]
    assert assembly_def["parts"][1]["rotate"] == [
        {"axis": "x", "angle": 90},
        {"axis": "y", "angle": 90},
        {"axis": "z", "angle": 90},
    ]
    assert assembly_def["parts"][2]["rotate"] == [{"axis": "x", "angle": 90}, {"axis": "y", "angle": 90}]
    assert assembly_def["parts"][3]["rotate"] == [{"axis": "y", "angle": 90}, {"axis": "x", "angle": 90}]
    assert assembly_def["parts"][4]["rotate"] == [{"axis": "z", "angle": 90}, {"axis": "y", "angle": 90}]
    assert assembly_def["parts"][5]["rotate"] == [{"axis": "y", "angle": 90}, {"axis": "z", "angle": 90}]
    assert assembly_def["parts"][6]["rotate"] == [{"axis": "x", "angle": 90}, {"axis": "z", "angle": 90}]
    assert assembly_def["parts"][7]["rotate"] == [{"axis": "z", "angle": 90}, {"axis": "x", "angle": 90}]
    assert assembly_def["parts"][8]["rotate"] == [
        {"axis": "x", "angle": 90},
        {"axis": "y", "angle": 90},
        {"axis": "z", "angle": 90},
        {"axis": "x", "angle": 90},
        {"axis": "y", "angle": 90},
        {"axis": "z", "angle": 90},
    ]
