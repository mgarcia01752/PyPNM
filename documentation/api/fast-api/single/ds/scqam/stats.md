# DOCSIS 3.0 Downstream SC-QAM Channel Stats API

This API provides diagnostic access to DOCSIS 3.0 downstream SC-QAM channel statistics. It includes essential RF metrics like signal power, RxMER, and codeword error counters. These statistics help identify impairments such as micro-reflections, low MER, or excessive uncorrectables that can degrade customer experience.

Use this endpoint to assess downstream signal health and modulation performance on legacy DOCSIS 3.0 modems.

## 📡 Endpoint

**POST** `/docs/if30/ds/scqam/chan/stats`

Retrieves DOCSIS 3.0 downstream SC-QAM channel configuration and signal quality statistics.

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

### 🔑 Request Fields

| Field       | Data Type | Description                    |
|-------------|-----------|--------------------------------|
| mac_address | string    | MAC address of the cable modem |
| ip_address  | string    | IP address of the cable modem  |
| snmp        | object    | SNMPv2c or SNMPv3 credentials  |

## 📤 Response Body (Array of Objects)

Each object in the response represents one downstream SC-QAM channel.

```json
[
  {
    "index": <SNMP_INDEX>,
    "channel_id": <CHANNEL_ID>,
    "entry": {
      "docsIfDownChannelId": 1,
      "docsIfDownChannelFrequency": 453000000,
      "docsIfDownChannelWidth": 6000000,
      "docsIfDownChannelModulation": 4,
      "docsIfDownChannelInterleave": 5,
      "docsIfDownChannelPower": -0.4,
      "docsIfSigQUnerroreds": 3222055495,
      "docsIfSigQCorrecteds": 48,
      "docsIfSigQUncorrectables": 0,
      "docsIfSigQMicroreflections": 3,
      "docsIfSigQExtUnerroreds": 41876941255,
      "docsIfSigQExtCorrecteds": 48,
      "docsIfSigQExtUncorrectables": 0,
      "docsIf3SignalQualityExtRxMER": 433
    }
  }
]
```

### 📊 Key Response Fields

| Field                                | Data Type | Description                                               |
|-------------------------------------|-----------|-----------------------------------------------------------|
| index                                | integer   | SNMP index of the downstream channel                      |
| channel_id                           | integer   | Logical channel ID                                        |
| entry.docsIfDownChannelFrequency     | integer   | Center frequency in Hz                                    |
| entry.docsIfDownChannelWidth         | integer   | Channel width in Hz                                       |
| entry.docsIfDownChannelModulation    | integer   | Modulation type (e.g., 4 = QAM256)                        |
| entry.docsIfDownChannelPower         | float     | RF power in dBmV                                          |
| entry.docsIfSigQUnerroreds           | integer   | Uncorrected codewords                                     |
| entry.docsIfSigQCorrecteds           | integer   | Corrected codewords                                       |
| entry.docsIfSigQUncorrectables       | integer   | Uncorrectable codewords                                   |
| entry.docsIfSigQMicroreflections     | integer   | Detected micro-reflections (indicative of RF impairments) |
| entry.docsIf3SignalQualityExtRxMER   | integer   | RxMER in tenths of dB (e.g., 433 = 43.3 dB)               |

> ℹ️ Fields align with DOCSIS-IF3-MIB and provide key insight into downstream signal quality.

## 📝 Notes

- Values like `RxMER`, `Uncorrectables`, and `Microreflections` are critical for identifying RF issues.
- `docsIfDownChannelModulation` should be interpreted via QAM type enum (e.g., 4 = QAM256).
- Extended counters (`ExtUnerroreds`, etc.) offer 64-bit insight where supported.

> 📂 For OID mappings and definitions, see `DOCS-IF-MIB` and `DOCS-IF3-MIB`
