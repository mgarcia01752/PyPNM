# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import pkg_resources

def export_requirements(output_file: str = "requirements.txt") -> None:
    """
    Write all installed packages (name==version) to a requirements.txt file.
    """
    # Sort alphabetically by package name
    installed = sorted(
        pkg_resources.working_set,
        key=lambda dist: dist.project_name.lower()
    )
    with open(output_file, "w") as f:
        for dist in installed:
            f.write(f"{dist.project_name}=={dist.version}\n")

if __name__ == "__main__":
    export_requirements()
    print("✅ requirements.txt generated.")
