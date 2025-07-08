# 📊 Interface Statistics

This endpoint retrieves detailed SNMP interface statistics for a DOCSIS cable modem, including both standard and high-capacity counters as defined in `ifEntry` and `ifXEntry`.

## 📡 Endpoint

**POST** `/docs/pnm/interface/stats`

## 📅 Request Body

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

| Field                       | Type   | Description                                                            |
| --------------------------- | ------ | ---------------------------------------------------------------------- |
| `mac_address`               | string | MAC address of the target cable modem (e.g., `aa:bb:cc:dd:ee:ff`)      |
| `ip_address`                | string | IP address used to contact the cable modem (e.g., `192.168.0.100`)     |
| `snmp.snmpV2C.community`    | string | SNMP community string for v2c (if using SNMPv2c)                       |
| `snmp.snmpV3.username`      | string | SNMPv3 username (if using SNMPv3)                                      |
| `snmp.snmpV3.securityLevel` | string | SNMPv3 security level (e.g., `noAuthNoPriv`, `authNoPriv`, `authPriv`) |
| `snmp.snmpV3.authProtocol`  | string | SNMPv3 authentication protocol (e.g., `MD5`, `SHA`)                    |
| `snmp.snmpV3.authPassword`  | string | SNMPv3 authentication password                                         |
| `snmp.snmpV3.privProtocol`  | string | SNMPv3 privacy protocol (e.g., `DES`, `AES`)                           |
| `snmp.snmpV3.privPassword`  | string | SNMPv3 privacy password                                                |

## 📤 Response Body

```json
{
  "docsCableMaclayer": [
    {
      "ifEntry": {
        "ifIndex": 2,
        "ifDescr": "RF MAC Interface",
        "ifType": 127,
        "ifMtu": 1522,
        "ifSpeed": 0,
        "ifPhysAddress": "0x38ad2b12494c",
        "ifAdminStatus": 1,
        "ifOperStatus": 1,
        "ifLastChange": 0,
        "ifInOctets": 171966389,
        "ifInUcastPkts": 551951,
        "ifInNUcastPkts": null,
        "ifInDiscards": 0,
        "ifInErrors": 0,
        "ifInUnknownProtos": 0,
        "ifOutOctets": 292133504,
        "ifOutUcastPkts": 494466,
        "ifOutNUcastPkts": null,
        "ifOutDiscards": 0,
        "ifOutErrors": 0,
        "ifOutQLen": null,
        "ifSpecific": null
      },
      "ifXEntry": {
        "ifName": "cni0",
        "ifInMulticastPkts": 37433,
        "ifInBroadcastPkts": 0,
        "ifOutMulticastPkts": 0,
        "ifOutBroadcastPkts": 895,
        "ifHCInOctets": 171966389,
        "ifHCInUcastPkts": 551951,
        "ifHCInMulticastPkts": 37433,
        "ifHCInBroadcastPkts": 0,
        "ifHCOutOctets": 292133504,
        "ifHCOutUcastPkts": 494466,
        "ifHCOutMulticastPkts": 0,
        "ifHCOutBroadcastPkts": 895,
        "ifLinkUpDownTrapEnable": 1,
        "ifHighSpeed": 0,
        "ifPromiscuousMode": true,
        "ifConnectorPresent": true,
        "ifAlias": "",
        "ifCounterDiscontinuityTime": 0
      }
    }
  ]
}
```

## 📃 Field Descriptions

| Field                                          | Source   | Description                                                       |
| ---------------------------------------------- | -------- | ----------------------------------------------------------------- |
| `ifIndex`                                      | ifEntry  | Unique index for the interface                                    |
| `ifDescr`                                      | ifEntry  | Textual description of the interface                              |
| `ifType`                                       | ifEntry  | Interface type (e.g. 6 = ethernetCsmacd, 127 = docsCableMaclayer) |
| `ifMtu`                                        | ifEntry  | Maximum transmission unit size in bytes                           |
| `ifSpeed`                                      | ifEntry  | Current bandwidth in bits per second                              |
| `ifPhysAddress`                                | ifEntry  | MAC address of the interface                                      |
| `ifAdminStatus`                                | ifEntry  | Admin status: 1 = up, 2 = down, 3 = testing                       |
| `ifOperStatus`                                 | ifEntry  | Operational status: 1 = up, 2 = down, 3 = testing                 |
| `ifLastChange`                                 | ifEntry  | Time since the last operational status change                     |
| `ifInOctets` / `ifOutOctets`                   | ifEntry  | Total bytes received/sent (32-bit)                                |
| `ifInUcastPkts` / `ifOutUcastPkts`             | ifEntry  | Unicast packets received/sent                                     |
| `ifInNUcastPkts` / `ifOutNUcastPkts`           | ifEntry  | Non-unicast (multicast/broadcast) packets                         |
| `ifInDiscards` / `ifOutDiscards`               | ifEntry  | Discarded packets due to resource limits                          |
| `ifInErrors` / `ifOutErrors`                   | ifEntry  | Packets with errors during reception/transmission                 |
| `ifInUnknownProtos`                            | ifEntry  | Received packets with unknown protocol                            |
| `ifOutQLen`                                    | ifEntry  | Length of output packet queue                                     |
| `ifSpecific`                                   | ifEntry  | Reserved for future use                                           |
| `ifName`                                       | ifXEntry | Interface name (system-specific)                                  |
| `ifInMulticastPkts` / `ifOutMulticastPkts`     | ifXEntry | Multicast packets received/sent                                   |
| `ifInBroadcastPkts` / `ifOutBroadcastPkts`     | ifXEntry | Broadcast packets received/sent                                   |
| `ifHCInOctets` / `ifHCOutOctets`               | ifXEntry | High-capacity (64-bit) byte counters                              |
| `ifHCInUcastPkts` / `ifHCOutUcastPkts`         | ifXEntry | High-capacity unicast packet counters                             |
| `ifHCInMulticastPkts` / `ifHCOutMulticastPkts` | ifXEntry | High-capacity multicast packet counters                           |
| `ifHCInBroadcastPkts` / `ifHCOutBroadcastPkts` | ifXEntry | High-capacity broadcast packet counters                           |
| `ifLinkUpDownTrapEnable`                       | ifXEntry | SNMP trap setting for link state change                           |
| `ifHighSpeed`                                  | ifXEntry | Interface speed in Mbps (deprecated in favor of ifSpeed)          |
| `ifPromiscuousMode`                            | ifXEntry | Boolean flag indicating promiscuous mode enabled                  |
| `ifConnectorPresent`                           | ifXEntry | True if physical connector is present                             |
| `ifAlias`                                      | ifXEntry | Administrator-assigned name for the interface                     |
| `ifCounterDiscontinuityTime`                   | ifXEntry | Time of last counter reset/discontinuity                          |

---

## 📆 Notes

* Null fields may indicate unsupported metrics or interface types.
* The `docsCableMaclayer` array may contain multiple entries for multiple interfaces.
* Prefer `HC` (high-capacity) counters for accurate measurement on high-traffic links.
