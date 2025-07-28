# DOCSIS Device Event Log

## 📡 Endpoint

**POST** `/docs/dev/eventLog`

Fetches the device event log from a DOCSIS modem using SNMP, which may include critical operational events, ranging issues, T3/T4 timeouts, and other system messages.

## 📅 Request Body (JSON)

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

## 📤 JSON Response

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "status": 0,
  "message": null,
  "logs": [
    {
      "docsDevEvFirstTime": "2025-07-02T13:14:20",
      "docsDevEvLastTime": "2025-07-02T13:14:36",
      "docsDevEvCounts": 2,
      "docsDevEvLevel": 5,
      "docsDevEvId": 85010200,
      "docsDevEvText": "TCS Partial Service;CM-MAC=a1:b2:c3:d4:e5:f6;CMTS-MAC=00:90:f0:01:00:00;CM-QOS=1.1;CM-VER=4.0;"
    }
  ]
}
```

## 📘 Response Field Details

| Field                | Type   | Description                                                                 |
| -------------------- | ------ | --------------------------------------------------------------------------- |
| `mac_address`        | string | MAC address of the cable modem                                              |
| `status`             | int    | 0 = success, non-zero indicates failure                                     |
| `logs`               | array  | List of log entries reported by the device                                  |
| `docsDevEvFirstTime` | string | First occurrence of the event (ISO 8601 timestamp)                          |
| `docsDevEvLastTime`  | string | Most recent occurrence of the event (ISO 8601 timestamp)                    |
| `docsDevEvCounts`    | int    | Number of times the event has occurred                                      |
| `docsDevEvLevel`     | int    | Severity level (higher values = more critical; 1 = low, 7 = emergency)      |
| `docsDevEvId`        | int    | Numeric event identifier                                                    |
| `docsDevEvText`      | string | Human-readable message text, typically includes MAC, CMTS, and version info |

## 📝 Notes

* Event levels range from **0 (emergency)** to **7 (debug)** following syslog severity conventions.
* Useful for diagnosing service disruptions, reboot causes, CMTS interactions, and firmware issues.
* The event text is often semi-structured; further parsing may be needed for analytics.
* Some modems may limit the number of stored log entries or rotate them over time.
