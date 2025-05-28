### `docs_if31_ds_ofdm_channel_stats.md`

# Endpoint: DOCSIS 3.1 Downstream OFDM Channel Stats

## URL

`POST /docs/if31/ds/ofdm/channel/stats`

## Description

Fetches downstream OFDM channel configuration and performance data from a DOCSIS 3.1 cable modem using SNMP. This includes subcarrier frequencies, channel indicators, codeword counts, and other PHY-layer statistics per channel index.

## Request Payload

| Field        | Type   | Description                                |
|--------------|--------|--------------------------------------------|
| mac_address  | string | MAC address of the target cable modem      |
| ip_address   | string | IP address of the target cable modem       |

### Example

```json
{
  "mac_address": "aabb.ccdd.eeff",
  "ip_address": "192.168.100.1"
}
````

## Response

Returns a list of downstream OFDM channel entries with statistical and configuration data.

### Example

```json
[
  {
    "index": 48,
    "channel_id": 34,
    "entry": {
      "docsIf31CmDsOfdmChanChanIndicator": 4,
      "docsIf31CmDsOfdmChanSubcarrierZeroFreq": 847100000,
      "docsIf31CmDsOfdmChanFirstActiveSubcarrierNum": 1238,
      "docsIf31CmDsOfdmChanLastActiveSubcarrierNum": 2857,
      "docsIf31CmDsOfdmChanNumActiveSubcarriers": 1583,
      "docsIf31CmDsOfdmChanSubcarrierSpacing": 50,
      "docsIf31CmDsOfdmChanCyclicPrefix": 512,
      "docsIf31CmDsOfdmChanRollOffPeriod": 256,
      "docsIf31CmDsOfdmChanPlcFreq": 954000000,
      "docsIf31CmDsOfdmChanNumPilots": 29,
      "docsIf31CmDsOfdmChanTimeInterleaverDepth": 16,
      "docsIf31CmDsOfdmChanPlcTotalCodewords": 264684790,
      "docsIf31CmDsOfdmChanPlcUnreliableCodewords": 0,
      "docsIf31CmDsOfdmChanNcpTotalFields": 3387947050,
      "docsIf31CmDsOfdmChanNcpFieldCrcFailures": 0
    }
  },
  {
    "index": 49,
    "channel_id": 33,
    "entry": {
      "docsIf31CmDsOfdmChanChanIndicator": 4,
      "docsIf31CmDsOfdmChanSubcarrierZeroFreq": 758600000,
      "docsIf31CmDsOfdmChanFirstActiveSubcarrierNum": 1148,
      "docsIf31CmDsOfdmChanLastActiveSubcarrierNum": 2947,
      "docsIf31CmDsOfdmChanNumActiveSubcarriers": 1761,
      "docsIf31CmDsOfdmChanSubcarrierSpacing": 50,
      "docsIf31CmDsOfdmChanCyclicPrefix": 512,
      "docsIf31CmDsOfdmChanRollOffPeriod": 256,
      "docsIf31CmDsOfdmChanPlcFreq": 861000000,
      "docsIf31CmDsOfdmChanNumPilots": 31,
      "docsIf31CmDsOfdmChanTimeInterleaverDepth": 16,
      "docsIf31CmDsOfdmChanPlcTotalCodewords": 264688869,
      "docsIf31CmDsOfdmChanPlcUnreliableCodewords": 0,
      "docsIf31CmDsOfdmChanNcpTotalFields": 3387999936,
      "docsIf31CmDsOfdmChanNcpFieldCrcFailures": 0
    }
  }
]
```

## Notes

* This endpoint is useful for visualizing OFDM channel characteristics and error metrics for proactive diagnostics.
* Make sure SNMP access is allowed from the server to the specified `ip_address`.

## Status Codes

| Code | Description                         |
| ---- | ----------------------------------- |
| 200  | Successful retrieval                |
| 400  | Invalid payload                     |
| 404  | Cable modem not found/reachable     |
| 500  | Internal server error or SNMP error |

