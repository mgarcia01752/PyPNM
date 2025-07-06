# DOCSIS System Description

## 📡 Endpoint

**POST** `/system/sysDescr`

Retrieves basic system identity and firmware metadata from a DOCSIS cable modem using SNMP. This includes hardware revision, vendor, software/bootloader versions, and device model.

## 🗓️ Request Body (JSON)

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "ip_address": "192.168.0.1",
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

## 📤 JSON Response

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "status": 0,
  "message": null,
  "results": {
    "sysDescr": {
      "hw_rev": "0A",
      "vendor": "Hitron Technologies",
      "boot_rev": "2022.01-MXL-v-4.0.350",
      "sw_rev": "8.4.0.0.2b1",
      "model": "CODA60V",
      "is_empty": false
    }
  }
}
```

## 📃 Response Field Details

| Field         | Type    | Description                                  |
| ------------- | ------- | -------------------------------------------- |
| `mac_address` | string  | MAC address of the queried device            |
| `status`      | int     | 0 = success; non-zero indicates failure      |
| `results`     | object  | Contains the parsed sysDescr fields          |
| `hw_rev`      | string  | Hardware revision reported by the device     |
| `vendor`      | string  | Manufacturer name parsed from sysDescr       |
| `boot_rev`    | string  | Bootloader version string                    |
| `sw_rev`      | string  | Software (firmware) version string           |
| `model`       | string  | Model identifier reported by the device      |
| `is_empty`    | boolean | True if parsing failed or response was empty |

## 📒 Notes

* Data is derived from the SNMP `sysDescr` OID (`1.3.6.1.2.1.1.1.0`) and parsed using known vendor patterns.
* Useful for populating device metadata dashboards or validation checks.
* `is_empty = true` typically means the response could not be parsed into structured fields.
