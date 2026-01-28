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
    cmd_cache,
    cmd_config,
)
from cycax.cli.config import Settings
from cycax.cli.run import CycaxCompiler

FORMAT = "%(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)
app.add_typer(cmd_config.app, name="config", help="Manage the CyCAx CLI config.")
app.add_typer(cmd_build.app, name="build", help="Build parts and assemblies.")
app.add_typer(cmd_cache.app, name="cache", help="Manage the CyCAx cache.")


@app.command("compile")
def compile_cmd(
    ctx: typer.Context,
    filename: Annotated[str, typer.Argument(help="A Python file to run with the CyCAx Code")],
):
    """Compile a Python file with the CyCAx Code.

    Creates JSON files, no CAD models are created.
    """
    compiler = CycaxCompiler(
        root_build_dir=ctx.obj.config.build_directory,
        cache_dir=ctx.obj.config.cache_directory,
        settings=dict(ctx.obj.config),
    )
    compiler.add_src(filename)
    compiler.compile()


@app.command()
def send(
    ctx: typer.Context,
    filename: Annotated[str, typer.Argument(help="A Python file to run with the CyCAx Code")],
):
    """Send the compiled JSON files to the CyCAx server to be compiled into usable CAD models."""
    compiler = CycaxCompiler(
        root_build_dir=ctx.obj.config.build_directory,
        cache_dir=ctx.obj.config.cache_directory,
        settings=dict(ctx.obj.config),
    )
    compiler.add_src(filename)
    compiler.compile()
    # compile.send(ctx.obj.config.nats_dsn)


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
        conf_file = Path(".cycax_config.json").expanduser().resolve().absolute()

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
