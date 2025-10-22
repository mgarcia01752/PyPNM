<p align="center">
  <a href="docs/index.md">
    <picture>
      <source srcset="docs/images/logo/pypnm-dark-mode.png" media="(prefers-color-scheme: dark)" />
      <img src="docs/images/logo/pypnm-light-mode.png" alt="PyPNM Logo" width="200" />
    </picture>
  </a>
</p>

# PyPNM (pre-alpha) — DOCSIS 3.x/4.0 Proactive Network Maintenance Toolkit

PyPNM is a modular, Python-based toolkit for collecting, parsing, and analyzing DOCSIS 3.x/4.0 Proactive Network Maintenance (PNM) telemetry. It supports real-time and offline workflows through a Python API and a FastAPI web service.

## Key Features

* **Structured SNMP integration**: poll DOCSIS modems for telemetry (RxMER, modulation profiles, spectrum, equalization).
* **Binary file decoding**: retrieve and parse modem-generated capture files delivered via TFTP or returned over SNMP.
* **FastAPI REST interface**: JSON endpoints for dashboards, automation, and analytics pipelines.
* **OFDM and upstream utilities**: channel estimation, FEC analysis, tap-delay visualization, and related calculators.
* **Analysis helpers**: Shannon capacity, margin deltas, and signal statistics.
* **Extensible framework**: plug in new capture types and algorithms.
* **CLI tools**: scriptable utilities for batch tasks.

## Prerequisites

### Operating Systems

Linux distributions; validated on:

* Ubuntu 22.04 LTS
* Ubuntu 24.04 LTS

### Shell Dependencies

```bash
sudo apt update
sudo apt install -y git
```

## Getting Started

### 1) Clone the repository

```bash
git clone https://github.com/mgarcia01752/PyPNM.git
cd PyPNM
```

### 2) Install system and Python dependencies

The included script installs system packages, creates a virtual environment, and installs PyPNM in editable mode:

```bash
./install.sh
```

### 3) Activate the virtual environment (if not already active)

```bash
python3 -m venv .env
source .env/bin/activate
```

### 4) Configure PyPNM (quick setup)

You’ll need:

* Cable Modem (CM) MAC address and IP address
* SNMPv2c write community string
* TFTP server IP (IPv4/IPv6) reachable by the CM and PyPNM
* A retrieval method for PNM files from the TFTP server

See: [PyPNM System Configuration](docs/api/fast-api/pypnm/system/system_config.md)

### 5) Launch the FastAPI service

```bash
pypnm --help
```

Example (HTTPS on port 443):

```bash
pypnm --host 0.0.0.0 --port 443 --ssl --cert ./certs/cert.pem --key ./certs/key.pem
```

Production (Local Host) Default:

http://127.0.0.1:8000 

```bash
pypnm
```

Development (Local Host) Default:

--reload flag for auto-restart on code changes:

```bash
pypnm --reload
```

### 6) (Optional) Serve the documentation locally

```bash
mkdocs serve
```

### 7) Explore the API

* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* Postman: [https://www.postman.com/downloads/](https://www.postman.com/downloads/)

Tip: Postman is often better for large or nested JSON payloads.

## API Documentation

* [Docs Index](./docs/index.md)
* [FastAPI Reference](./docs/api/fast-api/index.md)
* [Python API Reference](./docs/api/python/index.md)

## Notes on SNMP

* SNMPv2c is supported in pre-alpha.
* SNMPv3 client is stubbed and not yet implemented; enabling SNMPv3 in config will raise a clear `NotImplementedError`.

## CableLabs Specifications and MIBs

* DOCSIS 3.1: [https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1)
* DOCSIS 4.0: [https://www.cablelabs.com/specifications/CM-SP-MULPIv4.0](https://www.cablelabs.com/specifications/CM-SP-MULPIv4.0)
* CM-SP-CM-OSSIv3.1 (PNM section): [https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1)
* CM-SP-CM-OSSIv4.0 (PNM section): [https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv4.0](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv4.0)
* DOCSIS MIBs: [https://mibs.cablelabs.com/MIBs/DOCSIS/](https://mibs.cablelabs.com/MIBs/DOCSIS/)

PNM architecture and guidance:

* CM-TR-PMA: [https://www.cablelabs.com/specifications/CM-TR-PMA](https://www.cablelabs.com/specifications/CM-TR-PMA)
* CM-GL-PNM-HFC: [https://www.cablelabs.com/specifications/CM-GL-PNM-HFC](https://www.cablelabs.com/specifications/CM-GL-PNM-HFC)
* CM-GL-PNM-3.1: [https://www.cablelabs.com/specifications/CM-GL-PNM-3.1](https://www.cablelabs.com/specifications/CM-GL-PNM-3.1)

## License

MIT License. See `LICENSE`.

## Maintainer

Maurice Garcia
[mgarcia01752@outlook.com](mailto:mgarcia01752@outlook.com)
