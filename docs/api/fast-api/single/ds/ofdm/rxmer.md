# PNM Operations – Downstream OFDM RxMER

Deep Visibility Into Downstream OFDM RxMER At The Subcarrier Level.

## Endpoint

`POST /docs/pnm/ds/ofdm/rxMer/getCapture`

## Request

Refer to [Common → Request](../../../common/request.md).
**Deltas (Analysis-only additions):** the request accepts optional `analysis`, `analysis.output`, and `analysis.plot.ui` controls.

Here’s a slightly expanded, tidy version with clearer wording and a couple of helpful notes:

### Delta Table

| JSON path                | Type   | Allowed values / format | Default   | Description                                                                                                                                                                  |
| ------------------------ | ------ | ----------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `analysis.type`          | string | `"basic"`               | `"basic"` | Selects the analysis mode used during capture processing.                                                                                                                    |
| `analysis.output.type`   | string | `"json"`, `"archive"`   | `"json"`  | Output format. **`json`** returns an inline body under `data` (`analysis` and `primative`). **`archive`** returns a downloadable ZIP (CSV exports and Matplotlib PNG plots). |
| `analysis.plot.ui.theme` | string | `"light"`, `"dark"`     | `"dark"`  | Theme hint for plot generation (colors, grid, ticks). Does not affect raw metrics/CSV.                                                                                       |

**Notes**

* When `analysis.output.type = "archive"`, the HTTP response body is the file (no `data` JSON payload).
* The `primative` section is a normalized representation of the raw PNM file with added statistics (e.g., mean, std, kurtosis).

### Example

```json
{
  "cable_modem": {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "ip_address": "192.168.0.100",
    "pnm_parameters": {
      "tftp": {
        "ipv4": "192.168.0.10",
        "ipv6": "2001:db8::10"
      }
    },
    "snmp": {
      "snmpV2C": {
        "community": "private"
      }
    }
  },
  "analysis": {
    "type": "basic",
    "output": {
      "type": "json"
    },
    "plot": {
      "ui": {
        "theme": "dark"
      }
    }
  }
}
```

## Response

Standard envelope with payload under `data`.

### When `output.type = "json"`

```json
    "output": {
      "type": "json"
    },
```

#### Abbreviated Example

```json
{
    "mac_address": "606c63e43684",
    "status": 0,
    "message": null,
    "data": {
        "analysis": [
            {
                "device_details": {
                    "system_description": {
                      "HW_REV": "1.0",
                      "VENDOR": "LANCity",
                      "BOOTR": "NONE",
                      "SW_REV": "1.0.0",
                      "MODEL": "LCPET-3"
                    }
                },
                "mac_address": "60:6c:63:e4:36:84",
                "channel_id": 193,
                "subcarrier_spacing": 50000,
                "first_active_subcarrier_index": 148,
                "subcarrier_zero_frequency": 251600000,
                "carrier_values": {
                    "carrier_status_map": {
                        "exclusion": "0",
                        "clipped": "1",
                        "normal": "2"
                    },
                    "magnitude_unit": "dB",
                    "frequency_unit": "Hz",
                    "carrier_count": 3800,
                    "magnitude": [],
                    "frequency": [],
                    "carrier_status": []
                },
                "regression": {
                    "slope": []
                },
                "modulation_statistics": {
                    "snr_db_values": [],
                    "bits_per_symbol": [],
                    "modulations": [],
                    "snr_db_min": [],
                    "supported_modulation_counts": {
                        "qam_2": 3800,
                        "qam_4": 3800,
                        "qam_8": 3800,
                        "qam_16": 3798,
                        "qam_32": 3787,
                        "qam_64": 3778,
                        "qam_128": 3762,
                        "qam_256": 3469,
                        "qam_512": 2733,
                        "qam_1024": 2362,
                        "qam_2048": 2019,
                        "qam_4096": 1467,
                        "qam_8192": 883,
                        "qam_16384": 60,
                        "qam_32768": 0,
                        "qam_65536": 0
                    }
                }
            }
        ],
        "primative": [
            {
                "status": "SUCCESS",
                "pnm_header": {
                    "file_type": "PNN",
                    "file_type_version": 4,
                    "major_version": 1,
                    "minor_version": 0,
                    "capture_time": 1761238473
                },
                "channel_id": 193,
                "mac_address": "60:6c:63:e4:36:84",
                "subcarrier_zero_frequency": 251600000,
                "first_active_subcarrier_index": 148,
                "subcarrier_spacing": 50000,
                "data_length": 3800,
                "occupied_channel_bandwidth": 190000000,
                "value_units": "dB",
                "values": [],
                "signal_statistics": {
                    "mean": 32.80559210526316,
                    "median": 34.0,
                    "std": 6.398852563006556,
                    "variance": 40.94531412309557,
                    "power": 1117.1521875,
                    "peak_to_peak": 32.0,
                    "mean_abs_deviation": 5.666524757617728,
                    "skewness": -0.25361308425026813,
                    "kurtosis": 1.883937273853999,
                    "crest_factor": 1.3089464730216689,
                    "zero_crossing_rate": 0.0,
                    "zero_crossings": 0
                }
            }
        ]
    }
}
```

### When `output.type = "archive"`

```json
    "output": {
      "type": "archive"
    },
```

The response is a downloadable ZIP file containing:

* CSV export of RxMER per subcarrier.
* Matplotlib PNG plots of RxMER vs. Subcarrier Index.

| DARK                                                                                  | Light                                                                       | Description                                |
| ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ------------------------------------------ |
| [RxMER (Ch 193)](./images/rxmer/dark_1761343516_193_rxmer.png)                        | [RxMER (Ch 193)](./images/rxmer/light_193_rxmer.png)                        | RxMER vs. Subcarrier Index — Channel 193   |
| [Modulation Counts (Ch 193)](./images/rxmer/dark_1761343516_193_modulation_count.png) | [Modulation Counts (Ch 193)](./images/rxmer/light_193_modulation_count.png) | Modulation Counts — Channel 193            |
| [RxMER (Ch 194)](./images/rxmer/dark_1761343516_194_rxmer.png)                        | [RxMER (Ch 194)](./images/rxmer/light_194_rxmer.png)                        | RxMER vs. Subcarrier Index — Channel 194   |
| [Modulation Counts (Ch 194)](./images/rxmer/dark_194_modulation_count.png)            | [Modulation Counts (Ch 194)](./images/rxmer/light_194_modulation_count.png) | Modulation Counts — Channel 194            |
| [RxMER (Ch 195)](./images/rxmer/dark_195_rxmer.png)                                   | [RxMER (Ch 195)](./images/rxmer/light_195_rxmer.png)                        | RxMER vs. Subcarrier Index — Channel 195   |
| [Modulation Counts (Ch 195)](./images/rxmer/dark_195_modulation_count.png)            | [Modulation Counts (Ch 195)](./images/rxmer/light_195_modulation_count.png) | Modulation Counts — Channel 195            |
| [RxMER (Ch 196)](./images/rxmer/dark_196_rxmer.png)                                   | [RxMER (Ch 196)](./images/rxmer/light_196_rxmer.png)                        | RxMER vs. Subcarrier Index — Channel 196   |
| [Modulation Counts (Ch 196)](./images/rxmer/dark_196_modulation_count.png)            | [Modulation Counts (Ch 196)](./images/rxmer/light_196_modulation_count.png) | Modulation Counts — Channel 196            |
| [RxMER (Ch 197)](./images/rxmer/dark_197_rxmer.png)                                   | [RxMER (Ch 197)](./images/rxmer/light_197_rxmer.png)                        | RxMER vs. Subcarrier Index — Channel 197   |
| [Modulation Counts (Ch 197)](./images/rxmer/dark_1761343516_197_modulation_count.png) | [Modulation Counts (Ch 197)](./images/rxmer/light_197_modulation_count.png) | Modulation Counts — Channel 197            |
| [Signal Aggregate](./images/rxmer/dark_1761343516_signal_aggregate.png)               | [Signal Aggregate](./images/rxmer/light_signal_aggregate.png)               | Aggregate Signal Statistics (All Channels) |

### Field Tables

**Payload: `measurement.data[]`**

| Field                         | Type         | Description                                       |
| ----------------------------- | ------------ | ------------------------------------------------- |
| status                        | string       | Result for this capture (e.g., `SUCCESS`).        |
| pnm_header.*                  | object       | PNM file header (type, version, capture time).    |
| channel_id                    | int          | OFDM downstream channel ID.                       |
| mac_address                   | string       | MacAddress of the device.                         |
| zero_frequency                | int (Hz)     | Channel zero frequency.                           |
| first_active_subcarrier_index | int          | Index of first active subcarrier.                 |
| subcarrier_spacing            | int (Hz)     | Subcarrier spacing.                               |
| data_length                   | int          | Number of RxMER samples.                          |
| occupied_channel_bandwidth    | int (Hz)     | Occupied bandwidth.                               |
| value_units                   | string       | Units for `values` (e.g., `dB`).                  |
| values                        | array(float) | RxMER values per subcarrier.                      |
| signal_statistics.*           | object       | Aggregate statistics (mean, std, variance, etc.). |
| supported_modulation_counts.* | object       | Count of subcarriers supporting each QAM order.   |
