# DOCSIS 3.1 Downstream OFDM Modulation Profile Stats

This API retrieves per-profile statistics from DOCSIS 3.1 downstream OFDM channels, giving operators visibility into how different modulation profiles are used across the spectrum. It includes codeword counts, frame-level metrics, and octet-based traffic counters for each active profile.

Profiles may include any combination of profile IDs 0 through 4, with profile ID `255` always included as the NCP (Next Codeword Pointer).

These metrics are essential for evaluating error correction trends, traffic segmentation, and overall modulation efficiency across a service group.

## 📡 Endpoint

**POST** `/docs/if31/ds/ofdm/profile/stats`

Retrieves statistics per modulation profile for each DOCSIS 3.1 downstream OFDM channel, including total codewords, corrected/uncorrectable counts, frame metrics, and octet statistics. Profiles include both user-assigned IDs (e.g., 0, 4) and profile 255, which represents the NCP (Next Codeword Pointer).

This data is useful for evaluating traffic utilization, identifying profile transitions, and monitoring FEC correction rates per modulation profile.

---

## 📥 Request Body (JSON)

```json
{
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

| Field        | Type   | Description                                 |
| ------------ | ------ | ------------------------------------------- |
| mac\_address | string | MAC address of the cable modem              |
| ip\_address  | string | IP address of the cable modem               |
| snmp         | object | SNMPv2c or SNMPv3 configuration credentials |

---

## 📤 Response Format (Abbreviated Example)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": [
    {
      "index": 48,
      "channel_id": 197,
      "profiles": {
        "0": { "total_codewords": 62095, "corrected": 0, "uncorrectable": 0 },
        "4": { "total_codewords": 17282, "corrected": 3201, "uncorrectable": 0 },
        "255": { "total_codewords": 53535309, "corrected": 0, "uncorrectable": 0 }
      }
    }
  ]
}
```

### 📊 Per-Profile Stats (Each profile: 0–4, 255)

| Field                                                | Type | Description                           |
| ---------------------------------------------------- | ---- | ------------------------------------- |
| `docsIf31CmDsOfdmProfileStatsTotalCodewords`         | int  | Total number of codewords received    |
| `docsIf31CmDsOfdmProfileStatsCorrectedCodewords`     | int  | Codewords corrected via FEC           |
| `docsIf31CmDsOfdmProfileStatsUncorrectableCodewords` | int  | Codewords that could not be corrected |
| `docsIf31CmDsOfdmProfileStatsInOctets`               | int  | Total bytes received for this profile |
| `docsIf31CmDsOfdmProfileStatsInUnicastOctets`        | int  | Bytes from unicast sources            |
| `docsIf31CmDsOfdmProfileStatsInMulticastOctets`      | int  | Bytes from multicast sources          |
| `docsIf31CmDsOfdmProfileStatsInFrames`               | int  | Number of data frames received        |
| `docsIf31CmDsOfdmProfileStatsInUnicastFrames`        | int  | Count of unicast frames               |
| `docsIf31CmDsOfdmProfileStatsInMulticastFrames`      | int  | Count of multicast frames             |
| `docsIf31CmDsOfdmProfileStatsInFrameCrcFailures`     | int  | Number of CRC-failed frames           |
| `docsIf31CmDsOfdmProfileStatsConfigChangeCt`         | int  | Configuration change counter          |
| `docsIf31CmDsOfdmProfileStatsCtrDiscontinuityTime`   | int  | Counter discontinuity indicator       |
