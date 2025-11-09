"""View the config."""

from typing import Annotated

import rich
import typer
from pydantic import ValidationError

from cycax.cli.tui import print_error, print_kv, print_table

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


@app.command()
def show(
    ctx: typer.Context,
    *,
    secrets: Annotated[bool, typer.Option(help="Include the secrets")] = False,
):
    """Show the config values."""
    if ctx.obj.json:
        # Gives colour coding and proper JSON, works with jq.
        rich.print_json(ctx.obj.config.model_dump_json())
    else:
        data = []
        for key, value in ctx.obj.config.model_dump().items():
            if key in ("cycax_config",):
                continue
            field_info = ctx.obj.config.model_fields[key]
            description = field_info.description
            row = {
                "key": key,
                "value": value,
                "description": description if description else "",
            }
            if not secrets and value:
                # If we hide secrets and we have a value.
                if key.endswith("_password") or key.endswith("_secret_key"):
                    # If the key is for a secret lets hide the value.
                    row["value"] = "*******"
            data.append(row)
        print_table(ctx, data, "Configuration")


@app.command("get")
def get_value(ctx: typer.Context, key: str):
    """Get a config value."""
    print_kv(ctx, {key: getattr(ctx.obj.config, key)})


@app.command("set")
def set_value(ctx: typer.Context, key: str, value: str):
    """Set a config value."""
    if key == "cycax_config":
        print_error(
            "Cannot change cycax_config file path through the CLI, "
            "use --cycax_config or cycax_CONFIG environmental variable."
        )
    try:
        setattr(ctx.obj.config, key, value)
        print_kv(ctx, {key: getattr(ctx.obj.config, key)})
        ctx.obj.config.save()
    except ValidationError as error:
        print_error(error)
