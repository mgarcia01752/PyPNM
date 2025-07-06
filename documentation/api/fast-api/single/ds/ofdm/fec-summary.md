# PNM Operations – Downstream OFDM FEC Summary API

## 📰 Endpoint

**POST** `/docs/pnm/ds/ofdm/fecSummary/getMeasurement`

Retrieves the Forward Error Correction (FEC) summary data from DOCSIS 3.1 downstream OFDM channels.

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
  "fec_summary_type": 2
}
```

### 🔑 Fields

| Field              | Type   | Description                                                      |
| ------------------ | ------ | ---------------------------------------------------------------- |
| mac\_address       | string | MAC address of the cable modem                                   |
| ip\_address        | string | IP address of the cable modem                                    |
| snmp               | object | SNMPv2c or SNMPv3 credentials                                    |
| fec\_summary\_type | int    | 2 = 10-minute (1 record/sec), <br> 3 = 24-hour summary (1 record/min) |

## 📦 Response Body

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": {
    "data": [
      {
        "status": "SUCCESS",
        "channel_id": 32,
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "summary_type": 2,
        "num_profiles": 3,
        "fec_summary_data": [
          {
            "profile_id": 255,
            "number_of_sets": 600,
            "codeword_entries": [
              {
                "timestamp": 2157931112,
                "total_codewords": 297467904,
                "corrected_codewords": 0,
                "uncorrectable_codewords": 0
              }
            ]
          },
          {
            "profile_id": 0,
            "number_of_sets": 600,
            "codeword_entries": [
              {
                "timestamp": 2157931112,
                "total_codewords": 50331648,
                "corrected_codewords": 0,
                "uncorrectable_codewords": 0
              }
            ]
          },
          {
            "profile_id": 4,
            "number_of_sets": 600,
            "codeword_entries": [
              {
                "timestamp": 2157931112,
                "total_codewords": 0,
                "corrected_codewords": 0,
                "uncorrectable_codewords": 0
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### 📊 Response Fields

| Field                        | Type        | Description                                    |
| ---------------------------- | ----------- | ---------------------------------------------- |
| status                       | int         | 0 = success                                    |
| channel\_id                  | int         | OFDM channel identifier                        |
| summary\_type                | int         | FEC type: 2 = 10-min, 3 = 24-hour              |
| num\_profiles                | int         | Total number of OFDM profiles reported         |
| fec\_summary\_data           | list        | List of FEC summaries for each profile         |
| └→ profile\_id               | int         | Profile identifier (e.g., 0, 1, 255)           |
| └→ number\_of\_sets          | int         | Total number of time samples                   |
| └→ codeword\_entries         | list        | List of codeword stats per time unit           |
| └└→ timestamp                | int (epoch) | Capture time (seconds since epoch)             |
| └└→ total\_codewords         | int         | Total number of received codewords             |
| └└→ corrected\_codewords     | int         | Count of FEC-corrected codewords               |
| └└→ uncorrectable\_codewords | int         | Count of codewords that could not be corrected |

## 📑 Notes

* The number of `codeword_entries` is tied to `fec_summary_type`:

  * Type 2 = 10-minute window (600 sets @ 1/sec)
  * Type 3 = 24-hour window (1440 sets @ 1/min)
* Profile ID `255` typically refers to NCP (Next Codeword Pointer).
* This summary data can be used to monitor FEC performance trends.

> 📂 For implementation, refer to `src/pnm/analysis/ofdm_fec_summary.py`.
