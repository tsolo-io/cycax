# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The one hash function for part and assembly specs (the cache key).

The CLI, the assembly export and the workers must agree on this value. It is xxh64 of the
orjson-serialised spec with every `meta` key removed (at any depth).
"""

from typing import Any

import orjson
import xxhash


def strip_meta(value: Any) -> Any:
    """Return a copy of `value` without any `meta` keys (recursively)."""
    if isinstance(value, dict):
        return {key: strip_meta(item) for key, item in value.items() if key != "meta"}
    if isinstance(value, list):
        return [strip_meta(item) for item in value]
    return value


def spec_hash(spec: dict) -> str:
    """Return the cache hash of a part or assembly spec (the dict that is saved as JSON)."""
    return xxhash.xxh64(orjson.dumps(strip_meta(spec))).hexdigest()
