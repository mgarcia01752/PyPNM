# PyPNM Database

This document provides an overview of how PyPNM stores and organizes measurement data, focusing on traceability, grouping, and REST-driven access.

## Data Repository (Example)

```
.data/
├── db
│   ├── capture_group.json
│   ├── operation_capture.json
│   └── transactions.json
├── pnm
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_193_1751950069.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_193_1751950075.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_194_1751950068.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_194_1751950074.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_195_1751950067.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_195_1751950073.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_196_1751950066.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_196_1751950071.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_197_1751950064.bin
│   └── ds_ofdm_rxmer_per_subcar_aabbccddeeff_197_1751950070.bin
└── xlsx
```

## 📋 Transaction Records

The `.data/db/transactions.json` file acts as the **ledger** of all file capture and upload events tracked by PyPNM.

Each entry represents a **single file transaction**, whether:

* Pulled automatically from a cable modem (e.g., via TFTP), or
* Manually uploaded by a user via the UI or API.

### 📌 Structure

Each transaction is indexed by a unique hash (e.g., UUID or digest of the filename and timestamp):

```json
"1e171e1f8ef5377a": {
  "timestamp": 1751950064,
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "pnm_test_type": "DS_OFDM_RXMER_PER_SUBCAR",
  "filename": "ds_ofdm_rxmer_per_subcar_aabbccddeeff_197_1751950064.bin",
  "device_details": {
    "sys_descr": {
      "HW_REV": "01",
      "VENDOR": "GenericVendor Inc.",
      "BOOTR": "1.0.0.0",
      "SW_REV": "1.2.3.4",
      "MODEL": "GenericModel123"
    }
  }
}
```

### 🧾 Field Overview

| Field            | Description                                                             |
| ---------------- | ----------------------------------------------------------------------- |
| `timestamp`      | Unix timestamp when the file was received or uploaded                   |
| `mac_address`    | Target cable modem's MAC address                                        |
| `pnm_test_type`  | The test type that produced the file (e.g., `DS_OFDM_RXMER_PER_SUBCAR`) |
| `filename`       | The saved binary file in `.data/pnm/` directory                         |
| `device_details` | Parsed device metadata from SNMP (if available)                         |

This transaction model is used internally by PyPNM to:

* Track which files were received
* Enable cross-referencing in Excel reports
* Provide lookup and filtering in REST APIs or UIs

## 🔁 Operation Capture Linking

The `.data/db/operation_capture.json` file links a **multi-measurement operation** to a **capture group**.

An operation represents a **higher-level, multi-measurement request** that may include different PNM test types (e.g., RxMER, FEC Summary, Modulation Profile).

```json
"6bc3877d9b374039": {
  "capture_group_id": "91d93f5309944ac8",
  "created": 1751950063
}
```

| Field              | Description                              |
| ------------------ | ---------------------------------------- |
| `capture_group_id` | Unique ID of the broader capture session |
| `created`          | Timestamp of the operation in Unix time  |

These operation IDs are useful for:

* Group-based retrieval via REST
* Session persistence and deferred analysis

## 🧩 Capture Group Registry

The `.data/db/capture_group.json` file serves as the **index of grouped transactions**.
Each capture group is defined by a unique ID and a list of transaction hashes.

Capture groups can be composed of multiple test types or measurements.
They serve as the data backbone for multi-file workflows, including Excel generation and signal correlation.

```json
"91d93f5309944ac8": {
  "created": 1751950063,
  "transactions": [
    "1e171e1f8ef5377a",
    "3ed8cb029bbba404",
    "d94ad704d79cfce9",
    "53ee3282cef409b5",
    "ce6b8d43b6c8bf0c",
    "fa34f5dea580119b",
    "41f23b8c451af271",
    "2c228e79d86e6bf0",
    "f446c7fec87e5ad3",
    "3889d1976fb68feb"
  ]
}
```

| Field          | Description                                           |
| -------------- | ----------------------------------------------------- |
| `created`      | Timestamp of group creation (matches first operation) |
| `transactions` | List of transaction IDs grouped in this capture       |

## 🔁 Summary of Relationships

* A **transaction** = single file with metadata (manual or auto).
* A **capture group** = collection of transactions (used in multi-measurement workflows).
* An **operation ID** = tracks a grouped request tied to one capture group.

Use operation ID for API recall. Use capture group for report generation. Use transactions for raw file lookup.
