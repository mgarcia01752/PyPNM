
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import ast
import importlib.util
from pathlib import Path

def find_imports_in_file(filepath):
    """Parse a Python file and return top-level module names it imports."""
    with open(filepath, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=str(filepath))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and not node.level:
                modules.add(node.module.split('.')[0])
    return modules

def is_third_party(module_name, project_root):
    """Determine if a module is third-party by checking its spec origin."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            origin = spec.origin.lower()
            # Exclude stdlib and project files
            if 'site-packages' in origin or 'dist-packages' in origin:
                return True
    except (ImportError, AttributeError):
        pass
    return False

def main():
    project_root = Path(__file__).parent
    src_dir = project_root / 'src'
    all_imports = set()

    # Collect imports from all .py files under src/
    for py_file in src_dir.rglob('*.py'):
        all_imports.update(find_imports_in_file(py_file))

    # Filter to third-party imports
    requirements = {
        mod: importlib.metadata.version(mod)
        for mod in sorted(all_imports)
        if is_third_party(mod, project_root)
    }

    # Write to requirements.txt
    req_file = project_root / 'requirements.txt'
    with open(req_file, 'w', encoding='utf-8') as f:
        for mod, ver in requirements.items():
            f.write(f"{mod}=={ver}\n")

    print(f"Generated {req_file} with {len(requirements)} packages.")

if __name__ == "__main__":
    main()
