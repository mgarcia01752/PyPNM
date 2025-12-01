# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import subprocess
import sys
from typing import List, Sequence, Tuple


Command = Tuple[str, Sequence[str]]


def _run_command(label: str, cmd: Sequence[str]) -> int:
    """
    Run A Single QA Tool Command And Stream Its Output.

    Parameters
    ----------
    label : str
        Human-readable label for the tool (e.g., "ruff", "pyright").
    cmd : Sequence[str]
        The command and arguments to execute.

    Returns
    -------
    int
        The process return code (0 on success, non-zero on failure).
    """
    print(f"\n=== [{label}] running: {' '.join(cmd)} ===", flush=True)
    try:
        proc = subprocess.run(cmd, check=False)
        if proc.returncode == 0:
            print(f"=== [{label}] OK ===", flush=True)
        else:
            print(f"=== [{label}] FAILED (exit code {proc.returncode}) ===", flush=True)
        return proc.returncode
    except FileNotFoundError:
        print(f"=== [{label}] NOT FOUND on PATH ===", flush=True)
        return 127


def _build_commands(include_pyright: bool) -> List[Command]:
    """
    Build The Ordered List Of QA Commands To Run.

    Parameters
    ----------
    include_pyright : bool
        If True, include a `pyright` static type-check step after Ruff.

    Returns
    -------
    list[Command]
        Ordered list of (label, cmd) tuples to execute.
    """
    commands: List[Command] = [
        ("ruff", ["ruff", "check", "src"]),
        ("pytest", ["pytest"]),
        ("pycycle", ["pycycle", "--here"]),
    ]

    if include_pyright:
        # Insert Pyright after Ruff but before pytest for faster feedback.
        commands.insert(1, ("pyright", ["pyright"]))

    return commands


def main() -> None:
    """
    Run The Standard PyPNM Software QA Suite.

    Default Behavior
    ----------------
    By default, this helper aggregates the core quality checks configured for
    the project:

    1) ruff check src      – syntax, style, and common bug patterns.
    2) pytest              – unit tests (pytest options from pyproject.toml).
    3) pycycle --here      – import cycle detection over the current project.

    Optional Pyright
    ----------------
    To enable static type checking with Pyright, pass the flag:

        pypnm-software-qa-checker --with-pyright

    This will run an additional step:

    - pyright              – static type analysis using [tool.pyright] settings.

    The process exit code is non-zero if any check fails.
    """
    # Detect and strip our own CLI flag so it is not propagated to subcommands.
    args = sys.argv[1:]
    include_pyright = "--with-pyright" in args
    filtered_args = [a for a in args if a != "--with-pyright"]
    sys.argv = [sys.argv[0], *filtered_args]

    commands = _build_commands(include_pyright=include_pyright)

    overall_rc = 0
    for label, cmd in commands:
        rc = _run_command(label, cmd)
        if rc != 0 and overall_rc == 0:
            overall_rc = rc

    print("\n=== PyPNM Software QA Suite Finished ===", flush=True)
    if overall_rc == 0:
        print("All checks passed.", flush=True)
    else:
        print(f"One or more checks failed (exit code {overall_rc}).", flush=True)

    sys.exit(overall_rc)


if __name__ == "__main__":
    main()
