#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Recursively add MIT license headers to all .py files in a directory tree,
skipping any file that already has an SPDX identifier.
"""

import os
import sys

# The two lines you want to insert
HEADER_LINES = [
    "# SPDX-License-Identifier: MIT\n",
    "# Copyright (c) 2025 Maurice Garcia\n",
    "\n"
]

def process_file(path: str) -> None:
    """
    Read the file at `path`. If it doesn't already contain our SPDX header,
    rewrite it with the header inserted (preserving a leading shebang if present).
    """
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Skip if header already there
    for line in lines[:5]:  # only need to check the top few lines
        if "SPDX-License-Identifier: MIT" in line:
            print(f"⏭ Skipping (already has header): {path}")
            return

    # Build new content
    new_lines = []
    idx = 0

    # Preserve shebang if present
    if lines and lines[0].startswith("#!"):
        new_lines.append(lines[0])
        idx = 1

    # Insert our header
    new_lines.extend(HEADER_LINES)

    # Append the rest of the file
    new_lines.extend(lines[idx:])

    # Write back
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"✅ Updated: {path}")

def walk_and_process(root: str) -> None:
    """
    Walk `root` directory recursively and process every .py file.
    """
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py"):
                full_path = os.path.join(dirpath, fn)
                process_file(full_path)

if __name__ == "__main__":
    # Allow passing a directory, default to current working directory
    target = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Scanning for .py files under: {target}\n")
    walk_and_process(target)
    print("\nDone.")
