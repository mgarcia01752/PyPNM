Here is a `reset_cable_modem.md` markdown file documenting the Cable Modem Reset API:
### 📡 `POST /docs/dev/reset` — Reset Cable Modem

Resets a DOCSIS cable modem by sending a `docsDevResetNow` SNMP command to the target device identified by MAC and IP address.


#### 🔁 Endpoint

```
POST /docs/dev/reset
```


#### 🧾 Request Schema

```json
{
  "mac_address": "aabb.ccdd.eeff",
  "ip_address": "192.168.100.1"
}
```

| Field         | Type   | Description                    |
| ------------- | ------ | ------------------------------ |
| `mac_address` | string | MAC address of the cable modem |
| `ip_address`  | string | IP (IPv4 or IPv6) of the modem |


#### ✅ Success Response

```json
{
  "status": "SUCCESS",
  "message": "Reset command sent to cable modem at 192.168.100.1 successfully."
}
```


#### ❌ Failure Responses

* **SNMP reset failed**

```json
{
  "status": "RESET_NOW_FAILED",
  "message": "Reset command to cable modem at 192.168.100.1 failed."
}
```

* **Internal Server Error**

```json
{
  "detail": "Exception details here..."
}
```


#### 🔐 Notes

* The backend uses SNMP `set` on `docsDevResetNow.0`.
* A failed SNMP transaction results in a `RESET_NOW_FAILED` status.
* An internal error raises HTTP 500 with error details.
