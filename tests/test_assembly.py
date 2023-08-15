from cycax.cycad import Assembly, SheetMetal


def test_part_names():
    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="test_part")
    mypart2 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="test_part")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assert list(assembly.parts.keys()) == ["test_part_1", "test_part_2"], "The parts names are correct."
    assert mypart1 is assembly.get_part("test_part_1"), "The same part is return when accessed through get_part."
    assert mypart2 is assembly.get_part("test_part_2"), "The same part is return when accessed through get_part."
    parts = assembly.get_parts_by_no("test_part")
    assert mypart1 in parts, "Part1 is in parts list."
    assert mypart2 in parts, "Part2 is in parts list."
