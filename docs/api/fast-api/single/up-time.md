# DOCSIS System Uptime

## 📡 Endpoint

**POST** `/system/upTime`

Retrieves the current system uptime of a DOCSIS cable modem using SNMP. Useful for identifying device reboots and system availability.

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

## 🛄 JSON Response

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "status": 0,
  "message": null,
  "results": {
    "uptime": "0:13:11.180000"
  }
}
```

## 📜 Response Field Details

| Field         | Type   | Description                                 |
| ------------- | ------ | ------------------------------------------- |
| `mac_address` | string | MAC address of the queried device           |
| `status`      | int    | 0 = success; non-zero indicates failure     |
| `uptime`      | string | Formatted uptime in `HH:MM:SS.microseconds` |

## 📒 Notes

* SNMP OID used: `1.3.6.1.2.1.1.3.0` (system uptime in hundredths of a second)
* Returned uptime is converted into human-readable format.
* Uptime can be used to detect unexpected reboots or system resets.
