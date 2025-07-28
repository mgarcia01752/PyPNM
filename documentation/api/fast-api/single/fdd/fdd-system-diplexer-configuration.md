# DOCSIS 4.0 FDD Diplexer Configuration

This API retrieves the currently configured diplexer band edge frequencies on a DOCSIS 4.0 cable modem. These values are advertised during registration and reflect the modem’s operating spectrum.

## 📚 Background

The following SNMP fields correspond to TLVs sent by the CM in the Registration Request:

* **TLV 5.79** → Downstream Lower Band Edge (`docsFddCmFddSystemCfgStateDiplexerDsLowerBandEdgeCfg`)
* **TLV 5.80** → Downstream Upper Band Edge (`docsFddCmFddSystemCfgStateDiplexerDsUpperBandEdgeCfg`)
* **TLV 5.81** → Upstream Upper Band Edge (`docsFddCmFddSystemCfgStateDiplexerUsUpperBandEdgeCfg`)

These fields are read-only and reflect the CM's active configuration.

## 📡 Endpoint

**POST** `/docs/fdd/system/diplexer/configurationr`

Retrieves the configured FDD diplexer band edges in MHz.

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

| Field         | Type   | Description                   |
| ------------- | ------ | ----------------------------- |
| `mac_address` | string | Target CM MAC address         |
| `ip_address`  | string | Target CM IP address          |
| `snmp`        | object | SNMPv2c or SNMPv3 credentials |

## 📤 Response

Returns the configured upstream and downstream band edge frequencies for the cable modem.

```json
{
  "index": 0,
  "entry": {
    "docsFddCmFddSystemCfgStateDiplexerDsLowerBandEdgeCfg": 258,
    "docsFddCmFddSystemCfgStateDiplexerDsUpperBandEdgeCfg": 1794,
    "docsFddCmFddSystemCfgStateDiplexerUsUpperBandEdgeCfg": 204
  }
}
```

### 📊 Response Fields

| Field Name                                             | Type       | Units | Description                              |
| ------------------------------------------------------ | ---------- | ----- | ---------------------------------------- |
| `docsFddCmFddSystemCfgStateDiplexerDsLowerBandEdgeCfg` | Unsigned32 | MHz   | Downstream starting frequency (TLV 5.79) |
| `docsFddCmFddSystemCfgStateDiplexerDsUpperBandEdgeCfg` | Unsigned32 | MHz   | Downstream ending frequency (TLV 5.80)   |
| `docsFddCmFddSystemCfgStateDiplexerUsUpperBandEdgeCfg` | Unsigned32 | MHz   | Upstream ending frequency (TLV 5.81)     |

## 🔎 Notes

* A value of `0` for any band edge indicates the CM is not configured for extended spectrum operation.
* These settings are crucial for verifying CM compatibility with FDD spectrum splits.
