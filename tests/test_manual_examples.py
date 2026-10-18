# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The manual examples in examples/ (task cycax/30) are tests too: each one must build its spec
and make its manual page."""

from pathlib import Path

import pytest

from cycax.report.manual import write_manual_page
from cycax.spec import validate_spec
from cycax.targets import load_targets

EXAMPLES = sorted((Path(__file__).resolve().parents[1] / "examples").glob("*.py"))


@pytest.mark.parametrize("example", EXAMPLES, ids=[e.stem for e in EXAMPLES])
def test_example(example, tmp_path):
    targets = load_targets(example)
    assert targets, f"{example.name} has no targets"
    for target in targets:
        assert target.description, f"{example.name}:{target.name} needs a docstring for the manual"
        for obj in target.make():
            validate_spec(obj.export())
    index = write_manual_page(example, tmp_path)
    page = index.read_text()
    assert page.count("```python") == len(targets)
