<p align="center">
  <a href="docs/master-index.md">
    <picture>
      <source srcset="docs/images/logo/pypnm-dark-mode.png" media="(prefers-color-scheme: dark)" />
      <img src="docs/images/logo/pypnm-light-mode.png" alt="PyPNM Logo" width="200" />
    </picture>
  </a>
</p>

# PyPNM (pre-alpha) — DOCSIS 3.x/4.0 Proactive Network Maintenance Toolkit

PyPNM is a modular, Python-based toolkit for parsing, analyzing, and visualizing DOCSIS 3.x/4.0 Proactive Network Maintenance (PNM) telemetry. It supports real-time and offline diagnostics via both a programmatic API and an interactive web interface.

## Key features

- Structured SNMP integration: poll DOCSIS modems for telemetry (RxMER, modulation profiles, spectrum, equalization).
- Binary file decoding: retrieve and parse modem-generated TFTP or SNMP-triggered binary capture files.
- FastAPI REST interface: JSON API for dashboards, automation, and analytics pipelines.
- OFDM and upstream tools: channel estimation, FEC analysis, tap delay visualization, and more.
- Built-in calculators: Shannon capacity, delta margin, signal statistics.
- Extensible analysis framework: plug in new capture types and algorithms.
- CLI utilities: command-line tools for scripting and automation workflows.

## Prerequisites

### Operating systems

PyPNM runs on standard Linux environments.

Tested distributions:
- Ubuntu 22.04 LTS
- Ubuntu 24.04 LTS

### Shell dependencies

Install git if not already present:

```bash
sudo apt update
sudo apt install -y git
````

## Getting started

### 1) Clone the repository

```bash
git clone https://github.com/mgarcia01752/PyPNM.git
cd PyPNM
```

### 2) Install system and Python dependencies

The included `install.sh` detects Ubuntu 22.04 vs 24.04 (or falls back to your distro’s default Python), installs system packages, creates a virtual environment, and installs PyPNM in editable mode:

```bash
./install.sh
```

### 3) Activate the Python virtual environment (if not already active)

```bash
python3 -m venv .env
source .env/bin/activate
```

### 4) Launch the PyPNM FastAPI service

```bash
pypnm --help
```

Example (HTTPS on port 443):

```bash
pypnm --host 0.0.0.0 --port 443 --ssl --cert ./certs/cert.pem --key ./certs/key.pem
```

Default run:

```bash
pypnm
```

### 5) Explore the API

* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* Postman: [https://www.postman.com/downloads/](https://www.postman.com/downloads/)

Tip: Use Postman for complex or large JSON payloads; Swagger UI can struggle with deeply nested schemas.

## Full documentation

* Master index: docs/master-index.md
* Python API reference: docs/api/python/index.md
* Example scripts: docs/examples/index.md

## CableLabs standards and specifications

DOCSIS 3.1 MIBs and PNM behavior:

* [https://www.cablelabs.com/specifications/search?category=DOCSIS&subcat=DOCSIS%203.1](https://www.cablelabs.com/specifications/search?category=DOCSIS&subcat=DOCSIS%203.1)
* [https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1)
* [https://mibs.cablelabs.com/MIBs/DOCSIS/](https://mibs.cablelabs.com/MIBs/DOCSIS/)

PNM architecture and guidelines:

* [https://www.cablelabs.com/specifications/CM-TR-PMA](https://www.cablelabs.com/specifications/CM-TR-PMA)
* [https://www.cablelabs.com/specifications/CM-GL-PNM-HFC](https://www.cablelabs.com/specifications/CM-GL-PNM-HFC)
* [https://www.cablelabs.com/specifications/CM-GL-PNM-3.1](https://www.cablelabs.com/specifications/CM-GL-PNM-3.1)

## License

Released under the MIT License. See LICENSE.

## Maintainer

Maurice Garcia
Email: [mgarcia01752@outlook.com](mailto:mgarcia01752@outlook.com)
