# Software Release And Versioning Strategy

This document describes a lightweight but robust release and versioning strategy designed for a solo developer today, with a clear path to grow into a multi‑developer workflow later.

## 1. Goals

- Keep the process simple enough for one person to follow consistently.
- Make it easy to reproduce and compare releases.
- Support General Available (GA), maintenance releases, and fast hotfixes.
- Allow future expansion to more branches and CI without changing the core versioning scheme.

## 2. Branch Model (Solo Developer)

For a single developer, keep long‑lived branches to a minimum.

### 2.1 Long‑Lived Branches

- `main`  
  - Always buildable and reasonably stable.  
  - All GA and maintenance releases come from this branch.  
  - Tagged releases are cut from `main`.

### 2.2 Short‑Lived Branches (Optional)

Use short‑lived branches only when you want isolation for a task:

- `feature/<topic>`  
  - New features, refactors, larger changes.  
  - Example: `feature/ofdm-heatmap`, `feature/group-delay-plot`.

- `fix/<topic>`  
  - Non‑critical bugfixes and minor changes.  
  - Example: `fix/pre-eq-metric`, `fix/constellation-normalization`.

Typical flow for a task:

```bash
git checkout main
git pull
git checkout -b feature/ofdm-heatmap
# work, commit, test
git checkout main
git merge feature/ofdm-heatmap
git branch -d feature/ofdm-heatmap
git push origin main
```

There is no need for a permanent `develop`, `maintenance`, or `daily-builds` branch at this stage; those can be introduced later if needed.

## 3. Versioning Scheme (Four‑Point x.x.x.x)

Use a four‑part version number:

> `MAJOR.MINOR.MAINTENANCE.BUILD`

### 3.1 Field Definitions

| Position | Name        | Purpose                                                                 | Example |
|----------|-------------|-------------------------------------------------------------------------|---------|
| 1        | MAJOR       | Breaking changes, major architecture or API changes                    | `2`     |
| 2        | MINOR       | New features and improvements, backward‑compatible                      | `3`     |
| 3        | MAINTENANCE | Maintenance / patch level for a given MAJOR.MINOR line                 | `1`     |
| 4        | BUILD       | Build or hotfix counter on top of a specific MAJOR.MINOR.MAINTENANCE   | `5`     |

Example full version: `2.3.1.5`

### 3.2 Mapping To Release Types

- **General Available (GA)**  
  - `BUILD = 0`  
  - Example: `1.4.2.0` is a GA release.

- **Maintenance Release**  
  - Increment `MAINTENANCE`, reset `BUILD` to `0`.  
  - Example: `1.4.3.0` is the next maintenance release on the 1.4 line.

- **Fix / Hotfix**  
  - Keep `MAJOR.MINOR.MAINTENANCE` constant, increment `BUILD`.  
  - Example: `1.4.3.1`, `1.4.3.2`, etc.

This lets you quickly see whether you are on an original GA, a later maintenance release, or a subsequent hotfix.

## 4. Tagging Conventions

Use annotated Git tags to record every release:

- Tag name format: `vMAJOR.MINOR.MAINTENANCE.BUILD`
- Examples:
  - `v1.3.0.0`  (GA)
  - `v1.3.1.0`  (maintenance)
  - `v1.3.1.1`  (hotfix)

Create tags from the `main` branch after bumping the version in code:

```bash
git checkout main
# edit version in pyproject.toml / __init__.py
git commit -am "Bump version to 1.3.0.0"
git tag -a v1.3.0.0 -m "PyPNM 1.3.0.0 GA"
git push origin main
git push origin v1.3.0.0
```

The tags are your single source of truth for which code went into which release.

## 5. Release Workflows

### 5.1 Day‑To‑Day Development

1. Start from `main`:
   - `git checkout main`
   - `git pull`
2. Optionally create a short‑lived branch:
   - `git checkout -b feature/<topic>` or `fix/<topic>`
3. Implement changes, commit as needed.
4. Run tests and minimal QA.
5. Merge back into `main` and push:
   - `git checkout main`
   - `git merge feature/<topic>`
   - `git branch -d feature/<topic>`
   - `git push origin main`

During this phase you do **not** need to bump the version for every commit.

### 5.2 Creating A General Available (GA) Release

When the current state of `main` is stable and you want to publish a new GA release:

1. Decide the new version, for example `1.3.0.0`.
2. Update the version field in your code (for example in `pyproject.toml` and/or `__init__.py`).
3. Commit the version bump:
   - `git commit -am "Bump version to 1.3.0.0"`
4. Tag the release:
   - `git tag -a v1.3.0.0 -m "PyPNM 1.3.0.0 GA"`
5. Push code and tag:
   - `git push origin main`
   - `git push origin v1.3.0.0`
6. Build and publish release artifacts (wheels, Docker images, documentation, etc.).

### 5.3 Creating A Maintenance Release

Use a maintenance release when you have accumulated bug fixes or small improvements on top of a GA:

1. Fix issues on `main` as part of normal development.
2. Decide the new version, for example `1.3.1.0` (increment `MAINTENANCE`, reset `BUILD` to `0`).
3. Update the version field in code and commit.
4. Tag:
   - `git tag -a v1.3.1.0 -m "PyPNM 1.3.1.0 maintenance release"`
5. Push `main` and the tag.
6. Build and publish artifacts.

### 5.4 Creating A Hotfix

For urgent bugs discovered in a just‑released version:

1. Fix the bug on `main` as soon as possible.
2. Bump `BUILD` for the current maintenance line, e.g. `1.3.1.0` → `1.3.1.1`.
3. Update the version in code and commit.
4. Tag:
   - `git tag -a v1.3.1.1 -m "PyPNM 1.3.1.1 hotfix"`
5. Push `main` and the tag.
6. Build and publish hotfix artifacts.

This keeps the process fast for a solo developer without sacrificing traceability.

## 6. Dev / Daily Builds

If you introduce CI later, you can distinguish “dev” or “daily” builds from the same scheme:

- Always build dev artifacts from the tip of `main` (or from a future `develop` branch).
- Use either:
  - A suffix on the version (in tags or artifacts), such as `1.4.0.0-dev.20251122` or `1.4.0.0-dev.<short-sha>`, or
  - Keep the code version at the next planned release number (for example `1.4.0.0`) and rely on the Git SHA and CI build number to identify the exact dev build.

Initially, you can keep it very simple:

- Only tag **real** GA, maintenance, and hotfix releases.
- For dev testing, just use `main` plus the Git commit hash.

## 7. Future Evolution (When The Team Grows)

If more developers join or you want more formal stabilization, you can extend this strategy without changing the versioning scheme:

- Add a `develop` branch as the integration branch for day‑to‑day work.
- Add `release/x.y` branches for stabilizing major or minor releases.
- Reserve `main` for code that has already passed release criteria.
- Keep using the same `MAJOR.MINOR.MAINTENANCE.BUILD` scheme and tag conventions.

Because the versioning scheme is stable and tag‑driven, you can grow the process around it over time without invalidating existing releases or documentation.
