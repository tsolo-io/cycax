from cycax.cycad import Assembly, Print3D

# Tests the rotation of a part.


def test_merge():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = Print3D(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")
    mypart2 = Print3D(x_size=length, y_size=width, z_size=thickness, part_no="part-test2")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assembly.merge(mypart1, mypart2)
     
    assert mypart1.features == mypart2.features
    assert mypart2.move_holes == mypart1.move_holes
 

# TODO: Add tests that level then rotate a part. If rotate after level is not allowed then err.
