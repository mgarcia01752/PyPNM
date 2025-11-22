# PyPNM Release And Versioning Guide

This guide describes how to manage versions, branches, and releases for the PyPNM project using the built‑in tools and GitHub Actions.

## 1. Branch Model

PyPNM uses three long‑lived branches:

- `main`  
  Active development branch. Most day‑to‑day work happens here.

- `develop` (optional for now)  
  You can use this later as a staging branch if you want a stricter flow. For initial phases, `main` and `stable` are usually enough.

- `stable`  
  Represents code that is considered General Available (GA). Releases intended for wider use should come from this branch.

When in doubt during early development, work from `main`, and when you are ready to ship a stable version, merge `main` into `stable` and release from `stable`.

## 2. Single Source Of Truth For Version

The canonical version string lives in:

```text
src/pypnm/version.py
```

Structure:

```python
from __future__ import annotations

__all__ = ["__version__"]

# MAJOR.MINOR.MAINTENANCE.BUILD
__version__: str = "0.1.2.0"
```

Only this file should be edited to change the version. All other places (for example, FastAPI’s `version` field) must import `__version__` from here.

Example in the FastAPI app:

```python
from fastapi import FastAPI
from pypnm.version import __version__

app = FastAPI(
    title="PyPNM REST API",
    version=__version__,
    description=fast_api_description,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

## 3. Versioning Scheme

PyPNM uses a four‑part version:

```text
MAJOR.MINOR.MAINTENANCE.BUILD
```

Guidelines:

- `MAJOR`  
  Increment when there are significant breaking changes or large structural shifts.

- `MINOR`  
  Increment when adding features in a backward‑compatible way.

- `MAINTENANCE`  
  Increment when fixing bugs or making compatible improvements that are smaller than a full minor release.

- `BUILD`  
  Increment for very small hotfixes or internal rebuilds that do not change public behavior but still need a distinct version.

Examples:

- `0.1.2.0` – Minor feature set with a couple of maintenance updates.  
- `0.2.0.0` – Next minor release from stable.  
- `1.0.0.0` – First major release.

## 4. Version Tools

Two main tools are used to manage versions and releases:

- `tools/bump_version.py`  
  Reads and updates `__version__` in `src/pypnm/version.py`.

- `tools/release.py`  
  Wraps `bump_version.py` plus git operations (tests, commit, tag, push).

### 4.1 `tools/bump_version.py`

This script can:

1. Show the current version.  
2. Compute and apply the next version.  
3. Set a specific version explicitly.

Examples:

```bash
# Show current version
tools/bump_version.py --current

# Compute and apply the next MAINTENANCE version
tools/bump_version.py --next maintenance

# Compute and apply the next BUILD version
tools/bump_version.py --next build

# Explicitly set the version
tools/bump_version.py 0.1.3.0
```

Notes:

- The script only edits the `__version__` line.  
- If the requested version is the same as the current one, it prints a message and exits without modifying the file.

### 4.2 `tools/release.py`

This script automates the release flow:

- Ensures the git working tree is clean.  
- Checks out the target branch (for example `main` or `stable`) and pulls with `--ff-only`.  
- Calls `tools/bump_version.py` with the target version.  
- Runs `pytest`.  
- Commits the version bump.  
- Creates an annotated git tag.  
- Pushes the branch and tag to `origin`.

Common usage patterns:

```bash
# Dry run: see what would happen, but do nothing
tools/release.py 0.1.3.0 --dry-run

# Release from main
tools/release.py 0.1.3.0

# Release from stable
tools/release.py 0.2.0.0 --branch stable

# Release without running tests (not recommended)
tools/release.py 0.1.3.0 --skip-tests

# Use a different tag prefix (for example, pypnm-0.1.3.0)
tools/release.py 0.1.3.0 --tag-prefix pypnm-
```

When using `--dry-run`, the script prints the planned steps and exits without changing anything.

## 5. Branch‑Based Release Flows

### 5.1 Releasing From `main`

Use this flow during early development or for internal builds.

Steps:

```bash
# 1) Make sure main is up to date and clean
git checkout main
git pull origin main
git status

# 2) Sanity check current version
tools/bump_version.py --current

# 3) Dry run the release
tools/release.py 0.1.3.0 --dry-run

# 4) Run the real release
tools/release.py 0.1.3.0
```

Results:

- `src/pypnm/version.py` is updated (for example `0.1.2.0` -> `0.1.3.0`).  
- A commit `Release 0.1.3.0` is added on `main`.  
- Tag `v0.1.3.0` is created and pushed to `origin`.

### 5.2 Releasing From `stable`

Use this flow when you are ready to expose a stable, GA‑quality build.

Steps:

```bash
# 1) Merge main into stable
git checkout main
git pull origin main

git checkout stable
git pull origin stable
git merge main

# Resolve conflicts if any, then push stable
git push origin stable

# 2) Ensure you are ready to release from stable
git status

# 3) Dry run the release from stable
tools/release.py 0.2.0.0 --branch stable --dry-run

# 4) Run the real release from stable
tools/release.py 0.2.0.0 --branch stable
```

Results:

- `src/pypnm/version.py` on `stable` is updated to the requested version.  
- A commit `Release 0.2.0.0` is added on `stable`.  
- Tag `v0.2.0.0` is created and pushed to `origin`.

## 6. Daily Build And Online Checks (GitHub Actions)

PyPNM uses GitHub Actions to run tests on a schedule. This provides an online “daily build” that confirms the project is still healthy.

The workflow file lives in:

```text
.github/workflows/daily-build.yml
```

Example content:

```yaml
name: Daily Build

on:
  schedule:
    - cron: "0 8 * * *"     # Every day at 08:00 UTC
  workflow_dispatch:         # Allow manual triggering from GitHub UI

jobs:
  daily-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]

      - name: Run tests
        run: |
          pytest
```

Notes:

- This file must be committed on the default branch (typically `main`) for the scheduled `cron` to run.  
- You can also trigger the workflow manually from the GitHub Actions tab (because of `workflow_dispatch`).

## 7. Quick Reference

### 7.1 Show Current Version

```bash
tools/bump_version.py --current
```

### 7.2 Bump Version Only

```bash
# Next maintenance version from current
tools/bump_version.py --next maintenance

# Explicit version
tools/bump_version.py 0.1.3.0
```

### 7.3 Full Release From Main

```bash
git checkout main
git pull origin main
git status

tools/bump_version.py --current
tools/release.py 0.1.3.0 --dry-run
tools/release.py 0.1.3.0
```

### 7.4 Full Release From Stable

```bash
git checkout main
git pull origin main

git checkout stable
git pull origin stable
git merge main
git push origin stable

tools/release.py 0.2.0.0 --branch stable --dry-run
tools/release.py 0.2.0.0 --branch stable
```

With these steps, PyPNM gains a repeatable software release strategy:
- A single canonical version source.  
- Scripts that manage version bumps and tagging.  
- Branch discipline between `main` and `stable`.  
- Automated daily tests via GitHub Actions.
