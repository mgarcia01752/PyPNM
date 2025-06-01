# `POST /docs/if30/us/scqam/chan/stats`

## Description

Fetches statistics for the upstream DOCSIS SC-QAM channels, including detailed metrics such as frequency, modulation profile, transmit power, and ranging status.

## Request

### URL

`POST /docs/if30/us/scqam/chan/stats`

### Request Body

```json
{
  "mac_address": "a0:b1:c2:d3:e4:f5",
  "ip_address": "192.168.100.1"
}
````

### Fields

| Field        | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| mac\_address | string | MAC address of the cable modem |
| ip\_address  | string | IP address of the cable modem  |

## Response

### Content-Type

`application/json`

### Response Body

```json
[
  {
    "index": 4,
    "channel_id": 4,
    "entry": {
      "docsIfUpChannelId": 4,
      "docsIfUpChannelFrequency": 29400000,
      "docsIfUpChannelWidth": 6400000,
      "docsIfUpChannelModulationProfile": 0,
      "docsIfUpChannelSlotSize": 4,
      "docsIfUpChannelTxTimingOffset": 9488,
      "docsIfUpChannelRangingBackoffStart": 0,
      "docsIfUpChannelRangingBackoffEnd": 4,
      "docsIfUpChannelTxBackoffStart": 2,
      "docsIfUpChannelTxBackoffEnd": 4,
      "docsIfUpChannelType": 2,
      "docsIfUpChannelCloneFrom": 0,
      "docsIfUpChannelUpdate": false,
      "docsIfUpChannelStatus": 1,
      "docsIfUpChannelPreEqEnable": true,
      "docsIf3CmStatusUsTxPower": 35.8,
      "docsIf3CmStatusUsT3Timeouts": 0,
      "docsIf3CmStatusUsT4Timeouts": 0,
      "docsIf3CmStatusUsRangingAborteds": 0,
      "docsIf3CmStatusUsModulationType": 2,
      "docsIf3CmStatusUsEqData": "0x08011800fffe000000060002fffa0000000a0004ffeafffa0022000affa9fff607f40000ffa900a50000ffd800020010fffefff8fffe000400000002000000000000fffe00020000000000000002000000020000000200020002fffefffefffefffefffe",
      "docsIf3CmStatusUsT3Exceededs": 0,
      "docsIf3CmStatusUsIsMuted": false,
      "docsIf3CmStatusUsRangingStatus": 4
    }
  }
]
```

### Fields

| Field                                 | Type   | Description                                        |
| ------------------------------------- | ------ | -------------------------------------------------- |
| index                                 | int    | SNMP channel index                                 |
| channel\_id                           | int    | `docsIfUpChannelId` value                          |
| entry                                 | object | Contains detailed DOCSIS upstream SC-QAM metrics   |
| ├─ docsIfUpChannelId                  | int    | DOCSIS upstream channel ID                         |
| ├─ docsIfUpChannelFrequency           | int    | Channel frequency in Hz                            |
| ├─ docsIfUpChannelWidth               | int    | Channel width in Hz                                |
| ├─ docsIfUpChannelModulationProfile   | int    | Modulation profile ID (e.g., QAM16, QAM64)         |
| ├─ docsIfUpChannelSlotSize            | int    | Slot size for the channel                          |
| ├─ docsIfUpChannelTxTimingOffset      | int    | Timing offset for transmission                     |
| ├─ docsIfUpChannelRangingBackoffStart | int    | Starting backoff for ranging                       |
| ├─ docsIfUpChannelRangingBackoffEnd   | int    | Ending backoff for ranging                         |
| ├─ docsIfUpChannelTxBackoffStart      | int    | Starting backoff for transmission                  |
| ├─ docsIfUpChannelTxBackoffEnd        | int    | Ending backoff for transmission                    |
| ├─ docsIfUpChannelType                | int    | Channel type (e.g., basic, extended)               |
| ├─ docsIfUpChannelCloneFrom           | int    | Channel clone ID                                   |
| ├─ docsIfUpChannelUpdate              | bool   | Whether the channel configuration has been updated |
| ├─ docsIfUpChannelStatus              | int    | Channel status (e.g., operational, down)           |
| ├─ docsIfUpChannelPreEqEnable         | bool   | Whether pre-equalization is enabled                |
| ├─ docsIf3CmStatusUsTxPower           | float  | Transmit power in dBmV                             |
| ├─ docsIf3CmStatusUsT3Timeouts        | int    | Number of T3 timeouts                              |
| ├─ docsIf3CmStatusUsT4Timeouts        | int    | Number of T4 timeouts                              |
| ├─ docsIf3CmStatusUsRangingAborteds   | int    | Number of aborted ranging attempts                 |
| ├─ docsIf3CmStatusUsModulationType    | int    | Modulation type (e.g., QAM16, QAM64)               |
| ├─ docsIf3CmStatusUsEqData            | string | Equalizer data in hexadecimal format               |
| ├─ docsIf3CmStatusUsT3Exceededs       | int    | Number of T3 exceeded timeouts                     |
| ├─ docsIf3CmStatusUsIsMuted           | bool   | Whether the upstream is muted                      |
| └─ docsIf3CmStatusUsRangingStatus     | int    | Ranging status (e.g., successful, failed)          |
