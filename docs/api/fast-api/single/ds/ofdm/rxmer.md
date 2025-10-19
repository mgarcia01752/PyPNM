# PNM Operations – Downstream OFDM RxMER

This API provides deep visibility into the signal quality of DOCSIS 3.1+ downstream OFDM channels by retrieving and analyzing Receive Modulation Error Ratio (RxMER) at the subcarrier level.

RxMER is one of the most powerful indicators of downstream plant health — capable of revealing narrowband interference, micro-reflections, and other impairments that traditional metrics cannot.

The `/getMeasurement` endpoint captures real-time RxMER data from a cable modem, while `/getAnalysis` transforms this into frequency-aligned, statistically rich datasets for visualization and decision-making.

## Table of Contents

* [Get Measurement](#get-measurement)
* [Get Measurement Statistics](#get-measurement-statistics)
* [Get Analysis](#get-analysis)
* [Analysis Type Reference](#analysis-type-reference)
* [Output Type Reference](#output-type-reference)
* [Returned File Types](#returned-file-types)
* [Example Output Gallery](#example-output-gallery)
* [Differences Between Measurement and Analysis](#differences-between-measurement-and-analysis)

## Get Measurement

### Endpoint

**POST** `/docs/pnm/ds/ofdm/rxMer/getMeasurement`

Retrieves subcarrier-level RxMER (Receive Modulation Error Ratio) measurements from a DOCSIS 3.1+ cable modem.
This data provides a high-resolution frequency-domain snapshot of downstream OFDM performance.

### Request Body

| Field                       | Type   | Description                                                      |
| --------------------------- | ------ | ---------------------------------------------------------------- |
| `cable_modem.mac_address`   | string | MAC address of the cable modem                                   |
| `cable_modem.ip_address`    | string | IPv4 or IPv6 address of the cable modem                          |
| `snmp.snmpV2C.community`    | string | SNMPv2c community string                                         |
| `snmp.snmpV3.username`      | string | SNMPv3 username                                                  |
| `snmp.snmpV3.securityLevel` | string | SNMPv3 security level (`noAuthNoPriv`, `authNoPriv`, `authPriv`) |
| `snmp.snmpV3.authProtocol`  | string | SNMPv3 authentication protocol (`MD5`, `SHA`)                    |
| `snmp.snmpV3.authPassword`  | string | SNMPv3 authentication password                                   |
| `snmp.snmpV3.privProtocol`  | string | SNMPv3 privacy protocol (`DES`, `AES`)                           |
| `snmp.snmpV3.privPassword`  | string | SNMPv3 privacy password                                          |

**Example JSON Request**

```json
{
  "cable_modem": {
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "ip_address": "192.168.0.100",
    "snmp": {
      "snmpV2C": { "community": "private" },
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

### Get Measurement Response Example

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
          "std": 1.20,
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

## Get Measurement Statistics

### Endpoint

**POST** `/docs/pnm/ds/ofdm/rxMer/getMeasurementStatistics`

Retrieves SNMP-based RxMER statistics and file information for downstream OFDM channels.

### Response Example

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

## Get Analysis

### Endpoint

**POST** `/docs/pnm/ds/ofdm/rxmer/getAnalysis`

Performs a full downstream RxMER analysis using real-time SNMP collection or pre-captured PNM files.
It executes regression fitting, Shannon limit evaluation, and modulation-order statistics per subcarrier.


### Request Body

| Field                                   | Type    | Description                            |
| --------------------------------------- | ------- | -------------------------------------- |
| `cable_modem.mac_address`               | string  | MAC address of the modem               |
| `cable_modem.ip_address`                | string  | IPv4 or IPv6 address of the modem      |
| `pnm_parameters.tftp.ipv4`              | string  | TFTP server IPv4 address               |
| `pnm_parameters.tftp.ipv6`              | string  | TFTP server IPv6 address               |
| `pnm_parameters.snmp.snmpV2C.community` | string  | SNMPv2C community string               |
| `pnm_parameters.snmp.snmpV3.*`          | object  | SNMPv3 credentials (optional)          |
| `analysis.type`                         | integer | Analysis mode selector                 |
| `output.type`                           | integer | Output type selector (JSON or ARCHIVE) |

**Example JSON Request**

```json
{
  "cable_modem": {
    "mac_address": "60:6C:63:E4:36:84",
    "ip_address": "172.19.32.234",
    "pnm_parameters": {
      "tftp": {
        "ipv4": "172.19.0.56",
        "ipv6": "2001:428:3800:100:283f:2967:938a:bd68"
      },
      "snmp": {
        "snmpV2C": { "community": "private" },
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
  },
  "analysis": { "type": 0 },
  "output": { "type": 1 }
}
```

### Analysis Type Reference

| Value | Constant             | Description                                                                                                                        |
| ----- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `0`   | `AnalysisType.BASIC` | Performs basic frequency-domain analysis. Calculates regression line, Shannon limits, and per-subcarrier modulation order support. |

### Output Type Reference

| Value | Constant           | Description                                                                        |
| ----- | ------------------ | ---------------------------------------------------------------------------------- |
| `0`   | `FileType.JSON`    | Returns structured JSON analysis for UI or programmatic use.                       |
| `1`   | `FileType.ARCHIVE` | Returns a ZIP archive containing CSV, PNG, and summary files for offline analysis. |

### Response Structure

When `output.type = FileType.JSON`, returns a structured model;
when `output.type = FileType.ARCHIVE`, returns a downloadable `.zip` file.

| Field                                               | Type          | Description                                          |
| --------------------------------------------------- | ------------- | ---------------------------------------------------- |
| `device_details`                                    | object        | System descriptor and firmware metadata              |
| `pnm_header`                                        | object        | PNM file header fields (type, version, capture time) |
| `channel_id`                                        | integer       | Downstream OFDM channel identifier                   |
| `carrier_values.frequency`                          | array (Hz)    | Subcarrier frequencies                               |
| `carrier_values.magnitude`                          | array (dB)    | RxMER values per subcarrier                          |
| `carrier_values.carrier_status`                     | array (int)   | 0=EXCLUSION, 1=CLIPPED, 2=NORMAL                     |
| `regression.slope`                                  | array (float) | Regression-fitted RxMER trend                        |
| `modulation_statistics.snr_db_min`                  | array (float) | Shannon minimum SNR                                  |
| `modulation_statistics.supported_modulation_counts` | object        | Modulation order counts by type                      |

## Returned File Types

When `output.type = FileType.ARCHIVE`, the system bundles the following outputs into a single `.zip` file:

| File Pattern                      | Format | Description                                                       |
| --------------------------------- | ------ | ----------------------------------------------------------------- |
| `rxmer_<MAC>_<CH>.csv`            | CSV    | Raw per-subcarrier RxMER with Shannon limit and regression values |
| `rxmer_<MAC>_<CH>_plot.png`       | PNG    | RxMER vs frequency plot with regression overlay                   |

**Example Archive Layout**

```shell
rxmer_analysis_aabbccddeeff_20251011_197.zip
├── rxmer_aabbccddeeff_ch197.csv
├── rxmer_aabbccddeeff_ch197_plot.png
```

---

## Example Output Gallery

Below are representative visual outputs generated by `/getAnalysis` when `output.type = FileType.ARCHIVE`.
These help visualize downstream OFDM health and modulation distribution.

| File                                  | Description                                                      | Preview                                                                       |
| ------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **`rxmer_<MAC>_<CH>_plot.png`**       | RxMER per subcarrier with regression overlay (MER vs frequency). | ![RxMER Plot](../../assets/examples/rxmer/rxmer_plot_example.png)             |
| **`modulation_count_<MAC>_<CH>.png`** | Histogram of modulation orders (bits per symbol vs count).       | ![Modulation Count](../../assets/examples/rxmer/modulation_count_example.png) |
| **`signal_aggregate_<MAC>.png`**      | Combined RxMER response across all OFDM downstream channels.     | ![Signal Aggregate](../../assets/examples/rxmer/signal_aggregate_example.png) |

To include previews in your documentation, store these PNGs in:

## Differences Between Measurement and Analysis

| Operation                   | Purpose                                 | Output                                               |
| --------------------------- | --------------------------------------- | ---------------------------------------------------- |
| `/getMeasurement`           | Collects raw RxMER data via SNMP        | Returns unprocessed subcarrier MER values            |
| `/getMeasurementStatistics` | Retrieves SNMP-level metrics            | Returns modem-calculated mean, stddev, and threshold |
| `/getAnalysis`              | Performs signal and modulation analysis | Returns structured or archived analytical results    |
