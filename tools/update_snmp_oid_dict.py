#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict
import tempfile

# Adjusted relative paths (script lives in 'tools/')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIB_DIR = PROJECT_ROOT / "mibs"
OUTPUT_FILE = PROJECT_ROOT / "src/pypnm/snmp/compiled_oids.py"

def run_snmptranslate(output_path: Path) -> None:
    """
    Runs `snmptranslate -Tz` using the local MIB directory and saves the output.

    Args:
        output_path (Path): File to save the raw output.
    """
    cmd = [
        "snmptranslate",
        "-M", str(MIB_DIR.resolve()),
        "-m", "all",
        "-Tz"
    ]
    with output_path.open("w", encoding="utf-8") as f:
        subprocess.run(cmd, check=True, stdout=f)

def parse_snmptranslate_output(file_path: Path) -> Dict[str, str]:
    """
    Parses the output of `snmptranslate -Tz` into a dictionary.

    Args:
        file_path (Path): Path to the file containing snmptranslate output.

    Returns:
        Dict[str, str]: Dictionary with OID names as keys and dotted-decimal OIDs as values.
    """
    oid_dict = {}
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r'"(.+?)"\s+"([\d\.]+)"', line.strip())
            if match:
                name, oid = match.groups()
                oid_dict[name] = oid
    return oid_dict

def write_python_dict(oid_dict: Dict[str, str], output_path: Path) -> None:
    """
    Writes the OID dictionary to a Python file as a formatted constant.

    Args:
        oid_dict (Dict[str, str]): Dictionary of OID names and values.
        output_path (Path): Path to output .py file.
    """
    timestamp = datetime.utcnow().isoformat()
    with output_path.open('w', encoding='utf-8') as f:
        f.write(f"""# Auto-generated OID dictionary from snmptranslate -Tz
# Do not modify manually. Generated on: {timestamp}

COMPILED_OIDS = {{
""")
        for name, oid in sorted(oid_dict.items()):
            f.write(f'    "{name}": "{oid}",\n')
        f.write("}\n")

def main():
    print("🔄 Generating compiled OIDs from MIBs...")

    if not MIB_DIR.exists():
        raise FileNotFoundError(f"MIB directory '{MIB_DIR}' not found.")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_output = Path(tmpdir) / "snmptranslate_output.txt"
        run_snmptranslate(tmp_output)
        oid_dict = parse_snmptranslate_output(tmp_output)
        write_python_dict(oid_dict, OUTPUT_FILE)

    print(f"✅ Compiled {len(oid_dict)} OIDs to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()
