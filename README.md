<p align="center">
  <a href="docs/index.md">
    <picture>
      <source srcset="docs/images/logo/pypnm-dark-mode-hp.png"
              media="(prefers-color-scheme: dark)" />
      <img src="docs/images/logo/pypnm-light-mode-hp.png"
           alt="PyPNM Logo"
           width="200"
           style="border-radius: 16px;" />
    </picture>
  </a>
</p>

# PyPNM - Proactive Network Maintenance Toolkit

[![PyPNM Version](https://img.shields.io/github/v/tag/mgarcia01752/PyPNM?label=PyPNM&sort=semver)](https://github.com/mgarcia01752/PyPNM/tags)
[![PyPI - Version](https://img.shields.io/pypi/v/pypnm-docsis.svg)](https://pypi.org/project/pypnm-docsis/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pypnm-docsis.svg)](https://pypi.org/project/pypnm-docsis/)
[![Daily Build](https://github.com/mgarcia01752/PyPNM/actions/workflows/daily-build.yml/badge.svg?branch=main)](https://github.com/mgarcia01752/PyPNM/actions/workflows/daily-build.yml)
![CodeQL](https://github.com/mgarcia01752/PyPNM/actions/workflows/codeql.yml/badge.svg)
[![PyPI Install Check](https://github.com/mgarcia01752/PyPNM/actions/workflows/pypi-install-check.yml/badge.svg?branch=main)](https://github.com/mgarcia01752/PyPNM/actions/workflows/pypi-install-check.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04%20%7C%2024.04%20LTS-E95420?logo=ubuntu&logoColor=white)](https://github.com/mgarcia01752/PyPNM)

PyPNM is a DOCSIS 3.x/4.0 Proactive Network Maintenance toolkit for engineers who want repeatable, scriptable visibility into modem health. It can run purely as a Python library or as a FastAPI web service for real-time dashboards and offline analysis workflows.

## Choose your path

- **Use PyPNM as a library** - install `pypnm-docsis` into an existing virtual environment and import the helpers inside notebooks or other tooling.
- **Run the full platform** - clone the repo, run `./install.sh`, and use the FastAPI + tooling stack for captures, dashboards, and automation.

## Table of contents

- [Key Features](#key-features)
- [Prerequisites](#prerequisites)
  - [Operating Systems](#operating-systems)
  - [Shell Dependencies](#shell-dependencies)
- [Getting Started](#getting-started)
  - [Install From PyPI (Library Only)](#install-from-pypi-library-only)
  - [1) Clone](#1-clone)
  - [2) Install](#2-install)
  - [3) Activate The Virtual Environment](#3-activate-the-virtual-environment)
  - [4) Configure System Settings](#4-configure-system-settings)
  - [5) Run The FastAPI Service Launcher](#5-run-the-fastapi-service-launcher)
  - [6) (Optional) Serve The Documentation](#6-optional-serve-the-documentation)
  - [7) Explore The API](#7-explore-the-api)
- [API Documentation Quick Links](#api-documentation-quick-links)
- [SNMP Notes](#snmp-notes)
- [CableLabs Specifications & MIBs](#cablelabs-specifications--mibs)
- [PNM Architecture & Guidance](#pnm-architecture--guidance)
- [License](#license)
- [Maintainer](#maintainer)

## Key features

- **Structured SNMP Integration**  
  Poll DOCSIS cable modems for RxMER, OFDM/OFDMA profiles, spectrum, upstream pre-EQ, and related telemetry using typed models.

- **Binary Capture Decoding**  
  Retrieve modem-generated PNM files (TFTP or SNMP) and decode them into structured objects instead of ad-hoc byte parsing.

- **FastAPI REST Service**  
  Expose capture, analysis, and file-management APIs for dashboards, automation pipelines, CI, or remote tools.

- **OFDM & OFDMA Utilities**  
  Channel estimation, FEC summary, tap-delay and group-delay helpers, constellation views, and related DSP utilities.

- **Analysis Helpers**  
  Shannon capacity, SNR / margin deltas, basic statistics, and reusable primitives for more advanced analysis.

- **Extensible Framework**  
  Add new PNM file types, analysis routines, and endpoints without rewriting the core plumbing.

- **CLI Tools**  
  Scriptable helpers for capture orchestration, file management, and repeatable lab workflows.

## Prerequisites

### Operating systems

Linux, validated on:

- Ubuntu 22.04 LTS
- Ubuntu 24.04 LTS

Other modern Linux distributions may work but are not yet part of the test matrix.

### Shell dependencies

From a fresh system, install Git:

```bash
sudo apt update
sudo apt install -y git
```

Python and remaining dependencies are handled by the installer.

## Getting started

### Install from PyPI (library only)

If you only need PyPNM as a Python library (for example, to embed DOCSIS PNM capture and analysis into your own tools or notebooks), you can install the published package directly from PyPI into an existing virtual environment:

```bash
pip install pypnm-docsis
```

For full FastAPI service usage and development, use the repository-based flow below.

### 1) Clone

```bash
git clone https://github.com/mgarcia01752/PyPNM.git
cd PyPNM
```

### 2) Install

The installer sets up OS prerequisites (where possible), creates a virtual environment, and installs PyPNM in editable mode with development and documentation extras.

```bash
./install.sh --help
```

Common flags (mix and match as needed):

| Flag | Purpose |
|------|---------|
| `--pnm-file-retrieval-setup` | Launches `tools/pnm_file_retrieval_setup.py` after install so you can pick a topology. See the [PNM File Retrieval Overview](docs/topology/index.md).
| `--demo-mode` | Seeds demo data/paths for offline exploration. See the [demo mode guide](./demo/README.md).
| `--production` | Reverts demo-mode changes and restores your previous `system.json` backup.
| `--demo-mode .env-demo` | Installs into a named virtual environment instead of `.env`.

> **Note:** `--pnm-file-retrieval-setup` backs up `system.json` automatically. Keep that backup handy if you are experimenting with different lab topologies.

Installer extras:

- Runs a silent alias helper (when available) that adds shortcuts—such as `config-menu`—to your shell rc file.
- After installation, source your shell rc file once (for example, `source ~/.bashrc`) to pick up any new aliases.

### 3) Activate the virtual environment

If you used the installer defaults, activate the `.env` environment:

```bash
source .env/bin/activate
```

If you installed into a custom environment directory, activate that instead (for example, `.env-demo`):

```bash
source .env-demo/bin/activate
```

### 4) Configure system settings

Have the following handy before diving in:

- Cable Modem (CM) MAC address and IP address
- SNMPv2c write community string
- A reachable TFTP/SSH path for moving PNM files between the modem, server, and PyPNM host

> **Tip:** Capture this info in a lab runbook before running the installer so you can paste it straight into the prompts without hunting for values mid-setup.

System configuration lives in `src/pypnm/settings/system.json`. Manage it via:

- `source ~/.bashrc && config-menu` (alias added by the installer) or `python ./tools/system_config/menu.py`
- The [System Configuration Reference](docs/system/system-config.md) for field-by-field detail
- `./tools/pnm_file_retrieval_setup.py` to select and initialize a file-retrieval topology (local, TFTP, SCP/SFTP, etc.)

If you installed with `--pnm-file-retrieval-setup`, the helper runs automatically and backs up `system.json` before any edits.

<!-- Removed duplicated Step 3/4 block -->

### 5) [Run the FastAPI service launcher](docs/system/pypnm-cli.md)

Show help:

```bash
pypnm --help
```

HTTP (default: `http://127.0.0.1:8000`):

```bash
pypnm
```

HTTPS example:

```bash
pypnm --host 0.0.0.0 --port 443 --ssl --cert ./certs/cert.pem --key ./certs/key.pem &
```

Development hot-reload:

```bash
pypnm --reload
```

### 6) (Optional) Serve the documentation

HTTP (default: `http://127.0.0.1:8001`):

```bash
mkdocs serve
```

### 7) Explore the API

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)  
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- MkDocs docs: [http://localhost:8001](http://localhost:8001)  
- Postman download: [https://www.postman.com/downloads/](https://www.postman.com/downloads/)

> **Tip:** Postman collections are a convenient way to rehearse larger JSON payloads and capture known-good requests for regression testing.

Postman is recommended for larger or nested JSON payloads and for collecting repeatable test collections and visualizations.

## Documentation

- [Docs hub](./docs/index.md) - task-based entry point (install, configure, operate, contribute).
- [FastAPI reference](./docs/api/fast-api/index.md) - Endpoint details and request/response schemas.
- [Python API reference](./docs/api/python/index.md) - Importable helpers and data models.

## SNMP notes

- SNMPv2c is supported  
- SNMPv3 is currently stubbed and not yet supported

## CableLabs specifications & MIBs

- [CM-SP-MULPIv3.1](https://www.cablelabs.com/specifications/CM-SP-MULPIv3.1)  
- [CM-SP-CM-OSSIv3.1](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1)  
- [CM-SP-MULPIv4.0](https://www.cablelabs.com/specifications/CM-SP-MULPIv4.0)  
- [CM-SP-CM-OSSIv4.0](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv4.0)  
- [DOCSIS MIBs](https://mibs.cablelabs.com/MIBs/DOCSIS/)

## PNM architecture & guidance

- [CM-TR-PMA](https://www.cablelabs.com/specifications/CM-TR-PMA)  
- [CM-GL-PNM-HFC](https://www.cablelabs.com/specifications/CM-GL-PNM-HFC)  
- [CM-GL-PNM-3.1](https://www.cablelabs.com/specifications/CM-GL-PNM-3.1)

## License

[`MIT LICENSE`](./LICENSE)

## Next steps

- Review [PNM topology options](docs/topology/index.md) to decide how captures will move through your network.
- Follow the [System Configuration guide](docs/system/system-config.md) to tailor `system.json` for your lab.
- Explore [system tools](docs/system/menu.md) and [operational scripts](docs/tools/index.md) for day-to-day automation.

## Maintainer

Maurice Garcia

- [Email](mailto:mgarcia01752@outlook.com)  
- [LinkedIn](https://www.linkedin.com/in/mauricemgarcia/)
