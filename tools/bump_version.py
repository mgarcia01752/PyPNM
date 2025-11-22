#!/usr/bin/env python3
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import argparse
import re
import sys
from pathlib import Path
from typing import Final


VERSION_FILE_PATH: Final[Path]               = Path("src/pypnm/version.py")
VERSION_VAR_NAME: Final[str]                 = "__version__"
VERSION_PART_SEPARATOR: Final[str]           = "."
EXPECTED_VERSION_PARTS: Final[int]           = 4

MAJOR_INDEX: Final[int]                      = 0
MINOR_INDEX: Final[int]                      = 1
MAINTENANCE_INDEX: Final[int]                = 2
BUILD_INDEX: Final[int]                      = 3

VERSION_ASSIGNMENT_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf'({VERSION_VAR_NAME}\s*:\s*str\s*=\s*")(\d+\.\d+\.\d+\.\d+)(")'
)

VERSION_VALUE_PATTERN: Final[re.Pattern[str]] = re.compile(
    rf'{VERSION_VAR_NAME}\s*:\s*str\s*=\s*"([^"]+)"'
)


def _validate_version_string(version: str) -> None:
    """Validate that the version string matches MAJOR.MINOR.MAINTENANCE.BUILD."""
    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version):
        print(
            f"ERROR: Invalid version '{version}'. Expected numeric MAJOR.MINOR.MAINTENANCE.BUILD.",
            file=sys.stderr,
        )
        sys.exit(1)

    parts = version.split(VERSION_PART_SEPARATOR)
    if len(parts) != EXPECTED_VERSION_PARTS:
        print(
            f"ERROR: Version '{version}' has {len(parts)} parts, expected {EXPECTED_VERSION_PARTS}.",
            file=sys.stderr,
        )
        sys.exit(1)


def _read_current_version(version_file: Path) -> str:
    """Read the current __version__ value from the version file."""
    if not version_file.exists():
        print(f"ERROR: Version file not found: {version_file}", file=sys.stderr)
        sys.exit(1)

    text = version_file.read_text(encoding="utf-8")
    match = VERSION_VALUE_PATTERN.search(text)
    if match is None:
        print(
            f"ERROR: Could not find {VERSION_VAR_NAME} assignment in {version_file}.",
            file=sys.stderr,
        )
        sys.exit(1)

    return match.group(1)


def _write_new_version(version_file: Path, new_version: str) -> None:
    """Write the new version into the version file, replacing the existing assignment."""
    text = version_file.read_text(encoding="utf-8")
    if VERSION_ASSIGNMENT_PATTERN.search(text) is None:
        print(
            f"ERROR: Could not match {VERSION_VAR_NAME} assignment for replacement in {version_file}.",
            file=sys.stderr,
        )
        sys.exit(1)

    new_text = VERSION_ASSIGNMENT_PATTERN.sub(
        rf'\1{new_version}\3',
        text,
        count=1,
    )
    version_file.write_text(new_text, encoding="utf-8")


def _compute_next_version(current_version: str, mode: str) -> str:
    """Compute the next version string by incrementing the requested component."""
    _validate_version_string(current_version)
    parts_str = current_version.split(VERSION_PART_SEPARATOR)
    parts_int = [int(part) for part in parts_str]

    match mode:
        case "major":
            parts_int[MAJOR_INDEX]      = parts_int[MAJOR_INDEX] + 1
            parts_int[MINOR_INDEX]      = 0
            parts_int[MAINTENANCE_INDEX] = 0
            parts_int[BUILD_INDEX]      = 0
        case "minor":
            parts_int[MINOR_INDEX]      = parts_int[MINOR_INDEX] + 1
            parts_int[MAINTENANCE_INDEX] = 0
            parts_int[BUILD_INDEX]      = 0
        case "maintenance":
            parts_int[MAINTENANCE_INDEX] = parts_int[MAINTENANCE_INDEX] + 1
            parts_int[BUILD_INDEX]       = 0
        case "build":
            parts_int[BUILD_INDEX]      = parts_int[BUILD_INDEX] + 1
        case _:
            print(f"ERROR: Unsupported --next mode '{mode}'.", file=sys.stderr)
            sys.exit(1)

    return VERSION_PART_SEPARATOR.join(str(part) for part in parts_int)


def main() -> None:
    """CLI entry point for inspecting or updating the PyPNM version in src/pypnm/version.py.

    Modes
    -----
    1) Show current version:
       tools/bump_version.py --current

    2) Compute and apply the next version:
       tools/bump_version.py --next major
       tools/bump_version.py --next minor
       tools/bump_version.py --next maintenance
       tools/bump_version.py --next build

    3) Explicitly set the version:
       tools/bump_version.py 1.3.1.0
    """
    parser = argparse.ArgumentParser(
        description=(
            "Inspect or update the __version__ string in src/pypnm/version.py. "
            "Version format: MAJOR.MINOR.MAINTENANCE.BUILD (e.g. 1.3.1.0)."
        )
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="Explicit version to set (MAJOR.MINOR.MAINTENANCE.BUILD), e.g. 1.3.1.0.",
    )
    parser.add_argument(
        "--current",
        action="store_true",
        help="Show the current version and exit.",
    )
    parser.add_argument(
        "--next",
        choices=["major", "minor", "maintenance", "build"],
        help="Compute and apply the next version by incrementing the selected component.",
    )

    args = parser.parse_args()
    explicit_version: str | None = args.version
    show_current: bool           = args.current
    next_mode: str | None        = args.next

    # Determine mode; exactly one of (--current, --next, explicit version) must be used.
    if show_current:
        if explicit_version is not None or next_mode is not None:
            print("ERROR: --current cannot be combined with a version argument or --next.", file=sys.stderr)
            sys.exit(1)

        current = _read_current_version(VERSION_FILE_PATH)
        print(f"Current version: {current}")
        sys.exit(0)

    if next_mode is not None:
        if explicit_version is not None:
            print("ERROR: --next cannot be combined with an explicit version argument.", file=sys.stderr)
            sys.exit(1)

        current = _read_current_version(VERSION_FILE_PATH)
        next_version = _compute_next_version(current, next_mode)

        if next_version == current:
            print(f"No change: computed next version is the same as current: {current}.")
            sys.exit(0)

        _write_new_version(VERSION_FILE_PATH, next_version)
        print(f"Updated version: {current} -> {next_version}")
        sys.exit(0)

    if explicit_version is None:
        print(
            "ERROR: You must specify one of: --current, --next <mode>, or an explicit version.",
            file=sys.stderr,
        )
        sys.exit(1)

    new_version = explicit_version
    _validate_version_string(new_version)
    current = _read_current_version(VERSION_FILE_PATH)

    if current == new_version:
        print(f"No change: version is already {current}.")
        sys.exit(0)

    _write_new_version(VERSION_FILE_PATH, new_version)
    print(f"Updated version: {current} -> {new_version}")


if __name__ == "__main__":
    main()
