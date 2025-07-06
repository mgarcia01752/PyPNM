# DOCSIS 3.1 System Diplexer API

## 📡 Endpoint

**POST** `/docs/if31/system/diplexer`

This endpoint retrieves the DOCSIS 3.1 diplexer configuration and capability values from a cable modem.

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

## 📤 Response Body

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "results": {
    "diplexer": {
      "diplexer_capability": 28,
      "cfg_band_edge": 204000000,
      "ds_lower_capability": 3,
      "cfg_ds_lower_band_edge": 258000000,
      "ds_upper_capability": 2,
      "cfg_ds_upper_band_edge": 1794000000
    }
  }
}
```

### 📊 Response Fields

| Field                      | Type | Description                                  |
| -------------------------- | ---- | -------------------------------------------- |
| diplexer\_capability       | int  | Upstream/Downstream diplexer capability code |
| cfg\_band\_edge            | int  | Configured upstream band edge frequency (Hz) |
| ds\_lower\_capability      | int  | Downstream lower frequency capability code   |
| cfg\_ds\_lower\_band\_edge | int  | Configured downstream lower band edge (Hz)   |
| ds\_upper\_capability      | int  | Downstream upper frequency capability code   |
| cfg\_ds\_upper\_band\_edge | int  | Configured downstream upper band edge (Hz)   |

## 📝 Notes

* This endpoint is used to extract modem hardware capabilities and software configuration for DOCSIS diplexers.
* Frequencies are provided in Hertz (Hz).
* Capability codes are device-specific and defined in CableLabs specifications.
