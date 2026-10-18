# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# The CLI must start fast: commands that never build must not load build123d/OCP (~2.7 s).
import subprocess
import sys


def test_cli_import_does_not_load_build123d():
    code = "import sys, cycax.cli.main; print(any(m.split('.')[0] in ('build123d', 'OCP') for m in sys.modules))"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "False"


def test_cli_help_is_fast():
    import time

    start = time.monotonic()
    subprocess.run([sys.executable, "-m", "cycax.cli.main", "--help"], capture_output=True, check=True)
    assert time.monotonic() - start < 3.0  # noqa: PLR2004 - generous for CI; locally ~0.3 s
