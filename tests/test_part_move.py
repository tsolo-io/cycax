from cycax.cycad import Assembly, Print3D

# Tests the move method and cardinal_possition methods of a part.


def test_move():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = Print3D(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")

    assembly.add(mypart1)

    assert mypart1.moves == [0, 0, 0]

    mypart1.move(x=10)

    assert mypart1.moves == [10, 0, 0]

    mypart1.move(y=10)

    assert mypart1.moves == [10, 10, 0]

    mypart1.move(z=10)

    assert mypart1.moves == [10, 10, 10]

    mypart1.move(x=10, y=10, z=10)

    assert mypart1.moves == [20, 20, 20]


def test_at():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = Print3D(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")

    assembly.add(mypart1)

    assert mypart1.moves == [0, 0, 0]

    mypart1.at(x=10)

    assert mypart1.moves == [10, 0, 0]

    mypart1.at(y=10)

    assert mypart1.moves == [10, 10, 0]

    mypart1.at(z=10)

    assert mypart1.moves == [10, 10, 10]

    mypart1.at(x=10, y=10, z=10)

    assert mypart1.moves == [10, 10, 10]
