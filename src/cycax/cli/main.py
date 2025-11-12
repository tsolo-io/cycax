"""A utility CLI for interfacing with CyCAx."""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated

import typer
from rich.logging import RichHandler

from cycax.cli import (
    cmd_build,
    cmd_config,
)
from cycax.cli.config import Settings
from cycax.cli.run import cmd_input_scrubber, make_build_map

FORMAT = "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
app.add_typer(cmd_config.app, name="config", help="Manage the CyCAx CLI config.")
app.add_typer(cmd_build.app, name="build", help="Build parts and assemblies.")

FUNCTION_NAMES = [
    "assemble",
    "parts",
    "cycax_assemble",
    "cycax_parts",
    "cycax_part",
]  # TODO: Decide on these, maybe only support cycax_ prefixes.


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
def send(
    filename: Annotated[str, typer.Argument(help="A Python file to run with the CyCAx Code")],
    build_dir: Annotated[str, typer.Option(help="The directory to save the build to")] = "./build",
    part_engine: Annotated[str, typer.Option(help="The directory to save the build to")] = "./build",
):
    """Send the compiled JSON files to the CyCAx server to be compiled into usable models."""
    build_order = make_build_map(filename, Path(build_dir))
    for _build in sorted(build_order.values(), key=lambda x: x["index"]):
        pass


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
