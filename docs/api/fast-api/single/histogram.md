# PNM Operations – Downstream Histogram Measurement API

## 📡 Endpoint

**POST** `/docs/pnm/ds/histogram/getMeasurement`

Captures and returns histogram distribution data from a DOCSIS cable modem's downstream channel. Useful for identifying noise distribution, symmetry, and signal stability.

## 📥 Request Body (JSON)

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

### 🔑 Fields

| Field            | Type   | Description                                 |
| ---------------- | ------ | ------------------------------------------- |
| mac\_address     | string | MAC address of the cable modem              |
| ip\_address      | string | IP address of the cable modem               |
| snmp             | object | SNMPv2c or SNMPv3 credentials               |
| sample\_duration | int    | Number of seconds to capture histogram data |

## 📤 Response Body

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": {
    "data": [
      {
        "status": "SUCCESS",
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "symmetry": 2,
        "dwell_count": 1406250000,
        "hit_counts": [0, 0, 0, 2, 5, 20, 50, 134, 512, 1503, 3205, 5980, 11392, 20856, 38901, 55210, 78452, 68800, 47032, 29300, 14502, 6230, 1830, 520, 82, 4, 0, 0]
      }
    ]
  }
}
```

### 📊 Response Fields

| Field           | Type   | Description                                                 |
| --------------- | ------ | ----------------------------------------------------------- |
| mac\_address    | string | MAC of the modem where capture was executed                 |
| status          | int    | 0 = success                                                 |
| message         | string | Optional message or null                                    |
| data            | object | Container for histogram capture results                     |
| ↳ data\[]       | array  | List of histogram samples                                   |
| ↳↳ status       | string | Capture status: SUCCESS, TIMEOUT, or ERROR                  |
| ↳↳ symmetry     | int    | Indicates histogram symmetry (ideal = 0, deviation = noise) |
| ↳↳ dwell\_count | int    | Number of samples collected during capture                  |
| ↳↳ hit\_counts  | int\[] | Array of bin hits (distribution of energy over time)        |

## 📝 Notes

* Histogram captures are valuable for tracking transient noise or interference in DOCSIS downstream.
* The `symmetry` field helps estimate noise floor characteristics.
* Higher `dwell_count` implies better statistical representation of the link.
* Bin sizes and ranges are implementation-defined and fixed per firmware/CM vendor.

> 📂 For decoding logic, see `src/pnm/analysis/histogram_processor.py`
