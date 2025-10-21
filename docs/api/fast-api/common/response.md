# Common Response

Standard Envelope For PyPNM API Responses.

Status Lookup: [Status Codes](../status/fast-api-status-codes.md)

## Envelope

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": []
}
```

> Some endpoints use `"results"` (object or array) instead of `"data"`. The chosen key is documented per-endpoint Guide.

## Fields

| Field              | Type            | Description                                                             |
| ------------------ | --------------- | ----------------------------------------------------------------------- |
| `mac_address`      | string          | Target CM MAC (any supported format; normalized internally).            |
| `status`           | integer         | Numeric result from `ServiceStatusCode` (see Status Codes link above).  |
| `message`          | string or null  | Optional human-readable message (`null` if not set).                    |
| `data` / `results` | object or array | Endpoint-specific payload (may be an object or an array; may be empty). |

## PNM Header

```json
{
  "pnm_header": {
    "file_type": "PNN",
    "file_type_version": 4,
    "major_version": 1,
    "minor_version": 0,
    "capture_time": 1760934388
  }
}
```

### PNM Header Fields

Each PNM file begins with a compact binary header; the API returns the **decoded** header as `pnm_header` inside items that originate from PNM-backed captures/analyses (e.g., RxMER, FEC Summary, Channel Estimation). For multi-capture or multi-channel responses, **each item** includes its own `pnm_header`.

| Field               | Type    | Units   | Description                                       |
| ------------------- | ------- | ------- | --------------------------------------------------|
| `file_type`         | string  | —       | PNM file type identifier (e.g., `"PNN"`, `"LLD"`).|
| `file_type_version` | integer | —       | Numeric version for the given file type (e.g., `4`). See mapping: [`pnm_file_type.py`](https://github.com/mgarcia01752/PyPNM/blob/main/src/pypnm/pnm/process/pnm_file_type.py). |
| `major_version`     | integer | —       | Major schema version of the payload embedded in the PNM file  |
| `minor_version`     | integer | —       | Minor schema version of the payload embedded in the PNM file  |
| `capture_time`      | integer | seconds | Unix epoch time (UTC) when the capture was recorded           |
