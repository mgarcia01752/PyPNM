# PNM Operations – Downstream OFDM Modulation Profile

## 📊 Endpoint

**POST** `/docs/pnm/ds/ofdm/modulationProfile/getMeasurement`

This endpoint retrieves the modulation profile used in DOCSIS 3.1 OFDM downstream channels. It provides metadata and modulation schemes across available OFDM profiles, including per-subcarrier modulation orders. Note that this is a raw conversion; additional processing is needed to analyze full bit-loading and carrier types.

---

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
  }
}
```

### 🔑 Fields

| Field        | Type   | Description                     |
| ------------ | ------ | ------------------------------- |
| mac\_address | string | MAC address of the cable modem  |
| ip\_address  | string | IP address of the cable modem   |
| snmp         | object | SNMPv2c or SNMPv3 configuration |

## 📤 Response Body

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
| ↳ file\_type                     | string   | File type identifier (e.g., PNN)                                      |
| ↳ file\_type\_version            | int      | Version of the file type                                              |
| ↳ major\_version                 | int      | Major version of the format                                           |
| ↳ minor\_version                 | int      | Minor version of the format                                           |
| ↳ capture\_time                  | int      | Timestamp when the data was captured                                  |
| channel\_id                      | int      | OFDM downstream channel ID                                            |
| mac\_address                     | string   | MAC address of the cable modem                                        |
| num\_profiles                    | int      | Number of profiles present                                            |
| zero\_frequency                  | int (Hz) | Frequency of subcarrier index 0                                       |
| first\_active\_subcarrier\_index | int      | First active subcarrier in the OFDM profile                           |
| subcarrier\_spacing              | int (Hz) | Spacing between subcarriers in Hz (e.g., 50 kHz)                      |
| profile\_data\_length\_bytes     | int      | Length in bytes of the encoded profile data                           |
| profiles                         | array    | List of profile entries                                               |
| ↳ profile\_id                    | int      | Profile identifier (e.g., 0, 4)                                       |
| ↳ schemes                        | array    | List of modulation schemes per profile                                |
| ↳↳ schema\_type                  | int      | Internal type ID (typically 0; may be reserved for future extensions) |
| ↳↳ modulation\_order             | string   | Modulation type (e.g., qam\_16, qam\_4096)                            |
| ↳↳ num\_subcarriers              | int      | Number of subcarriers using this modulation scheme                    |

## 📊 Notes

* This response includes the base profile breakdown, indexed by `profile_id`, with modulation scheme types.
* Each `scheme` indicates how many subcarriers use a specific modulation order.
* Data may require further aggregation to map exact modulation to subcarrier index range.

> 📂 For parsing and visualization, see: `src/pnm/analysis/analysis_modulation_profile.py`
