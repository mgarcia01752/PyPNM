# DOCSIS Device Event Log

Provides Access To A Cable Modem’s Device Event Log For Operational And Troubleshooting Insight (Ranging, T3/T4, Profile Changes, CM-Status).

## Endpoint

**POST** `/docs/dev/eventLog`

## Request

Use the SNMP-only format: [Common → Request](../../../common/request.md)
TFTP parameters are not required.

## Response

This endpoint returns the standard envelope described in [Common → Response](../../../common/response.md) (`mac_address`, `status`, `message`, `data`).

`data.logs` is an array of log entries reported by the device.

### Abbreviated Example (Real Data, Masked MAC)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": {
    "logs": [
      {
        "docsDevEvFirstTime": "2025-10-19T18:39:24",
        "docsDevEvLastTime": "2025-10-19T18:39:24",
        "docsDevEvCounts": 1,
        "docsDevEvLevel": 6,
        "docsDevEvId": 67061601,
        "docsDevEvText": "US profile assignment change.  US Chan ID: 42; Previous Profile: 12; New Profile: 11.;CM-MAC=60:6c:63:xx:xx:xx;CMTS-MAC=00:90:f0:01:00:00;CM-QOS=1.1;CM-VER=4.0;"
      },
      {
        "docsDevEvFirstTime": "2025-10-19T18:40:09",
        "docsDevEvLastTime": "2025-10-19T18:40:09",
        "docsDevEvCounts": 3,
        "docsDevEvLevel": 6,
        "docsDevEvId": 74010100,
        "docsDevEvText": "CM-STATUS message sent.  Event Type Code: 5; Chan ID: 13; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=60:6c:63:xx:xx:xx;CMTS-MAC=00:90:f0:01:00:00;CM-QOS=1.1;CM-VER=4.0;"
      },
      {
        "docsDevEvFirstTime": "2025-10-19T18:41:24",
        "docsDevEvLastTime": "2025-10-19T18:49:14",
        "docsDevEvCounts": 35,
        "docsDevEvLevel": 6,
        "docsDevEvId": 74010100,
        "docsDevEvText": "CM-STATUS message sent.  Event Type Code: 5; Chan ID: 13; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.;CM-MAC=60:6c:63:xx:xx:xx;CMTS-MAC=00:90:f0:01:00:00;CM-QOS=1.1;CM-VER=4.0;"
      },
      { "...": "additional log entries elided" }
    ]
  }
}
```

## Response Field Details

| Field                | Type   | Description                                                                            |
| -------------------- | ------ | -------------------------------------------------------------------------------------- |
| `mac_address`        | string | MAC address of the cable modem returned in the common envelope.                        |
| `status`             | int    | Operation status (`0` = success; non-zero indicates failure).                          |
| `message`            | string | Human-readable status or error message (nullable).                                     |
| `data.logs`          | array  | Array of device log entry objects.                                                     |
| `docsDevEvFirstTime` | string | First occurrence of the event (ISO-8601 timestamp).                                    |
| `docsDevEvLastTime`  | string | Most recent occurrence of the event (ISO-8601 timestamp).                              |
| `docsDevEvCounts`    | int    | Number of times the event has occurred.                                                |
| `docsDevEvLevel`     | int    | Syslog-style severity (`0`=Emergency, `1`=Alert, …, `7`=Debug; lower = more critical). |
| `docsDevEvId`        | int    | Numeric event identifier.                                                              |
| `docsDevEvText`      | string | Human-readable message; often includes CM/CMTS MACs, profiles, versions.               |

## Notes

* Event levels follow syslog conventions: **0 (Emergency)** … **7 (Debug)**.
* Entries are semi-structured; downstream analytics may parse `docsDevEvText` for fields like channel IDs, profiles, and MACs.
* Devices may cap or rotate stored logs; poll and archive if long-term history is required.
