#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Recursively ensure every .py file has:
1) MIT SPDX header (inserted if missing)
2) `from __future__ import annotations` (inserted if missing, with version-aware control)

Python ≥ 3.14 behavior:
- Because annotations are lazily evaluated by default in 3.14+, the future import
  is not needed. By default, this script will ASK ONCE at startup whether to continue
  inserting it. Use `--future yes` to force insertion or `--future no` to skip insertion.

Also skips virtualenvs and common non-source directories.

Usage:
  ./tools/add-spdx.py [ROOT_DIR] [--exclude dir1,dir2,...] [--future {auto,yes,no}]

Notes:
- Preserves a leading shebang and encoding declaration (PEP 263).
- Inserts SPDX header after shebang/encoding if not present.
- Places the future import after the top-level module docstring if present,
  otherwise right after the header.
- Idempotent and safe to re-run.
"""

import ast
import os
import re
import sys
import argparse
from typing import List, Tuple, Set

HEADER_LINES = [
    "# SPDX-License-Identifier: MIT\n",
    "# Copyright (c) 2025 Maurice Garcia\n",
    "\n",
]

FUTURE_LINE = "from __future__ import annotations\n"

# PEP 263 encoding cookie (must be on line 1 or 2)
ENCODING_RE = re.compile(r"^#.*coding[:=]\s*([-\w.]+)")

# Default directories to skip
DEFAULT_EXCLUDED_DIRS: Set[str] = {
    ".git",
    ".env", "env", "venv", ".venv",
    "__pycache__",
    ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox",
    "node_modules",
    "build", "dist",
    ".idea", ".vscode",
}

def has_spdx(lines: List[str]) -> bool:
    """Return True if SPDX header appears near the top."""
    for line in lines[:12]:
        if "SPDX-License-Identifier: MIT" in line:
            return True
    return False

def has_future_import(lines: List[str]) -> bool:
    """Return True if `from __future__ import annotations` appears anywhere in the file."""
    return "from __future__ import annotations" in "".join(lines)

def split_shebang_encoding(lines: List[str]) -> Tuple[List[str], List[str]]:
    """
    Return (prefix, remainder):
      - prefix: preserved top lines (shebang + optional encoding line)
      - remainder: rest of file
    """
    prefix: List[str] = []
    idx = 0

    # Shebang
    if lines and lines[0].startswith("#!"):
        prefix.append(lines[0])
        idx = 1

    # Encoding cookie may be on line 1 or 2
    if len(lines) > idx and ENCODING_RE.match(lines[idx] or ""):
        prefix.append(lines[idx])
        idx += 1

    return prefix, lines[idx:]

def find_module_docstring_span(body_lines: List[str]) -> Tuple[int, int]:
    """
    Using AST, detect the top-level module docstring span within `body_lines`.

    Returns (start_idx, end_idx_inclusive) within `body_lines`, or (-1, -1) if none.
    """
    text = "".join(body_lines)
    try:
        mod = ast.parse(text)
    except Exception:
        return -1, -1

    if not getattr(mod, "body", None):
        return -1, -1

    first = mod.body[0]
    if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), (ast.Str, ast.Constant)):
        value = first.value.s if isinstance(first.value, ast.Str) else (
            first.value.value if isinstance(first.value, ast.Constant) and isinstance(first.value.value, str) else None
        )
        if isinstance(value, str):
            start = getattr(first, "lineno", None)
            end = getattr(first, "end_lineno", None)
            if start is not None and end is not None:
                return start - 1, end - 1
    return -1, -1

def ensure_header_and_future(path: str, add_future: bool) -> None:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original = lines[:]

    # Keep shebang/encoding at very top
    prefix, remainder = split_shebang_encoding(lines)

    # 1) Ensure SPDX header
    body: List[str] = []
    header_added = False
    if not has_spdx(lines):
        body.extend(HEADER_LINES)
        header_added = True

    # Append remainder of file
    body.extend(remainder)

    # 2) Ensure future import (respect global decision `add_future`)
    future_added = False
    if add_future and not has_future_import(lines):
        ds_start, ds_end = find_module_docstring_span(body)
        insert_at = 0 if ds_start == -1 else ds_end + 1

        # blank line BEFORE if needed
        if insert_at < len(body) and body[insert_at].strip():
            body.insert(insert_at, "\n")
            insert_at += 1

        # insert the future import
        body.insert(insert_at, FUTURE_LINE)
        insert_at += 1

        # blank line AFTER if needed
        if insert_at >= len(body) or body[insert_at].strip():
            body.insert(insert_at, "\n")

        future_added = True

    new_lines = prefix + body

    if new_lines != original:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        bits = []
        if header_added:
            bits.append("header")
        if future_added:
            bits.append("future")
        tag = "+".join(bits) if bits else "modified"
        print(f"✅ Updated ({tag}): {path}")
    else:
        print(f"⏭ No changes: {path}")

def is_virtualenv_dir(path: str) -> bool:
    """
    Heuristics to detect venv-like directories (non-standard names included):
    - Contains `pyvenv.cfg`, or
    - Has `bin/activate` (POSIX) or `Scripts/activate` (Windows)
    """
    if os.path.isfile(os.path.join(path, "pyvenv.cfg")):
        return True
    if os.path.isfile(os.path.join(path, "bin", "activate")):
        return True
    if os.path.isfile(os.path.join(path, "Scripts", "activate")):
        return True
    return False

def is_site_packages_path(path: str) -> bool:
    parts = set(path.split(os.sep))
    return "site-packages" in parts

def should_skip_dir(path: str, extra_excluded: Set[str]) -> bool:
    base = os.path.basename(path)
    if base in DEFAULT_EXCLUDED_DIRS or base in extra_excluded:
        return True
    if os.path.islink(path):
        return True
    if is_virtualenv_dir(path):
        return True
    if is_site_packages_path(path):
        return True
    return False

def walk_and_process(root: str, extra_excluded: Set[str], add_future: bool) -> None:
    """
    Walk `root` directory recursively and process every .py file,
    skipping virtualenvs and excluded directories.
    """
    # If the root itself is a venv or excluded, bail out safely
    if should_skip_dir(root, extra_excluded):
        print(f"⏭ Root appears to be a virtualenv or excluded: {root}")
        return

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune dirs in-place to prevent descending into them
        dirnames[:] = [
            d for d in dirnames
            if not should_skip_dir(os.path.join(dirpath, d), extra_excluded)
        ]

        for fn in filenames:
            if fn.endswith(".py"):
                full_path = os.path.join(dirpath, fn)
                try:
                    ensure_header_and_future(full_path, add_future=add_future)
                except Exception as exc:
                    print(f"❌ Error processing {full_path}: {exc}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure SPDX headers and future import across a tree.")
    parser.add_argument("root", nargs="?", default=os.getcwd(), help="Root directory (default: CWD)")
    parser.add_argument(
        "--exclude",
        help="Comma-separated extra directory names to exclude (in addition to defaults).",
        default=""
    )
    parser.add_argument(
        "--future",
        choices=("auto", "yes", "no"),
        default="auto",
        help=(
            "Control insertion of `from __future__ import annotations`.\n"
            "  auto: Python < 3.14 -> insert; Python >= 3.14 -> prompt once (interactive) or skip (non-interactive)\n"
            "  yes : always insert\n"
            "  no  : never insert"
        ),
    )
    return parser.parse_args()

def decide_add_future(policy: str) -> bool:
    """
    Decide whether we should insert the future import, considering Python version
    and (if needed) prompting the user once at startup.
    """
    if policy == "yes":
        return True
    if policy == "no":
        return False

    # auto policy
    vi = sys.version_info
    if vi < (3, 14):
        return True

    # Python 3.14+ — default is to ask once if interactive; skip if non-interactive
    if sys.stdin.isatty():
        print(
            "Python 3.14+ detected: annotations are already lazy by default.\n"
            "Inserting `from __future__ import annotations` is not required and may be deprecated later.\n"
            "Do you still want to insert it across files? [y/N]: ",
            end="",
            flush=True,
        )
        try:
            ans = input().strip().lower()
        except EOFError:
            ans = ""
        return ans in ("y", "yes")
    else:
        print(
            "Python 3.14+ detected and non-interactive session — skipping insertion of "
            "`from __future__ import annotations`. Use `--future yes` to force.",
        )
        return False

if __name__ == "__main__":
    args = parse_args()
    extra = {x.strip() for x in args.exclude.split(",") if x.strip()}
    add_future = decide_add_future(args.future)

    print(f"Scanning for .py files under: {args.root}")
    if extra:
        print(f"Additional excludes: {sorted(extra)}")
    print(f"Adding future import: {'YES' if add_future else 'NO'}")
    walk_and_process(args.root, extra_excluded=extra, add_future=add_future)
    print("Done.")
