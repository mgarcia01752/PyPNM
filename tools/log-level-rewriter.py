#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Bulk Logging Level Rewriter For PyPNM.

Use This Script To Rewrite Logger Calls Across The Tree, For Example:
    logger.info(...)  →  logger.debug(...)

Features
--------
- Traverses The Project Tree From A Given Root.
- Skips Hidden Directories Automatically (".git", ".env", etc.).
- Respects A Hardcoded Exclude List For Directories And Files.
- Supports A Safe --dry-run Mode.
- Shows Per-Match Row:Column Locations During Dry-Run.
- Asks For An Explicit "yes" Acknowledgement Before Applying Changes.
"""

from __future__ import annotations

import argparse
import bisect
import os
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

# ──────────────────────────────────────────────────────────────
# Types & Configuration Knobs
# ──────────────────────────────────────────────────────────────

DirName = str          # Directory name only (e.g., "tools", ".git"), not full path
FileName = str         # File name only (e.g., "manager.py"), not full path
LogLevelName = str     # logger level name (e.g., "info", "debug")

# Directories (names, not full paths) that will be skipped entirely.
EXCLUDE_DIRS: set[DirName] = {
    "tools",
    ".git",
    ".env",
    "venv",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}

# Filenames (base name only) to skip.
EXCLUDE_FILES: set[FileName] = {
    # Example:
    # "manager.py",
}

# Map of logger level changes. Key = old level, Value = new level.
# This drives both detection and replacement.
LOG_LEVEL_MAP: dict[LogLevelName, LogLevelName] = {
    "info": "debug",
    # You can add more, e.g.:
    # "warning": "info",
    # "error": "warning",
}

# Regex to find logger.<level>(...
# Group 1 = prefix ".logger."
# Group 2 = level name (info, warning, etc.)
_LOG_CALL_RE = re.compile(
    r"(\.logger\.)(%s)\s*\(" % "|".join(map(re.escape, LOG_LEVEL_MAP.keys()))
)


# ──────────────────────────────────────────────────────────────
# Core Helpers
# ──────────────────────────────────────────────────────────────

def _iter_python_files(root: Path) -> Iterable[Path]:
    """
    Yield All .py Files Under `root`, Respecting Excludes And Hidden Dirs.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dir_path = Path(dirpath)

        # Strip hidden directories and excluded ones so os.walk skips them
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in EXCLUDE_DIRS
        ]

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            if fname in EXCLUDE_FILES:
                continue
            if fname.startswith("."):
                continue

            yield dir_path / fname


def _compute_line_starts(text: str) -> list[int]:
    """
    Return A List Of Line Start Offsets For `text`.

    Example: line_starts[0] = 0; line_starts[1] = index after first '\n', etc.
    """
    starts = [0]
    for match in re.finditer(r"\n", text):
        starts.append(match.end())
    return starts


def _index_to_line_col(starts: list[int], index: int) -> tuple[int, int]:
    """
    Convert A 0-Based Character Index Into 1-Based (line, col) Using `starts`.
    """
    line_idx = bisect.bisect_right(starts, index) - 1
    if line_idx < 0:
        line_idx = 0
    line_no = line_idx + 1
    col_no = index - starts[line_idx] + 1
    return line_no, col_no


def scan_file(path: Path) -> tuple[int, list[tuple[int, int, LogLevelName, LogLevelName]]]:
    """
    Scan A Single File For Logger Level Calls.

    Parameters
    ----------
    path : Path
        Python source file.

    Returns
    -------
    count : int
        Number of replacements that *would* be made.
    matches : list[(line, col, old_level, new_level)]
        Per-match metadata for reporting purposes.
    """
    text = path.read_text(encoding="utf-8")
    line_starts = _compute_line_starts(text)

    matches: list[tuple[int, int, LogLevelName, LogLevelName]] = []
    for m in _LOG_CALL_RE.finditer(text):
        prefix, old_level = m.group(1), m.group(2)
        new_level = LOG_LEVEL_MAP.get(old_level)
        if new_level is None:
            continue

        idx = m.start(2)  # position of the level name
        line, col = _index_to_line_col(line_starts, idx)
        matches.append((line, col, old_level, new_level))

    return len(matches), matches


def rewrite_file(path: Path) -> int:
    """
    Rewrite Logger Calls In `path` According To LOG_LEVEL_MAP.

    Returns
    -------
    int
        Number of replacements performed in this file.
    """
    text = path.read_text(encoding="utf-8")

    def _repl(match: re.Match[str]) -> str:
        prefix, old_level = match.group(1), match.group(2)
        new_level = LOG_LEVEL_MAP.get(old_level, old_level)
        return f"{prefix}{new_level}("

    new_text, n_subs = _LOG_CALL_RE.subn(_repl, text)
    if n_subs > 0:
        path.write_text(new_text, encoding="utf-8")
    return n_subs


# ──────────────────────────────────────────────────────────────
# Main Logic
# ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Bulk-rewrite logger levels (e.g., .logger.info(...) → .logger.debug(...)) "
            "across the project tree."
        )
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Project root directory to scan (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report changes (with row:column locations) but do not modify files.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: root directory '{root}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(2)

    print(f"Scanning for logger calls under: {root}", flush=True)
    print(f"Excluded directories: {sorted(EXCLUDE_DIRS)}", flush=True)
    print(f"Excluded files: {sorted(EXCLUDE_FILES)}", flush=True)
    print(f"Log level map: {LOG_LEVEL_MAP}", flush=True)

    total_files = 0
    total_replacements = 0

    candidates: list[tuple[Path, int, list[tuple[int, int, LogLevelName, LogLevelName]]]] = []
    for path in _iter_python_files(root):
        count, matches = scan_file(path)
        if count > 0:
            candidates.append((path, count, matches))
            total_files += 1
            total_replacements += count

    if not candidates:
        print("No matching logger calls found. Nothing to do.", flush=True)
        sys.exit(0)

    print("\n=== DRY SCAN RESULTS ===", flush=True)
    for path, count, matches in candidates:
        print(f"[FILE] {path}  :: {count} matches", flush=True)
        for line, col, old_lvl, new_lvl in matches:
            print(f"  - {path}:{line}:{col}  {old_lvl} → {new_lvl}", flush=True)

    print(
        f"\nSummary: files touched={total_files}, replacements={total_replacements}, "
        f"dry_run={args.dry_run}",
        flush=True,
    )

    if args.dry_run:
        print("\nDry run complete. No files were modified.", flush=True)
        sys.exit(0)

    print(
        "\nWARNING: This will modify the files listed above in-place.\n"
        "Type 'yes' to proceed, or anything else to cancel.",
        flush=True,
    )
    response = input("Proceed with rewrite? [yes/NO]: ").strip().lower()
    if response != "yes":
        print("Aborted by user. No files were modified.", flush=True)
        sys.exit(0)

    applied_files = 0
    applied_replacements = 0
    print("\n=== APPLYING REWRITES ===", flush=True)
    for path, _, _ in candidates:
        n_subs = rewrite_file(path)
        if n_subs > 0:
            applied_files += 1
            applied_replacements += n_subs
            print(f"[MOD] {path} :: {n_subs} replacements", flush=True)

    print(
        f"\nDone. Files modified={applied_files}, total replacements={applied_replacements}.",
        flush=True,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
