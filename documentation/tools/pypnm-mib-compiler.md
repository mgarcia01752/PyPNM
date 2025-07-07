# PyPNM MIB Compiler

The **PyPNM MIB Compiler** is a command-line utility script located in the `tools/` directory that automates the generation of a Python dictionary mapping SNMP OID names to their numeric representations. This mapping is essential for structured SNMP integration within the PyPNM framework.

## 📄 Purpose

To convert all MIB definitions found in the `mibs/` directory into a usable Python dictionary (`COMPILED_OIDS`) and save them into:

```
src/pypnm/snmp/compiled_oids.py
```

This file is automatically overwritten and includes a UTC timestamp indicating when the OID data was last compiled.

⚡ **Why this matters**: Pre-compiling OIDs dramatically reduces SNMP lookup overhead and avoids dynamic MIB parsing at runtime with PySNMP. This speeds up application startup and ensures stability in production environments.


## 🔧 How It Works

The script:

1. Executes `snmptranslate -Tz` against MIBs in the local `mibs/` directory.
2. Saves the raw output to a temporary file.
3. Parses name-to-OID mappings.
4. Writes the result as `COMPILED_OIDS` to `compiled_oids.py`.

## 🗂 Directory Structure

```
PyPNM/
├── mibs/                          # Input MIB files (.txt/.my)
├── src/pypnm/snmp/               # Target module location
│   └── compiled_oids.py          # Auto-generated dictionary
└── tools/
    └── update_snmp_oid_dict.py  # This script
```

## ▶️ Usage

From the PyPNM root directory:

```bash
python3 tools/update_snmp_oid_dict.py
```

This will output something like:

```
🔄 Generating compiled OIDs from MIBs...
✅ Compiled 782 OIDs to 'src/pypnm/snmp/compiled_oids.py'
```

## 🧱 Prerequisites

### 1. Python

* Python 3.6 or newer

### 2. Net-SNMP

The script depends on the `snmptranslate` utility provided by the Net-SNMP package. Install it using:

```bash
sudo apt update && sudo apt install -y snmp snmp-mibs-downloader
```

Or on Red Hat–based systems:

```bash
sudo dnf install net-snmp-utils
```

Make sure `snmptranslate` is in your `PATH`:

```bash
which snmptranslate
```

### 3. Download Latest CableLabs MIBs

To populate the `mibs/` directory with the latest CableLabs MIBs:

```bash
mkdir -p mibs
wget -r -np -nH --cut-dirs=3 -R index.html \
  https://www.cablelabs.com/wp-content/uploads/mibs/current/ -P mibs/
```

> This pulls the latest published MIBs into your local `mibs/` directory for compilation.

## 📝 Output Format

The resulting file will contain:

```python
# Auto-generated OID dictionary from snmptranslate -Tz
# Do not modify manually. Generated on: 2025-07-06T20:15:45.123456

COMPILED_OIDS = {
    "docsIf3CmtsCmUsStatusRxPower": "1.3.6.1.4.1.1166.1.19.2.3.1.6",
    ...
}
```
