# PNM Operations – Downstream OFDM Modulation Profile Analysis

## 📡 Endpoint

**POST** `/docs/pnm/ds/ofdm/modulationProfile/getAnalysis`

Performs analysis of the downstream OFDM modulation profile for DOCSIS 3.1, calculating per‑subcarrier modulation and Shannon capacity estimates. Supports JSON or XLSX output for easy visualization and processing.

## 📥 Request Body (JSON)

```json
{
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

### 🔑 Request Fields

| Field           | Type   | Description                                            |
| --------------- | ------ | ------------------------------------------------------ |
| `mac_address`   | string | Cable modem MAC address                                |
| `ip_address`    | string | Cable modem IP address                                 |
| `snmp`          | object | SNMPv2c or SNMPv3 configuration object                 |
| └ `snmpV2C`     | object | SNMPv2c config (requires `community`)                  |
| └ `snmpV3`      | object | SNMPv3 config (username, passwords, protocols, levels) |
| `analysis.type` | int    | Analysis type (0 = basic modulation analysis)          |
| `output.type`   | int    | 0 = JSON <br> 1 = XLSX                   |

## 📤 JSON Response (Output Type 0)

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

## 📊 Response Field Breakdown

| Field                  | Type          | Description                                                            |
| ---------------------- | ------------- | ---------------------------------------------------------------------- |
| `mac_address`          | string        | MAC address of the cable modem                                         |
| `status`               | int           | 0 for success, non-zero for failure                                    |
| `data.analysis[]`      | array         | List of analysis entries (typically one per file/channel)              |
| └ `pnm_header`         | object        | Metadata describing the source/capture info of the PNM file            |
| └└ `file_type`         | string        | Identifier of the file type (e.g., PNN)                                |
| └└ `file_type_version` | int           | File format version                                                    |
| └└ `major_version`     | int           | Major version of the capture format                                    |
| └└ `minor_version`     | int           | Minor version of the capture format                                    |
| └└ `capture_time`      | int           | UNIX timestamp when capture occurred                                   |
| └ `mac_address`        | string        | MAC address of the modem in the capture                                |
| └ `channel_id`         | int           | DOCSIS OFDM downstream channel ID                                      |
| └ `frequency_unit`     | string        | Unit for the carrier frequencies (typically Hz)                        |
| └ `shannon_limit_unit` | string        | Unit for calculated Shannon limit (typically dB)                       |
| └ `profiles[]`         | array         | List of per-profile modulation breakdowns                              |
| └└ `profile_id`        | int           | OFDM profile ID                                                        |
| └└ `carrier_values`    | object        | Detailed values for each subcarrier                                    |
| └└└ `frequency`        | array\[int]   | Subcarrier center frequencies                                          |
| └└└ `modulation`       | array\[str]   | Modulation format (e.g., qam\_256, qam\_4096) for each subcarrier      |
| └└└ `shannon_limit`    | array\[float] | Shannon capacity limit for each subcarrier (based on modulation order) |

## 📦 XLSX Output (Output Type 1)

When `output.type` is set to 1, the response is an Excel file with columns:

* Frequency (Hz)
* Modulation Order (e.g., QAM-256)
* Shannon Limit (dB)
* Profile ID

Useful for data visualization, graphing, and statistical modeling.

## 📝 Notes

* Analysis type 0 performs static profile decoding with theoretical performance estimates.
* Future analysis types may incorporate live BER/SNR overlays or delta-detection.
* See `src/pnm/analysis/analysis_modulation_profile.py` for implementation.
