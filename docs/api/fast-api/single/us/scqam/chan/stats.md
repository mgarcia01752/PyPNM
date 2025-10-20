# DOCSIS 3.0 Upstream ATDMA Channel Statistics

Provides Access To DOCSIS 3.0 Upstream SC-QAM (ATDMA) Channel Statistics.

## Endpoint

**POST** `/docs/if30/us/scqam/chan/stats`

## Request

Use the SNMP-only format: [Common → Request](../../../common/request.md)  
TFTP parameters are not required.

## Response

This endpoint returns the standard envelope described in [Common → Response](../../../common/response.md) (`mac_address`, `status`, `message`, `data`).

`data` is an **array** of upstream channels. Each item contains the SNMP table `index`, the upstream `channel_id`, and an `entry` with configuration, status, and (where available) raw pre-EQ data (`docsIf3CmStatusUsEqData`).

### Abbreviated Example

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": [
    {
      "index": 80,
      "channel_id": 1,
      "entry": {
        "docsIfUpChannelId": 1,
        "docsIfUpChannelFrequency": 14600000,
        "docsIfUpChannelWidth": 6400000,
        "docsIfUpChannelModulationProfile": 0,
        "docsIfUpChannelSlotSize": 2,
        "docsIfUpChannelTxTimingOffset": 6436,
        "docsIfUpChannelRangingBackoffStart": 3,
        "docsIfUpChannelRangingBackoffEnd": 8,
        "docsIfUpChannelTxBackoffStart": 2,
        "docsIfUpChannelTxBackoffEnd": 6,
        "docsIfUpChannelType": 2,
        "docsIfUpChannelCloneFrom": 0,
        "docsIfUpChannelUpdate": false,
        "docsIfUpChannelStatus": 1,
        "docsIfUpChannelPreEqEnable": true,
        "docsIf3CmStatusUsTxPower": 49.0,
        "docsIf3CmStatusUsT3Timeouts": 0,
        "docsIf3CmStatusUsT4Timeouts": 0,
        "docsIf3CmStatusUsRangingAborteds": 0,
        "docsIf3CmStatusUsModulationType": 2,
        "docsIf3CmStatusUsEqData": "0x08011800ffff0003...00020001",
        "docsIf3CmStatusUsT3Exceededs": 0,
        "docsIf3CmStatusUsIsMuted": false,
        "docsIf3CmStatusUsRangingStatus": 4
      }
    },
    {
      "index": 81,
      "channel_id": 2,
      "entry": {
        "docsIfUpChannelId": 2,
        "docsIfUpChannelFrequency": 21000000,
        "docsIfUpChannelWidth": 6400000,
        "docsIfUpChannelModulationProfile": 0,
        "docsIfUpChannelSlotSize": 2,
        "docsIfUpChannelTxTimingOffset": 6436,
        "docsIfUpChannelRangingBackoffStart": 3,
        "docsIfUpChannelRangingBackoffEnd": 8,
        "docsIfUpChannelTxBackoffStart": 2,
        "docsIfUpChannelTxBackoffEnd": 6,
        "docsIfUpChannelType": 2,
        "docsIfUpChannelCloneFrom": 0,
        "docsIfUpChannelUpdate": false,
        "docsIfUpChannelStatus": 1,
        "docsIfUpChannelPreEqEnable": true,
        "docsIf3CmStatusUsTxPower": 48.5,
        "docsIf3CmStatusUsT3Timeouts": 0,
        "docsIf3CmStatusUsT4Timeouts": 0,
        "docsIf3CmStatusUsRangingAborteds": 0,
        "docsIf3CmStatusUsModulationType": 2,
        "docsIf3CmStatusUsEqData": "0x08011800ffff0001...0002",
        "docsIf3CmStatusUsT3Exceededs": 0,
        "docsIf3CmStatusUsIsMuted": false,
        "docsIf3CmStatusUsRangingStatus": 4
      }
    }
  ]
}
```

## Channel Fields

| Field        | Type | Description                                                                 |
| ------------ | ---- | --------------------------------------------------------------------------- |
| `index`      | int  | **SNMP table index** (OID instance) for this channel’s row in the CM table. |
| `channel_id` | int  | DOCSIS upstream SC-QAM (ATDMA) logical channel ID.                          |

## Entry Fields

| Field                                | Type   | Units | Description                                             |
| ------------------------------------ | ------ | ----- | ------------------------------------------------------- |
| `docsIfUpChannelId`                  | int    | —     | Upstream channel ID (mirrors logical ID).               |
| `docsIfUpChannelFrequency`           | int    | Hz    | Center frequency.                                       |
| `docsIfUpChannelWidth`               | int    | Hz    | Channel width.                                          |
| `docsIfUpChannelModulationProfile`   | int    | —     | Modulation profile index.                               |
| `docsIfUpChannelSlotSize`            | int    | —     | Slot size (minislot units).                             |
| `docsIfUpChannelTxTimingOffset`      | int    | —     | Transmit timing offset (implementation-specific units). |
| `docsIfUpChannelRangingBackoffStart` | int    | —     | Initial ranging backoff window start.                   |
| `docsIfUpChannelRangingBackoffEnd`   | int    | —     | Initial ranging backoff window end.                     |
| `docsIfUpChannelTxBackoffStart`      | int    | —     | Data/backoff start window.                              |
| `docsIfUpChannelTxBackoffEnd`        | int    | —     | Data/backoff end window.                                |
| `docsIfUpChannelType`                | int    | —     | Channel type enum (e.g., `2` = ATDMA).                  |
| `docsIfUpChannelCloneFrom`           | int    | —     | Clone source channel (if used).                         |
| `docsIfUpChannelUpdate`              | bool   | —     | Indicates a pending/active update.                      |
| `docsIfUpChannelStatus`              | int    | —     | Operational status enum.                                |
| `docsIfUpChannelPreEqEnable`         | bool   | —     | Whether pre-equalization is enabled.                    |
| `docsIf3CmStatusUsTxPower`           | float  | dBmV  | Upstream transmit power.                                |
| `docsIf3CmStatusUsT3Timeouts`        | int    | —     | T3 timeouts counter.                                    |
| `docsIf3CmStatusUsT4Timeouts`        | int    | —     | T4 timeouts counter.                                    |
| `docsIf3CmStatusUsRangingAborteds`   | int    | —     | Aborted ranging attempts.                               |
| `docsIf3CmStatusUsModulationType`    | int    | —     | Modulation type enum.                                   |
| `docsIf3CmStatusUsEqData`            | string | hex   | Raw pre-EQ coefficient payload (hex string).            |
| `docsIf3CmStatusUsT3Exceededs`       | int    | —     | Exceeded T3 attempts.                                   |
| `docsIf3CmStatusUsIsMuted`           | bool   | —     | Whether the upstream transmitter is muted.              |
| `docsIf3CmStatusUsRangingStatus`     | int    | —     | Ranging state enum.                                     |

## Notes

* `docsIf3CmStatusUsEqData` contains the raw equalizer payload; decode to taps (location, magnitude, phase) in analysis workflows.
* Use the combination of `TxPower`, timeout counters, and ranging status to corroborate upstream health with pre-EQ shape.
* Channels are discovered automatically; no channel list is required in the request.
