# DOCSIS Event Log API

## Overview

The **DOCSIS Event Log API** provides access to the event log data of DOCSIS cable modems. This API allows users to query for event logs, including timestamps, event levels, counts, and descriptive messages related to the cable modem's operations. It can be used for diagnostic purposes to investigate issues such as ranging failures, timeouts, and other critical system events.

## Endpoint

**POST** `/docs/dev/eventLog`

This endpoint fetches the event log entries from a DOCSIS cable modem, based on the provided MAC address and IP address.

### Request

The request body must contain the following JSON structure:

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
}
```

* **mac\_address** (string): The MAC address of the DOCSIS cable modem.
* **ip\_address** (string): The IP address of the DOCSIS cable modem.

### Response

The response will contain a JSON object with the following structure:

```json
{
  "status": "0",
  "logs": [
    {
      "docsDevEvFirstTime": "1970-01-01T00:02:29",
      "docsDevEvLastTime": "1970-01-01T02:08:20",
      "docsDevEvCounts": 62,
      "docsDevEvLevel": 4,
      "docsDevEvId": 68000403,
      "docsDevEvText": "ToD request sent - No Response received;CM-MAC=00:50:f1:12:dc:c3;CMTS-MAC=00:17:10:93:df:65;CM-QOS=1.1;CM-VER=3.1;"
    }
  ]
}
```

* **status** (string): The status of the request. A value of "0" indicates success.
* **logs** (array of objects): A list of event log entries, each containing the following fields:

  * **docsDevEvFirstTime** (string): Timestamp of when the event first occurred.
  * **docsDevEvLastTime** (string): Timestamp of when the event last occurred.
  * **docsDevEvCounts** (integer): The number of times this event has occurred.
  * **docsDevEvLevel** (integer): The severity level of the event.
  * **docsDevEvId** (integer): The event ID.
  * **docsDevEvText** (string): A descriptive message providing more details about the event.

### Example

**Request Example:**

```json
{
  "mac_address": "00:11:22:33:44:55",
  "ip_address": "192.168.100.1"
}
```

**Response Example:**

```json
{
  "status": "0",
  "logs": [
    {
      "docsDevEvFirstTime": "1970-01-01T00:02:29",
      "docsDevEvLastTime": "1970-01-01T02:08:20",
      "docsDevEvCounts": 62,
      "docsDevEvLevel": 4,
      "docsDevEvId": 68000403,
      "docsDevEvText": "ToD request sent - No Response received;CM-MAC=00:50:f1:12:dc:c3;CMTS-MAC=00:17:10:93:df:65;CM-QOS=1.1;CM-VER=3.1;"
    }
  ]
}
```

## Purpose

The DOCSIS Event Log API serves as a diagnostic tool to query event logs from DOCSIS cable modems. It retrieves event details such as timestamps, severity levels, counts, and messages related to the modem's performance. The API is helpful for investigating network issues or understanding modem behavior.
