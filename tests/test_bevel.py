import hashlib
from pathlib import Path
from tests.shared import hex_code_check

from cycax.cycad import SheetMetal



def fancy_edge(edge_loc, edge_type:str, part_no:str):
    sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no=part_no)

    sheet.beveled_edge(edge_type=edge_type, side1="FRONT", side2="RIGHT", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="FRONT", side2="LEFT", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="BACK", side2="LEFT", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="BACK", side2="RIGHT", size=3)

    sheet.beveled_edge(edge_type=edge_type, side1="TOP", side2="FRONT", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="BOTTOM", side2="FRONT", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="BACK", side2="TOP", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="BACK", side2="BOTTOM", size=3)

    sheet.beveled_edge(edge_type=edge_type, side1="LEFT", side2="TOP", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="LEFT", side2="BOTTOM", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="RIGHT", side2="TOP", size=3)
    sheet.beveled_edge(edge_type=edge_type, side1="RIGHT", side2="BOTTOM", size=3)

    sheet.save(path=edge_loc)
    sheet.render("preview3d")
    sheet.render("freecad")


def test_edge(tmp_path):
    #This test checks that the two designs of beveled edges are being produced as they should.
    edge_loc = tmp_path

    fancy_edge(edge_loc, edge_type="round", part_no="sheet_round")
    fancy_edge(edge_loc, edge_type="chamfer", part_no="sheet_chamfer")

    hex_code_check(path=edge_loc, filename="sheet_round", ext=".scad", hex_code = "38c839069c2bf7a697245006ad029e78d0043a0cb8ef6a55ed8f41de07ba048d")
    

    hex_code_check(path=edge_loc, filename="sheet_round", ext=".stl", hex_code = "c892edb3a703bc73451939074edd2ab1ce1dad683688639b67bb8a9f6d08c98d")
     

    hex_code_check(path=edge_loc, filename="sheet_round", ext=".json", hex_code = "c7f71ccaf8ae33bec2ba3744c030ac0c161edfb677b3d1050e239fae19a133e1")
     

    hex_code_check(path=edge_loc, filename="sheet_chamfer", ext=".scad", hex_code = "57a2817114160c1eb1cb4724860764d1406ecc942ecbcfa8486da35e26e36797")
    

    hex_code_check(path=edge_loc, filename="sheet_chamfer", ext=".stl", hex_code = "d54290cb0918cbb3c89481422b5d7b1baf014b1d6c0c612a62fa25d42fd141f7")
    

    hex_code_check(path=edge_loc, filename="sheet_chamfer", ext=".json", hex_code = "03eb89beb1a07aef9524fa6bbcd8da4103c0b453e793b3d94639e0ed85770f1e")

