# DOCSIS 4.0 FDD Diplexer Band Edge Capability

This API exposes a cable modem’s supported FDD diplexer band edge frequencies for downstream and upstream signal planning in DOCSIS 4.0 environments.

## 📚 Background

Modern DOCSIS 4.0 FDD (Frequency Division Duplex) cable modems advertise their spectrum capabilities during registration using TLVs. These include the supported upstream and downstream band edge frequencies, critical for determining compatibility with extended spectrum deployments.

These capabilities are reflected in the following SNMP tables:

- `docsFddDiplexerUsUpperBandEdgeCapabilityTable` → TLV 5.84
- `docsFddDiplexerDsLowerBandEdgeCapabilityTable` → TLV 5.82
- `docsFddDiplexerDsUpperBandEdgeCapabilityTable` → TLV 5.83

Each table contains a list of supported frequencies in MHz for the corresponding band edge direction.

## 📡 Endpoint

**POST** `/docs/fdd/diplexer/bandEdgeCapability`

Retrieves all supported upstream and downstream diplexer band edge configurations from the cable modem.

### 🧾 Request Body

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

| Field         | Type   | Description                         |
|---------------|--------|-------------------------------------|
| `mac_address` | string | Target CM MAC address               |
| `ip_address`  | string | Target CM IP address                |
| `snmp`        | object | SNMPv2c or SNMPv3 credentials       |

## 📤 Response

Returns a list of supported band edge triplets (Upstream Upper, Downstream Lower, Downstream Upper) grouped by capability index.

### ✅ Example Response

```json
[
  {
    "index": 1,
    "entry": {
      "docsFddDiplexerUsUpperBandEdgeCapability": 85,
      "docsFddDiplexerDsLowerBandEdgeCapability": 108,
      "docsFddDiplexerDsUpperBandEdgeCapability": 1794
    }
  },
  {
    "index": 2,
    "entry": {
      "docsFddDiplexerUsUpperBandEdgeCapability": 204,
      "docsFddDiplexerDsLowerBandEdgeCapability": 258,
      "docsFddDiplexerDsUpperBandEdgeCapability": 1794
    }
  },
  {
    "index": 3,
    "entry": {
      "docsFddDiplexerUsUpperBandEdgeCapability": 396,
      "docsFddDiplexerDsLowerBandEdgeCapability": 468,
      "docsFddDiplexerDsUpperBandEdgeCapability": 1794
    }
  }
]
```

### 📊 Response Table

| Field Name                                      | Type    | Description                                                         |
|-------------------------------------------------|---------|---------------------------------------------------------------------|
| `index`                                         | integer | Capability set identifier                                           |
| `entry.docsFddDiplexerUsUpperBandEdgeCapability` | integer | Supported upstream upper band edge frequency in MHz                |
| `entry.docsFddDiplexerDsLowerBandEdgeCapability` | integer | Supported downstream lower band edge frequency in MHz              |
| `entry.docsFddDiplexerDsUpperBandEdgeCapability` | integer | Supported downstream upper band edge frequency in MHz              |

### 🧾 Response Summary Table

| Index | Upstream Upper (MHz) | Downstream Lower (MHz) | Downstream Upper (MHz) |
|-------|----------------------|-------------------------|-------------------------|
| 1     | 85                   | 108                     | 1794                   |
| 2     | 204                  | 258                     | 1794                   |
| 3     | 396                  | 468                     | 1794                   |

Each row corresponds to a diplexer configuration set supported by the cable modem.

---

## 🔎 Notes

- Frequencies are in MHz and may include values not currently active, but supported by the CM.
- A `0` value indicates the device does not support extended spectrum for that band.
- This endpoint is useful when planning spectrum compatibility between modems and CMTS FDD profiles.
