<p align="center">
  <a href="documentation/master-index.md">
    <picture>
      <!-- when in dark mode, use the dark logo -->
      <source srcset="documentation/images/logo/pypnm-dark-mode.png" media="(prefers-color-scheme: dark)" />
      <!-- fallback (light mode) -->
      <img src="documentation/images/logo/pypnm-light-mode.png" alt="PyPNM Logo" width="200" />
    </picture>
  </a>
</p>

# PyPNM (pre-alpha) — DOCSIS 3.1/4.0 Proactive Network Maintenance Toolkit

[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
![Pre-Release](https://img.shields.io/badge/release-pre--alpha-lightgrey)

**PyPNM** is a modular, Python-based toolkit for parsing, analyzing, and visualizing DOCSIS 3.0/3.1 Proactive Network Maintenance (PNM) telemetry. It provides:

* **Structured SNMP integration** for real-time cable modem telemetry (RxMER, spectrum, equalization, modulation profiles, FEC, etc.)
* **Binary capture parsing** via TFTP/SNMP–triggered files (OFDM symbols, histograms, latency traces)
* **FastAPI REST service** delivering clean JSON for integration into dashboards and automation
* **Extensible architecture** for adding new measurement types and custom analytics

## 🛠 Key Features

* **PyPNM API**: programmatic access to core parsing, aggregation, and analysis routines
* **SNMP v2c Support**: Telemetry acquisition via SNMP v2c
* **OFDM Diagnostics**: RxMER, FEC summary, spectrum analysis, channel estimation, constellation display, modulation profiles
* **Upstream Support**: ATDMA & TDMA pre-equalization tap analysis, latency reporting
* **Error-Correction Insights**: Aggregate FEC counters over time 
* **Capacity Margin Calculations**: OFDM Shannon-based bit-per-subcarrier limits and deltas
* **RESTful API**: Auto-generated OpenAPI, Swagger UI, Postman collection
* **Command-Line Examples**: Standalone analysis scripts and batch processing utilities

## Prerequisites

### Operating System

PyPNM runs on standard Linux environments—no custom kernel patches required.

**Tested distributions:**

* Ubuntu 22.04 LTS
* Ubuntu 24.04 LTS

### Shell Dependencies

Install `git` if not already present (before cloning the repo):

```bash
sudo apt update
sudo apt install -y git
```

## 🚀 Getting Started

### Step 1: Clone the repository

```bash
git clone https://github.com/mgarcia01752/PyPNM.git
cd PyPNM
```

### Step 2: Install system & Python dependencies

The included `install.sh` will detect Ubuntu 22.04 vs 24.04 (or fall back to your distro’s default Python), install system packages, create a virtual environment, and install PyPNM in editable mode:

```bash
./install.sh
```

### Step 3: (If not already active) activate the virtual environment

```bash
python3 -m venv .env
source .env/bin/activate
```

### Step 4: Launch the PyPNM FastAPI service

```bash
pypnm --help
```

**Example (HTTPS on port 443):**

```bash
pypnm --host 0.0.0.0 --port 443 --ssl --cert ./certs/cert.pem --key ./certs/key.pem
```

*OR* with defaults:

```bash
pypnm
```

### Step 5: Explore the API

* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**:     [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **Postman**:   [`Download Postman`](https://www.postman.com/downloads/)

> ⚠️ Tip: Use Postman for complex or large JSON payloads—Swagger UI can struggle with deeply nested schemas.

## [PyPNM Documentation](documentation/master-index.md)

PyPNM Documentation to navigate through all guides, API references, examples, and system docs.

## PyPNM API

Integrate PNM telemetry end-to-end in your own Python scripts:

* **Full Reference**: [PyPNM API Reference →](documentation/api/python/index.md)
* **Hands-On Examples**: [Example Scripts →](documentation/examples/index.md)

## 📦 Supported Standards & Specs

* **DOCSIS 3.1 MIBs & PNM behavior** (CableLabs)

  * [DOCSIS 3.1 Suite](https://www.cablelabs.com/specifications/search?category=DOCSIS&subcat=DOCSIS%203.1)
  * [CM-SP-CM-OSS Iv3.1](https://www.cablelabs.com/specifications/CM-SP-CM-OSSIv3.1)
  * [DOCSIS MIB Repository](https://mibs.cablelabs.com/MIBs/DOCSIS/)

* **PNM Architecture & Guidelines**

  * [CM-TR-PMA](https://www.cablelabs.com/specifications/CM-TR-PMA)
  * [CM-GL-PNM-HFC & CM-GL-PNM-3.1](https://www.cablelabs.com/specifications/CM-GL-PNM-HFC)

## 📜 License

Released under the **MIT License**. See [LICENSE](LICENSE)

## 👤 Maintainer

**Maurice Garcia**
✉️ `mgarcia01752@outlook.com`
