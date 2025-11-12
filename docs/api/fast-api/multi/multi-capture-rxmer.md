# Multi‑RxMER Capture & Analysis API

A concise, implementation‑ready reference for orchestrating downstream OFDM RxMER captures, status polling, result retrieval, early termination, and post‑capture analysis.

## 📚 Contents

* [At a Glance](#at-a-glance)
* [Workflow](#workflow)
* [Endpoints](#endpoints)

  * [1) Start Capture](#1-start-capture)
  * [2) Status Check](#2-status-check)
  * [3) Download Results](#3-download-results)
  * [4) Stop Capture Early](#4-stop-capture-early)
  * [5) Analysis](#5-analysis)
* [Timing & Polling](#timing--polling)
* [Compatibility Matrix](#compatibility-matrix)
* [Conventions](#conventions)

## At a Glance

| Step | HTTP   | Path                                           | Purpose                                  |
| ---: | :----- | :--------------------------------------------- | :--------------------------------------- |
|    1 | POST   | `/advance/multiRxMer/start`                    | Begin a background capture               |
|    2 | GET    | `/advance/multiRxMer/status/{operation_id}`    | Poll capture progress                    |
|    3 | GET    | `/advance/multiRxMer/results/{operation_id}`   | Download a ZIP of captured PNM files     |
|    4 | DELETE | `/advance/multiRxMer/stop/{operation_id}`      | Stop the capture after current iteration |
|    5 | POST   | `/advance/multiRxMer/analysis`                 | Run post‑capture analytics               |

**Identifiers**

* `group_id`: Logical grouping for related operations.
* `operation_id`: Unique handle for one capture session. Use it for status, stop, results, and analysis.

## Workflow

1. **Start Capture** → receive `group_id` and `operation_id`.
2. **Poll Status** until `state ∈ ["completed","stopped"]`.
3. **Download Results** once finished or stopped.
4. **(Optional)** **Stop Early** to end after the current iteration.
5. **Run Analysis** on the finished capture using `operation_id` + analysis type.

## Endpoints

### 1) Start Capture

Starts a background RxMER capture with a fixed duration and sample interval.

**Request** `POST /advance/multiRxMer/start`
**Body** (`MultiRxMerRequest`):

```json
{
  "cable_modem": {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "ip_address": "192.168.0.100"
  },
  "snmp": {
    "snmpV2C": { "community": "public" },
    "snmpV3": {
      "username": "user",
      "securityLevel": "noAuthNoPriv",
      "authProtocol": "MD5",
      "authPassword": "password",
      "privProtocol": "DES",
      "privPassword": "password"
    }
  },
  "capture": {
    "parameters": {
      "measurement_duration": 60,
      "sample_interval": 10
    }
  },
  "measure": { "mode": 0 }
}
```

**Fields**

* `cable_modem.mac_address` *(string)* – CM MAC.
* `cable_modem.ip_address` *(string)* – IPv4/IPv6 address.
* `snmp` *(object)* – Either `snmpV2C` **or** `snmpV3`.
* `capture.parameters.measurement_duration` *(int, s)* – Total runtime.
* `capture.parameters.sample_interval` *(int, s)* – Interval between samples.
* `measure.mode` *(int)* – `0` = continuous sampling; `1` = OFDM performance.

**Response** (`MultiRxMerStartResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "running",
  "message": null,
  "group_id": "3bd6f7c107ad465b",
  "operation_id": "4aca137c1e9d4eb6"
}
```

* `status` is `"running"` immediately after start.

### 2) Status Check

**Request** `GET /advance/multiRxMer/status/4aca137c1e9d4eb6`

**Response** (`MultiRxMerStatusResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "success",
  "message": null,
  "operation": {
    "operation_id": "4aca137c1e9d4eb6",
    "state": "running",
    "collected": 2,
    "time_remaining": 50,
    "message": null
  }
}
```

**Operation Fields**

* `state` ∈ `running | completed | stopped`
* `collected` *(int)* – number of samples captured so far
* `time_remaining` *(int, s)* – rough remaining seconds
* `message` *(string|null)* – optional details

### 3) Download Results

**Request** `GET /advance/multiRxMer/results/4aca137c1e9d4eb6`

**Response**

* `Content-Type: application/zip`
* Zip name: `multiRxMer_<mac>_4aca137c1e9d4eb6.zip`
* Contains PNM files like:

  ```text
  ds_ofdm_rxmer_per_subcar_aabbccddeeff_193_1751762613.bin
  ds_ofdm_rxmer_per_subcar_aabbccddeeff_194_1751762613.bin
  ...
  ```

**Notes**

* Each file = one snapshot at `sample_interval` cadence.
* File count == `operation.collected`.

### 4) Stop Capture Early

**Request** `DELETE /advance/multiRxMer/stop/4aca137c1e9d4eb6`

**Response** (`MultiRxMerStatusResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "stopped",
  "message": null,
  "operation": {
    "operation_id": "4aca137c1e9d4eb6",
    "state": "stopped",
    "collected": 4,
    "time_remaining": 42,
    "message": null
  }
}
```

* `status` is `"stopped"` when accepted.
* Expect up to one `sample_interval` for the stop to take effect.

### 5) Analysis

**Request** `POST /advance/multiRxMer/analysis`
**Body** (`MultiRxMerAnalysisRequest`):

```json
{
  "analysis": {
    "type": 0
  },
  "output": {
    "type": 4
  },
  "operation_id": "hash-like-string"
}
```

**Analysis Types** (`analysis.type`)

| Code | Name                       | Description                        | Requires Mode |
| ---: | -------------------------- | ---------------------------------- | ------------- |
|  `0` | `MIN_AVG_MAX`              | Min/avg/max RxMER across samples   | `0`           |
|  `1` | `RXMER_HEAT_MAP`           | Time×frequency heatmap grid        | `0`           |
|  `2` | `OFDM_PROFILE_PERFORMANCE_1` | Per‑subcarrier performance metrics | `0` or `1`    |

**Output Types** (`output.type`)

| Code | Name      | Description                              | Media Type         |
| ---: | --------- | ---------------------------------------- | ------------------ |
|  `json`     | `JSON`    | Structured JSON body                     | `application/json` |
|  `archive`  | `ARCHIVE` | ZIP containing multiple output artifacts | `application/zip`  |

**Response** (`MultiRxMerAnalysisResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Analysis MIN_AVG_MAX completed for group 3bd6f7c107ad465b",
  "data": { "min": 28.5, "avg": 31.2, "max": 33.8 }
}
```

* `status` `0` = success; non‑zero indicates error (see `message`).
* `data` varies by analysis type:

  * **MIN_AVG_MAX** → `{ "min": 28.5, "avg": 31.2, "max": 33.8 }`
  * **RXMER_HEAT_MAP** → `{ "timestamps": [1697040000], "frequencies": [193000000, 194000000], "heatmap": [[30.1, 29.8]] }`
  * **OFDM_PROFILE_PERFORMANCE** → `{ "193": { "rxmer": 31.5, "snr": 34.1 }, "194": { "rxmer": 30.9, "snr": 33.7 } }`

> Use canonical schemas in `api/routes/advance/multi_rxmer/schemas.py` for exact field names and enums.

## Timing & Polling

### Capture Timing

* `measurement_duration` *(s)* → total run length.
  Example: `60` means a one‑minute capture.
* `sample_interval` *(s)* → period between samples.
  Example: `10` over `60` seconds → **6** samples.

### Polling Strategy

* Poll **no more than once per** `sample_interval`.
* `time_remaining == 0` **and** `state == "completed"` → stop polling.

### Results Availability

* When `state ∈ ["completed","stopped"]`, ZIP is immediately available.
* Files are produced at sampling time; the archive is just a bundle step.

### Stop Semantics

1. Current iteration finishes.
2. Final PNM for that iteration is written.
3. `state → "stopped"` (remaining time may be > 0 if mid‑interval).

## Compatibility Matrix

| Measure Mode | Suited Analyses                                             |
| :----------: | ----------------------------------------------------------- |
|      `0`     | `MIN_AVG_MAX`, `RXMER_HEAT_MAP`, `OFDM_PROFILE_PERFORMANCE` |
|      `1`     | `OFDM_PROFILE_PERFORMANCE`, `MIN_AVG_MAX`, `RXMER_HEAT_MAP` |

> Choose `mode=1` when you specifically want OFDM performance context; otherwise `mode=0` is recommended for continuous monitoring.

## Conventions

* Use generic addresses in examples:
  `mac_address = "aa:bb:cc:dd:ee:ff"`, `ip_address = "192.168.0.100"`.
* Zip name format: `multiRxMer_<mac>_4aca137c1e9d4eb6.zip`.
* PNM file name format: `ds_ofdm_rxmer_per_subcar_<mac>_<channel_id>_<epoch>.bin`.
* Status codes: prefer 2xx on success; include concise error text in `message` for failures.
