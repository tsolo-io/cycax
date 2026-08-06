# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
import shutil
from pathlib import Path
from typing import Annotated

import typer

from cycax.cli.fs_utils import format_size, get_all_subdirectory_stats, guess_name_cache_directory_name
from cycax.cli.tui import print_table

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


def get_cache_list(
    cache_path: Path, *, reverse: bool = False, ctime: bool = False, atime: bool = False
) -> list[dict[str, int]]:
    cache_store = []
    cache_size = get_all_subdirectory_stats(cache_path)
    if ctime:
        logging.info("Sorting by creation time")
        sort_by = "ctime"
    elif atime:
        logging.info("Sorting by access time")
        sort_by = "atime"
    else:
        sort_by = "size"
    for path in sorted(cache_size, key=lambda a: cache_size[a].get(sort_by), reverse=not reverse):
        cache = cache_size[path]
        size = cache["size"]
        _cache = {
            "id": path.name,
            "name": guess_name_cache_directory_name(path),
            "path": path,
            "size": format_size(size),
            "Created": datetime.datetime.fromtimestamp(cache["ctime"], tz=datetime.timezone.utc)
            .astimezone()
            .strftime("%Y-%m-%d %H:%M:%S"),
            "Last Accessed": datetime.datetime.fromtimestamp(cache["atime"], tz=datetime.timezone.utc)
            .astimezone()
            .strftime("%Y-%m-%d %H:%M:%S"),
        }
        cache_store.append(_cache)
    return cache_store


@app.command("list")
def cache_list(
    ctx: typer.Context,
    *,
    reverse: Annotated[bool, typer.Option(help="Change the sort order")] = False,
    ctime: Annotated[bool, typer.Option(help="Sort by creation time")] = False,
    atime: Annotated[bool, typer.Option(help="Sort by access time")] = False,
):
    """List all the caches.

    Caches can be sorted by size, creation time, or access time.
    Sort order can be reversed by using the --reverse option.
    """
    cache_path = ctx.obj.config.cache_directory
    cache_stat_list = get_cache_list(cache_path, reverse=reverse, ctime=ctime, atime=atime)
    print_table(ctx, cache_stat_list, "Cache Summary")


@app.command("open")
def cache_open(
    cache_id: Annotated[str, typer.Argument(help="ID of the cache to open")],
    ctx: typer.Context,
):
    """Open the cache directory in the default file manager."""
    cache_path = ctx.obj.config.cache_directory / cache_id

    if not cache_path.exists():
        typer.echo(f"Cache '{cache_id}' not found.")
        raise typer.Exit(code=1)

    typer.launch(str(cache_path))


@app.command("remove")
def cache_remove(
    ctx: typer.Context,
    *,
    cache_id: Annotated[str, typer.Argument(help="ID of the cache to remove")],
    oldest: Annotated[bool, typer.Option(help="Remove the oldest cache entry")] = False,
    largest: Annotated[bool, typer.Option(help="Remove the largest cache entry")] = False,
    all_entries: Annotated[bool, typer.Option("--all", help="Remove all cache entries")] = False,
):
    """Remove a cached build of a part.

    Removing the cache will force a rebuild on the next run for a matching cache ID.
    """
    if all_entries:
        cache_stat_list = get_cache_list(ctx.obj.config.cache_directory)
        for cache in cache_stat_list:
            cache_path = ctx.obj.config.cache_directory / cache["id"]
            shutil.rmtree(cache_path)
            logging.warning(f"Cache '{cache['id']}' removed.")
        return  # Nothing else to remove

    if oldest:
        cache_stat_list = get_cache_list(ctx.obj.config.cache_directory, ctime=True)
        oldest_cache = cache_stat_list[0]
        oldest_cache_path = ctx.obj.config.cache_directory / oldest_cache["id"]
        shutil.rmtree(oldest_cache_path)
        logging.warning(f"Oldest cache '{oldest_cache['id']}' removed.")

    if largest:
        cache_stat_list = get_cache_list(ctx.obj.config.cache_directory)
        largest_cache = cache_stat_list[0]
        largest_cache_path = ctx.obj.config.cache_directory / largest_cache["id"]
        shutil.rmtree(largest_cache_path)
        logging.warning(f"Largest cache '{largest_cache['id']}' removed.")

    if cache_id.startswith("."):
        typer.echo("Invalid cache ID")
        raise typer.Exit(code=1)

    cache_path = ctx.obj.config.cache_directory / cache_id
    cache_path = cache_path.resolve().absolute().expanduser()

    if not cache_path.exists():
        typer.echo(f"Cache '{cache_path}' not found.")
        raise typer.Exit(code=1)

    if cache_path.parent != ctx.obj.config.cache_directory:
        typer.echo(f"Cannot delete '{cache_path}', not in {ctx.obj.config.cache_directory}.")
        raise typer.Exit(code=1)

    shutil.rmtree(cache_path)
    logging.warning(f"Cache '{cache_id}' removed.")
