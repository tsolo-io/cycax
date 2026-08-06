<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Cycax Data File Specification: V1

## Assembly JSON Structure

An assembly JSON file describes a collection of parts and their arrangement:

```json
{
  "name": "assembly_name",
  "parts": [
    {
      "part_no": "part_identifier",
      "position": [x, y, z],
      "rotate": [rx, ry, rz],
      "rotmax": [x_size, y_size, z_size],
      "colour": "color_name",
      "hash": "unique_identifier"
    }
  ]
}
```

## Part JSON Structure

A part JSON file describes an individual part with its features:

```json
{
  "name": "part_identifier",
  "features": [
    {
      "name": "polygon_name",
      "type": "add",
      "side": "side_name",
      "x": x_coordinate,
      "y": y_coordinate,
      "z": z_coordinate,
      "x_size": x_dimension,
      "y_size": y_dimension,
      "z_size": z_dimension,
      "center": false
    },
    {
      "type": "feature_type",
      "feature_specific_field": "feature_specific_value"
    }
  ],
  "subtract": [
    {
      "type": "feature_type",
      "feature_specific_field": "feature_specific_value"
    }
  ]
}
```

## Key Fields

- `name`: Unique identifier for the part or assembly
- `parts`: Array of part objects (assembly only)
- `part_no`: Identifier for the part type
- `position`: 3D coordinates [x, y, z]
- `rotate`: 3D rotation [rx, ry, rz] in degrees
- `rotmax`: Size dimensions [x_size, y_size, z_size]
- `colour`: Color specification
- `hash`: Unique identifier for caching
- `features`: List of feature objects added to the part
- `subtract`: List of feature objects for subtraction
- `type`: Type of feature (e.g., "add", "cylinder", "hole", etc.)
- `side`: Side of the part the feature is applied to
- `x/y/z`: Coordinate positions for feature placement
- `x_size/y_size/z_size`: Dimensions for features
- `center`: Boolean indicating if coordinates represent center point
