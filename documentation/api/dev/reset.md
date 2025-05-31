# Reset Cable Modem (REST Equivalent of `docsDevResetNow`)

Resets a DOCSIS cable modem by issuing a reboot command via SNMP. When this endpoint is called, the modem will immediately restart and become temporarily unreachable until the reboot completes. Any failure to send the reset command returns a `RESET_NOW_FAILED` status.

## 🔁 Endpoint

```
POST /docs/dev/reset
```

## 🧾 Request Schema

```json
{
  "mac_address": "aabb.ccdd.eeff",
  "ip_address": "192.168.100.1"
}
```

| Field         | Type   | Description                                                    |
| ------------- | ------ | -------------------------------------------------------------- |
| `mac_address` | string | MAC address of the target cable modem (e.g., `aabb.ccdd.eeff`) |
| `ip_address`  | string | IP address of the cable modem (IPv4 or IPv6)                   |

## ✅ Success Response

HTTP 200 OK

```json
{
  "status": "SUCCESS",
  "message": "Reset command sent to cable modem at 192.168.100.1 successfully."
}
```

| Field     | Type   | Description                                          |
| --------- | ------ | ---------------------------------------------------- |
| `status`  | string | Always `"SUCCESS"` on a successful reset command.    |
| `message` | string | Human‐readable confirmation, includes the target IP. |


## ❌ Failure Responses

### 1. SNMP Reset Failed

Returned when the SNMP `docsDevResetNow.0` set operation does not succeed (e.g., no SNMP response, authentication failure).

HTTP 200 OK

```json
{
  "status": "RESET_NOW_FAILED",
  "message": "Reset command to cable modem at 192.168.100.1 failed."
}
```

| Field     | Type   | Description                                      |
| --------- | ------ | ------------------------------------------------ |
| `status`  | string | Always `"RESET_NOW_FAILED"` if SNMP set fails.   |
| `message` | string | Human‐readable error message with the target IP. |

### 2. Internal Server Error (HTTP 500)

Returned when an unexpected exception occurs during processing.

HTTP 500 Internal Server Error

```json
{
  "detail": "Exception details here..."
}
```

| Field    | Type   | Description                                                  |
| -------- | ------ | ------------------------------------------------------------ |
| `detail` | string | Description of the internal error (can include stack trace). |


## 🔐 Notes

* The backend issues an SNMP **SET** operation on the object `docsDevResetNow.0`.
* If the SNMP set does not return a success response, the endpoint returns status `RESET_NOW_FAILED`.
* For any unhandled exception (e.g., network error, code bug), the endpoint responds with HTTP 500 and includes the exception details in the `detail` field.
* Ensure the SNMP write community (or SNMPv3 credentials) is correctly configured on the cable modem, and that the device is reachable on the network before invoking this endpoint.
* After issuing a reset, the cable modem will reboot and be temporarily unreachable. Subsequent operations (e.g., SNMP gets) should wait until the device finishes rebooting.

---

© 2025 Maurice Garcia (MIT License)
