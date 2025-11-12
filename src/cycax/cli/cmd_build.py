import json
import logging
from pathlib import Path
from typing import Annotated

import typer

from cycax.cli.run import make_build_map
from cycax.cycad.assembly_openscad import AssemblyOpenSCAD
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


def load_cycax_json(filename: str) -> dict:
    _filename = Path(filename).expanduser().resolve().absolute()
    if not _filename.exists():
        msg = f"File {_filename} does not exist"
        raise FileNotFoundError(msg)
    data = json.loads(_filename.read_text())
    return _filename, data


@app.command("freecad")
def build_freecad(
    ctx: typer.Context,
    filename: Annotated[str, typer.Argument(help="A JSON file with CyCAx Features")],
):
    logging.info("Listing objects")
    build_order = make_build_map(filename)
    for build in sorted(build_order.values(), key=lambda x: x["index"]):
        _filename, data = load_cycax_json(build["path"])
        if data.get("features"):
            engine = PartEngineFreeCAD(name=data["name"], path=_filename.parent.parent)
            engine._json_file = _filename
            engine.build(None)
        else:
            logging.warning("No features found in JSON file")


def build_part(engine, part_json_file: Path):
    _filename, data = load_cycax_json(part_json_file)
    if data.get("features"):
        engine = PartEngineOpenSCAD(name=data["name"], path=_filename.parent.parent)
        engine._json_file = _filename
        files = engine.build(None)
        for file in files:
            logging.info("Created %s file %s", file["type"], file["file"])
    else:
        logging.warning("No features found in JSON file")


@app.command("openscad")
def build_openscad(
    ctx: typer.Context,
    filename: Annotated[str, typer.Argument(help="A JSON file with CyCAx Features")],
):
    _filename, data = load_cycax_json(filename)
    build_part(PartEngineOpenSCAD, _filename)

    if data.get("parts"):
        engine = AssemblyOpenSCAD(name=data["name"])
        engine.set_path(_filename.parent)
        engine._json_file = _filename
        for part in data["parts"]:
            _part_filename = _filename.parent / part["part_no"] / f"{part['part_no']}.json"
            build_part(PartEngineOpenSCAD, _part_filename)
            engine.add(part)
        engine.build(_filename.parent)
    else:
        logging.warning("No parts found in JSON file")
