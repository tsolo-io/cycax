import json
import logging
from pathlib import Path
from typing import Annotated

import typer

from cycax.cli.run import CycaxCompiler, make_build_map
from cycax.cycad.assembly_openscad import AssemblyOpenSCAD
from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


@app.command("freecad")
def build_freecad(
    ctx: typer.Context,
    filename: Annotated[str, typer.Argument(help="A Python/JSON CyCAx code file or directory with CyCAx files.")],
):
    compiler = CycaxCompiler(
        root_build_dir=ctx.obj.config.build_directory,
        cache_dir=ctx.obj.config.cache_directory,
        settings=dict(ctx.obj.config),
    )
    compiler.add_src(filename)
    compiler.compile()

    for json_file in compiler.src_json:
        # If there are any JSON files that needs to be loaded, load them.
        compiler.load_json(json_file["filename"])

    # Loop through the build order and build the parts.
    from cycax.cycad.engines.part_freecad import bulk_build  # noqa PLC0415 Import here to make CLI faster
    from cycax.cycad.engines.engine_freecad import EngineFreeCAD

    write_back_to_cache = []
    freecad_part_list = []
    freecad_assembly_list = []
    for part in compiler.build_order():
        if not compiler.from_cache(part):
            if part["assembly"]:
                freecad_assembly_list.append(str(part["definition_file"]))
            else:
                write_back_to_cache.append(part)
                freecad_part_list.append(str(part["definition_file"]))

    if freecad_part_list:
        bulk_build(
            app_bin=compiler.settings["freecad_app"], path=compiler.settings["build_directory"], parts=freecad_part_list
        )
    if freecad_assembly_list:
        engine = EngineFreeCAD()
        engine.build_bulk(freecad_assembly_list)

    for part in write_back_to_cache:
        compiler.to_cache(part)


def load_cycax_json(filename: str) -> dict:
    _filename = Path(filename).expanduser().resolve().absolute()
    if not _filename.exists():
        msg = f"File {_filename} does not exist"
        raise FileNotFoundError(msg)
    data = json.loads(_filename.read_text())
    return _filename, data


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
