from cycax.cycad import Assembly, SheetMetal

# Test that if the part is levelled and rotated or rotated and then move the same assembly will be created.


def test_move_level():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")
    mypart2 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test2")
    mypart3 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test3")
    mypart4 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test4")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assembly.add(mypart3)
    assembly.add(mypart4)

    mypart4.move(100, 100, 100)

    # Test that a part is rotated multiple times.
    assembly.rotateFreezeLeft(mypart1)
    assembly.rotateFreezeFront(mypart1)
    assembly.rotateFreezeTop(mypart1)

    assembly.rotateFreezeLeft(mypart3)
    assembly.rotateFreezeFront(mypart3)
    assembly.rotateFreezeTop(mypart3)

    assembly.level(mypart3.bottom, mypart4.top)

    assembly.rotateFreezeLeft(mypart1)
    assembly.rotateFreezeFront(mypart1)
    assembly.rotateFreezeTop(mypart1)

    assembly.rotateFreezeLeft(mypart3)
    assembly.rotateFreezeFront(mypart3)
    assembly.rotateFreezeTop(mypart3)

    assembly.level(mypart3.bottom, mypart2.top)
    assembly.level(mypart1.bottom, mypart2.top)

    assembly_def = assembly.export()
    assert assembly_def["parts"][0]["position"] == assembly_def["parts"][2]["position"]
