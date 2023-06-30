from cycax.cycad import Assembly, SheetMetal

# Tests the rotation of a part.


def test_level():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")
    mypart2 = SheetMetal(x_size=length, y_size=width, z_size=thickness, part_no="part-test2")
 
    assembly.add(mypart1)
    assembly.add(mypart2)
    
    assembly.level(mypart1.bottom, mypart2.bottom)
    
    assert mypart1.moves == mypart2.moves
    
    assembly.level(mypart1.right, mypart2.right)
    
    assert mypart1.moves == mypart2.moves
    
    assembly.level(mypart1.front, mypart2.front)
    
    assert mypart1.moves == mypart2.moves
    
    assembly.level(mypart1.bottom, mypart2.top)
    
    assert mypart1.moves == [0,0,2]
    
    assembly.level(mypart1.left, mypart2.right)
    
    assert mypart1.moves == [1000, 0, 2]
    
    assembly.level(mypart1.front, mypart2.back)
    
    assert mypart1.moves == [1000, 100, 2]
    
    assembly.level(mypart1.top, mypart2.bottom)
    
    assert mypart1.moves == [1000,100,-2]
    
    assembly.level(mypart1.right, mypart2.left)
    
    assert mypart1.moves == [-1000, 100, -2]
    
    assembly.level(mypart1.back, mypart2.front)
    
    assert mypart1.moves == [-1000, -100, -2]


# TODO: Add tests that rotate the part in multiple directions.
# TODO: Add tests that level then rotate a part. If rotate after level is not allowed then err.
# TODO: Test Print3D
