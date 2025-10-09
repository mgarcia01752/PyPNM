#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Ensure each .py has:
1) SPDX MIT header
2) Current-year copyright
3) (Optionally) `from __future__ import annotations`

Usage:
  ./tools/add-spdx.py [ROOT_DIR] [--exclude a,b] [--future {auto,yes,no}] [--author "Name"] [--year 2025] [--verbose]
"""

import ast
import os
import re
import sys
import argparse
from datetime import datetime
from typing import List, Tuple, Set, Optional

DEFAULT_AUTHOR = "Maurice Garcia"
DEFAULT_YEAR = datetime.now().year
FUTURE_LINE = "from __future__ import annotations\n"

COPYRIGHT_RE = re.compile(r"^#\s*Copyright\s*\(c\)\s*(\d{4})\s+(.*)$")
ENCODING_RE = re.compile(r"^#.*coding[:=]\s*([-\w.]+)")

DEFAULT_EXCLUDED_DIRS: Set[str] = {
    ".git", ".env", "env", "venv", ".venv", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", "node_modules", "build", "dist",
    ".idea", ".vscode",
}

def spdx_line() -> str:
    return "# SPDX-License-Identifier: MIT\n"

def copyright_line(year: int, author: str) -> str:
    return f"# Copyright (c) {year} {author}\n"

def has_spdx(lines: List[str]) -> bool:
    return any("SPDX-License-Identifier: MIT" in line for line in lines[:12])

def find_copyright_line_index(lines: List[str]) -> Optional[int]:
    for i, line in enumerate(lines[:12]):
        if COPYRIGHT_RE.match(line):
            return i
    return None

def has_future_import(lines: List[str]) -> bool:
    return "from __future__ import annotations" in "".join(lines)

def split_shebang_encoding(lines: List[str]) -> Tuple[List[str], List[str]]:
    prefix: List[str] = []
    idx = 0
    if lines and lines[0].startswith("#!"):
        prefix.append(lines[0]); idx = 1
    if len(lines) > idx and ENCODING_RE.match(lines[idx] or ""):
        prefix.append(lines[idx]); idx += 1
    return prefix, lines[idx:]

def find_module_docstring_span(body_lines: List[str]) -> Tuple[int, int]:
    text = "".join(body_lines)
    try:
        mod = ast.parse(text)
    except Exception:
        return -1, -1
    if not getattr(mod, "body", None):
        return -1, -1
    first = mod.body[0]
    if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), (ast.Str, ast.Constant)):
        val = first.value.s if isinstance(first.value, ast.Str) else (
            first.value.value if isinstance(first.value, ast.Constant) and isinstance(first.value.value, str) else None
        )
        if isinstance(val, str):
            return first.lineno - 1, first.end_lineno - 1
    return -1, -1

def ensure_header_and_future(path: str, add_future: bool, author: str, year: int, verbose: bool) -> None:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original = lines[:]
    prefix, remainder = split_shebang_encoding(lines)

    body: List[str] = []
    header_added = False
    header_updated = False

    if not has_spdx(lines):
        body.append(spdx_line())
        body.append(copyright_line(year, author))
        body.append("\n")
        header_added = True
    else:
        idx = find_copyright_line_index(lines)
        if idx is not None:
            m = COPYRIGHT_RE.match(lines[idx])
            if m:
                old_year = int(m.group(1))
                old_author = m.group(2).strip()
                if old_year != year:
                    lines[idx] = copyright_line(year, old_author or author)
                    header_updated = True
        else:
            rem_copy = remainder[:]
            inserted = False
            for i, l in enumerate(rem_copy[:5]):
                if "SPDX-License-Identifier: MIT" in l:
                    insert_at = i + 1
                    rem_copy.insert(insert_at, copyright_line(year, author))
                    rem_copy.insert(insert_at + 1, "\n")
                    remainder = rem_copy
                    header_updated = True
                    inserted = True
                    break
            if not inserted:
                body.append(spdx_line())
                body.append(copyright_line(year, author))
                body.append("\n")
                header_added = True

    body.extend(remainder)

    future_added = False
    if add_future and not has_future_import(lines):
        ds_start, ds_end = find_module_docstring_span(body)
        insert_at = 0 if ds_start == -1 else ds_end + 1
        if insert_at < len(body) and body[insert_at].strip():
            body.insert(insert_at, "\n"); insert_at += 1
        body.insert(insert_at, FUTURE_LINE); insert_at += 1
        if insert_at >= len(body) or body[insert_at].strip():
            body.insert(insert_at, "\n")
        future_added = True

    new_lines = prefix + body

    if new_lines != original:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        bits = []
        if header_added: bits.append("header")
        if header_updated and not header_added: bits.append("copyright-year")
        if future_added: bits.append("future")
        tag = "+".join(bits) if bits else "modified"
        print(f"✅ Updated ({tag}): {path}")
    else:
        if verbose:
            print(f"⏭ No changes: {path}")

def is_virtualenv_dir(path: str) -> bool:
    if os.path.isfile(os.path.join(path, "pyvenv.cfg")): return True
    if os.path.isfile(os.path.join(path, "bin", "activate")): return True
    if os.path.isfile(os.path.join(path, "Scripts", "activate")): return True
    return False

def is_site_packages_path(path: str) -> bool:
    return "site-packages" in set(path.split(os.sep))

def should_skip_dir(path: str, extra_excluded: Set[str]) -> bool:
    base = os.path.basename(path)
    if base in DEFAULT_EXCLUDED_DIRS or base in extra_excluded: return True
    if os.path.islink(path): return True
    if is_virtualenv_dir(path): return True
    if is_site_packages_path(path): return True
    return False

def walk_and_process(root: str, extra_excluded: Set[str], add_future: bool, author: str, year: int, verbose: bool) -> None:
    if should_skip_dir(root, extra_excluded):
        if verbose:
            print(f"⏭ Root appears to be a virtualenv or excluded: {root}")
        return

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(os.path.join(dirpath, d), extra_excluded)]
        for fn in filenames:
            if fn.endswith(".py"):
                full_path = os.path.join(dirpath, fn)
                try:
                    ensure_header_and_future(full_path, add_future=add_future, author=author, year=year, verbose=verbose)
                except Exception as exc:
                    print(f"❌ Error processing {full_path}: {exc}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure SPDX headers, current year, and future import across a tree.")
    parser.add_argument("root", nargs="?", default=os.getcwd(), help="Root directory (default: CWD)")
    parser.add_argument("--exclude", default="", help="Comma-separated extra directory names to exclude.")
    parser.add_argument("--future", choices=("auto", "yes", "no"), default="auto",
                        help="Control insertion of `from __future__ import annotations`.")
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="Author name (default: %(default)s)")
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR, help="Year (default: current year)")
    parser.add_argument("--verbose", action="store_true", help="Print scan summary and unchanged files.")
    return parser.parse_args()

def decide_add_future(policy: str) -> bool:
    if policy == "yes": return True
    if policy == "no": return False
    vi = sys.version_info
    if vi < (3, 14): return True
    if sys.stdin.isatty():
        print("Python 3.14+ detected: annotations are lazy by default.\n"
              "Insert `from __future__ import annotations` anyway? [y/N]: ", end="", flush=True)
        try: ans = input().strip().lower()
        except EOFError: ans = ""
        return ans in ("y", "yes")
    else:
        return False

if __name__ == "__main__":
    args = parse_args()
    extra = {x.strip() for x in args.exclude.split(",") if x.strip()}
    add_future = decide_add_future(args.future)

    if args.verbose:
        print(f"Scanning for .py files under: {args.root}")
        if extra: print(f"Additional excludes: {sorted(extra)}")
        print(f"Adding future import: {'YES' if add_future else 'NO'}")
        print(f"Using author: {args.author} • year: {args.year}")

    walk_and_process(args.root, extra_excluded=extra, add_future=add_future, author=args.author, year=args.year, verbose=args.verbose)

    if args.verbose:
        print("Done.")
