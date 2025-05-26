# DOCSIS Downstream Histogram API

This API initiates and retrieves DOCSIS Downstream Histogram measurements from a cable modem. The histogram provides insights into nonlinear channel effects such as amplifier compression and laser clipping.

---

## Endpoint

**POST** `/docs/pnm/ds/histogram/getMeasurement`

### Tags
- `PNM Operations - Downstream Histogram`

---

## Purpose

The downstream histogram provides a measurement of nonlinear effects in the downstream DOCSIS channel, such as:

- **Amplifier Compression**
- **Laser Clipping**: Often characterized by one-sided truncation and a sharp spike in the histogram.

The cable modem (CM) captures a histogram of time-domain samples from the wideband front end of the receiver across the full downstream band. This two-sided histogram represents values from far-negative to far-positive sample amplitudes.

The histogram data includes:
- **Bin Count**: 255 or 256 equally spaced bins (typically from the 8 MSBs of the ADC).
- **Dwell Count (per bin)**: Number of samples observed per bin (typically constant across bins).
- **Hit Count (per bin)**: Number of samples falling into each specific bin.

Each histogram run accumulates samples over time, terminating upon:
- Manual restart
- Timeout
- Histogram disable command
- 32-bit overflow of the dwell counter

---

## Request

### Request Body: `PnmHistogramRequest`

```json
{
  "mac_address": "string",
  "ip_address": "string",
  "sample_duration": "integer"
}
````

### Example

```json
{
  "mac_address": "00:11:22:33:44:55",
  "ip_address": "192.168.100.1",
  "sample_duration": 10
}
```

#### Parameters

| Field            | Type    | Description                                         |
| ---------------- | ------- | --------------------------------------------------- |
| mac\_address     | string  | MAC address of the target cable modem.              |
| ip\_address      | string  | IP address (IPv4/IPv6) of the cable modem.          |
| sample\_duration | integer | Duration (in seconds) for which the histogram runs. |

---

## Response

### Response Body: `PnmHistogramResponse`

Thanks! Based on your provided response snippet, I’ve updated the **Response** section of the markdown to better reflect the real-world structure of the `PnmHistogramResponse`. Here's the revised section of the `.md` file:

---

### ✅ Response Body: `PnmHistogramResponse`

```json
{
  "mac_address": "00:50:f1:12:df:0c",
  "status": 0,
  "message": null,
  "data": {
    "data": [
      {
        "status": "SUCCESS",
        "mac_address": "00:50:F1:12:DF:0C",
        "symmetry": 2,
        "dwell_count": 16777216,
        "hit_counts": [
          0, 0, 0, 0, 0, 0, 0, 0,
          ...
        ]
      }
    ]
  }
}
```

---

### 🔎 Field Descriptions

| Field                | Type             | Description                                                                 |
| -------------------- | ---------------- | --------------------------------------------------------------------------- |
| `mac_address`        | string           | MAC address of the queried cable modem.                                     |
| `status`             | integer          | Status code (typically `0` for success).                                    |
| `message`            | string \| null   | Optional status or error message.                                           |
| `data`               | object           | Result payload.                                                             |
| `data.data`          | list             | List of result objects per histogram run (only one expected normally).      |
| `data[].status`      | string           | Status of the histogram process (`SUCCESS`, `FAILURE`, etc.).               |
| `data[].mac_address` | string           | MAC address reported in the result.                                         |
| `data[].symmetry`    | integer          | Indicates histogram symmetry (e.g., 2 = full-range, symmetric).             |
| `data[].dwell_count` | integer          | Number of samples observed per bin (usually uniform across bins).           |
| `data[].hit_counts`  | list of integers | List of counts per histogram bin (255 or 256 values depending on bin size). |


## Error Responses

### HTTP 500

* **Downstream Histogram SNMP execution failed**
  The modem failed to begin measurement or complete it properly.

* **Measurement retrieval failed: \[error message]**
  Generic failure, including file retrieval or processing issues.

---

## Behavior and Timing Notes

* Histogram typically completes in **30 seconds or less** for a dwell of **10 million samples**.
* Histogram continues accumulating samples until:

  * Disabled manually
  * Timeout occurs
  * Measurement restarted
  * Dwell count overflows (32-bit limit)

---

## Dependencies

* **SNMP Access** to `docsPnmCmDsHist*` MIB entries
* **TFTP Server** for retrieving measurement data files

---

## Logging

* Logs MAC, IP, duration, and internal processing status
* Exceptions are logged with detailed stack traces for troubleshooting

---

## Related Components

* **Router Class**: `DsHistogramRouter`
* **Service Class**: `CmDsHistogramService`
* **Schema Classes**: `PnmHistogramRequest`, `PnmHistogramResponse`

---

## Example Use Case

A CMTS operator notices increased downstream packet loss and distortion. By running this histogram API, they identify a clipped histogram tail — likely caused by laser clipping — and can take corrective action (e.g., adjusting optical power levels or replacing faulty hardware).

---

## Author

* MaxLinear, Inc.
* PyPNM Platform
