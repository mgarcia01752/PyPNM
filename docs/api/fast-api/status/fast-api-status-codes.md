# `ServiceStatusCode` Enum Documentation

This enum defines status codes used by PNM service classes to indicate the result of operations such as SNMP reachability, RxMER capture, and TFTP interactions.

> 📁 **Location**: `api/routes/status_codes/codes.py`

---

## ✅ Success Codes

| Name                | Value | Description                                      |
|---------------------|--------|--------------------------------------------------|
| `SUCCESS`           | `0`    | Operation completed successfully.                |

---

## ❌ General Error Codes

| Name                          | Value | Description                                                  |
|-------------------------------|--------|--------------------------------------------------------------|
| `UNREACHABLE_PING`            | `1`    | The cable modem is not reachable via ICMP ping.             |
| `UNREACHABLE_SNMP`           | `2`    | The cable modem is not reachable via SNMP.                  |
| `NO_PLC_FOUND`               | `3`    | No PLC frequencies were found on the modem.                 |
| `INVALID_PLC`               | `4`    | A requested PLC frequency was invalid.                      |
| `TFTP_INET_MISMATCH`        | `5`    | TFTP server has a mismatched IP version (IPv4 vs IPv6).     |
| `FILE_SET_FAIL`             | `6`    | Failed to configure RxMER filename on the cable modem.      |
| `TEST_ERROR`                | `7`    | A generic error occurred during the RxMER test.             |
| `MEASUREMENT_TIMEOUT`       | `8`    | The measurement process timed out waiting for readiness.    |
| `TFTP_SERVER_PATH_SET_FAIL`| `9`    | Unable to set the TFTP server address or path on the modem. |
| `NOT_REACY_AFTER_FILE_CAPTURE` | `10` | Modem did not enter READY state after RxMER capture.        |

---

## 📊 RxMER Status Code Block

Future RxMER-specific error codes should begin at `100` and follow a structured range up to `199`.

```python
# RXMER STATUS CODE START (100-199)
