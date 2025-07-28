# DOCSIS 3.0 Upstream ATDMA Channel Stats API

This endpoint provides detailed telemetry on DOCSIS 3.0 upstream SC-QAM (ATDMA) channels from cable modems. It includes modulation, frequency, bandwidth, timing offsets, transmit power, timeout counters, and equalizer data—critical for evaluating upstream performance and identifying plant impairments.


## 📡 Endpoint

**POST** `/docs/if30/us/scqam/chan/stats`

Retrieves statistics for upstream SC-QAM (ATDMA) channels on a DOCSIS 3.0 cable modem.

## 📥 Request Body (JSON)

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

### 🔑 Fields

| Field        | Type   | Description                    |
|---|---|---|
| mac\_address | string | MAC address of the cable modem |
| ip\_address  | string | IP address of the cable modem  |
| snmp         | object | SNMPv2c or SNMPv3 credentials  |

## 📤 Response Body (Array of Objects)

Each object in the response represents one upstream ATDMA channel.

```json
[
  {
    "index": <SNMP_INDEX>,
    "channel_id": <CHANNEL_ID>,
    "entry": {
      "docsIfUpChannelId": 2,
      "docsIfUpChannelFrequency": 21000000,
      "docsIfUpChannelWidth": 6400000,
      "docsIfUpChannelModulationProfile": 0,
      "docsIfUpChannelSlotSize": 2,
      "docsIfUpChannelTxTimingOffset": 8591,
      "docsIfUpChannelRangingBackoffStart": 3,
      "docsIfUpChannelRangingBackoffEnd": 8,
      "docsIfUpChannelTxBackoffStart": 2,
      "docsIfUpChannelTxBackoffEnd": 6,
      "docsIfUpChannelType": 2,
      "docsIfUpChannelCloneFrom": 0,
      "docsIfUpChannelUpdate": false,
      "docsIfUpChannelStatus": 1,
      "docsIfUpChannelPreEqEnable": true,
      "docsIf3CmStatusUsTxPower": 45.5,
      "docsIf3CmStatusUsT3Timeouts": 1,
      "docsIf3CmStatusUsT4Timeouts": 0,
      "docsIf3CmStatusUsRangingAborteds": 0,
      "docsIf3CmStatusUsModulationType": 2,
      "docsIf3CmStatusUsEqData": "0x...",
      "docsIf3CmStatusUsT3Exceededs": 0,
      "docsIf3CmStatusUsIsMuted": false,
      "docsIf3CmStatusUsRangingStatus": 4
    }
  },
  { }
]
```

### 📊 Key Response Fields

| Field                                  | Type    | Description                             |
| -- | - |  |
| index                                  | integer | SNMP index of the upstream channel      |
| channel\_id                            | integer | Logical channel ID                      |
| entry.docsIfUpChannelFrequency         | integer | Center frequency in Hz                  |
| entry.docsIfUpChannelWidth             | integer | Channel bandwidth in Hz                 |
| entry.docsIfUpChannelTxTimingOffset    | integer | Timing offset                           |
| entry.docsIfUpChannelType              | integer | Channel type (e.g., ATDMA = 2)          |
| entry.docsIf3CmStatusUsTxPower         | float   | Transmit power in dBmV                  |
| entry.docsIf3CmStatusUsT3Timeouts      | integer | Number of T3 timeouts                   |
| entry.docsIf3CmStatusUsT4Timeouts      | integer | Number of T4 timeouts                   |
| entry.docsIf3CmStatusUsRangingAborteds | integer | Count of aborted ranging attempts       |
| entry.docsIf3CmStatusUsEqData          | string  | Hex-encoded upstream equalizer tap data |
| entry.docsIf3CmStatusUsIsMuted         | boolean | Whether the channel is currently muted  |
| entry.docsIf3CmStatusUsRangingStatus   | integer | Current ranging status code             |

> ℹ️ Other fields follow DOCSIS-IF3-MIB conventions.

## 📝 Notes

* The response is an array and may contain multiple upstream ATDMA channels.
* The `docsIf3CmStatusUsEqData` field is a binary string and may be parsed for tap coefficient analysis.
* This endpoint is used for troubleshooting upstream channel performance on DOCSIS 3.0 modems.

> 📂 For OID definitions and structure, refer to: `DOCS-IF-MIB` and `DOCS-IF3-MIB`
