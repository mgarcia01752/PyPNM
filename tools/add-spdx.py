#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Recursively ensure every .py file has:
1) MIT SPDX header (inserted if missing)
2) `from __future__ import annotations` (inserted if missing)

Rules:
- Preserve a leading shebang (line 1) and an encoding declaration on line 1 or 2 (PEP 263).
- Insert SPDX header right after shebang/encoding if not present.
- Place the `from __future__ import annotations`:
    * immediately after the top-level module docstring if one exists at the start, or
    * otherwise right after the SPDX header (and shebang/encoding), before any other imports/code.
- Idempotent: never duplicates header or future import.
"""

import os
import re
import sys
from typing import List, Tuple

HEADER_LINES = [
    "# SPDX-License-Identifier: MIT\n",
    "# Copyright (c) 2025 Maurice Garcia\n",
    "\n",
]

FUTURE_LINE = "from __future__ import annotations\n"

# PEP 263 encoding cookie (must be on line 1 or 2)
ENCODING_RE = re.compile(r"^#.*coding[:=]\s*([-\w.]+)")

def has_spdx(lines: List[str]) -> bool:
    """Return True if SPDX header appears near the top."""
    for line in lines[:12]:
        if "SPDX-License-Identifier: MIT" in line:
            return True
    return False

def has_future_import(lines: List[str]) -> bool:
    """Return True if `from __future__ import annotations` appears in the file."""
    # Look through more than just the first few lines to be safe,
    # though we will insert near the top if missing.
    head = "".join(lines[:400])
    return "from __future__ import annotations" in head

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

    # Encoding cookie must be on line 1 or 2
    if len(lines) > idx and ENCODING_RE.match(lines[idx]):
        prefix.append(lines[idx])
        idx += 1

    return prefix, lines[idx:]

def find_top_docstring_block(remainder: List[str]) -> Tuple[int, int]:
    """
    If the file (after header/comments) starts with a module docstring,
    return (start_idx, end_idx_inclusive) within `remainder`. Else (-1, -1).

    Accepts simple prefixes r/u/f and triple quotes ''' or """.
    """
    i = 0
    # Skip leading blanks and comment-only lines
    while i < len(remainder) and (not remainder[i].strip() or remainder[i].lstrip().startswith("#")):
        i += 1
    if i >= len(remainder):
        return -1, -1

    line = remainder[i].lstrip()
    triple = None
    if re.match(r'^[rRuUfF]?"""', line):
        triple = '"""'
    elif re.match(r"^[rRuUfF]?'''", line):
        triple = "'''"
    else:
        return -1, -1

    # Single-line docstring?
    if line.count(triple) >= 2:
        return i, i

    # Multi-line docstring: search closing triple
    j = i + 1
    while j < len(remainder):
        if triple in remainder[j]:
            return i, j
        j += 1

    # Unclosed triple quotes—treat as absent
    return -1, -1

def ensure_header_and_future(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    original = lines[:]

    # Always split off shebang/encoding first (they must remain at top)
    prefix, remainder = split_shebang_encoding(lines)

    # 1) Ensure SPDX header (independent of future import)
    body: List[str] = []
    header_added = False
    if not has_spdx(lines):
        body.extend(HEADER_LINES)
        header_added = True

    # Continue with the rest of the file content after shebang/encoding
    body.extend(remainder)

    # 2) Ensure future import (ALWAYS check, even when SPDX already present)
    future_added = False
    if not has_future_import(lines):
        # Find a real top-level module docstring (if any) in 'body'
        ds_start, ds_end = find_top_docstring_block(body)

        # We want to insert the future import:
        # - right after the docstring block if found, else
        # - at the top of 'body' (which is after header if we added it)
        insert_at = 0 if ds_start == -1 else ds_end + 1

        # Make sure there is exactly one blank line before/after for neatness
        # Insert a blank line BEFORE if the insertion point is on a non-blank line
        if insert_at < len(body) and body[insert_at].strip():
            body.insert(insert_at, "\n")
            insert_at += 1

        body.insert(insert_at, FUTURE_LINE)
        insert_at += 1

        # Ensure a blank line AFTER the future import unless one already exists
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

def walk_and_process(root: str) -> None:
    """
    Walk `root` directory recursively and process every .py file.
    """
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py"):
                full_path = os.path.join(dirpath, fn)
                try:
                    ensure_header_and_future(full_path)
                except Exception as exc:
                    print(f"❌ Error processing {full_path}: {exc}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Scanning for .py files under: {target}\n")
    walk_and_process(target)
    print("\nDone.")
