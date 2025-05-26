# Multi-RxMER Capture API Guide

The Multi-RxMER Capture API provides a set of REST endpoints to orchestrate, monitor, and retrieve periodic downstream OFDM RxMER captures from a DOCSIS cable modem. This threaded background process supports continuous sampling or specific performance modes, enabling clients to start captures, poll status, download raw PNM data, prematurely stop operations, and run signal analysis on the collected measurements.

## Workflow Overview

1. **Start Capture** (`POST /advance/multiRxMer/start`)

   * Initiates a background RxMER capture session with defined duration and sample interval.
   * Select a measurement mode (e.g., continuous sampling or OFDM performance analysis).
   * Returns a `group_id` and `operation_id` for subsequent operations.

2. **Check Status** (`GET /advance/multiRxMer/status/{operation_id}`)

   * Poll the session state to see how many samples have been collected and the remaining time.

3. **Download Results** (`GET /advance/multiRxMer/results/{operation_id}`)

   * Streams a ZIP archive of all captured PNM files for offline processing or archival.

4. **Stop Capture Early** (`DELETE /advance/multiRxMer/stop/{operation_id}`)

   * Signals the capture task to end after the current iteration.
   * Returns final sample count and state.

5. **Analysis** (`POST /advance/multiRxMer/analysis`)

   * Submits an `operation_id` and desired `analysis_type` to execute post-capture analytics.
   * Returns processed metrics such as min/avg/max RxMER, heatmaps, or profile performance.

---

## Endpoint Stubs

### 1. Start Capture

**Request** (`MultiRxMerRequest` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "ip_address": "192.168.0.100",
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
  "measure": {
    "mode": 0
  }
}
```

**Response** (`MultiRxMerStartResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "running",
  "message": null,
  "group_id": "3bd6f7c107ad465b",
  "operation_id": "4aca137c1e9d4eb6"
}
```

---

### 2. Status Check

**Request**: `GET /advance/multiRxMer/status/{operation_id}`

**Response** (`MultiRxMerStatusResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "success",
  "message": null,
  "operation": {
    "operation_id": "35ecc8fb1b3c44bd",
    "state": "running",
    "collected": 2,
    "time_remaining": 50,
    "message": null
  }
}
```

---

### 3. Download Results

**Request**: `GET /advance/multiRxMer/results/{operation_id}`

**Response**: ZIP archive (`application/zip`) containing:

```
4aca137c1e9d4eb6/sample_0001.pnm
4aca137c1e9d4eb6/sample_0002.pnm
... etc.
```

---

### 4. Stop Capture Early

**Request**: `DELETE /advance/multiRxMer/stop/{operation_id}`

**Response** (`MultiRxMerStatusResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "stopped",
  "message": null,
  "operation": {
    "operation_id": "3e310a2296b24c78",
    "state": "stopped",
    "collected": 4,
    "time_remaining": 42,
    "message": null
  }
}
```

---

### 5. Analysis

**Request** (`MultiRxMerAnalysisRequest` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "analysis": {
    "analysis_type": 0
  },
  "operation_id": "string"
}
```

**Response** (`MultiRxMerAnalysisResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Analysis MIN_AVG_MAX completed for group 3fbc19a7fffe49c4",
  "data": {
    // Data structure varies by analysis type: e.g. { "min": 28.5, "avg": 31.2, "max": 33.8 }
  }
}
```

---

> **Note:** The `data` payload will differ depending on the `analysis_type` (MIN\_AVG\_MAX, OFDM\_PROFILE\_PERFORMANCE, RXMER\_HEAT\_MAP, etc.). Use the corresponding schema in `api/routes/advance/multi_rxmer/schemas.py` for full details.
