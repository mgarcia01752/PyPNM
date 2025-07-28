# PNM Operations - Downstream OFDM RxMER

This API provides deep visibility into the signal quality of DOCSIS 3.1+ downstream OFDM channels by retrieving and analyzing Receive Modulation Error Ratio (RxMER) at the subcarrier level. RxMER is one of the most powerful indicators of downstream plant health, capable of exposing narrowband interference, ingress, micro-reflections, and other impairments that traditional metrics may overlook.

The /getMeasurement endpoint captures real-time RxMER values, while /getAnalysis transforms that data into a structured format with frequency mappings, carrier status classification, and inferred modulation capabilities. Combined, these endpoints enable operators to localize RF impairments with high precision and assess modem channel performance using Shannon-theoretic analysis.

These insights are instrumental in PNM workflows and can be correlated with constellation diagrams, modulation profiles, and equalizer tap data for full-spectrum diagnostics.

## 📚 Table of Contents

* [Get Measurement](#get-measurement)
* [Get Measurement Statistics](#get-measurement-statistics)
* [Get Analysis](#get-analysis)
* [Analysis and Output Types](#analysis-and-output-types)
* [Differences Between Measurement and Analysis](#differences-between-measurement-and-analysis)

## Get Measurement

### 🛡️ Endpoint

**POST** `/docs/pnm/ds/ofdm/rxMer/getMeasurement`

Retrieves subcarrier-level RxMER (Receive Modulation Error Ratio) measurements from a DOCSIS 3.1+ cable modem. RxMER is critical in evaluating signal quality across the OFDM channel bandwidth. This includes statistical summaries and calculated modulation support per subcarrier.

### 📜 Request Body (JSON)

```json
{
  "cable_modem": {
	"mac_address": "aa:bb:cc:dd:ee:ff",
	"ip_address": "192.168.0.100",
  "snmp": {
    "snmpV2C": {
      "community": "private"
    },
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
```

### 📄 JSON Response

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
        "bits_per_symbol": [14, 14, 14, 14, 14],
        "modulations": ["qam_16384", "qam_16384", "qam_16384", "qam_16384", "qam_16384"],
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

### 🛡️ Endpoint

**POST** `/docs/pnm/ds/ofdm/rxMer/getMeasurementStatistics`

```json
{
  "cable_modem": {
	"mac_address": "aa:bb:cc:dd:ee:ff",
	"ip_address": "192.168.0.100",
  "snmp": {
    "snmpV2C": {
      "community": "private"
    },
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
```

### 📄 JSON Response

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Measurement Statistics for RxMER",
  "results": {
    "DS_OFDM_RXMER_PER_SUBCAR": [
      {
        "index": <SNMP_INDEX>,
        "channel_id": <CHANNEL_UD>,
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
