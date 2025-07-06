# PNM Operations - Downstream OFDM RxMER

## 📚 Table of Contents

* [Get Measurement](#get-measurement)
* [Get Analysis](#get-analysis)
* [Analysis and Output Types](#analysis-and-output-types)
* [Differences Between Measurement and Analysis](#differences-between-measurement-and-analysis)

## Get Measurement

### 📡 Endpoint

**POST** `/docs/pnm/ds/ofdm/rxMer/getMeasurement`

Retrieves subcarrier-level RxMER (Receive Modulation Error Ratio) measurements from a DOCSIS 3.1+ cable modem. RxMER is critical in evaluating signal quality across the OFDM channel bandwidth. This includes statistical summaries and calculated modulation support per subcarrier.

### 🗒️ Request Body (JSON)

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "ip_address": "192.168.0.1",
  "snmp": {
    "snmpV2C": {
      "community": "private"
    },
    "snmpV3": {
      "username": "string",
      "securityLevel": "noAuthNoPriv",
      "authProtocol": "MD5",
      "authPassword": "string",
      "privProtocol": "DES",
      "privPassword": "string"
    }
  }
}
```

### 📤 JSON Response

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "status": 0,
  "message": null,
  "measurement": {
    "data": [
      {
        "status": "SUCCESS",
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 4,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751831578
        },
        "channel_id": 197,
        "mac_address": "a1:b2:c3:d4:e5:f6",
        "zero_frequency": 1217600000,
        "first_active_subcarrier_index": 148,
        "subcarrier_spacing": 50000,
        "data_length": 3800,
        "occupied_channel_bandwidth": 190000000,
        "value_units": "dB",
        "values": [43.5, 44.5, 43.5, 43.5, 44],
        "signal_statistics": {
          "mean": 43.45,
          "median": 43.5,
          "std": 1.20,
          "variance": 1.44,
          "power": 1889.31,
          "peak_to_peak": 7.75,
          "mean_abs_deviation": 0.97,
          "skewness": -0.085,
          "kurtosis": 2.75,
          "crest_factor": 1.08,
          "zero_crossing_rate": 0,
          "zero_crossings": 0
        },
        "bits_per_symbol": [14, 14, 14, 14, 14],
        "modulations": ["qam_16384", "qam_16384", "qam_16384", "qam_16384", "qam_16384"],
        "supported_modulation_counts": {
          "qam_2": 3800,
          "qam_4": 3800,
          "qam_8": 3800,
          "qam_16": 3800,
          "qam_32": 3800,
          "qam_64": 3800,
          "qam_128": 3800,
          "qam_256": 3800,
          "qam_512": 3800,
          "qam_1024": 3800,
          "qam_2048": 3800,
          "qam_4096": 3800,
          "qam_8192": 3800,
          "qam_16384": 3273
        }
      }
    ]
  }
}
```

### 📃 Response Field Details

| Field                           | Type      | Description                                                     |
| ------------------------------- | --------- | --------------------------------------------------------------- |
| `mac_address`                   | string    | MAC address of the cable modem                                  |
| `status`                        | int       | 0 = success                                                     |
| `pnm_header`                    | object    | Metadata header for the PNM file                                |
| `channel_id`                    | int       | Downstream OFDM channel ID                                      |
| `zero_frequency`                | int       | Frequency corresponding to subcarrier index 0                   |
| `first_active_subcarrier_index` | int       | Index of first active subcarrier                                |
| `subcarrier_spacing`            | int       | Subcarrier spacing in Hz                                        |
| `data_length`                   | int       | Number of subcarrier measurements (N)                           |
| `occupied_channel_bandwidth`    | int       | Width of the occupied channel in Hz                             |
| `value_units`                   | string    | Always in dB for RxMER                                          |
| `values`                        | float\[]  | RxMER values for each subcarrier                                |
| `signal_statistics`             | object    | Statistical analysis of RxMER signal                            |
| `bits_per_symbol`               | int\[]    | Calculated Shannon-based bit support per subcarrier             |
| `modulations`                   | string\[] | Shannon-inferred modulation type per subcarrier                 |
| `supported_modulation_counts`   | object    | Dictionary showing how many bins support each modulation format |

### 📒 Notes

* RxMER measurements allow detection of localized impairments in the frequency domain.
* Calculated modulation support is based on Shannon capacity approximation.
* Statistical metrics can help assess system noise, distortion, and dynamic range.
* Use in conjunction with modulation profile and constellation analysis for complete link evaluation.

## Get Analysis

### 📡 Endpoint

**POST** `/docs/pnm/ds/ofdm/rxMer/getAnalysis`

Analyzes the RxMER sample data from a prior measurement and extracts additional carrier-level statistics. The analysis is returned as structured values including frequency, MER, and carrier status per subcarrier.

Supports multiple output formats (`JSON`, `xlsx`) with `type=0` currently for `BASIC` analysis only.

### 🗒️ Request Body (JSON)

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "ip_address": "192.168.0.1",
  "snmp": {
    "snmpV2C": {
      "community": "private"
    },
    "snmpV3": {
      "username": "string",
      "securityLevel": "noAuthNoPriv",
      "authProtocol": "MD5",
      "authPassword": "string",
      "privProtocol": "DES",
      "privPassword": "string"
    }
  },
  "analysis": {
    "type": 0
  },
  "output": {
    "type": 0
  }
}
```

### 📤 JSON Response

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "status": 0,
  "data": {
    "analysis": [
      {
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 4,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751832573
        },
        "mac_address": "a1:b2:c3:d4:e5:f6",
        "channel_id": 197,
        "magnitude_unit": "dB",
        "frequency_unit": "Hz",
        "carrier_status_map": {
          "exclusion": "0",
          "clipped": "1",
          "normal": "2"
        },
        "carrier_values": {
          "carrier_count": 3800,
          "magnitude": [float],
          "frequency": [int],
          "carrier_status": [int]
        },
        "modulation_statistics": {
          "bits_per_symbol": [int],
          "modulations": [str],
          "supported_modulation_counts": {
            "qam_2": 3800,
            "qam_4": 3800,
            "qam_8": 3800,
            "qam_16": 3800,
            "qam_32": 3800,
            "qam_64": 3800,
            "qam_128": 3800,
            "qam_256": 3800,
            "qam_512": 3800,
            "qam_1024": 3800,
            "qam_2048": 3800,
            "qam_4096": 3800,
            "qam_8192": 3800,
            "qam_16384": 3265
          }
        }
      }
    ]
  }
}
```

## Analysis and Output Types

### `analysis.type`

| Value | Type  | Description                                                                                                                                                                |
| ----- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0`   | BASIC | Default analysis mode. Extracts magnitude, frequency, and status per subcarrier. Future types may include spectral anomaly detection, slope detection, and delta tracking. |

### `output.type`

| Value | Format | Description                                                                              |
| ----- | ------ | ---------------------------------------------------------------------------------------- |
| `0`   | JSON   | Standard structured JSON suitable for API responses and dashboards.                      |
| `0`   | CSV    | Not Supported                                                                            |
| `2`   | XLSX   | Excel-compatible output for offline review, reporting, or spreadsheet use.               |

## Differences Between Measurement and Analysis

| Feature               | `/getMeasurement`                              | `/getAnalysis`                                                 |
| --------------------- | ---------------------------------------------- | -------------------------------------------------------------- |
| Primary Output        | Raw RxMER values and statistics                | Parsed carrier-level data with status/frequency                |
| Channel Coverage      | Each OFDM channel captured individually        | Per-carrier view across each OFDM channel                      |
| Additional Metadata   | Yes (signal stats, modulations)                | Yes (mapped carrier status, frequencies, derived values)       |
| Output Format Options | JSON only                                      | JSON or XLSX (`output.type`)                                   |
| Analysis Mode         | Not applicable                                 | Supports `BASIC` (more to come)                                |
| Best Use Case         | Real-time subcarrier signal quality monitoring | Structured post-processing, reporting, and visualization input |
