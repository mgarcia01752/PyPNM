# DOCSIS Device Reset

## 📡 Endpoint

**POST** `/docs/dev/reset`

Initiates a remote reset (reboot) of the specified DOCSIS cable modem via SNMP.


## 📅 Request Body (JSON)

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "ip_address": "192.168.0.1",
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


## 📤 JSON Response

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "status": 0,
  "message": "Reset command sent to cable modem at 192.168.0.1 successfully.",
  "data": null
}
```


## 📘 Response Field Details

| Field         | Type   | Description                                     |
| ------------- | ------ | ----------------------------------------------- |
| `mac_address` | string | MAC address of the targeted cable modem         |
| `status`      | int    | 0 = success, non-zero indicates failure         |
| `message`     | string | Success or error message with IP/MAC detail     |
| `data`        | null   | Reserved for future use or extended diagnostics |


## 📃 Notes

* Make sure the SNMP credentials are valid and the modem is reachable.
* This operation reboots the modem and may temporarily disrupt service.
* Use this for remote troubleshooting, recovery, or provisioning workflows.
