# DOCSIS 3.0 Upstream ATDMA Pre-Equalization

Provides Access To DOCSIS 3.0 Upstream SC-QAM (ATDMA) Pre-Equalization Tap Data For Plant Analysis (Reflections, Group Delay, Pre-Echo).

## Endpoint

**POST** `/docs/if30/us/atdma/chan/preEqualization`

## Request

Use the SNMP-only format: [Common → Request](../../../../common/request.md)  
TFTP parameters are not required.

## Response

This endpoint returns the standard envelope described in [Common → Response](../../../../common/response.md) (`mac_address`, `status`, `message`, `data`).

`data` is an **object** keyed by the **SNMP table index** of each upstream channel.  
Each value contains decoded tap configuration and coefficient arrays.

### Abbreviated Example

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "data": {
    "80": {
      "main_tap_location": 8,
      "forward_taps_per_symbol": 1,
      "num_forward_taps": 24,
      "num_reverse_taps": 0,
      "forward_coefficients": [
        { "real": 0, "imag": 4, "magnitude": 4.0, "magnitude_power_dB": 12.04 },
        { "real": 2, "imag": -15425, "magnitude": 15425.0, "magnitude_power_dB": 83.76 },
        { "real": -15426, "imag": 1, "magnitude": 15426.0, "magnitude_power_dB": 83.77 }
        /* ... taps elided ... */
      ],
      "reverse_coefficients": []
    },
    "81": {
      "main_tap_location": 8,
      "forward_taps_per_symbol": 1,
      "num_forward_taps": 24,
      "num_reverse_taps": 0,
      "forward_coefficients": [
        { "real": -15425, "imag": -15425, "magnitude": 21814.24, "magnitude_power_dB": 86.77 },
        { "real": 1, "imag": 3, "magnitude": 3.16, "magnitude_power_dB": 10.0 },
        { "real": 1, "imag": -15425, "magnitude": 15425.0, "magnitude_power_dB": 83.76 }
        /* ... taps elided ... */
      ],
      "reverse_coefficients": []
    }
    /* ... other upstream channel indices elided ... */
  }
}
```

## Container Keys

| Key (top-level under `data`) | Type   | Description                                                       |
| ---------------------------- | ------ | ----------------------------------------------------------------- |
| `"80"`, `"81"`, …            | string | **SNMP table index** for the upstream channel row (OID instance). |

## Channel-Level Fields

| Field                     | Type    | Description                                                 |
| ------------------------- | ------- | ----------------------------------------------------------- |
| `main_tap_location`       | integer | Location of the main tap (typically near the filter center) |
| `forward_taps_per_symbol` | integer | Number of forward taps per symbol                           |
| `num_forward_taps`        | integer | Total forward equalizer taps                                |
| `num_reverse_taps`        | integer | Total reverse equalizer taps (often `0` for ATDMA)          |
| `forward_coefficients`    | array   | Complex tap coefficients applied in forward direction       |
| `reverse_coefficients`    | array   | Complex tap coefficients applied in reverse direction       |

## Coefficient Object Fields

| Field                | Type  | Units | Description                          |
| -------------------- | ----- | ----- | ------------------------------------ |
| `real`               | int   | —     | Real part of the complex coefficient |
| `imag`               | int   | —     | Imaginary part of the coefficient    |
| `magnitude`          | float | —     | Magnitude of the complex tap         |
| `magnitude_power_dB` | float | dB    | Power of the tap in dB               |

## Notes

* Each top-level key under `data` is the DOCSIS **SNMP index** for an upstream SC-QAM (ATDMA) channel.
* Forward taps pre-compensate the channel (handling pre-echo/echo paths); reverse taps are uncommon in ATDMA.
* Use tap shapes and main-tap offset to infer echo path delay and alignment health.
* Tap coefficients are signed integers; convert to floating-point as needed for analysis.
