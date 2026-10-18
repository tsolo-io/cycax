# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The CyCAx JSON spec (version 2): models, validation, hashing and JSON Schema.

The spec is the contract between the Python DSL, the CLI and every worker. See
docs/content/data-file-spec.md.

Version 2 rules:
- Every spec has `spec_version` (2), `kind` ("part" or "assembly") and `name`.
- Geometry fields stay at the top level (`features`/`subtract` for parts, `parts` for
  assemblies). Information that does not change the shape (description, notes, material,
  colour, manufacturing, doc_view) is in `meta` objects.
- The cache hash is computed with every `meta` key removed, at any depth, so changing the
  text, the material or a colour never causes a rebuild.
"""

from cycax.spec.hashing import spec_hash, strip_meta
from cycax.spec.models import (
    SPEC_VERSION,
    AssemblySpec,
    PartSpec,
    SpecVersionError,
    json_schemas,
    validate_spec,
)

__all__ = [
    "SPEC_VERSION",
    "AssemblySpec",
    "PartSpec",
    "SpecVersionError",
    "json_schemas",
    "spec_hash",
    "strip_meta",
    "validate_spec",
]
