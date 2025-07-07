# PyPNM Examples

This directory contains runnable examples showing how to use the PyPNM project in four main contexts:

```
examples/
├── fast-api          # Scripts demonstrating FastAPI endpoints
├── pnm               # Standalone PNM‐file parsing and reporting
├── service           # Wrapped service‐layer calls using CableModem API
└── snmp              # Low‐level SNMP get / walk and bulk‐set examples
```

[FastAPI](endpoint-fetcher.md)

## 1. [FastAPI](endpoint-fetcher.md) 

PyPNM FastAPI router:

## 2. PNM File Parsing Examples (`examples/pnm`)

Standalone Python scripts that load PNM binary files (from `examples/data/pnm`) and print parsed output:

| Script                            | Description                               |
| --------------------------------- | ----------------------------------------- |
| `cm-pnm-ds-histogram.py`          | Parses downstream histogram profiles      |
| `cm-pnm-ds-ofdm-const-display.py` | Parses OFDM constellation data            |
| `cm-pnm-ds-ofdm-fec-summary.py`   | Parses FEC summary                        |
| `cm-pnm-ds-ofdm-mod-profile.py`   | Parses modulation profile                 |
| `cm-pnm-ds-ofdm-rxmer.py`         | Parses RxMER (modulation error ratio)     |
| `cm-pnm-ds-symbol-capture.py`     | Parses symbol capture buffers             |
| `cm-pnm-latency-report.py`        | Parses latency reports                    |
| `cm-pnm-spectrum-analyzer.py`     | Parses spectrum analysis data             |
| `cm-pnm-us-ofdma-pre-eq.py`       | Parses upstream OFDMA pre‐equalizer state |

**Usage**:

```bash
python cm-pnm-ds-ofdm-fec-summary.py examples/data/pnm/sample.pnm
```

## 3. Service Layer Examples (`examples/service`)

Shows how to wrap low‐level PNM or SNMP calls into higher‐level service functions:

* **Run a service**:

  ```bash
  python cm-service-set-ds-histogram.py --mac 00:11:22:33:44:55 --inet 192.168.1.100
  ```

Each `cm-service-*.py` script invokes the corresponding `Service` class method and prints a Pydantic‐validated response.

## 4. SNMP Raw Examples (`examples/snmp`)

Demonstrates SNMP: GET, SET, WALK

* **GET**:

  ```bash
  MAC="00:11:22:33:44:55"
  INET="192.168.1.100"
  COMMUNITY="private"
  CLI="--mac ${MAC} --inet ${INET} --community-write ${COMMUNITY}"

  ./cm-get-sysDescr.py ${CLI}
  ```

* **SET**:

  ```bash
  MAC="00:11:22:33:44:55"
  INET="192.168.1.100"
  COMMUNITY="private"
  CLI="--mac ${MAC} --inet ${INET} --community-write ${COMMUNITY}"

  ./cm-get-sysDescr.py ${CLI}
  ```

* **WALK**:

  ```bash
  MAC="00:11:22:33:44:55"
  INET="192.168.1.100"
  COMMUNITY="private"
  CLI="--mac ${MAC} --inet ${INET} --community-write ${COMMUNITY}"

  ./cm-get-sysDescr.py ${CLI}
  ```

**Happy Testing!**
These examples should help you get started quickly with parsing PNM files, invoking SNMP operations, and standing up the full FastAPI service. Let us know if you need more!
