# PNM Operations – Upstream OFDMA Pre-Equalization

## 📛 Table of Contents

* [Get Measurement](#get-measurement)
* [Get Analysis](#get-analysis)
* [Analysis and Output Types](#analysis-and-output-types)


## Get Measurement

### 🛰 Endpoint

**POST** `/docs/pnm/us/ofdma/preEqualization/getMeasurement`

Retrieves OFDMA upstream pre-equalization complex coefficients from a DOCSIS 3.1 cable modem for PNM diagnostics.

### 👥 Request Body (JSON)

```json
{
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

### 🔑 Fields

| Field        | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| mac\_address | string | MAC address of the cable modem |
| ip\_address  | string | IP address of the cable modem  |
| snmp         | object | SNMPv2c or SNMPv3 credentials  |

### 📄 Response Body (Object)

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
          "file_type_version": 6,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751781817
        },
        "upstream_channel_id": 42,
        "cm_mac_address": "aa:bb:cc:dd:ee:ff",
        "cmts_mac_address": "00:90:f0:01:00:00",
        "subcarrier_zero_frequency": 104800000,
        "first_active_subcarrier_index": 74,
        "subcarrier_spacing": 50000,
        "value_length": 7584,
        "value_unit": "[Real, Imaginary]",
        "values": [
          [1.0764, 0.6097],
          [..., ...]
        ]
      }
    ]
  }
}
```

### 📊 Key Response Fields

| Field                              | Type    | Description                                 |
| ---------------------------------- | ------- | ------------------------------------------- |
| mac\_address                       | string  | MAC address used in the request             |
| status                             | integer | 0 = success                                 |
| measurement.data                   | array   | List of measurement entries per capture     |
| ↳ status                           | string  | Capture status (e.g., "SUCCESS")            |
| ↳ upstream\_channel\_id            | integer | Channel ID associated with this capture     |
| ↳ cm\_mac\_address                 | string  | Cable modem MAC address                     |
| ↳ cmts\_mac\_address               | string  | CMTS MAC address                            |
| ↳ subcarrier\_zero\_frequency      | integer | Base frequency (Hz) of subcarrier 0         |
| ↳ first\_active\_subcarrier\_index | integer | Index of first active subcarrier            |
| ↳ subcarrier\_spacing              | integer | Frequency spacing between subcarriers in Hz |
| ↳ value\_length                    | integer | Total number of subcarriers represented     |
| ↳ value\_unit                      | string  | Format of data (e.g., \[Real, Imaginary])   |
| ↳ values                           | array   | List of complex coefficient pairs           |

> ℹ️ Each value represents a decoded complex tap coefficient used for plant characterization.

### 📍 Notes

* This endpoint is part of the proactive diagnostics suite used to assess in-channel echo and group delay distortion.
* Each `values` array contains I/Q (real/imaginary) values per subcarrier.
* Timing information and versioning are provided via the `pnm_header` block.

## Get Analysis

### 🛰 Endpoint

**POST** `/docs/pnm/us/ofdma/preEqualization/getAnalysis`

Returns statistical analysis of decoded upstream OFDMA pre-equalization coefficients for DOCSIS 3.1 cable modems.

### 👥 Request Body (JSON)

```json
{
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
  },
  "analysis": {
    "type": 0
  },
  "output": {
    "type": 0
  }
}
```

### 🔑 Fields

| Field         | Type   | Description                                            |
| ------------- | ------ | ------------------------------------------------------ |
| mac\_address  | string | MAC address of the cable modem                         |
| ip\_address   | string | IP address of the cable modem                          |
| snmp          | object | SNMPv2c or SNMPv3 credentials                          |
| analysis.type | int    | 0 = basic                                              |
| output.type   | int    | 0 = json <br> 2 = xlsx                                 |

### 📄 Response Body – Output Type `0`

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "data": {
    "analysis": [
      {
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 6,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751782748
        },
        "mac_address": null,
        "channel_id": null,
        "frequency_unit": "Hz",
        "magnitude_unit": "dB",
        "group_delay_unit": "microsecond",
        "complex_unit": "[Real, Imaginary]",
        "carrier_values": {
          "carrier_count": 1896,
          "frequency": [...],
          "magnitude": [...],
          "group_delay": [...],
          "complex": [[-1.9545, -1.0011]]
        }
      }
    ]
  }
}
```

### 📊 Response Fields

| Field                | Type        | Description                                  |
| -------------------- | ----------- | -------------------------------------------- |
| mac\_address         | string      | MAC of the target modem                      |
| status               | int         | 0 = success                                  |
| data.analysis        | list        | List of OFDMA analysis entries               |
| ↳ pnm\_header        | object      | Metadata about the measurement file          |
| ↳ frequency\_unit    | string      | Unit for x-axis of frequency array           |
| ↳ magnitude\_unit    | string      | Unit for RxMER/magnitude in dB               |
| ↳ group\_delay\_unit | string      | Unit for group delay values                  |
| ↳ complex\_unit      | string      | Format of the complex coefficients           |
| ↳ carrier\_values    | object      | Actual subcarrier data and computed analysis |
| ↳↳ carrier\_count    | int         | Total number of OFDMA subcarriers            |
| ↳↳ frequency         | float\[]    | Array of subcarrier center frequencies (Hz)  |
| ↳↳ magnitude         | float\[]    | Array of magnitude values in dB              |
| ↳↳ group\_delay      | float\[]    | Group delay per subcarrier (μs)              |
| ↳↳ complex           | float\[]\[] | Complex I/Q tap coefficients per subcarrier  |

### 📍 Notes

* This endpoint performs full-spectrum statistical analysis on captured OFDMA coefficients.
* Output type 0 is structured and suitable for plotting or CSV export.
* Group delay is computed from the phase slope across adjacent subcarriers.

## Analysis and Output Types

### `analysis.type`

| Value | Description                              |
| ----- | ---------------------------------------- |
| `0`   | Basic Magnitude and Group Delay Analysis |

### `output.type`

| Value | Format  | Description                                           |
| ----- | ------- | ----------------------------------------------------- |
| `0`   | JSON    | Structured data for dashboards or raw API consumption |
| `1`   | CSV     | Not Supported   |
| `2`   | XLSX    | (Planned) Taps overlay and echo/impulse view          |
