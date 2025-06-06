#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia


import re

# snmptranslate -M mibs -m all -Tz > snmptranslate_output.txt

def parse_snmptranslate_output(file_path: str) -> dict:
    """
    Parses the output of `snmptranslate -Tz` into a Python dictionary.

    Args:
        file_path (str): Path to the file containing snmptranslate output.

    Returns:
        dict: Dictionary with OID names as keys and dotted-decimal OIDs as values.
    """
    oid_dict = {}

    with open(file_path, 'r') as f:
        for line in f:
            match = re.match(r'"(.+?)"\s+"([\d\.]+)"', line.strip())
            if match:
                name, oid = match.groups()
                oid_dict[name] = oid

    return oid_dict


def write_python_dict(oid_dict: dict, output_path: str):
    """
    Writes the OID dictionary to a Python file as a formatted constant.

    Args:
        oid_dict (dict): Dictionary with name → OID mappings.
        output_path (str): Destination .py file.
    """
    with open(output_path, 'w') as f:
        f.write("COMPILED_OIDS = {\n")
        for name, oid in oid_dict.items():
            f.write(f'    "{name}" : "{oid}",\n')
        f.write("}\n")


if __name__ == "__main__":
    input_file = "snmptranslate_output.txt"   # <-- Replace this with your actual input file
    output_file = "docs_oids.py"

    docs_oids = parse_snmptranslate_output(input_file)
    write_python_dict(docs_oids, output_file)

    print(f"Converted {len(docs_oids)} OIDs to Python dictionary and saved to '{output_file}'")
