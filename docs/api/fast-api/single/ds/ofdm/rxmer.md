# PNM Operations – Downstream OFDM RxMER

Deep Visibility Into Downstream OFDM RxMER At The Subcarrier Level.

## Endpoint

`POST /docs/pnm/ds/ofdm/rxMer/getMeasurement`

## Request

Refer to [Common → Request](../../../common/request.md).
**Deltas:** None (uses the standard SNMP request structure).

## Response

Standard envelope with payload under `measurement`.

### Abbreviated Example

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": null,
  "measurement": {
    "data": [
      {
        "status": "SUCCESS",
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 4,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751831578
        },
        "channel_id": 197,
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "zero_frequency": 1217600000,
        "first_active_subcarrier_index": 148,
        "subcarrier_spacing": 50000,
        "data_length": 3800,
        "occupied_channel_bandwidth": 190000000,
        "value_units": "dB",
        "values": [43.5, 44.5, 43.5, 43.5, 44],
        "signal_statistics": {
          "mean": 43.45,
          "median": 43.5,
          "std": 1.2,
          "variance": 1.44,
          "power": 1889.31,
          "peak_to_peak": 7.75,
          "mean_abs_deviation": 0.97,
          "skewness": -0.085,
          "kurtosis": 2.75,
          "crest_factor": 1.08,
          "zero_crossing_rate": 0,
          "zero_crossings": 0
        },
        "supported_modulation_counts": {
          "qam_2": 3800,
          "qam_4": 3800,
          "qam_8": 3800,
          "qam_16": 3800,
          "qam_32": 3800,
          "qam_64": 3800,
          "qam_128": 3800,
          "qam_256": 3800,
          "qam_512": 3800,
          "qam_1024": 3800,
          "qam_2048": 3800,
          "qam_4096": 3800,
          "qam_8192": 3800,
          "qam_16384": 3273
        }
      }
    ]
  }
}
```

### Field Tables


**Payload: `measurement.data[]`**

| Field                         | Type         | Description                                       |
| ----------------------------- | ------------ | ------------------------------------------------- |
| status                        | string       | Result for this capture (e.g., `SUCCESS`).        |
| pnm_header.*                  | object       | PNM file header (type, version, capture time).    |
| channel_id                    | int          | OFDM downstream channel ID.                       |
| mac_address                   | string       | Masked MAC for the capture.                       |
| zero_frequency                | int (Hz)     | Channel zero frequency.                           |
| first_active_subcarrier_index | int          | Index of first active subcarrier.                 |
| subcarrier_spacing            | int (Hz)     | Subcarrier spacing.                               |
| data_length                   | int          | Number of RxMER samples.                          |
| occupied_channel_bandwidth    | int (Hz)     | Occupied bandwidth.                               |
| value_units                   | string       | Units for `values` (e.g., `dB`).                  |
| values                        | array(float) | RxMER values per subcarrier.                      |
| signal_statistics.*           | object       | Aggregate statistics (mean, std, variance, etc.). |
| supported_modulation_counts.* | object       | Count of subcarriers supporting each QAM order.   |

## Endpoint

`POST /docs/pnm/ds/ofdm/rxMer/getMeasurementStatistics`

## Request

Refer to [Common → Request](../../../common/request.md).
**Deltas:** None (uses the standard SNMP request structure).

## Response

Standard envelope with payload under `results`.

### Abbreviated Example

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Measurement Statistics for RxMER",
  "results": {
    "DS_OFDM_RXMER_PER_SUBCAR": [
      {
        "index": 1,
        "channel_id": 160,
        "entry": {
          "docsPnmCmDsOfdmRxMerFileEnable": false,
          "docsPnmCmDsOfdmRxMerPercentile": 2,
          "docsPnmCmDsOfdmRxMerMean": 4474,
          "docsPnmCmDsOfdmRxMerStdDev": 100,
          "docsPnmCmDsOfdmRxMerThrVal": 171,
          "docsPnmCmDsOfdmRxMerThrHighestFreq": 803700000,
          "docsPnmCmDsOfdmRxMerMeasStatus": 4,
          "docsPnmCmDsOfdmRxMerFileName": "ds_ofdm_rxmer_per_subcar_aabbccddeeff_160_1752254123.bin"
        }
      }
    ]
  }
}
```

### Field Tables

**Envelope**

| Field       | Type   | Description                                      |
| ----------- | ------ | ------------------------------------------------ |
| mac_address | string | Masked MAC `aa:bb:cc:dd:ee:ff`.                  |
| status      | int    | Operation status code.                           |
| message     | string | Message describing the results set.              |
| results     | object | Container for SNMP-level measurement statistics. |

**Payload: `results.DS_OFDM_RXMER_PER_SUBCAR[]`**

| Field      | Type   | Description                  |
| ---------- | ------ | ---------------------------- |
| index      | int    | Table index.                 |
| channel_id | int    | OFDM downstream channel ID.  |
| entry.*    | object | SNMP fields for RxMER stats. |

## Endpoint

`POST /docs/pnm/ds/ofdm/rxmer/getAnalysis`

## Request

Refer to [Common → Request](../../../common/request.md).
**Deltas (Analysis Only):**

* `pnm_parameters` is **top-level** (do **not** nest under `cable_modem`).
* `analysis.type` (int) selects the analysis mode.
* `output.type` (int) selects the output format.

### Analysis Type Reference

| Value | Constant             | Description                                                                 |
| ----- | -------------------- | --------------------------------------------------------------------------- |
| 0     | `AnalysisType.BASIC` | Basic RxMER analysis (trend/regression, Shannon limits, modulation counts). |

### Output Type Reference

| Value | Constant           | Description                                             |
| ----- | ------------------ | ------------------------------------------------------- |
| 0     | `FileType.JSON`    | JSON response (payload under `data`).                   |
| 4     | `FileType.ARCHIVE` | ZIP archive (CSV/PNG outputs), no `data` body returned. |

### Abbreviated Example Request Delta

```json
{
  "cable_modem": {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "ip_address": "192.168.0.100"
  },
  "pnm_parameters": {
    "tftp": { "ipv4": "192.168.0.100" },
    "snmp": { "snmpV2C": { "community": "private" } }
  },
  "analysis": { "type": 0 },
  "output": { "type": 0 }
}
```

## Response

Standard envelope with payload under `data` when `output.type = 0`.
When `output.type = 1`, the response is a downloadable archive. See [Common → Response](../../../common/response.md).

### Abbreviated Example (JSON Mode)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
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
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 4,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1760934388
        },
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "channel_id": 197,
        "carrier_values": {
          "frequency": [1217600000, 1217650000],
          "magnitude": [43.5, 44.5],
          "carrier_status": [2, 2]
        },
        "regression": { "slope": [-0.0001, -0.0001] },
        "modulation_statistics": {
          "snr_db_min": [36.0, 36.1],
          "supported_modulation_counts": {
            "qam_256": 3800,
            "qam_4096": 3800
          }
        }
      }
    ]
  }
}
```

### Field Tables

**Envelope**

| Field       | Type              | Description                                                |
| ----------- | ----------------- | ---------------------------------------------------------- |
| mac_address | string            | Masked MAC `aa:bb:cc:dd:ee:ff`.                            |
| status      | int or string     | Operation status (numeric code or string).                 |
| message     | string (nullable) | Human-readable result; may be `null` when not applicable.  |
| data        | object (optional) | Present when `output.type = 0`; contains `analysis` array. |

**Payload (`data.analysis[]`)**

| Field                                               | Type          | Description                                                                           |
| --------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------- |
| device_details.system_description.*                 | object        | Parsed fields from `sysDescr` (e.g., `MODEL`, `SW_REV`, `VENDOR`, `BOOTR`, `HW_REV`). |
| pnm_header.*                                        | object        | PNM header (type, version, capture time).                                             |
| mac_address                                         | string        | Masked MAC for this analysis item.                                                    |
| channel_id                                          | int           | OFDM downstream channel ID.                                                           |
| carrier_values.frequency                            | array (Hz)    | Subcarrier frequencies.                                                               |
| carrier_values.magnitude                            | array (dB)    | RxMER values per subcarrier.                                                          |
| carrier_values.carrier_status                       | array (int)   | Per-carrier status: `0=EXCLUSION`, `1=CLIPPED`, `2=NORMAL`.                           |
| regression.slope                                    | array (float) | Fitted trend across frequency.                                                        |
| modulation_statistics.snr_db_min                    | array (float) | Shannon minimum SNR by subcarrier.                                                    |
| modulation_statistics.supported_modulation_counts.* | object        | Counts by supported QAM order (e.g., `qam_256`, `qam_4096`).                          |
~