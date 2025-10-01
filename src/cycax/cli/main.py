"""A utility CLI for interfacing with CyCAx."""

import importlib
import importlib.util
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any

import typer
from rich.logging import RichHandler

from cycax.cli import (
    cmd_config,
)
from cycax.cli.config import Settings

FORMAT = "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
app.add_typer(cmd_config.app, name="config", help="Manage the CyCAx CLI config.")

FUNCTION_NAMES = [
    "assemble",
    "parts",
    "cycax_assemble",
    "cycax_parts",
    "cycax_part",
]  # TODO: Decide on these, maybe only support cycax_ prefixes.


def run_function(file_path: Path, function_name: str | None = None) -> Path:
    try:
        spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if function_name is None:
            for _function_name in FUNCTION_NAMES:
                if hasattr(module, _function_name):
                    function_name = _function_name
                    break
        if function_name is None:
            logging.error("No function found in file %s, looked for %s", file_path, FUNCTION_NAMES)
            raise typer.Exit(code=1)
        elif not hasattr(module, function_name):
            logging.error("Error finding function %s in file %s", function_name, file_path)
            raise typer.Exit(code=1)

        function = getattr(module, function_name)
        result = function()
        return result
    except Exception as error:
        logging.error("Error running function %s from file %s: %s", function_name, file_path, error)
        raise typer.Exit(code=1) from error


def run_compile(filename: Path, function_name: str | None = None, build_dir: Path = Path("./build")):
    files = []
    cycax_build = run_function(filename, function_name)
    if not isinstance(cycax_build, list):
        cycax_build = [cycax_build]

    for build in cycax_build:
        # TODO: Check the type
        build_file = build.save(build_dir)
        files.append(build_file)

    return files


def cmd_input_scrubber(filename: str, build_dir: str) -> dict[str, Any]:
    if ":" in filename:
        filename, function_name = filename.split(":", 1)
    else:
        function_name = None
    _filename = Path(filename).expanduser().resolve().absolute()
    if not _filename.exists():
        msg = f"File {_filename} does not exist."
        raise FileNotFoundError(msg)
    return {"filename": _filename, "build_dir": Path(build_dir), "function_name": function_name}


@app.command("compile")
def compile_cmd(
    filename: Annotated[str, typer.Argument(help="A Python file to run with the CyCAx Code")],
    build_dir: Annotated[str, typer.Option(help="The directory to save the build to")] = "./build",
):
    fields = cmd_input_scrubber(filename, build_dir)
    if fields["filename"].suffix != ".py":
        msg = f"File {fields['filename']} is not a Python file."
        raise ValueError(msg)
    run_compile(filename=fields["filename"], function_name=fields["function_name"], build_dir=fields["build_dir"])


@app.command()
def build(
    filename: Annotated[str, typer.Argument(help="A Python file to run with the CyCAx Code")],
    build_dir: Annotated[str, typer.Option(help="The directory to save the build to")] = "./build",
):
    json_files = []
    fields = cmd_input_scrubber(filename, build_dir)
    if fields["filename"].suffix == ".py":
        json_files = run_compile(
            filename=fields["filename"], function_name=fields["function_name"], build_dir=fields["build_dir"]
        )
    elif fields["filename"].suffix == ".json":
        json_files = [fields["filename"]]
    elif fields["filename"].is_dir():
        json_files = [Path(f) for f in fields["filename"].iterdir() if f.suffix == ".json"]
    else:
        logging.error("The path %s is not a Python file, JSON file, or directory.", filename)
        raise typer.Exit(code=1)

    for json_file in json_files:
        _json_file = json_file.expanduser().resolve().absolute()
        if not _json_file.exists():
            logging.error("The file %s does not exist.", _json_file)
            raise typer.Exit(code=1)
        logging.info("Building %s", _json_file)
        # build_json(json_file, build_dir)


def conf_file_selector(cycax_config: str | None = None) -> Path:
    """Select the appropriate configuration file.

    If CyCAx_config is provided, use it. Otherwise, use the default configuration file.

    Args:
        CyCAx_config (str | None): The path to the configuration file.

    Returns:
        Path: The path to the selected configuration file.
    """
    if cycax_config:
        conf_file = Path(cycax_config).expanduser().resolve().absolute()
    else:
        conf_file = Path("~/.config/cycax/config.json").expanduser().resolve().absolute()

    if conf_file.exists():
        logging.info("Using configuration file: %s", conf_file)
    else:
        logging.warning("Creating configuration file: %s", conf_file)
        conf_file.parent.mkdir(parents=True, exist_ok=True)
        conf_file.write_text(json.dumps({}))

    return conf_file


@app.callback()
def main(
    ctx: typer.Context,
    *,
    cycax_config: str = typer.Option(None, envvar="CYCAX_CONFIG", help="Path to the configuration file."),
    json: bool = typer.Option(False, help="Output in JSON format."),
):
    if json:
        # Drop the log level to WARNING.
        logging.getLogger().setLevel(logging.WARNING)
    settings = Settings(cycax_config=conf_file_selector(cycax_config))
    ctx.obj = SimpleNamespace(config=settings, json=json)


if __name__ == "__main__":
    app()
