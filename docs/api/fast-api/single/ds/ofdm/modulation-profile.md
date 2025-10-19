# PNM Operations – Downstream OFDM Modulation Profile

This API gives operators visibility into how subcarriers are modulated within DOCSIS 3.1 OFDM downstream channels. Each OFDM channel can carry multiple modulation profiles (e.g., QAM-16 to QAM-4096), each tailored to the SNR conditions across frequency ranges. This endpoint retrieves the raw profile data and maps which modulation scheme is used across subcarrier groups.

By pairing the /getMeasurement and /getAnalysis endpoints, operators can transform raw schema data into a meaningful per-subcarrier view, including estimated Shannon limits. These insights are crucial for validating profile assignments, identifying potential overmodulation or underutilization, and assessing channel capacity performance under real-world conditions.

The analysis output is suitable for both automation and visualization, supporting export to Excel for offline diagnostics and engineering reports.

## 📂 Table of Contents

* [Get Measurement](#get-measurement)
* [Get Analysis](#get-analysis)
* [Analysis and Output Types](#analysis-and-output-types)
* [Differences Between Measurement and Analysis](#differences-between-measurement-and-analysis)

## Get Measurement

### 📊 Endpoint

**POST** `/docs/pnm/ds/ofdm/modulationProfile/getMeasurement`

This endpoint retrieves the modulation profile used in DOCSIS 3.1 OFDM downstream channels. It provides metadata and modulation schemes across available OFDM profiles, including per-subcarrier modulation orders. Note that this is a raw conversion; additional processing is needed to analyze full bit-loading and carrier types.

### 📅 Request Body (JSON)

```json
{
  "cable_modem": {
  "mac_address": "aa:bb:cc:dd:ee:ff", 
  "ip_address": "192.168.0.100",
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

### 📤 Response Body

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "measurement": {
    "data": [
      {
        "status": "SUCCESS",
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 10,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751820333
        },
        "channel_id": 197,
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "num_profiles": 2,
        "zero_frequency": 1217600000,
        "first_active_subcarrier_index": 148,
        "subcarrier_spacing": 50000,
        "profile_data_length_bytes": 926,
        "profiles": [
          {
            "profile_id": 4,
            "schemes": [
              {
                "schema_type": 0,
                "modulation_order": "qam_4096",
                "num_subcarriers": 38
              }
            ]
          },
          {
            "profile_id": 0,
            "schemes": [
              {
                "schema_type": 0,
                "modulation_order": "qam_16",
                "num_subcarriers": 38
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 📘 Field Breakdown

| Field                            | Type     | Description                                                           |
| -------------------------------- | -------- | --------------------------------------------------------------------- |
| status                           | string   | Status of the measurement (e.g., SUCCESS)                             |
| pnm\_header                      | object   | Header metadata for the PNM file                                      |
| → file\_type                     | string   | File type identifier (e.g., PNN)                                      |
| → file\_type\_version            | int      | Version of the file type                                              |
| → major\_version                 | int      | Major version of the format                                           |
| → minor\_version                 | int      | Minor version of the format                                           |
| → capture\_time                  | int      | Timestamp when the data was captured                                  |
| channel\_id                      | int      | OFDM downstream channel ID                                            |
| mac\_address                     | string   | MAC address of the cable modem                                        |
| num\_profiles                    | int      | Number of profiles present                                            |
| zero\_frequency                  | int (Hz) | Frequency of subcarrier index 0                                       |
| first\_active\_subcarrier\_index | int      | First active subcarrier in the OFDM profile                           |
| subcarrier\_spacing              | int (Hz) | Spacing between subcarriers in Hz (e.g., 50 kHz)                      |
| profile\_data\_length\_bytes     | int      | Length in bytes of the encoded profile data                           |
| profiles                         | array    | List of profile entries                                               |
| → profile\_id                    | int      | Profile identifier (e.g., 0, 4)                                       |
| → schemes                        | array    | List of modulation schemes per profile                                |
| →→ schema\_type                  | int      | Internal type ID (typically 0; may be reserved for future extensions) |
| →→ modulation\_order             | string   | Modulation type (e.g., qam\_16, qam\_4096)                            |
| →→ num\_subcarriers              | int      | Number of subcarriers using this modulation scheme                    |

## Get Analysis

### 🛁 Endpoint

**POST** `/docs/pnm/ds/ofdm/modulationProfile/getAnalysis`

Performs analysis of the downstream OFDM modulation profile for DOCSIS 3.1, calculating per-subcarrier modulation and Shannon capacity estimates. Supports JSON or XLSX output for easy visualization and processing.

### 📅 Request Body (JSON)

```json
{
  "cable_modem": {
	"mac_address": "aa:bb:cc:dd:ee:ff",
	"ip_address": "192.168.0.100",
  "snmp": {
    "snmpV2C": { "community": "private" },
    "snmpV3": {
      "username": "string",
      "securityLevel": "noAuthNoPriv",
      "authProtocol": "MD5",
      "authPassword": "string",
      "privProtocol": "DES",
      "privPassword": "string"
    }
  },
  "analysis": { "type": 0 },
  "output": { "type": 0 }
}
```

### 📤 JSON Response (Output Type 0)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "data": {
    "analysis": [
      {
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 10,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751821207
        },
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "channel_id": 197,
        "frequency_unit": "Hz",
        "shannon_limit_unit": "dB",
        "profiles": [
          {
            "profile_id": 4,
            "carrier_values": {
              "frequency": [1225000000],
              "modulation": ["qam_4096"],
              "shannon_limit": [36.12]
            }
          }
        ]
      }
    ]
  }
}
```

### 📊 XLSX Output (Output Type 2)

When `output.type` is set to 2, the response is an Excel file with columns:

* Frequency (Hz)
* Modulation Order (e.g., QAM-256)
* Shannon Limit (dB)
* Profile ID

Useful for data visualization, graphing, and statistical modeling.

## Analysis and Output Types

### `analysis.type`

| Value | Type  | Description                                                                                |
| ----- | ----- | ------------------------------------------------------------------------------------------ |
| `0`   | BASIC | Performs static profile decoding and Shannon performance estimation per subcarrier profile |

### `output.type`

| Value | Format | Description                                                               |
| ----- | ------ | ------------------------------------------------------------------------- |
| `0`   | JSON   | Standard structured JSON suitable for API responses and dashboards        |
| `1`   | CSV    | Not supported                                                             |
| `2`   | XLSX   | Excel-compatible output for offline review, reporting, or spreadsheet use |

## Differences Between Measurement and Analysis

| Feature               | `/getMeasurement`                        | `/getAnalysis`                                           |
| --------------------- | ---------------------------------------- | -------------------------------------------------------- |
| Primary Output        | Raw modulation profile and scheme data   | Per-subcarrier frequency, modulation, Shannon capacity   |
| Channel Coverage      | Captures all OFDM profiles               | Breaks down per-profile subcarrier-level detail          |
| Output Format Options | JSON only                                | JSON or XLSX                                             |
| Analysis Mode         | Not applicable                           | Supports `BASIC` (additional types planned)              |
| Best Use Case         | Profile decoding and metadata inspection | Visualization, modeling, advanced modulation diagnostics |
