from cycax.cycad import Assembly, SheetMetal

# Tests the rotation of a part.


def test_rotate():
    # Test the base functionality of rotate.
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

    # Test that a part is rotated multiple times.
    for count in range(1, 4):
        assembly.rotateFreezeLeft(mypart2)
        assembly.rotateFreezeFront(mypart3)
        assembly.rotateFreezeTop(mypart4)
        assembly_def = assembly.export()
        assert assembly_def["parts"][0]["rotate"] == []
        assert assembly_def["parts"][1]["rotate"] == [{"axis":"x", "angle":90}] * count
        assert assembly_def["parts"][2]["rotate"] == [{"axis":"y", "angle":90}]  * count
        assert assembly_def["parts"][3]["rotate"] == [{"axis":"z", "angle":90}]  * count


def test_rotate_side():
    length = 10
    width = 800
    thickness = 200

    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")
    mypart2 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test2")
    mypart3 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test3")
    mypart4 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test4")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assembly.add(mypart3)
    assembly.add(mypart4)

    # Test that a part is rotated multiple times.
    for count in range(1, 4):
        # assembly.rotateFreezeLeft(mypart2)
        mypart2.left.rotate()
        # assembly.rotateFreezeFront(mypart3)
        mypart3.front.rotate()
        # assembly.rotateFreezeTop(mypart4)
        mypart4.top.rotate()
        assembly_def = assembly.export()
        assert assembly_def["parts"][0]["rotate"] == []
        assert assembly_def["parts"][1]["rotate"] == [{"axis":"x", "angle":90}] * count
        assert assembly_def["parts"][2]["rotate"] == [{"axis":"y", "angle":90}]  * count
        assert assembly_def["parts"][3]["rotate"] == [{"axis":"z", "angle":90}]  * count


# TODO: Add tests that rotate the part in multiple directions.
# TODO: Add tests that level then rotate a part. If rotate after level is not allowed then err.
# TODO: Test Print3D
