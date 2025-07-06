# PNM Operations – Downstream OFDM Modulation Profile Analysis

## 📊 Endpoint

**POST** `/docs/pnm/ds/ofdm/modulationProfile/getAnalysis`

This endpoint performs an analysis on the modulation profile retrieved from a DOCSIS 3.1 downstream OFDM channel. It returns calculated modulation data, per-subcarrier values, and estimated Shannon limits. This basic analysis helps visualize per-subcarrier modulation density and theoretical channel capacity.

> ⚡ Supports optional XLSX output for offline inspection and visualization.

## 📅 Request Body (JSON)

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

| Field         | Type   | Description                           |
| ------------- | ------ | ------------------------------------- |
| mac\_address  | string | MAC address of the cable modem        |
| ip\_address   | string | IP address of the cable modem         |
| snmp          | object | SNMPv2c or SNMPv3 configuration       |
| analysis.type | int    | Analysis type (0 = Basic)             |
| output.type   | int    | 0 = JSON <br>1 = XLSX file |

## 📄 JSON Response Example (Output Type 0)

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
              "frequency": [1225000000, ...],
              "modulation": ["qam_4096", ...],
              "shannon_limit": [36.12, ...]
            }
          }
        ]
      }
    ]
  }
}
```

## 📈 Field Breakdown

| Field              | Type          | Description                                                           |
| ------------------ | ------------- | --------------------------------------------------------------------- |
| mac\_address       | string        | MAC of the modem analyzed                                             |
| channel\_id        | int           | OFDM channel ID used for modulation analysis                          |
| profiles           | array         | List of modulation profiles (per OFDM profile ID)                     |
| └─ profile\_id     | int           | Identifier for the modulation profile                                 |
| └─ carrier\_values | object        | Contains per-subcarrier frequency, modulation, and theoretical limits |
| ├─ frequency       | array\[int]   | Frequency of each subcarrier                                          |
| ├─ modulation      | array\[str]   | Modulation type per subcarrier (e.g., qam\_4096)                      |
| └─ shannon\_limit  | array\[float] | Shannon capacity estimate (in dB)                                     |

## 📆 XLSX Output (Output Type 1)

If `"output.type": 1`, the response will return a downloadable Excel file. This file includes:

* Per-profile subcarrier modulation breakdown
* Shannon limit per subcarrier
* Statistical summaries

Useful for offline analytics, charting, and advanced PNM diagnostics.

> 📊 For advanced visualization or automation, refer to: `src/pnm/analysis/analysis_modulation_profile.py`
