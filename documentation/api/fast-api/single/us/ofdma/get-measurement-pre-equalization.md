# PNM Operations – Upstream OFDMA Pre-Equalization API

## 📡 Endpoint

**POST** `/docs/pnm/us/ofdma/preEqualization/getMeasurement`

Retrieves OFDMA upstream pre-equalization complex coefficients from a DOCSIS 3.1 cable modem for PNM diagnostics.

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
  }
}
```

### 🔑 Fields

| Field        | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| mac\_address | string | MAC address of the cable modem |
| ip\_address  | string | IP address of the cable modem  |
| snmp         | object | SNMPv2c or SNMPv3 credentials  |

## 📤 Response Body (Object)

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
          [1.076416015625, 0.6097412109375],
          [..., ...]
        ]
      },
      {}
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

## 📝 Notes

* This endpoint is part of the proactive diagnostics suite used to assess in-channel echo and group delay distortion.
* Each `values` array contains I/Q (real/imaginary) values per subcarrier.
* Timing information and versioning are provided via the `pnm_header` block.

> 📂 For more details on OFDMA coefficient structure, refer to `CableLabs CM-SP-PNMv3` and internal PNN format decoder specification.
