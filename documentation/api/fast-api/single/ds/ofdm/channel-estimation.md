# PNM Operations – Downstream OFDM Channel Estimation

This API provides critical visibility into the downstream physical layer of DOCSIS 3.1 OFDM channels by retrieving and analyzing channel estimation coefficients. These complex values—captured per subcarrier—represent the modem's internal estimation of the channel response, allowing operators to assess signal fidelity, detect multipath, and quantify in-channel distortion.

The `/getMeasurement` endpoint returns raw complex coefficients (real/imaginary pairs), while the `/getAnalysis` endpoint derives key physical characteristics including:

* **Magnitude response** (signal attenuation across frequency)
* **Group delay** (timing variation due to multipath)
* **Per-subcarrier complex response**
* **Echo detection** (early/late reflection signatures using phase slope or time-domain analysis)

Echo detection is particularly important in identifying micro-reflections and impedance mismatches in the coaxial plant, which often lead to burst errors, degraded MER, and overall link instability.

Engineers can use this data for detailed spectral diagnostics, plant maintenance planning, and troubleshooting elusive performance issues. The structured output also includes summary signal statistics and supports export to JSON or Excel for visualization and offline analysis.

## 📚 Table of Contents

* [Get Measurement](#get-measurement)
* [Get Analysis](#get-analysis)
* [Get Measurement Statistics](#get-measurement-statistics)
* [Analysis and Output Types](#analysis-and-output-types)
* [Measurement Status Codes](#measurement-status-codes)

## Measurement Status Codes

| Code | Meaning                    | Context                                                            |
| ---- | -------------------------- | ------------------------------------------------------------------ |
| 0    | SUCCESS                    | Measurement completed and results are valid                        |
| 1    | CAPTURE FILE MISSING       | SNMP points to a missing or unavailable binary data file           |
| 2    | PARTIAL DATA               | Measurement file present, but content is truncated or incomplete   |
| 3    | INVALID FORMAT             | Measurement file is unreadable or has invalid structure            |
| 4    | UNSUPPORTED MODEM RESPONSE | Modem responded with unexpected or unhandled data layout           |
| 5    | TIMEOUT                    | SNMP timeout or capture request did not complete within time limit |
| 6    | NOT IMPLEMENTED            | Capture or parsing functionality not supported on current platform |

## Get Measurement

### 🚱 Endpoint

**POST** `/docs/pnm/ds/ofdm/channelEstCoeff/getMeasurement`

Retrieves complex channel estimation coefficients from a DOCSIS 3.1 cable modem for a downstream OFDM channel. These values are used to assess multipath and in-channel distortion.

### 📒 Request Body (JSON)

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

### 📤 JSON Response

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
          "file_type_version": 2,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751835648
        },
        "channel_id": 197,
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "zero_frequency": 1217600000,
        "first_active_subcarrier_index": 148,
        "subcarrier_spacing": 50000,
        "coefficient_data_length": 15200,
        "number_of_coefficients": 3800,
        "occupied_channel_bandwidth": 190000000,
        "value_units": "[Real(I),Imaginary(Q)]",
        "values": [[...]]
      }
    ]
  }
}
```

### 📘️ Response Field Breakdown

| Field                           | Type     | Description                                                      |
| ------------------------------- | -------- | ---------------------------------------------------------------- |
| `pnm_header`                    | object   | Metadata from the capture file                                   |
| `channel_id`                    | int      | Downstream OFDM channel ID                                       |
| `mac_address`                   | string   | MAC address of the modem                                         |
| `zero_frequency`                | int (Hz) | Subcarrier index 0 reference frequency                           |
| `first_active_subcarrier_index` | int      | First usable subcarrier index                                    |
| `subcarrier_spacing`            | int (Hz) | Frequency spacing between subcarriers (typically 50 kHz)         |
| `coefficient_data_length`       | int      | Raw data size in bytes                                           |
| `number_of_coefficients`        | int      | Number of complex coefficients                                   |
| `occupied_channel_bandwidth`    | int (Hz) | Width of the active OFDM channel                                 |
| `value_units`                   | string   | Format of the data, e.g. `[Real, Imaginary]`                     |
| `values`                        | list     | List of complex coefficients (length = number\_of\_coefficients) |

## Get Analysis

### 🚱 Endpoint

**POST** `/docs/pnm/ds/ofdm/channelEstCoeff/getAnalysis`

Performs structured analysis of the channel estimation coefficients, including magnitude, group delay, and complex tap data per subcarrier. Includes signal quality statistics such as skewness, variance, and power.

️ Due to response size, use tools like Postman or cURL instead of Swagger UI.

### 📒 Request Body (JSON)

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

### 📤 JSON Response

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "data": {
    "analysis": [
      {
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 2,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751835918
        },
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "channel_id": 197,
        "frequency_unit": "Hz",
        "magnitude_unit": "dB",
        "group_delay_unit": "microsecond",
        "complex_unit": "[Real, Imaginary]",
        "carrier_values": {
          "occupied_channel_bandwidth": 190000000,
          "carrier_count": 3800,
          "frequency": [],
          "magnitude": [],
          "group_delay": [],
          "complex": [],
          "complex_dimension": "2"
        },
        "signal_statistics_target": "magnitude",
        "signal_statistics": {
          "mean": 8.72,
          "median": 10.03,
          "std": 4.64,
          "variance": 21.49,
          "power": 97.55,
          "peak_to_peak": 41.23,
          "mean_abs_deviation": 3.40,
          "skewness": -1.86,
          "kurtosis": 8.07,
          "crest_factor": 2.66,
          "zero_crossing_rate": 0.113,
          "zero_crossings": 430
        }
      }
    ]
  }
}
```

## Get Measurement Statistics

### 🚱 Endpoint

**POST** `/docs/pnm/ds/ofdm/channelEstCoeff/getMeasurementStatistics`

Returns high-level measurement statistics for downstream OFDM Channel Estimation Coefficients.

### 📒 Request Body (JSON)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "ip_address": "172.19.24.23",
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
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Measurement Statistics for OFDM Channel Estimation Coefficients",
  "results": {
    "DS_OFDM_CHAN_EST_COEF": [
      {
        "index": <SNMP_INDEX>,
        "channel_id": <CHANNEL_ID>,
        "entry": {
          "docsPnmCmOfdmChEstCoefTrigEnable": false,
          "docsPnmCmOfdmChEstCoefAmpRipplePkToPk": 1484,
          "docsPnmCmOfdmChEstCoefAmpRippleRms": 379,
          "docsPnmCmOfdmChEstCoefAmpSlope": 1,
          "docsPnmCmOfdmChEstCoefGrpDelayRipplePkToPk": 112741,
          "docsPnmCmOfdmChEstCoefGrpDelayRippleRms": 3164,
          "docsPnmCmOfdmChEstCoefMeasStatus": 4,
          "docsPnmCmOfdmChEstCoefFileName": "ds-chan-est_48_1752333441.bin",
          "docsPnmCmOfdmChEstCoefAmpMean": 4468,
          "docsPnmCmOfdmChEstCoefGrpDelaySlope": 5,
          "docsPnmCmOfdmChEstCoefGrpDelayMean": 1558514
        }
      }
    ]
  }
}
```

## Analysis and Output Types

### `analysis.type`

| Value | Type  | Description                                         |
| ----- | ----- | --------------------------------------------------- |
| `0`   | BASIC | Magnitude, group delay, complex taps per subcarrier |

### `output.type`

| Value | Format | Description                                                                  |
| ----- | ------ | ---------------------------------------------------------------------------- |
| `0`   | JSON   | Structured JSON for dashboards and offline processing                        |
| `1`   | CSV    | Not supported                                                                |
| `2`   | XLSX   | Excel-compatible output for visualization or detailed statistical breakdowns |
