<p align="center">
  <picture>
    <!-- when in dark mode, use the dark logo -->
    <source srcset="documentation/images/logo/pypnm-dark-mode.png" media="(prefers-color-scheme: dark)" />
    <!-- fallback (light mode) -->
    <img src="documentation/images/logo/pypnm-light-mode.png" alt="PyPNM Logo" width="200" />
  </picture>
</p>

# PyPNM — DOCSIS 3.1/4.0 Proactive Network Maintenance Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

**PyPNM** is a modular, Python-based toolkit for parsing, analyzing, and visualizing DOCSIS 3.0/3.1 Proactive Network Maintenance (PNM) telemetry. It provides:

* **Structured SNMP integration** for real-time cable modem telemetry (RxMER, spectrum, equalization, modulation profiles, FEC, etc.)
* **Binary capture parsing** via TFTP/SNMP–triggered files (OFDM symbols, histograms, latency traces)
* **FastAPI REST service** delivering clean JSON for integration into dashboards and automation
* **Extensible architecture** for adding new measurement types and custom analytics

## Prerequisites

### System Tools

Make sure you have these installed on Ubuntu/Debian:

```bash
  sudo apt update
  sudo apt install -y \
    git               \
    curl              \
  python3.10          \
  python3.10-venv     \
  python3-pip
  ```


## System Configuration

[SystemConfiguration](documentation/system/system_config.md)

Core application settings—including SNMP credentials, PNM file transfer methods, logging rules, and FastAPI defaults—are centralized in the system configuration file.

* **Schema**: `src/pypnm/settings/system.json`
* **Loader**: `ConfigManager` (`src/pypnm/config/config_manager.py`)

---

## 🛠 Key Features

* **Python API**: programmatic access to core parsing, aggregation, and analysis routines for seamless integration in custom Python applications.
* **SNMP v2c Support**: currently supports SNMP v2c for telemetry acquisition.
* **OFDM Diagnostics**: RxMER, FEC summary, spectrum analysis, channel estimation, constellation display, modulation-profiles
* **Upstream Support**: ATDMA & TDMA pre-equalization tap analysis, latency reporting
* **Error-Correction Insights**: Aggregate FEC counters over time windows for reliability metrics
* **Capacity Margin Calculations**: Shannon-based bit-per-subcarrier limits and deltas
* **RESTful API**: Auto-generated OpenAPI, Swagger UI, Postman collection for large-payload endpoints
* **Command-Line Examples**: Utilities for standalone analysis scripts and batch processing

---

## 🚀 Getting Started

### Step 1: Clone & Install Locally

> PyPNM is not published on PyPI. You can install it locally using an editable mode for development.

**Editable install (recommended for development):**

```bash
git clone https://github.com/mgarcia01752/PyPNM.git
cd PyPNM
```

### Step 2: Create a Virtual Environment

```bash
python3 -m venv .env
source .env/bin/activate
```

### Step 3: Install in Editable Mode

```bash
pip install -e .
```

### Step 4: (Optional) Create a `.env` File

If you need to override runtime settings, create a `.env` file in the root directory:

```bash
touch .env
```

Example `.env` contents:

```env
PNM_CONFIG_PATH=src/pypnm/settings/system.json
LOG_LEVEL=DEBUG
SNMP_COMMUNITY=public
```

Environment variables will be loaded automatically if `python-dotenv` is installed (included in setup).

---

### Step 5: Launch the FastAPI Web Service

```bash
pypnm --help

usage: pypnm [-h] [--host HOST] [--port PORT] [--ssl] [--cert CERT] [--key KEY]

Launch the PyPNM FastAPI service with optional HTTPS support.

options:
  -h, --help   show this help message and exit
  --host HOST  Host to bind (default: 127.0.0.1)
  --port PORT  Port to bind (default: 8000)
  --ssl        Enable HTTPS (requires cert and key)
  --cert CERT  Path to SSL certificate
  --key KEY    Path to SSL private key

```
**Optional CLI arguments:**

```bash
pypnm --host 0.0.0.0 --port 443 --ssl --cert ./certs/cert.pem --key ./certs/key.pem
```

**Start with defaults**

```bash
pypnm
```

---

### Step 6: Open the API Docs

* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Postman**: Import [`postman_collection.json`](./postman_collection.json)

> ⚠️ Tip: Use Postman for complex or nested JSON payloads—Swagger UI can struggle with large datasets.

---

## Python API

PyPNM’s Python API lets you integrate PNM telemetry end-to-end in your own Python scripts and applications:

* **Full Reference**
  Browse the complete API docs for classes, methods, parameters, and return schemas:
  [Python API Reference →](documentation/api/python/index.md)

* **Hands-On Examples**
  Ready-to-run scripts demonstrating common tasks—loading a PNM file, batch RxMER captures, spectrum plots, etc.:
  [Example Scripts →](documentation/examples/index.md)

**SNMP Client**

Under the hood, PyPNM uses the pure-Python [pysnmp](https://pypi.org/project/pysnmp/) library for v1/v2c/v3 operations.
You can install it directly (if you only need SNMP support) with:

```bash
pip install pysnmp
```

* **SNMPv2c Guide & API**
  Learn how to use the built-in async SNMPv2c client:

  * [SNMPv2c Overview →](documentation/api/python/snmp/index.md)
  * [Class Reference →](src/pypnm/snmp/snmp_v2c.py)

**Core Capabilities**

1. **CableModem client**: SNMP/TFTP interface to trigger and retrieve PNM captures.
2. **PNM Parsers**: Classes like `CmDsOfdmRxMer` and `CmSymbolCapture` to convert raw bytes into `dict` or Pydantic models.
3. **Services & Aggregators**: High-level helpers combining capture, retrieval, parsing, and post-processing in a few method calls.

Use these building blocks to integrate PNM workflows into dashboards, automation pipelines, or custom analytics tools.

---

## 📦 Supported Standards & Specs

* **DOCSIS 3.1 MIBs** & PNM behavior (CableLabs):

  * [DOCSIS 3.1 Suite](https://www.cablelabs.com/specifications/search?category=DOCSIS&subcat=DOCSIS%203.1)
  * [CM-SP-CM-OSS Iv3.1](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1)
  * [DOCSIS MIB Repository](https://mibs.cablelabs.com/MIBs/DOCSIS/)
* **PNM Architecture & Guidelines**:

  * [CM-TR-PMA](https://www.cablelabs.com/specifications/CM-TR-PMA)
  * [CM-GL-PNM-HFC & CM-GL-PNM-3.1](https://www.cablelabs.com/specifications/CM-GL-PNM-HFC)

---

## 🏗️ Architecture & Design

* **Modular Aggregators**: Collect and merge time-series data (RxMER, FEC, profiles) into master stores.
* **Analysis Services**: Encapsulate Shannon-limit calculations, deltas, and PNM file retrieval workflows.
* **FastAPI Routers**: Standardized `APIRouter` modules with `POST` endpoints, explicit `response_model` schemas, and `JSONResponse`.
* **ConfigManager**: JSON-based, reloadable configuration for SNMP/TFTP parameters.
* **CI/CD Ready**: Integration with Jenkins pipelines and pytest for automated validation.

---

## 🔧 Examples

See the `examples/` folder for:

* **RxMER Batch Processing**
* **Spectrum Analysis via SNMP & PNM file**
* **Modulation Profile Performance Reports**
* **Live SNMP Session Scripts**

---

## 📜 License

Released under the **MIT License**. See [LICENSE](LICENSE)

---

## 👤 Maintainer

**Maurice Garcia**
✉️ `mgarcia01752@outlook.com`
