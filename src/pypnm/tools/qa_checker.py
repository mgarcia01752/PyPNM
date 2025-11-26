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
        Human-readable label for the tool (e.g., "ruff", "mypy").
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


def main() -> None:
    """
    Run The Standard PyPNM Software QA Suite.

    This helper aggregates the core quality checks configured for the project:

    1) ruff check src      – fast syntax/unused-imports checks (F-series).
    2) mypy src            – static type checking with the configured mypy settings.
    3) pytest              – unit tests, using pytest.ini options from pyproject.toml.
    4) pycycle --here      – import cycle detection over the current project.

    The process exit code is non-zero if any check fails.
    """
    commands: List[Command] = [
        ("ruff",   ["ruff", "check", "src"]),
        ("mypy",   ["mypy", "src"]),
        ("pytest", ["pytest"]),
        ("pycycle", ["pycycle", "--here"]),
    ]

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
