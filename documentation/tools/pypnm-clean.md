# PyPNM Cleanup Script

The **PyPNM Cleanup Script** is a flexible shell utility located in the `tools/` directory. It provides a structured way to clean up logs, Python cache files, build artifacts, generated output, and internal `.data` folders related to PNM processing.

> This tool is essential for maintaining a clean development environment and resetting analysis directories.

## 🚀 Features

* Clean specific or all categories of build and runtime artifacts
* Supports scoped operations (e.g., logs only)
* Works from any root directory (defaults to current dir)
* Safe deletion with checks

## 📁 Directory Structure Cleaned

| Option     | Cleans                                   |
| ---------- | ---------------------------------------- |
| `--logs`   | `logs/`                                  |
| `--python` | `__pycache__/`, `*.pyc`, `.pytest_cache` |
| `--build`  | `build/`, `dist/`, `*.egg-info`          |
| `--pnm`    | `.data/pnm/`, `.data/db/`                |
| `--excel`  | `.data/xlsx/`, `.data/csv/`              |
| `--output` | `output/`                                |
| `--all`    | All of the above                         |

## 🧪 Usage

```bash
./tools/clean.sh [OPTIONS] [ROOT_DIR]
```

* `OPTIONS`: One or more of:

  * `--all`
  * `--logs`
  * `--python`
  * `--build`
  * `--pnm`
  * `--excel`
  * `--output`
* `ROOT_DIR`: Optional path to apply the cleanup (defaults to current directory)

### ✅ Examples

Clean everything:

```bash
./tools/clean.sh --all
```

Clean only logs and build artifacts:

```bash
./tools/clean.sh --logs --build
```

Clean PNM and Excel data from a different root:

```bash
./tools/clean.sh --pnm --excel ~/Projects/PyPNM
```