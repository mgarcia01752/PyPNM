# Multi-DS Channel Estimation API Guide

The Multi-DS Channel Estimation API allows clients to schedule periodic captures of downstream OFDM channel estimation coefficients, monitor progress, retrieve the raw PNM sample files, stop an in-progress capture, and perform post-capture analysis.

## Workflow Overview

1. **Start a Capture** (`POST /advance/multiChannelEstimation/start`)

   * Submit capture parameters (duration, interval) and SNMP settings.
   * Returns a `group_id` and `operation_id` for tracking.

2. **Check Status** (`GET /advance/multiChannelEstimation/status/{operation_id}`)

   * Poll to obtain current state, number of samples collected, and time remaining.

3. **Download Results** (`GET /advance/multiChannelEstimation/results/{operation_id}`)

   * Stream a ZIP archive containing all captured PNM files for the operation.

4. **Stop Early** (`DELETE /advance/multiChannelEstimation/stop/{operation_id}`)

   * Signal the background task to cease after the current iteration; returns final status.

5. **Analysis** (`POST /advance/multiChannelEstimation/analysis`)

   * Provide `operation_id` and an `analysis_type` to run signal-analysis routines on collected samples.


## Endpoint Stubs

### 1. Start Capture

**Request** (`MultiChanEstimationRequest` stub):

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
      "measurement_duration": 120,
      "sample_interval": 15
    }
  }
}
```

**Response** (`MultiChanEstimationStartResponse` stub):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "RUNNING",
  "message": null,
  "group_id": "grp-abc123",
  "operation_id": "op-xyz789"
}
```

**Response** (`MultiChanEstimationStartResponse` stub):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "RUNNING",
  "message": null,
  "group_id": "grp-abc123",
  "operation_id": "op-xyz789"
}
```

### 2. Status Check

**Request**: `GET /advance/multiChannelEstimation/status/{operation_id}`

**Response** (`MultiChanEstimationStatusResponse` stub):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "success",
  "message": null,
  "operation": {
    "operation_id": "op-xyz789",
    "state": "RUNNING",
    "collected": 3,
    "time_remaining": 105,
    "message": null
  }
}
```

### 3. Download Results

**Request**: `GET /advance/multiChannelEstimation/results/{operation_id}`

**Response**: ZIP archive (`application/zip`) containing files:

```
op-xyz789/chan_est_0001.pnm
op-xyz789/chan_est_0002.pnm
... etc.
```

op-xyz789/chan\_est\_0001.pnm
op-xyz789/chan\_est\_0002.pnm
... etc.

````

### 4. Stop Capture Early

**Request**: `DELETE /advance/multiChannelEstimation/stop/{operation_id}`

**Response** (`MultiChanEstimationStatusResponse` stub):
```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "STOPPED",
  "message": null,
  "operation": {
    "operation_id": "op-xyz789",
    "state": "STOPPED",
    "collected": 5,
    "time_remaining": 0,
    "message": null
  }
}
````

### 5. Analysis

**Request** (`MultiChanEstimationAnalysisRequest` stub):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "operation_id": "op-xyz789",
  "analysis": {
    "analysis_type": 1  // e.g., GROUP_DELAY
  }
}
```

**Response** (`MultiChanEstimationAnalysisResponse` stub):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Analysis GROUP_DELAY completed for group grp-abc123",
  "data": {
    // Results structure varies by analysis_type
  }
}
```
