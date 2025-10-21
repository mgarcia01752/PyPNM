# System Configuration Reference

Canonical Structure And Field Semantics For `system.json`.

* **Config File**: [`config/system.json`](../../src/pypnm/settings/system.json)
* **ConfigManager Class**: [`ConfigManager`](../../src/pypnm/config/config_manager.py)
* **PNM ConfigManager Class**: [`PnmConfigManager`](../../src/pypnm/config/pnm_config_manager.py)

## 1. FastApiRequestDefault

Default Parameters For REST Requests To The FastAPI Service.

```json
"FastApiRequestDefault": {
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "ip_address": "192.168.0.100"
}
```

| Field       | Type   | Description                       |
| ----------- | ------ | --------------------------------- |
| mac_address | string | Default device MAC address.       |
| ip_address  | string | Default device IP (IPv4 or IPv6). |

## 2. SNMP

Global SNMP Settings, Including Version-Specific Options.

```json
"SNMP": {
  "timeout": 5,
  "version": {
    "2c": {
      "enable": true,
      "retries": 5,
      "read_community": "private",
      "write_community": "private"
    },
    "3": {
      "enable": false,
      "retries": 5,
      "username": "user",
      "securityLevel": "authPriv",
      "authProtocol": "SHA",
      "authPassword": "pass",
      "privProtocol": "AES",
      "privPassword": "privpass"
    }
  }
}
```

**Top-Level**

| Field   | Type   | Description                        |
| ------- | ------ | ---------------------------------- |
| timeout | number | Per-request timeout (seconds).     |
| version | object | Container for v2c/v3 configuration |

**SNMP v2c**

| Field           | Type    | Description                     |
| --------------- | ------- | ------------------------------- |
| enable          | boolean | Enable v2c operations.          |
| retries         | number  | Retry count on timeout/failure. |
| read_community  | string  | Community for GET/WALK.         |
| write_community | string  | Community for SET.              |

**SNMP v3** *(if enabled in your environment)*

| Field         | Type    | Description                                  |
| ------------- | ------- | -------------------------------------------- |
| enable        | boolean | Enable v3 operations.                        |
| retries       | number  | Retry count on timeout/failure.              |
| username      | string  | Security name.                               |
| securityLevel | string  | `noAuthNoPriv`, `authNoPriv`, or `authPriv`. |
| authProtocol  | string  | For example `MD5`, `SHA`.                    |
| authPassword  | string  | Required when `auth*` is used.               |
| privProtocol  | string  | For example `DES`, `AES`.                    |
| privPassword  | string  | Required when `*Priv` is used.               |

## 3. PnmBulkDataTransfer

Transport Parameters For CM-Generated Files (e.g., RxMER, FEC Summary) Sent To A Server.

```json
"PnmBulkDataTransfer": {
  "method": "tftp",
  "tftp": { "ip_v4": "192.168.0.10", "ip_v6": "2001:db8::10", "remote_dir": "" },
  "http":  { "base_url": "http://files.example.com/",  "port": 80  },
  "https": { "base_url": "https://files.example.com/", "port": 443 }
}
```

| Field   | Type   | Description                                                |
| ------- | ------ | ---------------------------------------------------------- |
| method  | string | Preferred bulk method: `tftp`, `http`, or `https`.         |
| tftp.*  | object | TFTP targets for IPv4/IPv6 plus optional remote directory. |
| http.*  | object | HTTP base URL and port for file delivery.                  |
| https.* | object | HTTPS base URL and port for file delivery.                 |

## 4. [PnmFileRetrieval](./file-transfer-methods.md)

Local Storage Layout And Remote Retrieval Methods.

```json
"PnmFileRetrieval": {
  "pnm_dir": ".data/pnm",
  "csv_dir": ".data/csv",
  "json_dir": ".data/json",
  "xlsx_dir": ".data/xlsx",
  "png_dir": ".data/png",
  "archive_dir": ".data/archive",
  "msg_rsp_dir": ".data/msg_rsp",
  "transaction_db": ".data/db/transactions.json",
  "capture_group_db": ".data/db/capture_group.json",
  "session_group_db": ".data/db/session_group.json",
  "operation_db": ".data/db/operation_capture.json",
  "retries": 5,
  "retrival_method": {
    "method": "local",
    "methods": {
      "local": { "src_dir": "/srv/tftp" },
      "tftp":  { "host": "localhost", "port": 69, "timeout": 5, "remote_dir": "" },
      "ftp":   { "host": "localhost", "port": 21, "tls": false, "timeout": 5, "user": "test", "password": "tftp", "remote_dir": "/srv/tftp" },
      "scp":   { "host": "localhost", "port": 22, "user": "test", "password": "tftp", "remote_dir": "/srv/tftp" },
      "sftp":  { "host": "localhost", "port": 22, "user": "test", "password": "tftp", "remote_dir": "/srv/tftp" },
      "http":  { "base_url": "http://STUB/",  "port": 80  },
      "https": { "base_url": "https://STUB/", "port": 443 }
    }
  }
}
```

**Directories And Databases**

| Field            | Type   | Description                                  |
| ---------------- | ------ | -------------------------------------------- |
| pnm_dir          | string | Local storage for raw PNM binaries.          |
| csv_dir          | string | Local storage for derived CSVs.              |
| json_dir         | string | Local storage for derived JSON.              |
| xlsx_dir         | string | Local storage for Excel reports.             |
| png_dir          | string | Local storage for generated PNGs.            |
| archive_dir      | string | Local storage for analysis ZIP archives.     |
| msg_rsp_dir      | string | Local storage for message/response metadata. |
| transaction_db   | string | JSON ledger of file transactions.            |
| capture_group_db | string | JSON map of grouped transactions.            |
| session_group_db | string | JSON map of session groups.                  |
| operation_db     | string | JSON map of operation→capture group.         |

**Retrieval Settings**

| Field                                 | Type   | Description                                                                      |
| ------------------------------------- | ------ | -------------------------------------------------------------------------------- |
| retrival_method.method                | string | Active retrieval method: `local`, `tftp`, `ftp`, `scp`, `sftp`, `http`, `https`. |
| retrival_method.methods.local.src_dir | string | Source directory to watch/copy from when using `local`.                          |
| retrival_method.methods.tftp.*        | object | TFTP host/port/timeout and remote directory.                                     |
| retrival_method.methods.ftp.*         | object | FTP connection, credentials, and remote directory.                               |
| retrival_method.methods.scp.*         | object | SCP connection and remote directory.                                             |
| retrival_method.methods.sftp.*        | object | SFTP connection and remote directory.                                            |
| retrival_method.methods.http.*        | object | HTTP base URL and port.                                                          |
| retrival_method.methods.https.*       | object | HTTPS base URL and port.                                                         |
| retries                               | number | Max attempts per retrieval operation.                                            |

> The key name `retrival_method` is preserved as implemented.

## 5. Logging

Application Logging Options.

```json
"logging": {
  "log_level": "INFO",
  "log_dir": "logs",
  "log_filename": "pypnm.log"
}
```

| Field        | Type   | Description                          |
| ------------ | ------ | ------------------------------------ |
| log_level    | string | `DEBUG`, `INFO`, `WARN`, or `ERROR`. |
| log_dir      | string | Directory for log files.             |
| log_filename | string | Log filename.                        |

## Loading Configuration

Typical Access Pattern Using The Manager Abstractions.

```python
from pypnm.config.config_manager import ConfigManager
from pypnm.config.pnm_config_manager import PnmConfigManager

# Load defaults
cfg = ConfigManager()

# Read values
mac = cfg.get("FastApiRequestDefault", "mac_address")
ip  = cfg.get("FastApiRequestDefault", "ip_address")

# PNM-specific helpers
pnm_cfg = PnmConfigManager()
tftp_v4 = pnm_cfg.get("PnmBulkDataTransfer", "tftp")["ip_v4"]
```
