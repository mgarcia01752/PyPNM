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

## Table Of Contents

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
  - [5) Run The FastAPI Service](#5-run-the-fastapi-service)
  - [6) (Optional) Serve The Documentation](#6-optional-serve-the-documentation)
  - [7) Explore The API](#7-explore-the-api)
- [API Documentation Quick Links](#api-documentation-quick-links)
- [SNMP Notes](#snmp-notes)
- [CableLabs Specifications & MIBs](#cablelabs-specifications--mibs)
- [PNM Architecture & Guidance](#pnm-architecture--guidance)
- [License](#license)
- [Maintainer](#maintainer)

## Key Features

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

### Operating Systems

Linux, validated on:

- Ubuntu 22.04 LTS
- Ubuntu 24.04 LTS

Other modern Linux distributions may work but are not yet part of the test matrix.

### Shell Dependencies

From a fresh system, install Git:

```bash
sudo apt update
sudo apt install -y git
```

Python and remaining dependencies are handled by the installer.

## Getting Started

### Install From PyPI (Library Only)

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

Show installer options:

```bash
./install.sh --help
```

Standard install in `.env`:

```bash
./install.sh
```

Demo-mode install (pre-configured with sample data and demo paths):

```bash
./install.sh --demo-mode
```

Revert to production settings (restore your original `system.json`):

```bash
./install.sh --production
```

Use a custom virtual environment directory:

```bash
./install.sh --demo-mode .env-demo
```

Install and immediately launch the interactive PNM file retrieval setup helper:

Don't know what to choose? [See the PNM File Retrieval Setup documentation](docs/topology/index.md)

```bash
./install.sh --pnm-file-retrieval-setup
```

When `--pnm-file-retrieval-setup` is used, the installer will attempt to run `tools/pnm_file_retrieval_setup.py` at the end of the install in interactive, non-CI environments.

The installer also runs a silent alias helper (when available) that adds convenient shell aliases such as `config-menu` to your shell rc file. After installation, source your shell rc file (for example `source ~/.bashrc`) once to pick up any new aliases.

### 3) Activate The Virtual Environment

```bash
python3 -m venv .env
source .env/bin/activate
```

### 4) Configure System Settings

You will need:

- Cable Modem (CM) MAC address and IP address  
- SNMPv2c write community string  
- TFTP server IP/hostname reachable by both the CM and PyPNM

If  `--pnm-file-retrieval-setup` was used during installation, this step is handled automatically.

- A PNM file retrieval method (`local`, `tftp`, `scp`, `sftp`) and credentials/paths for your environment  

[System Configuration](docs/system/system-config.md) is stored in [system.json](https://github.com/mgarcia01752/PyPNM/blob/main/src/pypnm/settings/system.json). For detailed field descriptions, see:

#### System Configuration Menu

PyPNM provides an interactive menu wrapper around the individual configuration helpers:

```bash
config-menu
```

or

```bash
python ./tools/system_config/menu.py
```

The menu allows you to edit:

- `FastApiRequestDefault`
- `SNMP`  
- `PnmBulkDataTransfer`
- `PnmFileRetrieval`
- `logging`  
- `TestMode`  

Refer to the [config-menu](docs/system/menu.md) documentation for full details:

#### PNM File Retrieval Setup Helper

PyPNM ships with an interactive helper that configures how PNM files are retrieved from the TFTP or HTTP(S) server into the local `.data/pnm` tree.

Run it any time after installation:

```bash
./tools/pnm_file_retrieval_setup.py
```

The helper:

- Backs up `src/pypnm/settings/system.json` before making changes  
- Lets you choose a retrieval method (`local`, `tftp`, `scp`, `sftp`)  
- For `scp` or `sftp`, prompts for host/port/user and optional password and/or private key path  
- Tests SSH connectivity for SCP/SFTP when credentials are provided  
- Updates the `PnmFileRetrieval.retrival_method` block in `system.json` so future captures can automatically fetch PNM files through the selected path

In **demo mode**, paths are redirected to demo directories so you can exercise the analysis stack using pre-captured PNM files without talking to a live modem.

### 5) [Run The FastAPI Service Launcher](docs/system/pypnm-cli.md)

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

### 6) (Optional) Serve The Documentation

HTTP (default: `http://127.0.0.1:8001`):

```bash
mkdocs serve
```

### 7) Explore The API

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)  
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- MkDocs docs: [http://localhost:8001](http://localhost:8001)  
- Postman download: [https://www.postman.com/downloads/](https://www.postman.com/downloads/)

Postman is recommended for larger or nested JSON payloads and for collecting repeatable test collections and visualizations.

## API Documentation Quick Links

- [Docs index](./docs/index.md)  
- [FastAPI reference](./docs/api/fast-api/index.md)  
- [Python API reference](./docs/api/python/index.md)

## SNMP Notes

- SNMPv2c is supported  
- SNMPv3 is currently stubbed and not yet supported

## CableLabs Specifications & MIBs

- [CM-SP-MULPIv3.1](https://www.cablelabs.com/specifications/CM-SP-MULPIv3.1)  
- [CM-SP-CM-OSSIv3.1](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1)  
- [CM-SP-MULPIv4.0](https://www.cablelabs.com/specifications/CM-SP-MULPIv4.0)  
- [CM-SP-CM-OSSIv4.0](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv4.0)  
- [DOCSIS MIBs](https://mibs.cablelabs.com/MIBs/DOCSIS/)

## PNM Architecture & Guidance

- [CM-TR-PMA](https://www.cablelabs.com/specifications/CM-TR-PMA)  
- [CM-GL-PNM-HFC](https://www.cablelabs.com/specifications/CM-GL-PNM-HFC)  
- [CM-GL-PNM-3.1](https://www.cablelabs.com/specifications/CM-GL-PNM-3.1)

## License

[`MIT LICENSE`](./LICENSE)

## Maintainer

Maurice Garcia

- [Email](mailto:mgarcia01752@outlook.com)  
- [LinkedIn](https://www.linkedin.com/in/mauricemgarcia/)
