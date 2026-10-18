# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Write the JSON Schema files: `python -m cycax.spec`."""

import json
from pathlib import Path

from cycax.spec.models import json_schemas

if __name__ == "__main__":
    out_dir = Path(__file__).parent / "schemas"
    for filename, schema in json_schemas().items():
        (out_dir / filename).write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {out_dir / filename}")  # noqa: T201
