# PyPNM — DOCSIS 3.1 Proactive Network Maintenance Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

**PyPNM** is a modular, Python-based toolkit for parsing, analyzing, and visualizing DOCSIS 3.0/3.1 Proactive Network Maintenance (PNM) telemetry. It provides:

* **Structured SNMP integration** for real-time cable modem telemetry (RxMER, spectrum, equalization, modulation profiles, FEC, etc.)
* **Binary capture parsing** via TFTP/SNMP–triggered files (OFDM symbols, histograms, latency traces)
* **FastAPI REST service** delivering clean JSON for integration into dashboards and automation
* **Extensible architecture** for adding new measurement types and custom analytics

## System Configuration

[SystemConfiguration](doc/system/system_config.md)

Core application settings—including SNMP credentials, PNM file transfer methods, logging rules, and FastAPI defaults—are centralized in the system configuration file.

* **Schema**: `config/system.json`
* **Loader**: `ConfigManager` (`src/lib/config_manager.py`)

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

### 1. Install from Source / Local Package

> **Note:** PyPNM is not published on PyPI. You can install it locally in two ways:

**Editable install** (ideal for development):

```bash
git clone <your-repo-url>
cd pypnm
pip install -e .
```

**Build and install a wheel** (for offline or locked-down environments):

```bash
cd pypnm
python setup.py bdist_wheel
pip install dist/pypnm-*.whl
```

### 2. Configure Your Environment

```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/src:${PWD}/startup"
```

### 3. Run the FastAPI Service

* **Single Measurement/Capture** — [Single-Capture API Guide](doc/api/fast-api/single/index.md)
* **Multi-RxMER Capture** — [Multi-RxMER Capture API Guide](doc/api/fast-api/multi/index.md)

```bash
./start-fastapi-service.sh
```

Open your browser:

* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Postman**: Import [`postman_collection.json`](./postman_collection.json)

> **Tip:** Use Postman for large or nested JSON responses—Swagger UI can struggle with very large data sets.

---

Here’s a cleaned-up, more consistent “## Python API” section—no code, just clear pointers and flow:

## Python API

PyPNM’s Python API lets you integrate PNM telemetry end-to-end in your own Python scripts and applications:

- **Full Reference**  
  Browse the complete API docs for classes, methods, parameters, and return schemas:  
  [Python API Reference →](doc/api/python/index.md)

- **Hands-On Examples**  
  Ready-to-run scripts demonstrating common tasks—loading a PNM file, batch RxMER captures, spectrum plots, etc.:  
  [Example Scripts →](doc/examples/index.md)

**SNMP Client**
  
  Under the hood, PyPNM uses the pure-Python [pysnmp](https://pypi.org/project/pysnmp/) library for v1/v2c/v3 operations.  
  You can install it directly (if you only need SNMP support) with:  
  
  ```bash
  pip install pysnmp
  ````

* **SNMPv2c Guide & API**
  Learn how to use the built-in async SNMPv2c client:

  * [SNMPv2c Overview →](doc/api/snmp/index.md)
  * [Class Reference →](src/snmp/snmp_v2c.py)


**Core Capabilities**

1. **CableModem client**: SNMP/TFTP interface to trigger and retrieve PNM captures.
2. **PNM Parsers**: Classes like `CmDsOfdmRxMer` and `CmSymbolCapture` to convert raw bytes into `dict` or Pydantic models.
3. **Services & Aggregators**: High-level helpers combining capture, retrieval, parsing, and post-processing in a few method calls.

**Getting Started**

1. Pick an example from the “Example Scripts” link above.
2. Adjust configuration (MAC, IP, file paths) for your environment.
3. Run the script to see how the API returns Python data structures you can plot, analyze, or store.

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

---
