# DOCSIS Base Capability

This API endpoint retrieves the DOCSIS Radio Frequency (RF) specification version supported by a cable modem (CM) or Cable Modem Termination System (CMTS). It is based on the object `docsIf31DocsisBaseCapability` defined in the DOCSIS-IF3-MIB.

## 📁 Background

The legacy DOCSIS-IF-MIB defined in [RFC-4546](https://tools.ietf.org/html/rfc4546) lacks support for OFDM channels introduced in DOCSIS 3.1 and higher. To address this, the DOCSIS 3.1 OSSI Working Group introduced new MIB objects under the `docsIf31MibObjects` subtree.

The object `docsIf31DocsisBaseCapability` reports the DOCSIS RF specification version:

* For **Cable Modems**, it indicates the supported DOCSIS version.
* For **CMTS**, it reflects the highest DOCSIS version the system supports.

This object supersedes `docsIfDocsisBaseCapability` in RFC-4546.

### MIB Object Definition

```text
ClabsDocsisVersion ::= TEXTUAL-CONVENTION
    SYNTAX INTEGER {
        other (0),
        docsis10 (1),
        docsis11 (2),
        docsis20 (3),
        docsis30 (4),
        docsis31 (5),
        docsis40 (6)
    }
```

## 🛰️ Endpoint

**POST** `/docs/if31/docsis/baseCapability`

Retrieves the supported DOCSIS RF version from the cable modem.

### 📟 Request Body

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

### 🔑 Fields

| Field         | Type   | Description                   |
| ------------- | ------ | ----------------------------- |
| `mac_address` | string | Target CM MAC address         |
| `ip_address`  | string | Target CM IP address          |
| `snmp`        | object | SNMPv2c or SNMPv3 credentials |

## 📤 Response

Returns the DOCSIS version supported by the device.

### 📈 Response Schema

| Field                          | Type   | Description                                      |
| ------------------------------ | ------ | ------------------------------------------------ |
| `mac_address`                  | string | Target MAC address                               |
| `status`                       | int    | Status code (0 = success)                        |
| `message`                      | string | Result message                                   |
| `results.docsis_version`       | string | DOCSIS version as enum string (e.g. `DOCSIS_40`) |
| `results.clabs_docsis_version` | int    | Integer value from ClabsDocsisVersion enum       |

### ✅ Example Response

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "DOCSIS Base Capability retrieved successfully.",
  "results": {
    "docsis_version": "DOCSIS_40",
    "clabs_docsis_version": 6
  }
}
```
