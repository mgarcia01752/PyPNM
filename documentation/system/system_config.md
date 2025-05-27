# System Configuration Reference

This document describes the structure and meaning of the `system.json` configuration file. It also includes stub links to the config file location and the `ConfigManager` implementation.

* **Config file**: [`config/system.json`](../../config/system.json)
* **ConfigManager class**: [`ConfigManager`](../../src/config/config_manager.py)
* **PNM ConfigManager class**: [`PnmConfigManager`](../../src/config/pnm_config_manager.py)

---

## 1. FastApiRequestDefault

Default parameters for REST requests to the FastAPI service.

```json
"FastApiRequestDefault": {
  "mac_address": "0050.f112.d72f",
  "ip_address": "172.20.58.7"
}
```

* **mac\_address**: The default MAC address used when instantiating SNMP/TFTP clients.
* **ip\_address**: The default IPv4 address of the cable modem or target device.

## 2. SNMP

Settings for SNMP v2c telemetry polling.

```json
"SNMP": {
  "version": "2",
  "retries": "5",
  "read_community": "public",
  "write_community": "private"
}
```

* **version**: SNMP protocol version (currently only v2c is supported).
* **retries**: Number of retry attempts on timeout or failure.
* **read\_community**: SNMP community string for GET operations.
* **write\_community**: SNMP community string for SET operations.

## 3. PnmBulkDataTransfer

Configuration for bulk PNM file transfers (e.g., spectrum or symbol captures).

```json
"PnmBulkDataTransfer": {
  "method": "tftp",
  "tftp": {
    "ip_v4": "172.20.10.153",
    "ip_v6": "2001:10::153",
    "remote_dir": ""
  },
  "http": {
    "base_url": "http://files.example.com/",
    "port": 80
  },
  "https": {
    "base_url": "https://files.example.com/",
    "port": 443
  }
}
```

* **method**: Transfer protocol (`tftp`, `http`, or `https`).
* **tftp**: TFTP server endpoints for IPv4/IPv6 and directory.
* **http/https**: Base URL and port for HTTP(S) downloads.

## 4. PnmFileRetrieval

Detailed settings for retrieving PNM capture files using various protocols.

```json
"PnmFileRetrieval": {
  "method": "local",
  "save_dir": "data/pnm",
  "transaction_db": "data/db/transactions.json",
  "capture_group_db": "data/db/capture_group.json",
  "operation_db": "data/db/operation_capture.json",
  "retries": 5,
  "local": { "src_dir": "/srv/tftp" },
  "tftp": { "host": "localhost", "port": 69, "remote_dir": "" },
  "ftp": { "host": "ftp.example.com", "port": 21, "user": "user", "password": "pass", "remote_dir": "/files" },
  "scp": { "host": "scp.example.com", "port": "22", "user": "user", "password": "pass", "remote_dir": "/files" },
  "sftp": { "host": "sftp.example.com", "port": 22, "user": "user", "password": "pass", "remote_dir": "/files" },
  "http": { "base_url": "http://files.example.com/", "port": 80 },
  "https": { "base_url": "https://files.example.com/", "port": 443 }
}
```

* **method**: Primary retrieval mode (`local`, `tftp`, `ftp`, `scp`, `sftp`, `http`, or `https`).
* **save\_dir**: Local directory to store fetched PNM files.
* **transaction\_db**: JSON file tracking file-transfer transactions.
* **capture\_group\_db**: JSON file grouping related captures.
* **operation\_db**: JSON file logging individual capture operations.
* **retries**: Number of attempts per file-transfer operation.
* **\<protocol>**: Section for each protocol’s connection details.

## 5. Logging

Configuration for application logging.

```json
"logging": {
  "log_level": "DEBUG",
  "log_dir": "logs",
  "log_filename": "pnm_log_%Y%m%d_%H%M%S.log"
}
```

* **log\_level**: Minimum level to record (`DEBUG`, `INFO`, `WARN`, `ERROR`).
* **log\_dir**: Directory to write log files.
* **log\_filename**: Timestamped filename pattern using `strftime` tokens.

---

## Loading Configuration

The `ConfigManager` reads this JSON file and exposes values via:

```python
from config.system import SystemConfig
from pypnm import ConfigManager

# Load default config
cfg = ConfigManager()

# Access values
mac = cfg.get("FastApiRequestDefault", "mac_address")
ip = cfg.get("FastApiRequestDefault", "ip_address")
```
