<p align="center">
  <a href="docs/index.md">
    <picture>
      <source srcset="docs/images/logo/pypnm-dark-mode.png" media="(prefers-color-scheme: dark)" />
      <img src="docs/images/logo/pypnm-light-mode.png" alt="PyPNM Logo" width="200" />
    </picture>
  </a>
</p>

# PyPNM (pre-alpha) — DOCSIS 3.x/4.0 Proactive Network Maintenance Toolkit

[![Daily Build](https://github.com/mgarcia01752/PyPNM/actions/workflows/daily-build.yml/badge.svg?branch=main)](https://github.com/mgarcia01752/PyPNM/actions/workflows/daily-build.yml)
[![Latest Tag](https://img.shields.io/github/v/tag/mgarcia01752/PyPNM?sort=semver&filter=v*&label=latest)](https://github.com/mgarcia01752/PyPNM/tags)


PyPNM is a modular toolkit for collecting, parsing, and analyzing DOCSIS 3.x/4.0 Proactive Network Maintenance (PNM) telemetry. Use it as a Python library or via a FastAPI web service for real-time and offline workflows.

## Key features

- **Structured SNMP integration**: poll DOCSIS modems for RxMER, modulation profiles, spectrum, and pre-EQ.
- **Binary capture decoding**: retrieve modem-generated files via TFTP or SNMP and parse them to structured data.
- **FastAPI REST service**: JSON endpoints for dashboards, automation, and pipelines.
- **OFDM & upstream utilities**: channel estimation, FEC analysis, tap-delay visualization, and helpers.
- **Analysis helpers**: Shannon capacity, margin deltas, signal statistics.
- **Extensible framework**: plug in new capture types and algorithms.
- **CLI tools**: scriptable utilities for batch tasks.

## Prerequisites

### Operating systems

Linux. Validated on:

- Ubuntu 22.04 LTS
- Ubuntu 24.04 LTS

### Shell dependencies

```bash
sudo apt update
sudo apt install -y git
```

## Getting started

### 1) Clone

```bash
git clone https://github.com/mgarcia01752/PyPNM.git
cd PyPNM
```

### 2) Install

The included script installs system packages, creates a virtualenv, and installs PyPNM in editable mode:

```bash
./install.sh
```

Show installer options:

```bash
./install.sh --help
```

Demo-mode install (uses demo/settings/system.json and backs up the default configuration to backup/src/pypnm/settings/system.json):

```bash
./install.sh --demo-mode
```

Revert to production settings (restore src/pypnm/settings/system.json from backup/src/pypnm/settings/system.json):

```bash
./install.sh --production
```

You can also provide a custom virtual environment directory:

```bash
./install.sh --demo-mode .env-demo
```

### 3) Activate the venv (if not already active)

```bash
python3 -m venv .env
source .env/bin/activate
```

### 4) Configure (quick setup)

You will need:

- Cable Modem (CM) MAC address and IP address
- SNMPv2c write community string
- TFTP server IP (IPv4/IPv6) reachable by the CM and PyPNM
- A retrieval method for PNM files from the TFTP server

See: [System Configuration](docs/api/fast-api/pypnm/system/system_config.md)

### 5) Run the FastAPI service

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
pypnm --host 0.0.0.0 --port 443 --ssl --cert ./certs/cert.pem --key ./certs/key.pem
```

Development Hot-Reload:

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
- MkDocs docs: [http://localhost:8001](http://localhost:8001)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Install Postman: [https://www.postman.com/downloads/](https://www.postman.com/downloads/)

Tip: Postman is often better for large or deeply nested JSON payloads.

## API Documentation Quick links

- [Docs index](./docs/index.md)
- [FastAPI reference](./docs/api/fast-api/index.md)
- [Python API reference](./docs/api/python/index.md)

## SNMP notes

- SNMPv2c Supported.
- SNMPv3 is stubbed, but not Supported as of yet.

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

## Maintainer

Maurice Garcia

- [Email](mailto:mgarcia01752@outlook.com)
- [LinkedIn](https://www.linkedin.com/in/mauricemgarcia/)
