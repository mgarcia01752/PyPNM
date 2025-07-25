# PNM File Manager

This set of endpoints supports file discovery, download, and automated analysis of PNM telemetry data captured from DOCSIS cable modems. Each file contains structured measurements such as RxMER, pre-equalization taps, spectrum scans, and more. These files are associated with a MAC address and a transaction ID, and can be queried for further analysis.

Use these APIs to:

* Locate files uploaded by a specific cable modem
* Download raw binary PNM files (e.g., RxMER, constellation)
* Trigger backend analysis workflows for uploaded telemetry

## 📑 Table of Contents

* [🔍 Search Uploaded Files](#-search-uploaded-files)
* [📦 Download File by Transaction](#-download-file-by-transaction)
* [📈 Trigger File Analysis](#-trigger-file-analysis)

## 🔍 Search Uploaded Files

**GET** `/docs/pnm/files/searchFiles/{mac_address}`

Returns a list of uploaded PNM measurement files for a given cable modem.

### 🟦 Response Body

```json
{
  "files": {
    "38:ad:2b:12:49:4c": [
      {
        "transaction_id": "9b261936786e6817",
        "filename": "ds_ofdm_rxmer_per_subcar_38ad2b12494c_197_1751831579.bin",
        "pnm_test_type": "DS_OFDM_RXMER_PER_SUBCAR",
        "timestamp": "2025-07-06 13:52:59 UTC",
        "sys_descr": {
          "HW_REV": "0A",
          "VENDOR": "Hitron Technologies",
          "BOOTR": "2022.01-MXL-v-4.0.350",
          "SW_REV": "8.4.0.0.2b1",
          "MODEL": "CODA60V"
        }
      },
      {...}
    ]
  }
}
```

## 📦 Download File by Transaction

**GET** `/docs/pnm/files/download/{transaction_id}`

Downloads the raw binary PNM measurement file associated with the provided transaction ID.

> **ℹ️ Note:**
> If using this endpoint through SwaggerUI, the file may either download automatically or appear as a clickable link in the browser. Click the link to start the download if it doesn’t begin on its own.

### 🟨 Response Headers

```
accept-ranges: bytes
content-disposition: attachment; filename="ds_ofdm_chan_est_coef_38ad2b12494c_193_1751835927.bin"
content-length: 15228
content-type: application/octet-stream
date: Mon,07 Jul 2025 00:38:05 GMT
etag: "3c91439d5c94960965838ad01f171b31"
last-modified: Sun,06 Jul 2025 21:05:27 GMT
server: uvicorn
```

## 📈 Trigger File Analysis

**POST** `/docs/pnm/files/getAnalysis`

Triggers an analysis pipeline on a specified PNM file.

### 🟩 Request Body

```json
{
  "mac_address": "38:AD:2B:12:49:4C",
  "transaction_id": "7832a31a37eec15a",
  "analysis_type": "auto"
} 
```
