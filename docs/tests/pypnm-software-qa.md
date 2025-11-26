# pypnm-software-qa-checker User Guide

A lightweight command-line helper that runs a standard set of **software quality checks** for the PyPNM
codebase. It is intended for local development (before commits) and for simple CI pipelines.

## 1. Prerequisites

Before using the QA checker, make sure you have the development dependencies installed in your virtual
environment:

```bash
cd ~/Projects/PyPNM
pip install -e '.[dev]'
```

This ensures the following tools are available (as defined in `pyproject.toml`):

- `ruff` – linting and unused-code detection
- `pytest` – unit and integration tests
- `pycycle` – import cycle detection (installed separately via `pip install pycycle` if not already present)

## 2. Command Overview

Once installed via `pyproject.toml` as a console script, the QA checker is available as:

```bash
pypnm-software-qa-checker [OPTIONS]
```

By default (with no options), it runs a **full QA sweep** over your project:

1. `ruff check src tests`  
2. `pytest`  
3. `pycycle --here` (from the project root)

Each step is run in sequence; if any step fails (non-zero exit code), the script exits with that code and
prints the failing command.

## 3. Options

The CLI is designed to be simple and focused on the PyPNM layout (`src/` and `tests/`).

> Note: The exact options must match the implementation in `pypnm/tools/pypnm_software_qa_checker.py`.
> The list below describes the **intended** interface.

| Option           | Description                                                                                         |
|------------------|-----------------------------------------------------------------------------------------------------|
| `--unused-only`  | Run only the **unused-code** checks via `ruff` (unused imports and unused local variables).        |
| `--no-tests`     | Skip running `pytest`.                                                                             |
| `--no-cycle`     | Skip running `pycycle --here` (import cycle detection).                                            |
| `-h`, `--help`   | Show help and exit.                                                                                |

### 3.1 Unused-only mode

When you only want to look for unused imports and unused local variables, use:

```bash
pypnm-software-qa-checker --unused-only
```

This is equivalent to running:

```bash
ruff check src tests --select F401,F841
```

Where:

- `F401` – unused imports  
- `F841` – local variable assigned but never used  

In `--unused-only` mode:

- No tests are run
- No cycle checks are run

## 4. Typical Workflows

### 4.1 Full QA before pushing

Use this when you are about to push a feature branch or submit a PR:

```bash
pypnm-software-qa-checker
```

Effectively runs:

- Lint (including style / unused / basic correctness via `ruff`)
- Tests (`pytest`)
- Import cycle detection (`pycycle --here`)

### 4.2 Quick unused-code cleanup

Use this when you are doing refactors and just want to strip unused imports/locals:

```bash
pypnm-software-qa-checker --unused-only
```

You can also call `ruff` directly if you want more control:

```bash
ruff check src tests --select F401,F841
```

### 4.3 Skip long-running tests

If you have expensive tests and only want lint + cycle detection:

```bash
pypnm-software-qa-checker --no-tests
```

### 4.4 Skip cycle detection

If you already know your imports are clean and just want lint + tests:

```bash
pypnm-software-qa-checker --no-cycle
```


## 5. Exit Codes and CI Integration

The script is designed to be CI-friendly:

- Exit code `0` – all selected checks passed
- Non-zero exit code – the first failing step’s exit code

A simple GitHub Actions step could look like:

```yaml
- name: PyPNM software QA
  run: pypnm-software-qa-checker
```

For a faster CI job that only cares about lint + tests (no cycle detection):

```yaml
- name: PyPNM software QA (no cycle)
  run: pypnm-software-qa-checker --no-cycle
```

## 6. Troubleshooting

### 6.1 `pypnm-software-qa-checker: command not found`

- Make sure you are in the right virtual environment.
- Reinstall in editable mode with dev extras:

  ```bash
  pip install -e '.[dev]'
  ```

- Confirm the console script is listed by running:

  ```bash
  pip show pypnm
  ```

### 6.2 Ruff or pytest not installed

If the script reports that it cannot find `ruff` or `pytest`, verify that:

- You are in the environment where `.[dev]` was installed.
- `ruff` and `pytest` appear in `pip list`.

## 7. Where the Script Lives

The recommended layout is:

- Script module: `src/pypnm/tools/pypnm_software_qa_checker.py`
- Console entry point in `pyproject.toml`:

  ```toml
  [project.scripts]
  pypnm      = "pypnm.cli:main"
  docs-serve = "mkdocs.__main__:serve"
  docs-build = "mkdocs.__main__:build"
  pypnm-software-qa-checker = "pypnm.tools.pypnm_software_qa_checker:main"
  ```

This keeps all tooling namespaced under `pypnm.tools` while giving you a short,
memorable `pypnm-software-qa-checker` command from the shell.
