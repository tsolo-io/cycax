from cycax.cycad import Assembly, SheetMetal

# Tests that with mulitple roations the expected outcome is still achieved


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
    assembly.rotateFreezeLeft(mypart1)
    assembly.rotateFreezeFront(mypart1)
    assembly.rotateFreezeTop(mypart1)
    assembly.rotateFreezeLeft(mypart1)
    assembly.rotateFreezeLeft(mypart1)

    assembly.rotateFreezeLeft(mypart2)
    assembly.rotateFreezeFront(mypart2)
    assembly.rotateFreezeTop(mypart2)

    assembly.rotateFreezeLeft(mypart3)
    assembly.rotateFreezeFront(mypart3)

    assembly.rotateFreezeFront(mypart4)
    assembly.rotateFreezeLeft(mypart4)

    assembly.rotateFreezeTop(mypart5)
    assembly.rotateFreezeFront(mypart5)

    assembly.rotateFreezeFront(mypart6)
    assembly.rotateFreezeTop(mypart6)

    assembly.rotateFreezeLeft(mypart7)
    assembly.rotateFreezeTop(mypart7)

    assembly.rotateFreezeTop(mypart8)
    assembly.rotateFreezeLeft(mypart8)

    assembly.rotateFreezeLeft(mypart9)
    assembly.rotateFreezeFront(mypart9)
    assembly.rotateFreezeTop(mypart9)
    assembly.rotateFreezeLeft(mypart9)
    assembly.rotateFreezeFront(mypart9)
    assembly.rotateFreezeTop(mypart9)

    assembly_def = assembly.export()
    assert assembly_def["parts"][0]["rotate"] == [{"axis":"x", "angle":90}, {"axis":"y", "angle":90}, {"axis":"z", "angle":90}, {"axis":"x", "angle":90}, {"axis":"x", "angle":90}]
    assert assembly_def["parts"][1]["rotate"] == [{"axis":"x", "angle":90}, {"axis":"y", "angle":90}, {"axis":"z", "angle":90}]
    assert assembly_def["parts"][2]["rotate"] == [{"axis":"x", "angle":90}, {"axis":"y", "angle":90}]
    assert assembly_def["parts"][3]["rotate"] == [{"axis":"y", "angle":90}, {"axis":"x", "angle":90}]
    assert assembly_def["parts"][4]["rotate"] == [{"axis":"z", "angle":90}, {"axis":"y", "angle":90}]
    assert assembly_def["parts"][5]["rotate"] == [{"axis":"y", "angle":90}, {"axis":"z", "angle":90}]
    assert assembly_def["parts"][6]["rotate"] == [{"axis":"x", "angle":90}, {"axis":"z", "angle":90}]
    assert assembly_def["parts"][7]["rotate"] == [{"axis":"z", "angle":90}, {"axis":"x", "angle":90}]
    assert assembly_def["parts"][8]["rotate"] == [{"axis":"x", "angle":90}, {"axis":"y", "angle":90}, {"axis":"z", "angle":90}, {"axis":"x", "angle":90}, {"axis":"y", "angle":90}, {"axis":"z", "angle":90}]
