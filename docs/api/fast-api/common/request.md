# Common Request

Shared Request Body Patterns For PyPNM Endpoints.

When using Swagger UI, many parameters auto-fill from system settings. See [System Configuration](../../fast-api/pypnm/system/system_config.md).

## PNM Operations With File Retrieval (TFTP)

Use this when the endpoint retrieves a file (for example, an RxMER capture written to a TFTP server).

```json
{
  "cable_modem": {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "ip_address": "192.168.0.100",
    "pnm_parameters": {
      "tftp": {
        "ipv4": "192.168.0.10",
        "ipv6": "2001:db8::10"
      }
    },
    "snmp": {
      "snmpV2C": {
        "community": "private"
      }
    }
  }
}
```

## SNMP-Only Operations (No File Retrieval)

Use this when the endpoint performs SNMP calls only.

```json
{
  "cable_modem": {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "ip_address": "192.168.0.100",
    "snmp": {
      "snmpV2C": {
        "community": "private"
      }
    }
  }
}
```

## Field Summary

### Cable Modem

| Field                     | Type   | Notes                                                                                                                                                    |
| ------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cable_modem.mac_address` | string | Accepts multiple formats; case-insensitive. Examples: `aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff`, `aabb.ccdd.eeff`, `aabbccddeeff`. Normalized internally. |
| `cable_modem.ip_address`  | string | Target CM IPv4 or IPv6 address.                                                                                                                          |

### TFTP (Only For File-Retrieval Endpoints)

| Field                      | Type   | Notes                    |
| -------------------------- | ------ | ------------------------ |
| `pnm_parameters.tftp.ipv4` | string | IPv4 of the TFTP server. |
| `pnm_parameters.tftp.ipv6` | string | IPv6 of the TFTP server. |

### SNMP (Choose One: v2c Or v3)

#### SNMPv2c

| Field                    | Type   | Notes                     |
| ------------------------ | ------ | ------------------------- |
| `snmp.snmpV2C.community` | string | Read/write community key. |

#### SNMPv3

> SNMPv3 must be enabled in [System Configuration](../../fast-api/pypnm/system/system_config.md). (Not implemented yet.)

| Field                       | Type   | Notes                                            |
| --------------------------- | ------ | ------------------------------------------------ |
| `snmp.snmpV3.username`      | string | SNMPv3 username.                                 |
| `snmp.snmpV3.securityLevel` | string | One of `noAuthNoPriv`, `authNoPriv`, `authPriv`. |
| `snmp.snmpV3.authProtocol`  | string | For example `MD5`, `SHA`.                        |
| `snmp.snmpV3.authPassword`  | string | Required if using `auth*`.                       |
| `snmp.snmpV3.privProtocol`  | string | For example `DES`, `AES`.                        |
| `snmp.snmpV3.privPassword`  | string | Required if using `*Priv`.                       |

## Notes

* For **analysis** endpoints, `pnm_parameters` is **top-level** (not nested under `cable_modem`). Example:
  `{ "cable_modem": {...}, "pnm_parameters": {...}, "analysis": {...}, "output": {...} }`.
* Choose **either** SNMPv2c **or** SNMPv3 fields—do not mix both in a single request.
