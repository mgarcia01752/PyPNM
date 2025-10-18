# Multi-DS Channel Estimation API Guide

The Multi-DS Channel Estimation API provides mechanisms to schedule periodic captures of downstream OFDM channel estimation coefficients, monitor capture progress, retrieve raw PNM sample files, stop an in-progress capture, and perform post-capture analysis.

## Endpoint Summary

| Endpoint | HTTP Method | Section Reference | Description |
|-----------|--------------|-------------------|--------------|
| `/advance/multiChannelEstimation/start` | `POST` | [Start Capture](#1-start-capture) | Begin a multi-sample ChannelEstimation capture |
| `/advance/multiChannelEstimation/status/{operation_id}` | `GET` | [Check Status](#2-check-status) | Retrieve capture progress and status |
| `/advance/multiChannelEstimation/results/{operation_id}` | `GET` | [Download Results](#3-download-results) | Download a ZIP of captured PNM files |
| `/advance/multiChannelEstimation/stop/{operation_id}` | `DELETE` | [Stop Capture Early](#4-stop-capture-early) | Stop an active capture gracefully |
| `/advance/multiChannelEstimation/analysis` | `POST` | [Analysis](#5-analysis) | Run signal analysis on collected data |

---

## Workflow Overview

1. **Start a Capture** (`POST /advance/multiChannelEstimation/start`)  
   Submit capture parameters (duration, interval) and SNMP settings.  
   Returns a `group_id` and `operation_id` for tracking.

2. **Check Status** (`GET /advance/multiChannelEstimation/status/{operation_id}`)  
   Poll the capture state, number of samples collected, and time remaining.

3. **Download Results** (`GET /advance/multiChannelEstimation/results/{operation_id}`)  
   Stream a ZIP archive containing all captured PNM files for the operation.

4. **Stop Early** (`DELETE /advance/multiChannelEstimation/stop/{operation_id}`)  
   Signal the background process to stop after the current iteration and return the final status.

5. **Analysis** (`POST /advance/multiChannelEstimation/analysis`)  
   Provide an `operation_id` and `analysis_type` to run signal-analysis routines on collected samples.

---

## 1. Start Capture

**Request** (`MultiChanEstimationRequest`):

```json
{
  "cable_modem": {
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
    }
  },
  "capture": {
    "parameters": {
      "measurement_duration": 120,
      "sample_interval": 15
    }
  }
}
````
**Response** (`MultiChanEstimationStartResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "started",
  "message": null,
  "operation": {
    "group_id": "grp-abc123",
    "operation_id": "3df9f479d7a549b7"
  }
}
```

## 2. Check Status

**Request**

`GET /advance/multiChannelEstimation/status/3df9f479d7a549b7`

**Response** (`MultiChanEstimationStatusResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "success",
  "message": null,
  "operation": {
    "operation_id": "3df9f479d7a549b7",
    "state": "RUNNING",
    "collected": 3,
    "time_remaining": 105,
    "message": null
  }
}
```

---

## 3. Download Results

**Request**

`GET /advance/multiChannelEstimation/results/3df9f479d7a549b7`

**Response**

ZIP archive (`application/zip`) containing captured ChannelEstimation files.

Example archive contents:

```

```

---

## 4. Stop Capture Early

**Request**

`DELETE /advance/multiChannelEstimation/stop/3df9f479d7a549b7`

**Response** (`MultiChanEstimationStatusResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "STOPPED",
  "message": null,
  "operation": {
    "operation_id": "3df9f479d7a549b7",
    "state": "STOPPED",
    "collected": 5,
    "time_remaining": 0,
    "message": null
  }
}
```

## 5. Analysis

**Available Analysis Types**

| Analysis Type                | Value | Description                                                                                     |
| ---------------------------- | ----- | ----------------------------------------------------------------------------------------------- |
| `MIN_AVG_MAX`                | `0`   | Computes minimum, average, and maximum amplitude or phase values across all captures.           |
| `GROUP_DELAY`                | `1`   | Calculates per-subcarrier group delay from the channel frequency response.                      |
| `LTE_DETECTION_PHASE_SLOPE`  | `2`   | Detects potential LTE interference using phase-slope anomalies across the OFDM spectrum.        |
| `ECHO_DETECTION_PHASE_SLOPE` | `3`   | Identifies in-channel echoes or reflections by evaluating abnormal phase slope discontinuities. |
| `ECHO_DETECTION_IFFT`        | `4`   | Performs echo detection via inverse FFT to reveal impulse-response peaks.                       |

**Request** (`MultiChanEstimationAnalysisRequest`):

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

**Response** (`MultiChanEstimationAnalysisResponse`):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Analysis GROUP_DELAY completed for group grp-abc123",
  "data": {
    "194": {
      "frequency": [90000000, 90001562, 90003125],
      "group_delay_us": [0.08, 0.07, 0.09]
    }
  }
}
```
