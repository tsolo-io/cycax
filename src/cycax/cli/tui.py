"""Text User Interface."""

import logging

import rich
import typer
from rich.console import Console
from rich.table import Table

console = Console()


def print_table(ctx: typer.Context, data: list[dict], title: str):
    if ctx.obj.json:
        rich.print_json(data=data)
    elif data:
        keys = dict(data[0]).keys()
        title_keys = [key.title().replace("_", " ") for key in keys]
        table = Table(*title_keys, title=title)
        for row in data:
            _row = dict(row)
            table.add_row(*[str(_row[key]) for key in keys])
        console.print(table)
    else:
        console.print("No data to display.")


def print_kv(ctx: typer.Context, data: dict):
    """"""
    if data is None:
        logging.warning("No data to display.")
    elif ctx.obj.json:
        rich.print_json(data=data)
    else:
        table = Table("Key", "Value")
        for key, value in data.items():
            table.add_row(str(key), str(value))
        console.print(table)


def print_error(error, *, stop_on_error=True):
    """Print and Alert and then the error and exit the program.

    Raises:
        typer Exit exception
    """
    rich.print(f":warning: [bold red]Alert![/bold red] {error}")
    if stop_on_error:
        raise typer.Exit(1)
