# Common response

Status lookup: [Status codes](../status/fast-api-status-codes.md)

## Envelope

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": []
}
````

## Fields

| Field         | Type           | Description                                                             |
| ------------- | -------------- | ----------------------------------------------------------------------- |
| `mac_address` | string         | Target CM MAC (any supported format; normalized internally).            |
| `status`      | integer        | Numeric result from `ServiceStatusCode` (see link above).               |
| `message`     | string | null  | Optional human-readable message (null if not set).                      |
| `data`        | object | array | Endpoint-specific payload (may be an object or an array; may be empty). |

## Notes

* `status = 0` indicates success; non-zero values indicate specific conditions/errors.
* Endpoints may return an empty array/object for `data` when no records are available.
* Long-running operations may use separate “start/status/results” endpoints; their bodies still follow this envelope.
