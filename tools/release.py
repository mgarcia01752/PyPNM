#!/usr/bin/env python3
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final


VERSION_FILE_PATH: Final[Path]           = Path("src/pypnm/version.py")
BUMP_SCRIPT_PATH: Final[Path]            = Path("tools/support") / "bump_version.py"
PYPROJECT_FILE_PATH: Final[Path]         = Path("pyproject.toml")

VERSION_PART_SEPARATOR: Final[str]       = "."
EXPECTED_VERSION_PARTS: Final[int]       = 4

MAJOR_INDEX: Final[int]                  = 0
MINOR_INDEX: Final[int]                  = 1
MAINTENANCE_INDEX: Final[int]            = 2
BUILD_INDEX: Final[int]                  = 3


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command and return the completed process."""
    proc = subprocess.run(cmd, text=True, capture_output=True, check=check)
    return proc


def _ensure_clean_worktree() -> None:
    """Ensure the git working tree has no uncommitted changes."""
    result = _run(["git", "status", "--porcelain"], check=False)
    output = (result.stdout or "").strip()
    if output:
        print("ERROR: Working tree is not clean. Commit or stash changes first.", file=sys.stderr)
        sys.exit(1)


def _checkout_and_pull(branch: str) -> None:
    """Checkout the target branch and fast-forward pull from origin."""
    _run(["git", "checkout", branch])
    _run(["git", "pull", "--ff-only"])


def _read_current_version() -> str:
    """Read the current __version__ value from the version file."""
    if not VERSION_FILE_PATH.exists():
        print(f"ERROR: Version file not found: {VERSION_FILE_PATH}", file=sys.stderr)
        sys.exit(1)

    text = VERSION_FILE_PATH.read_text(encoding="utf-8")
    prefix = '__version__: str = "'
    start_index = text.find(prefix)
    if start_index < 0:
        print(
            f"ERROR: Could not find __version__ assignment in {VERSION_FILE_PATH}.",
            file=sys.stderr,
        )
        sys.exit(1)

    start_index = start_index + len(prefix)
    end_index = text.find('"', start_index)
    if end_index < 0:
        print(
            f"ERROR: Unterminated __version__ string in {VERSION_FILE_PATH}.",
            file=sys.stderr,
        )
        sys.exit(1)

    return text[start_index:end_index]


def _read_pyproject_version() -> str:
    """Read the [project].version value from pyproject.toml."""
    if not PYPROJECT_FILE_PATH.exists():
        print(f"ERROR: pyproject.toml not found: {PYPROJECT_FILE_PATH}", file=sys.stderr)
        sys.exit(1)

    text = PYPROJECT_FILE_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_project_section = False

    for line in lines:
        stripped = line.strip()
        if stripped == "[project]":
            in_project_section = True
            continue

        if in_project_section and stripped.startswith("[") and stripped.endswith("]"):
            break

        if in_project_section and stripped.startswith("version") and "=" in stripped and '"' in stripped:
            first_quote = line.find('"')
            second_quote = line.find('"', first_quote + 1)
            if first_quote == -1 or second_quote == -1:
                print(
                    f"ERROR: Malformed [project].version line in {PYPROJECT_FILE_PATH}: {line!r}",
                    file=sys.stderr,
                )
                sys.exit(1)
            return line[first_quote + 1 : second_quote]

    print(
        f"ERROR: Could not find [project].version in {PYPROJECT_FILE_PATH}.",
        file=sys.stderr,
    )
    sys.exit(1)


def _validate_version_string(version: str) -> None:
    """Validate that the version string matches MAJOR.MINOR.MAINTENANCE.BUILD."""
    parts = version.split(VERSION_PART_SEPARATOR)
    if len(parts) != EXPECTED_VERSION_PARTS:
        print(
            f"ERROR: Version '{version}' has {len(parts)} parts, expected {EXPECTED_VERSION_PARTS}.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not all(part.isdigit() for part in parts):
        print(
            f"ERROR: Invalid version '{version}'. Expected numeric MAJOR.MINOR.MAINTENANCE.BUILD.",
            file=sys.stderr,
        )
        sys.exit(1)


def _compute_next_version(current_version: str, mode: str) -> str:
    """Compute the next version string by incrementing the requested component."""
    _validate_version_string(current_version)
    parts_str = current_version.split(VERSION_PART_SEPARATOR)
    parts_int = [int(part) for part in parts_str]

    match mode:
        case "major":
            parts_int[MAJOR_INDEX]       = parts_int[MAJOR_INDEX] + 1
            parts_int[MINOR_INDEX]       = 0
            parts_int[MAINTENANCE_INDEX] = 0
            parts_int[BUILD_INDEX]       = 0
        case "minor":
            parts_int[MINOR_INDEX]       = parts_int[MINOR_INDEX] + 1
            parts_int[MAINTENANCE_INDEX] = 0
            parts_int[BUILD_INDEX]       = 0
        case "maintenance":
            parts_int[MAINTENANCE_INDEX] = parts_int[MAINTENANCE_INDEX] + 1
            parts_int[BUILD_INDEX]       = 0
        case "build":
            parts_int[BUILD_INDEX]       = parts_int[BUILD_INDEX] + 1
        case _:
            print(f"ERROR: Unsupported next mode '{mode}'.", file=sys.stderr)
            sys.exit(1)

    return VERSION_PART_SEPARATOR.join(str(part) for part in parts_int)


def _bump_version(new_version: str) -> None:
    """Invoke tools/bump_version.py to update the version string."""
    if not BUMP_SCRIPT_PATH.exists():
        print(f"ERROR: Version bump script not found: {BUMP_SCRIPT_PATH}", file=sys.stderr)
        sys.exit(1)

    _run([sys.executable, str(BUMP_SCRIPT_PATH), new_version])


def _run_tests() -> None:
    """Run the test suite before finalizing the release."""
    print("Running tests (pytest)...")
    result = _run(["pytest"], check=False)
    if result.returncode != 0:
        print("ERROR: pytest failed. Aborting release.", file=sys.stderr)
        sys.exit(result.returncode)


def _commit_version_bump(new_version: str) -> None:
    """Commit the version bump change."""
    _run(["git", "add", str(VERSION_FILE_PATH), str(PYPROJECT_FILE_PATH)])
    _run(["git", "commit", "-m", f"Release {new_version}"])


def _create_tag(new_version: str, tag_prefix: str) -> str:
    """Create an annotated git tag for the release."""
    tag_name = f"{tag_prefix}{new_version}"
    _run(["git", "tag", "-a", tag_name, "-m", f"Release {new_version}"])
    return tag_name


def _push_branch_and_tag(branch: str, tag_name: str) -> None:
    """Push the branch and tag to the origin remote."""
    _run(["git", "push", "origin", branch])
    _run(["git", "push", "origin", tag_name])


def main() -> None:
    """Automate a release: bump version, run tests, commit, tag, and push.

    Typical flows
    -------------
    1) Let the script compute the next maintenance version:
       tools/release.py

    2) Let the script compute the next version by mode:
       tools/release.py --next minor
       tools/release.py --next major
       tools/release.py --next maintenance
       tools/release.py --next build

    3) Release an explicit version:
       tools/release.py --version 0.2.1.0

    4) Show what would happen without changing anything:
       tools/release.py --next maintenance --dry-run
       tools/release.py --dry-run
    """
    parser = argparse.ArgumentParser(
        description=(
            "Automate a PyPNM release: compute or apply a version using tools/bump_version.py, "
            "run tests, commit, tag, and push."
        )
    )
    parser.add_argument(
        "--version",
        help="Explicit release version in MAJOR.MINOR.MAINTENANCE.BUILD format (e.g. 0.1.0.0).",
    )
    parser.add_argument(
        "--next",
        choices=["major", "minor", "maintenance", "build"],
        help="Compute the next version from the current one (default: maintenance if omitted).",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch to release from (default: main). Use 'stable' when ready.",
    )
    parser.add_argument(
        "--tag-prefix",
        default="v",
        help="Prefix for git tag names (default: 'v', e.g. v0.1.0.0).",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running pytest before committing and tagging.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned actions without modifying anything.",
    )

    args = parser.parse_args()
    explicit_version: str | None = args.version
    next_mode: str | None        = args.next
    branch: str                  = args.branch
    tag_prefix: str              = args.tag_prefix
    skip_tests: bool             = args.skip_tests
    dry_run: bool                = args.dry_run

    current_version   = _read_current_version()
    pyproject_version = _read_pyproject_version()

    if current_version != pyproject_version:
        print(
            "ERROR: Version mismatch between src/pypnm/version.py "
            f"({current_version}) and pyproject.toml [project].version "
            f"({pyproject_version}). Run tools/bump_version.py or fix manually.",
            file=sys.stderr,
        )
        sys.exit(1)

    if explicit_version is not None and next_mode is not None:
        print("ERROR: --version and --next cannot be used together.", file=sys.stderr)
        sys.exit(1)

    if explicit_version is not None:
        new_version = explicit_version
        _validate_version_string(new_version)
    else:
        mode       = next_mode or "maintenance"
        new_version = _compute_next_version(current_version, mode)

    if new_version == current_version:
        print(f"No change: version is already {current_version}.")
        sys.exit(0)

    if dry_run:
        print("Dry run: the following actions would be performed:")
        print("  1) Ensure git working tree is clean")
        print(f"  2) Checkout branch '{branch}' and pull with --ff-only")
        print(f"  3) Update version {current_version} -> {new_version} via tools/bump_version.py")
        if not skip_tests:
            print("  4) Run pytest")
        print(f"  5) Commit version bump: 'Release {new_version}'")
        print(f"  6) Create annotated tag '{tag_prefix}{new_version}'")
        print(f"  7) Push branch '{branch}' and tag to origin")
        sys.exit(0)

    if explicit_version is None:
        print(f"Current version: {current_version}")
        print(f"Planned version bump: {current_version} -> {new_version}")
        answer = input("Proceed with release? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Aborted: release was not confirmed.")
            sys.exit(1)

    _ensure_clean_worktree()
    _checkout_and_pull(branch)

    print(f"Bumping version: {current_version} -> {new_version}")
    _bump_version(new_version)

    if not skip_tests:
        _run_tests()

    _commit_version_bump(new_version)
    tag_name = _create_tag(new_version, tag_prefix)
    _push_branch_and_tag(branch, tag_name)

    print(f"Release {new_version} completed on branch '{branch}' with tag '{tag_name}'.")


if __name__ == "__main__":
    main()
