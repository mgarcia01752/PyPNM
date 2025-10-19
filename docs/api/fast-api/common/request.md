# Common request

Shared request body patterns used across PyPNM endpoints.

When using Swagger UI, many parameters are auto-filled from the system configuration. See [system configuration](../pypnm/system/index.md).

## PNM operations with file retrieval (TFTP)

Use this form when the endpoint retrieves a file (for example, RxMER capture written to a TFTP server).

```json
{
  "cable_modem": {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "ip_address": "192.168.0.100",
    "pnm_parameters": {
      "tftp": {
        "ipv4": "192.168.0.10",
        "ipv6": "2001:db8::10"
      },
      "snmp": {
        "snmpV2C": {
          "community": "private"
        },
        "snmpV3": {
          "username": "user",
          "securityLevel": "noAuthNoPriv",
          "authProtocol": "MD5",
          "authPassword": "pass",
          "privProtocol": "DES",
          "privPassword": "pass"
        }
      }
    }
  }
}
```

## SNMP-only operations (no file retrieval)

Use this form when the endpoint only performs SNMP calls.

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
        "username": "user",
        "securityLevel": "noAuthNoPriv",
        "authProtocol": "MD5",
        "authPassword": "pass",
        "privProtocol": "DES",
        "privPassword": "pass"
      }
    }
  }
}
```

---

## Field summary

### Cable modem

| Field                     | Type   | Notes                                                                                                                                                    |
| ------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cable_modem.mac_address` | string | Accepts multiple formats; case-insensitive. Examples: `aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff`, `aabb.ccdd.eeff`, `aabbccddeeff`. Normalized internally. |
| `cable_modem.ip_address`  | string | Target CM IPv4 or IPv6 address.                                                                                                                          |

### TFTP (only for file-retrieval endpoints)

| Field                      | Type   | Notes                    |
| -------------------------- | ------ | ------------------------ |
| `pnm_parameters.tftp.ipv4` | string | IPv4 of the TFTP server. |
| `pnm_parameters.tftp.ipv6` | string | IPv6 of the TFTP server. |

### SNMP (choose one: v2c or v3)

#### SNMPv2c

| Field                    | Type   | Notes                   |
| ------------------------ | ------ | ----------------------- |
| `snmp.snmpV2C.community` | string | Community string (v2c). |

#### SNMPv3

| Field                       | Type   | Notes                                            |
| --------------------------- | ------ | ------------------------------------------------ |
| `snmp.snmpV3.username`      | string | SNMPv3 username.                                 |
| `snmp.snmpV3.securityLevel` | string | One of `noAuthNoPriv`, `authNoPriv`, `authPriv`. |
| `snmp.snmpV3.authProtocol`  | string | For example `MD5`, `SHA`.                        |
| `snmp.snmpV3.authPassword`  | string | Required if using `auth*`.                       |
| `snmp.snmpV3.privProtocol`  | string | For example `DES`, `AES`.                        |
| `snmp.snmpV3.privPassword`  | string | Required if using `*Priv`.                       |

