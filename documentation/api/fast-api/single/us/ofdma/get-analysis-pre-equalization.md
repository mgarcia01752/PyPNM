# PNM Operations – Upstream OFDMA Pre-Equalization Analysis API

## 📡 Endpoint

**POST** `/docs/pnm/us/ofdma/preEqualization/getAnalysis`

Returns statistical analysis of decoded upstream OFDMA pre-equalization coefficients for DOCSIS 3.1 cable modems.

## 📥 Request Body (JSON)

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
| analysis.type | int    | Type of analysis to perform (0 = magnitude, 1 = delay) |
| output.type   | int    | Output format (0 = structured, 1 = graph, 2 = overlay) |

## 📤 Response Body – Output Type `0`

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
          "complex": [[-1.95452880859375, -1.0010986328125]]
        }
      }, {}
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

## 📝 Notes

* This endpoint performs full-spectrum statistical analysis on captured OFDMA coefficients.
* Output type 0 is structured and suitable for plotting or CSV export.
* Group delay is computed from the phase slope across adjacent subcarriers.

> 📂 For implementation details, see `src/pnm/analysis/analysis_ofdma.py`.
