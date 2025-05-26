# SNMP

The SNMP module in PyPNM provides a lightweight, asynchronous Python client for SNMP v2c operations. Under the hood it uses the [pysnmp](https://pypi.org/project/pysnmp/) library for network communication and supports:

* Asynchronous **GET**, **WALK**, and **SET** operations
* Optional pre‑compiled MIB/OID mapping for fast lookups
* Convenient utilities for parsing responses, extracting indices, and converting SNMP DateAndTime values

## Installation

```bash
# Install PyPNM (includes SNMP client)
pip install pypnm

# Or install pysnmp standalone if you're only using SNMP features
pip install pysnmp
```

## Prerequisites

* Python 3.10+
* Network reachability to the target SNMP agent
* Correct SNMP community strings configured on the device

## Modules & Usage Guides

* **SNMPv2c Client** — [`snmp-v2c.md`](snmp-v2c.md)
  Details on using the `Snmp_v2c` class for asynchronous SNMP operations.

> **Tip:** You can browse the full API in the auto‑generated docs: `doc/api/snmp/index.md`
