## 🛰️ DOCSIS Constellation Display API

This document outlines the usage of the Constellation Display endpoints under the `/docs/pnm/ds/ofdm/constDisplay` path. These endpoints allow retrieving, analyzing, and managing soft-decision constellation data captured from DOCSIS 3.1 cable modems.

---

## 🔧 Endpoints

| Endpoint                                             | Description                                                                 |
| ---------------------------------------------------- | --------------------------------------------------------------------------- |
| `POST /docs/pnm/ds/ofdm/constDisplay/getMeasurement` | Captures a raw constellation measurement using the modem's current profile. |
| `POST /docs/pnm/ds/ofdm/constDisplay/getAnalysis`    | Analyzes the captured constellation data for diagnostics or visualization.  |
| `POST /docs/pnm/ds/ofdm/constDisplay/getFiles`       | Lists or retrieves saved constellation files for a target cable modem.      |

---

## 📍 `POST /docs/pnm/ds/ofdm/constDisplay/getMeasurement`

### Description

Captures OFDM constellation samples from the target modem's downstream subcarriers, based on the modulation order offset. The capture includes I/Q samples for a number of OFDM symbols, and is saved for later analysis.

### Request Body

```json
{
  "mac_address": "00:1a:2b:3c:4d:5e",
  "ip_address": "172.20.58.24",
  "modulation_order_offset": 0,
  "number_sample_symbol": 8192
}
```

| Field                     | Type    | Description                                                                                                                                              |
| ------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mac_address`             | string  | MAC address of the target cable modem (colon or dot-separated formats accepted).                                                                         |
| `ip_address`              | string  | IPv4 address of the modem to which the request is sent.                                                                                                  |
| `modulation_order_offset` | integer | Offset from the **lowest modulation order** in the OFDM profile. A value of 0 targets the lowest QAM order; higher values step through available orders. |
| `number_sample_symbol`    | integer | Number of OFDM symbols to capture (commonly 8192).                                                                                                       |

---

### Response Example

```json
{
  "mac_address": "00:1a:2b:3c:4d:5e",
  "status": 0,
  "message": null,
  "data": {
    "data": [
      {
        "status": "SUCCESS",
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 3,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 90326
        },
        "channel_id": 34,
        "mac_address": "00:1a:2b:3c:4d:5e",
        "subcarrier_zero_frequency": 631100000,
        "actual_modulation_order": "qam256",
        "num_sample_symbols": 8192,
        "subcarrier_spacing": 25000,
        "sample_length": 32768,
        "value_units": "[Real(I), Imaginary(Q)]",
        "values": [
          [-3.5628662109375, 1.52734375],
          ...
        ]
      }
    ]
  }
}
```

---

### Notes

* The `modulation_order_offset` is useful when multiple QAM profiles (e.g., 256-QAM, 1024-QAM, 4096-QAM) are in use. Offset 0 targets the lowest active profile.
* Each `value` pair in the output represents a single complex I/Q sample: `[I, Q]`.
* `sample_length` represents the total number of complex samples.
* Captured values are raw and unnormalized, intended for constellation plotting or signal integrity checks.
