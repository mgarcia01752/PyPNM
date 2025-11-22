#!/usr/bin/env python3
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final


VERSION_FILE_PATH: Final[Path] = Path("src/pypnm/version.py")
BUMP_SCRIPT_PATH: Final[Path]  = Path("tools") / "bump_version.py"


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
    _run(["git", "add", str(VERSION_FILE_PATH)])
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
    1) Release a specific version from main:
       tools/release.py 0.1.0.0

    2) Release from stable:
       tools/release.py 0.1.0.0 --branch stable

    3) Release without running tests (not recommended):
       tools/release.py 0.1.0.0 --skip-tests

    4) Show what would happen without changing anything:
       tools/release.py 0.1.0.0 --dry-run
    """
    parser = argparse.ArgumentParser(
        description=(
            "Automate a PyPNM release: bump version using tools/bump_version.py, "
            "run tests, commit, tag, and push."
        )
    )
    parser.add_argument(
        "version",
        help="Release version in MAJOR.MINOR.MAINTENANCE.BUILD format (e.g. 0.1.0.0).",
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
    new_version: str  = args.version
    branch: str       = args.branch
    tag_prefix: str   = args.tag_prefix
    skip_tests: bool  = args.skip_tests
    dry_run: bool     = args.dry_run

    current_version = _read_current_version()

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
