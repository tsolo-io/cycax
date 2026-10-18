# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Known errors: each has a message and, where possible, a fix (the next step for the user).

Exit codes (CLI): 1 = a build failed, 2 = usage error, 3 = a tool or the server is not available.
"""


class CycaxError(Exception):
    exit_code = 1

    def __init__(self, message: str, fix: str | None = None):
        super().__init__(message)
        self.message = message
        self.fix = fix


class UsageError(CycaxError):
    exit_code = 2


class TargetNotFoundError(UsageError):
    pass


class ProjectError(UsageError):
    pass


class ToolMissingError(CycaxError):
    exit_code = 3


class ServerUnavailableError(CycaxError):
    exit_code = 3


class BuildFailedError(CycaxError):
    exit_code = 1


def user_code_error(error: BaseException, *, context: str = "") -> CycaxError:
    """A known error as it is, or an error in user code with the user's file and line.

    The location is the last traceback frame that is not in CyCAx, the standard library or an
    installed package. `--debug` shows the full traceback.
    """
    if isinstance(error, CycaxError):
        return error
    import sys  # noqa: PLC0415
    import traceback  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    package = Path(__file__).resolve().parents[1]
    system = {Path(p).resolve() for p in (sys.prefix, sys.base_prefix, sys.exec_prefix)}
    frames = traceback.extract_tb(error.__traceback__)
    user = None
    for frame in frames:
        path = Path(frame.filename).resolve()
        if path.is_relative_to(package) or "site-packages" in path.parts or any(path.is_relative_to(s) for s in system):
            continue
        if frame.filename.startswith("<"):
            continue
        user = frame
    lines = [f"{type(error).__name__}: {error}"]
    if user is not None:
        try:
            shown = Path(user.filename).resolve().relative_to(Path.cwd())
        except ValueError:
            shown = Path(user.filename)
        lines.append(f"{shown}, line {user.lineno}")
        if user.line:
            lines.append(f"    {user.line.strip()}")
    fix = "Correct the code at this line." if user is not None else None
    if context:
        more = f"for the full traceback: {context} --debug"
        fix = f"{fix} Or, {more}" if fix else f"Run {context} --debug to see the full traceback."
    return CycaxError("\n".join(lines), fix)
