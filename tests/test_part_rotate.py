from cycax.cycad import Assembly, SheetMetal

# Tests the rotation of a part.


def test_rotate():
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
    for angle in range(90, 721, 90):
        assembly.rotateFreezeLeft(mypart2)
        assembly.rotateFreezeFront(mypart3)
        assembly.rotateFreezeTop(mypart4)
        assembly_def = assembly.export()
        assert assembly_def[0]["rotate"] == [0, 0, 0]
        assert assembly_def[1]["rotate"] == [angle % 360, 0, 0]
        assert assembly_def[2]["rotate"] == [0, angle % 360, 0]
        assert assembly_def[3]["rotate"] == [0, 0, angle % 360]

    # Test that after being rotate full circle, twice, that the part is still the same.
    for i in range(1, 4):
        assert assembly_def[0]["rotate"] == assembly_def[i]["rotate"]
        assert assembly_def[0]["rotmax"] == assembly_def[i]["rotmax"]


# TODO: Add tests that rotate the part in multiple directions.
# TODO: Add tests that level then rotate a part. If rotate after level is not allowed then err.
# TODO: Test Print3D
