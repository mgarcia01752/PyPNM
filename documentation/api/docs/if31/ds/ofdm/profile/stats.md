### 📄 `ofdm_profile_stats.md`

````markdown
# POST /docs/if31/ds/ofdm/profile/stats

Retrieves DOCSIS 3.1 OFDM downstream profile statistics for a given cable modem using its MAC and IP address.

## 🔍 Purpose

This endpoint provides detailed statistics per OFDM downstream profile per channel, including codeword counts, CRC failures, and frame-level metrics. It is useful for analyzing CM performance and diagnosing profile-related issues in the downstream OFDM path.

---

## 📥 Request

### Headers
- `Content-Type: application/json`

### Body

```json
{
  "mac_address": "A0:B1:C2:D3:E4:F5",
  "ip_address": "192.168.100.1"
}
````

| Field        | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| mac\_address | string | MAC address of the cable modem |
| ip\_address  | string | IP address of the cable modem  |

---

## 📤 Response

### Success Response

```json
{
  "status": "0",
  "data": [
    {
      "index": 48,
      "channel_id": 3,
      "profiles": {
        "1": {
          "docsIf31CmDsOfdmProfileStatsConfigChangeCt": 0,
          "docsIf31CmDsOfdmProfileStatsTotalCodewords": 13456789,
          "docsIf31CmDsOfdmProfileStatsCorrectedCodewords": 12,
          "docsIf31CmDsOfdmProfileStatsUncorrectableCodewords": 3,
          "docsIf31CmDsOfdmProfileStatsInOctets": 56781234,
          "docsIf31CmDsOfdmProfileStatsInUnicastOctets": 45231234,
          "docsIf31CmDsOfdmProfileStatsInMulticastOctets": 11550000,
          "docsIf31CmDsOfdmProfileStatsInFrames": 67890,
          "docsIf31CmDsOfdmProfileStatsInUnicastFrames": 60000,
          "docsIf31CmDsOfdmProfileStatsInMulticastFrames": 7890,
          "docsIf31CmDsOfdmProfileStatsInFrameCrcFailures": 2,
          "docsIf31CmDsOfdmProfileStatsCtrDiscontinuityTime": 0
        },
        ...
      }
    },
    ...
  ]
}
```

| Field       | Type    | Description                                |
| ----------- | ------- | ------------------------------------------ |
| status      | string  | `"0"` indicates success                    |
| data        | list    | List of OFDM channel statistics            |
| index       | integer | OFDM channel SNMP index                    |
| channel\_id | integer | CM-reported OFDM channel ID                |
| profiles    | dict    | Mapping of profile ID → profile statistics |

---

## ❗ Errors

* `status: "1"` – Invalid MAC/IP or SNMP failure
* `status: "2"` – CM not reachable or no OFDM profiles available
* `status: "3"` – Internal server error

---

## 🛠️ Backend Class Reference

* `DocsIf31CmDsOfdmProfileStatsEntry`
* SNMP OIDs from `docsIf31CmDsOfdmProfileStats*` and `docsIf31CmDsOfdmChanChannelId`
* Uses `CableModem.getDocsIf31CmDsOfdmProfileStatsEntry()`

---

## ✅ Example Use Case

```bash
curl -X POST http://localhost:8000/docs/if31/ds/ofdm/profile/stats \
     -H "Content-Type: application/json" \
     -d '{"mac_address": "A0:B1:C2:D3:E4:F5", "ip_address": "192.168.100.1"}'
```

