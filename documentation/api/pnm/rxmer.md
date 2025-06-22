# 📡 DOCSIS RxMER Analysis API

This document outlines the usage of the RxMER (Receive Modulation Error Ratio) endpoints under the `/docs/pnm/ds/ofdm/rxMer` path. These endpoints allow for retrieving, analyzing, and managing RxMER measurement data from DOCSIS cable modems.

## 🔧 Endpoints

| Endpoint                                      | Description                                                                                        |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `POST /docs/pnm/ds/ofdm/rxMer/getMeasurement` | Retrieves the most recent RxMER subcarrier measurement from the cable modem.                       |
| `POST /docs/pnm/ds/ofdm/rxMer/getAnalysis`    | Generates and returns an analysis of RxMER values per subcarrier for visualization or diagnostics. |
| `POST /docs/pnm/ds/ofdm/rxMer/getFiles`       | Lists or fetches saved RxMER measurement files for a given cable modem.                            |

## 🔍 `POST /docs/pnm/ds/ofdm/rxMer/getMeasurement`

### Description

Fetches the latest RxMER subcarrier data from a target cable modem.

### Request Body

```json
{
  "mac_address": "00:11:22:33:44:55",
  "ip_address": "192.168.100.1"
}
```

### Response

```json
{
  "status": "success",
  "data": {
    "pnm_header": { ... },
    "channel_id": 1,
    "subcarrier_spacing": 60000,
    "zero_frequency": 275000000,
    "active_subcarrier_index": 4096,
    "values": [35.0, 34.8, 34.9, ..., 33.5]
  }
}
```

## 📈 `POST /docs/pnm/ds/ofdm/rxMer/getAnalysis`

### Description

Generates analysis output based on the measurement and requested `analysis_type`.

### Supported Analysis Types

| Value | Name  | Description                                                                     |
| ----- | ----- | ------------------------------------------------------------------------------- |
| 0     | BASIC | Provides frequency, magnitude (RxMER in dB), and carrier status classification. |

### Request Body

```json
{
  "mac_address": "00:11:22:33:44:55",
  "ip_address": "192.168.100.1",
  "analysis_type": 0
}
```

### Response Example

```json
{
  "status": "success",
  "data": {
    "analysis": [
      {
        "pnm_header": { ... },
        "channel_id": 1,
        "magnitude_unit": "dB",
        "frequency_unit": "Hz",
        "carrier_status_map": {
          "exclusion": 0,
          "clipped": 1,
          "normal": 2
        },
        "carrier_values": {
          "carrier_count": 4096,
          "magnitude": [35.0, 34.8, ..., 33.5],
          "frequency": [275000000, 275060000, ..., 519760000],
          "carrier_status": [0, 0, 2, ..., 2]
        }
      }
    ]
  }
}
```

## 🗂️ `POST /docs/pnm/ds/ofdm/rxMer/getFiles`

### Description

Retrieves a list of saved RxMER measurement files for the target modem or fetches specific file contents.

### Request Body

```json
{
  "mac_address": "00:11:22:33:44:55",
  "ip_address": "192.168.100.1"
}
```

### Response

```json
{
  "status": "success",
  "data": {
    "files": [
      {
        "filename": "rxmer_2025-05-14T12:00:00Z.json",
        "timestamp": "2025-05-14T12:00:00Z",
        "size_bytes": 3421
      },
      ...
    ]
  }
}
```

## 📘 Notes

* `carrier_status_map` defines how each subcarrier is classified:

  * `normal`: valid RxMER value
  * `clipped`: too low or high to be trusted
  * `exclusion`: intentionally excluded (e.g., PLC/guard bands)
* Magnitude values are in decibels (dB), frequency values are in Hertz (Hz).
