#!/usr/bin/env python3
import hashlib
from pathlib import Path

from cycax.cycad import SheetMetal

def fancy_edge(edge_loc): 
    sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no="sheet_bevel")
    
    sheet.beveled_edge(edge_type="round", side1="FRONT", side2="RIGHT", size=3)
    sheet.beveled_edge(edge_type="round", side1="FRONT", side2="LEFT", size=3)
    sheet.beveled_edge(edge_type="round", side1="BACK", side2="LEFT", size=3)
    sheet.beveled_edge(edge_type="round", side1="BACK", side2="RIGHT", size=3)
        
    sheet.beveled_edge(edge_type="round", side1="TOP", side2="FRONT", size=3)
    sheet.beveled_edge(edge_type="round", side1="BOTTOM", side2="FRONT", size=3)
    sheet.beveled_edge(edge_type="round", side1="BACK", side2="TOP", size=3)
    sheet.beveled_edge(edge_type="round", side1="BACK", side2="BOTTOM", size=3)

    sheet.beveled_edge(edge_type="round", side1="LEFT", side2="TOP", size=3)
    sheet.beveled_edge(edge_type="round", side1="LEFT", side2="BOTTOM", size=3)
    sheet.beveled_edge(edge_type="round", side1="RIGHT", side2="TOP", size=3)
    sheet.beveled_edge(edge_type="round", side1="RIGHT", side2="BOTTOM", size=3)
    
    edge_loc.mkdir()
    sheet.save(path=edge_loc)
    sheet.render("preview3d")
    sheet.render("freecad")

    sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no="sheet_taper")
    sheet.beveled_edge(edge_type="chamfer", side1="FRONT", side2="LEFT", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="FRONT", side2="RIGHT", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="LEFT", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="RIGHT", size=3)

    sheet.beveled_edge(edge_type="chamfer", side1="TOP", side2="FRONT", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="BOTTOM", side2="FRONT", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="TOP", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="BOTTOM", size=3)

    sheet.beveled_edge(edge_type="chamfer", side1="LEFT", side2="TOP", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="LEFT", side2="BOTTOM", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="RIGHT", side2="TOP", size=3)
    sheet.beveled_edge(edge_type="chamfer", side1="RIGHT", side2="BOTTOM", size=3)
    sheet.save(path=edge_loc)
    
    sheet.save(path=edge_loc)
    sheet.render("preview3d")
    sheet.render("freecad")


def hex_code(edge_path, filename:str, ext:str):
    """Test save on assembly and parts."""

    filename = edge_path / filename / f"{filename}{ext}"

    content = filename.read_text()
    hash_value_file = hashlib.sha256(content.encode("UTF-8")).hexdigest()
    
    return hash_value_file

    
def test_edge(tmp_path):

    edge_loc = tmp_path / "edge"
    
    fancy_edge(edge_loc)
    
    hash_value_face_scad = hex_code(edge_path = edge_loc, filename = "sheet_bevel", ext = ".scad")
    assert hash_value_face_scad == "38c839069c2bf7a697245006ad029e78d0043a0cb8ef6a55ed8f41de07ba048d"
    
    hash_value_face_stl = hex_code(edge_path = edge_loc, filename = "sheet_bevel", ext = ".stl")
    assert hash_value_face_stl == "c892edb3a703bc73451939074edd2ab1ce1dad683688639b67bb8a9f6d08c98d"
    
    hash_value_face_stl = hex_code(edge_path = edge_loc, filename = "sheet_bevel", ext = ".json")
    assert hash_value_face_stl == "edd35c667ecda6d511aa1f504645e0032e82f3a54f7e5ba604025c5ac9fcf56d"
    
    hash_value_face_scad = hex_code(edge_path = edge_loc, filename = "sheet_taper", ext = ".scad")
    assert hash_value_face_scad == "87a686e5e378a0c3623d2414a89edbc753a93775f26ca509f8fd51a4774b9f92"
    
    hash_value_face_stl = hex_code(edge_path = edge_loc, filename = "sheet_taper", ext = ".stl")
    assert hash_value_face_stl == "d54290cb0918cbb3c89481422b5d7b1baf014b1d6c0c612a62fa25d42fd141f7"
    
    hash_value_face_stl = hex_code(edge_path = edge_loc, filename = "sheet_taper", ext = ".json")
    assert hash_value_face_stl == "0e2d4c49d81f51cd933756c78d9cdd51a75ab47ce2e7def7b4c251d0394464f4"
    
    
    
   
            


