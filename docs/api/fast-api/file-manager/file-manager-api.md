# PNM Operations – PNM File Manager

REST API For Searching, Downloading, Uploading, And Analyzing PNM Capture Files.

## Table Of Contents

- [Overview](#overview)
- [Endpoints](#endpoints)
- [Search Files By MAC Address](#1-search-files-by-mac-address)
- [Download File By Transaction ID](#2-download-file-by-transaction-id)
- [Download Files By MAC Address (ZIP Archive)](#3-download-files-by-mac-address-zip-archive)
- [Download Files By Operation ID (ZIP Archive)](#4-download-files-by-operation-id-zip-archive)
- [Upload PNM File](#5-upload-pnm-file)
- [Analyze PNM File](#6-analyze-pnm-file)
- [Request And Response Examples](#request-and-response-examples)

## Overview

The PNM File Manager API exposes a small set of endpoints that allow clients to:

- Discover previously captured PNM files associated with a cable modem.
- Download individual PNM files or grouped archives.
- Upload external PNM capture files into the PyPNM transaction database.
- Trigger analysis on a stored PNM file.

Endpoints live under the FastAPI router:

```text
/docs/pnm/files
```

Typical workflow:

1. Upload or capture files so they appear in the transaction database.
2. Query the list of files by MAC address.
3. Download single files or archive groups (MAC or operation-wide).
4. Optionally invoke analysis on a specific transaction.

## Endpoints

### 1) Search Files By MAC Address

**Endpoint**

```text
POST /docs/pnm/files/searchFiles/{mac_address}
```

**Description**

Return a mapping of MAC address to a list of file entries associated with that modem. Each file entry carries the transaction identifier, filename, PNM test type, timestamp, and optional system description metadata.

**Path Parameter**

| Name        | Type   | Description                                                               |
| ----------- | ------ | ------------------------------------------------------------------------- |
| mac_address | string | MAC address of the cable modem. Example: `aa:bb:cc:dd:ee:ff`             |

**Successful Response (200)**

- Content type: `application/json`
- Body schema: `FileQueryResponse`

```json
{
  "files": {
    "aa:bb:cc:dd:ee:ff": [
      {
        "transaction_id": "f67dd3ffb40420d6",
        "filename": "ds_ofdm_rxmer_per_subcar_aa_bb_cc_dd_ee_ff.bin",
        "pnm_test_type": "DS_OFDM_RXMER_PER_SUBCAR",
        "timestamp": 1763736292,
        "system_description": {
          "HW_REV": "1.0",
          "VENDOR": "LANCity",
          "BOOTR": "NONE",
          "SW_REV": "1.0.0",
          "MODEL": "LCPET-3"
        }
      }
    ]
  }
}
```

### 2) Download File By Transaction ID

**Endpoint**

```text
GET /docs/pnm/files/download/transactionID/{transaction_id}
```

**Description**

Download a single PNM capture file associated with a given transaction identifier.

**Path Parameter**

| Name           | Type   | Description                                          |
| -------------- | ------ | ---------------------------------------------------- |
| transaction_id | string | Unique transaction identifier for the PNM file.     |

**Successful Response (200)**

- Content type: `application/octet-stream`
- Body: Raw PNM binary file.

If the transaction ID is not found:

```json
{
  "detail": "Transaction ID not found."
}
```

with HTTP 404 status.

### 3) Download Files By MAC Address (ZIP Archive)

**Endpoint**

```text
GET /docs/pnm/files/download/macAddress/{mac_address}
```

**Description**

Resolve all transactions for the given MAC address, collect their on-disk PNM files, and return a ZIP archive containing all existing files.

**Path Parameter**

| Name        | Type   | Description                                                               |
| ----------- | ------ | ------------------------------------------------------------------------- |
| mac_address | string | MAC address of the cable modem. Example: `aa:bb:cc:dd:ee:ff`             |

**Successful Response (200)**

- Content type: `application/zip`
- Body: ZIP archive of PNM capture files.

Errors can include:

```json
{
  "detail": "No transactions found for MAC address."
}
```

or

```json
{
  "detail": "No files on disk for MAC address."
}
```

both with HTTP 404 status.

### 4) Download Files By Operation ID (ZIP Archive)

**Endpoint**

```text
GET /docs/pnm/files/download/operationID/{operation_id}
```

**Description**

Resolve the capture group associated with a given operation ID, collect all transactions in that group, and return a ZIP archive containing all corresponding PNM files that exist on disk.

**Path Parameter**

| Name         | Type   | Description                                   |
| ------------ | ------ | --------------------------------------------- |
| operation_id | string | Operation identifier from the capture service.|

**Successful Response (200)**

- Content type: `application/zip`
- Body: ZIP archive of all PNM files associated with the operation.

Example error:

```json
{
  "detail": "No transactions found for Operation ID."
}
```

or

```json
{
  "detail": "No files on disk for Operation ID."
}
```

with HTTP 404 status.

### 5) Upload PNM File

**Endpoint**

```text
POST /docs/pnm/files/upload
```

**Description**

Upload a PNM capture file (for example, RxMER, constellation, histogram, spectrum) via multipart/form-data. The server persists the file, identifies the PNM file type from its header, maps it to a DOCSIS test, and registers a transaction using a placeholder null MAC address (to be backfilled later).

**Request**

- Content type: `multipart/form-data`
- Fields:

| Name | Type        | Description                                                                     |
| ---- | ----------- | ------------------------------------------------------------------------------- |
| file | binary file | Raw PNM capture file payload.                                                   |

**Successful Response (200)**

- Content type: `application/json`
- Body schema: `UploadFileResponse`

```json
{
  "mac_address": "00:00:00:00:00:00",
  "filename": "ds_ofdm_rxmer_per_subcar_example.bin",
  "transaction_id": "ea18519a572e2487"
}
```

If the file type is unrecognized:

```json
{
  "detail": "Unsupported or unrecognized PNM file type."
}
```

with HTTP 400 status.

### 6) Analyze PNM File

**Endpoint**

```text
POST /docs/pnm/files/getAnalysis
```

**Description**

Trigger an analysis run for a specific PNM file identified by transaction ID. The backend resolves the transaction, locates the PNM file, inspects its header, and routes it to the appropriate analysis pipeline. Current implementation returns a stubbed analysis response and plot URL.

**Request**

- Content type: `application/json`
- Body schema: `FileAnalysisRequest`

```json
{
  "transaction_id": "ea18519a572e2487",
  "analysis_type": "auto"
}
```

**Successful Response (200)**

- Content type: `application/json`
- Body schema: `AnalysisResponse`

```json
{
  "analysis_type": "auto",
  "plot_url": "/static/plots/ds_ofdm_rxmer_per_subcar_example.png",
  "summary": "Auto analysis placeholder for transaction ea18519a572e2487"
}
```

If the transaction is not found:

```json
{
  "detail": "Transaction ID not found for analysis."
}
```

with HTTP 404 status.

## Request And Response Examples

This section summarizes the core JSON shapes used by the PNM File Manager endpoints. All types are shown as they appear on the wire (FastAPI OpenAPI / SwaggerUI and tools such as Postman or curl).

### FileQueryResponse (Search Files)

```json
{
  "files": {
    "aa:bb:cc:dd:ee:ff": [
      {
        "transaction_id": "f67dd3ffb40420d6",
        "filename": "ds_ofdm_rxmer_per_subcar_aa_bb_cc_dd_ee_ff.bin",
        "pnm_test_type": "DS_OFDM_RXMER_PER_SUBCAR",
        "timestamp": 1763736292,
        "system_description": {
          "HW_REV": "1.0",
          "VENDOR": "LANCity",
          "BOOTR": "NONE",
          "SW_REV": "1.0.0",
          "MODEL": "LCPET-3"
        }
      }
    ]
  }
}
```

### UploadFileResponse (Upload PNM File)

```json
{
  "mac_address": "00:00:00:00:00:00",
  "filename": "ds_ofdm_rxmer_per_subcar_example.bin",
  "transaction_id": "ea18519a572e2487"
}
```

### AnalysisResponse (Analyze PNM File)

```json
{
  "analysis_type": "auto",
  "plot_url": "/static/plots/ds_ofdm_rxmer_per_subcar_example.png",
  "summary": "Auto analysis placeholder for transaction ea18519a572e2487"
}
```
