# PyPNM Database

Overview Of How PyPNM Stores, Organizes, And Links Measurement Data For Traceability And REST Access.

## Data Repository (Example)

```
.data
├── archive
│   └── aabbccddeeff_lcpet3_1760940313.zip
├── csv
│   ├── aabbccddeeff_lcpet3_1760940313_ofdm_profile_perf_1_ch33_pid0.csv
│   ├── aabbccddeeff_lcpet3_1760940313_ofdm_profile_perf_1_ch33_pid1.csv
│   ├── aabbccddeeff_lcpet3_1760940313_ofdm_profile_perf_1_ch33_pid3.csv
│   ├── aabbccddeeff_lcpet3_1760940313_ofdm_profile_perf_1_ch34_pid0.csv
│   ├── aabbccddeeff_lcpet3_1760940313_ofdm_profile_perf_1_ch34_pid1.csv
│   └── aabbccddeeff_lcpet3_1760940313_ofdm_profile_perf_1_ch34_pid3.csv
├── db
│   ├── capture_group.json
│   ├── operation_capture.json
│   └── transactions.json
├── json
├── msg_rsp
├── png
│   ├── aabbccddeeff_lcpet3_1760940313_33_profile_0_ofdm_profile_perf_1.png
│   ├── aabbccddeeff_lcpet3_1760940313_33_profile_1_ofdm_profile_perf_1.png
│   ├── aabbccddeeff_lcpet3_1760940313_33_profile_3_ofdm_profile_perf_1.png
│   ├── aabbccddeeff_lcpet3_1760940313_34_profile_0_ofdm_profile_perf_1.png
│   ├── aabbccddeeff_lcpet3_1760940313_34_profile_1_ofdm_profile_perf_1.png
│   └── aabbccddeeff_lcpet3_1760940313_34_profile_3_ofdm_profile_perf_1.png
├── pnm
│   ├── ds_ofdm_codeword_error_rate_aabbccddeeff_33_1760940254.bin
│   ├── ds_ofdm_codeword_error_rate_aabbccddeeff_33_1760940285.bin
│   ├── ds_ofdm_codeword_error_rate_aabbccddeeff_34_1760940287.bin
│   ├── ds_ofdm_modulation_profile_aabbccddeeff_33_1760940269.bin
│   ├── ds_ofdm_modulation_profile_aabbccddeeff_34_1760940270.bin
│   ├── ds_ofdm_rxmer_per_subcar_aabbccddeeff_33_1760940252.bin
│   └── ds_ofdm_rxmer_per_subcar_aabbccddeeff_33_1760940260.bin
│
└── xlsx
```

## Directory Reference

| Directory  | Typical Contents                                                | Example Filenames                                                     | Purpose                                                              |
| ---------- | --------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `archive/` | ZIP archives combining multi-file outputs (CSV, PNG, summaries) | `aabbccddeeff_lcpet3_1760940313.zip`                                  | One-stop bundle for download/sharing and offline review.             |
| `csv/`     | Per-measurement CSV exports                                     | `aabbccddeeff_lcpet3_1760940313_ofdm_profile_perf_1_ch34_pid1.csv`    | Tabular data for analysis, BI tools, and spreadsheets.               |
| `db/`      | JSON ledgers and indexes                                        | `transactions.json`, `operation_capture.json`, `capture_group.json`   | Traceability: transactions, operation→group links, grouped captures. |
| `json/`    | Raw/processed JSON outputs (when enabled)                       | —                                                                     | Structured artifacts for programmatic consumption.                   |
| `msg_rsp/` | Request/response message snapshots (optional)                   | —                                                                     | Diagnostics and audit of REST or SNMP exchanges.                     |
| `png/`     | Visualization images per capture/profile/channel                | `aabbccddeeff_lcpet3_1760940313_34_profile_1_ofdm_profile_perf_1.png` | Quick-look plots for reports and UIs.                                |
| `pnm/`     | Binary PNM files pulled from devices or uploads                 | `ds_ofdm_rxmer_per_subcar_aabbccddeeff_33_1760940252.bin`             | Source files used by analyses; include `pnm_header`.                 |
| `xlsx/`    | Excel workbooks                                                 | —                                                                     | Multi-sheet summaries and cross-linked reports.                      |

## Operation Capture Linking

The `.data/db/operation_capture.json` file links a multi-measurement **operation** to a single **capture group**.
An operation represents a higher-level request that may include different PNM test types (RxMER, FEC Summary, Modulation Profile).

```json
"6bc3877d9b374039": {
  "capture_group_id": "91d93f5309944ac8",
  "created": 1751950063
}
```

### Field Overview

| Field              | Type    | Description                                   |
| ------------------ | ------- | --------------------------------------------- |
| `capture_group_id` | string  | Unique ID of the broader capture session.     |
| `created`          | integer | Operation creation timestamp (epoch seconds). |

Common uses:

* Retrieve a complete session by operation ID via REST.
* Persist session context for deferred or repeat analysis.

## Capture Group Registry

The `.data/db/capture_group.json` file is the index of **grouped transactions**.
Capture groups can span multiple test types or measurements and underpin multi-file workflows (Excel generation, correlation, etc.).

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

### Field Overview

| Field          | Type    | Description                                                               |
| -------------- | ------- | ------------------------------------------------------------------------- |
| `created`      | integer | Group creation timestamp (epoch seconds; often the first operation time). |
| `transactions` | array   | List of transaction IDs belonging to this capture group.                  |

## Transaction Records

The `.data/db/transactions.json` file is the ledger of all file captures and uploads tracked by PyPNM.
Each entry represents a single file **transaction**, whether:

* Pulled automatically from a cable modem (e.g., via TFTP), or
* Manually uploaded by a user via the UI or API.

### Structure

Each transaction is indexed by a unique hash (e.g., UUID/digest of filename + timestamp):

```json
"1e171e1f8ef5377a": {
  "timestamp": 1751950064,
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "pnm_test_type": "DS_OFDM_RXMER_PER_SUBCAR",
  "filename": "ds_ofdm_rxmer_per_subcar_aabbccddeeff_197_1751950064.bin",
  "device_details": {
    "sys_descr": {
      "HW_REV": "1.0",
      "VENDOR": "LANCity",
      "BOOTR": "NONE",
      "SW_REV": "1.0.0",
      "MODEL": "LCPET-3"
    }
  }
}
```

### Field Overview

| Field            | Type    | Description                                                                 |
| ---------------- | ------- | --------------------------------------------------------------------------- |
| `timestamp`      | integer | Unix epoch seconds when the file was received or uploaded.                  |
| `mac_address`    | string  | Cable modem MAC address.                                                    |
| `pnm_test_type`  | string  | Test type that produced the file (e.g., `DS_OFDM_RXMER_PER_SUBCAR`).        |
| `filename`       | string  | Saved binary filename in `.data/pnm/`.                                      |
| `device_details` | object  | Parsed device metadata from SNMP when available (`sys_descr` fields shown). |

## Summary Of Relationships

* **Operation Capture → Capture Group → Transaction**
  An **operation** creates or references a single **capture group**, which aggregates many **transactions**.
* Use **operation ID** for API recall, **capture group** for report generation/correlation, and **transactions** for raw file lookup.
