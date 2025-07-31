# DOCSIS 3.0 Downstream SC‑QAM Channel Codeword Error Rate API

This endpoint computes per‑channel codeword error statistics for DOCSIS 3.0 downstream SC‑QAM channels. It returns uncorrectable error counts, normalized error rates, and codeword throughput, helping you detect impairment or service‑level issues on legacy cable modems.

## Endpoint

```text
POST /docs/if30/ds/scqam/chan/codewordErrorRate
```

Computes codeword error statistics over a sampling interval.

## Request Body

```json
{
  "cable_modem": {
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
    }
  },
  "sample_time_elapsed": 5.0
}
```

### Request Fields

| Field                | Type    | Description                                             |
| -------------------- | ------- | ------------------------------------------------------- |
| `cable_modem`        | object  | Cable modem connection parameters                       |
| `mac_address`        | string  | MAC address of the cable modem                          |
| `ip_address`         | string  | IP address of the cable modem                           |
| `snmp`               | object  | SNMP credentials (`snmpV2C` or `snmpV3`)                |
| `sample_time_elapsed`| number  | Sampling interval in seconds (default: 5)               |

## Response Body

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Successfully retrieved codeword error rate",
  "results": [
    {
      "index": 52,
      "channel_id": 32,
      "codeword_totals": {
        "total_codewords": 1502550,
        "total_errors": 0,
        "time_elapsed": 5,
        "error_rate": 0.0,
        "codewords_per_second": 300510.0,
        "errors_per_second": 0.0
      }
    }
  ]
}
```

### Key Response Fields

| Field                           | Type    | Description                                               |
| ------------------------------- | ------- | --------------------------------------------------------- |
| `mac_address`                   | string  | MAC address of the cable modem                            |
| `status`                        | integer | 0 = success; non‑zero indicates an error                   |
| `message`                       | string  | Human‑readable status message                             |
| `results`                       | array   | List of per‑channel error rate entries                    |
| `results[] .index`              | integer | SNMP index of the downstream channel                      |
| `results[] .channel_id`         | integer | DOCSIS logical channel ID                                 |
| `results[] .codeword_totals`    | object  | Nested counters and rate metrics                          |
| `codeword_totals.total_codewords` | integer | Total codewords counted over the interval               |
| `codeword_totals.total_errors`  | integer | Number of uncorrectable codeword errors                   |
| `codeword_totals.time_elapsed`  | number  | Sampling interval used (seconds)                          |
| `codeword_totals.error_rate`    | number  | Fraction of uncorrectable errors (errors/codewords)       |
| `codeword_totals.codewords_per_second` | number | Normalized codewords per second (s⁻¹)                |
| `codeword_totals.errors_per_second`    | number | Normalized errors per second (s⁻¹)                   |

> Rates use SI unit s⁻¹; multiply `error_rate` by 100 to get a percentage.

## Notes

- Ensure SNMP counters support 64‑bit to avoid overflow on high‑traffic channels.
- `sample_time_elapsed` defaults to **5 seconds** if omitted; adjust to match your SNMP polling interval.
- This API automatically introspects all downstream SC‑QAM channels—no need to specify channel IDs.
