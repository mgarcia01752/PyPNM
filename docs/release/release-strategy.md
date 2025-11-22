# PyPNM Release And Versioning Guide (Single-Branch Model)

This guide describes how to manage versions, branches, and releases for the PyPNM project using a single primary branch and GitHub Actions.

## 1. Branch Model

For current PyPNM development, a **single-branch** model is used:

- `main`  
  Active development and release branch. All regular work and official releases happen from `main`.

Optional branches you may use later:

- `feature/*`  
  Short-lived branches for experiments or isolated changes. Merge back into `main` when done, then delete.

- `stable` (optional, future)  
  You can introduce a `stable` branch later if you need a dedicated GA branch. For now, it is not required; tags on `main` provide clear release points.

When in doubt, work directly on `main`, create tags for each release, and use Git history plus tags to reproduce any version.

## 2. Single Source Of Truth For Version

The canonical version string lives in:

```text
src/pypnm/version.py
```

Recommended structure:

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

PyPNM uses a four-part version:

```text
MAJOR.MINOR.MAINTENANCE.BUILD
```

Guidelines:

- `MAJOR`  
  Increment when there are significant breaking changes or large structural shifts.

- `MINOR`  
  Increment when adding features in a backward-compatible way.

- `MAINTENANCE`  
  Increment when fixing bugs or making compatible improvements that are smaller than a full minor release.

- `BUILD`  
  Increment for very small hotfixes or internal rebuilds that do not change public behavior but still need a distinct version.

Examples:

- `0.1.2.0` – Minor feature set with maintenance updates.  
- `0.2.0.0` – Next minor release.  
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

- The script only edits the `__version__` line in `src/pypnm/version.py`.  
- If the requested version is the same as the current one, it prints a message and exits without modifying the file.

### 4.2 `tools/release.py`

This script automates the release flow from a branch (by default `main`):

- Ensures the git working tree is clean.  
- Checks out the target branch and pulls with `--ff-only`.  
- Calls `tools/bump_version.py` with the target version.  
- Runs `pytest`.  
- Commits the version bump.  
- Creates an annotated git tag.  
- Pushes the branch and tag to `origin`.

Common usage patterns:

```bash
# Dry run: see what would happen, but do nothing
tools/release.py 0.1.3.0 --dry-run

# Release from main (single-branch model)
tools/release.py 0.1.3.0

# Release without running tests (not recommended)
tools/release.py 0.1.3.0 --skip-tests

# Use a different tag prefix (for example, pypnm-0.1.3.0)
tools/release.py 0.1.3.0 --tag-prefix pypnm-
```

When using `--dry-run`, the script prints the planned steps and exits without changing anything.

The `--branch` option still exists (for example, `--branch stable`) but is optional and only needed if you introduce additional long-lived branches in the future.

## 5. Tag-Based Release Flow On `main`

In the single-branch model, releases are created from `main` and marked with tags, for example:

- `v0.1.2.0`  
- `v0.1.3.0`  
- `v0.2.0.0`

### 5.1 Standard Release Flow From `main`

Use this flow for each new release:

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
- You can later reproduce this release with:

  ```bash
  git checkout v0.1.3.0
  ```

### 5.2 Optional Future: Introducing `stable`

If, in the future, you want stricter separation between development and GA releases, you can introduce a `stable` branch without changing the scripts:

```bash
# Create or update stable from main
git checkout main
git pull origin main

git checkout stable
git pull origin stable || true    # if stable is new, this may fail and can be ignored
git merge main
git push origin stable
```

Then release from `stable` instead of `main`:

```bash
tools/release.py 0.2.0.0 --branch stable --dry-run
tools/release.py 0.2.0.0 --branch stable
```

The rest of this guide still applies; only the target branch changes.

## 6. Daily Build And Online Checks (GitHub Actions)

PyPNM uses GitHub Actions to run tests on a schedule. This acts as an online “daily build” confirming that `main` is still healthy.

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

### 7.2 Bump Version Only (Without Tagging)

```bash
# Next maintenance version from current
tools/bump_version.py --next maintenance

# Explicit version
tools/bump_version.py 0.1.3.0
```

### 7.3 Full Release From `main` (Single-Branch Model)

```bash
git checkout main
git pull origin main
git status

tools/bump_version.py --current
tools/release.py 0.1.3.0 --dry-run
tools/release.py 0.1.3.0
```

### 7.4 Optional Future Release From `stable`

```bash
git checkout main
git pull origin main

git checkout stable
git pull origin stable || true
git merge main
git push origin stable

tools/release.py 0.2.0.0 --branch stable --dry-run
tools/release.py 0.2.0.0 --branch stable
```

With these steps, PyPNM gains a repeatable software release strategy based on a single primary branch with tags:
- A single canonical version source.  
- Scripts that manage version bumps and tagging.  
- Clear release points via git tags on `main`.  
- Automated daily tests via GitHub Actions.
