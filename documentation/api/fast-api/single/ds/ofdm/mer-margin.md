# OFDM MER Margin

The purpose of this item is to provide an estimate of the MER margin available on the downstream data channel with respect to a modulation profile. The profile may be a profile that the modem has already been assigned or a candidate profile. This is similar to the MER Margin reported in the OPT-RSP Message \[MULPIv3.1].

The CM calculates the Required Average MER for the profile based on the bit loading for the profile and the Required MER per Modulation Order provided in the CmDsOfdmRequiredQamMer table. For profiles with mixed modulation orders, this value is computed as an arithmetic mean of the required MER values for each non-excluded subcarrier in the Modulated Spectrum. The CM then measures the RxMER per subcarrier and calculates the Average MER for the Active Subcarriers used in the Profile and stores the value as MeasuredAvgMer. The Operator may also compute the value for Required Average MER for the profile and set that value for the test.

The CM also counts the number of MER per Subcarrier values that are below the threshold determined by the CmDsOfdmRequiredQamMer and the ThrshldOffset. The CM reports that value as NumSubcarriersBelowThrshld.

This table will have a row for each ifIndex for the modem.

## 📚 Table of Contents

* [Get Measurement](#get-measurement)
* [Get Measurement Status](#get-measurement-status)

## Get Measurement

### 🚀 Endpoint

**POST** `/docs/pnm/ds/ofdm/merMargin/getMeasurement`

Initiates a MER margin measurement on a DOCSIS 3.1 downstream OFDM profile.

### 📒 Request Body (JSON)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "ip_address": "192.168.0.1",
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
  },
  "profile_id": 2,
  "threshold_offset": 2,
  "symbols_to_average": 8,
  "required_avg_mer": 360
}
```

### 🔑 Request Fields

| Field                | Type   | Description                                     |
| -------------------- | ------ | ----------------------------------------------- |
| `mac_address`        | string | MAC address of the cable modem                  |
| `ip_address`         | string | IP address of the cable modem                   |
| `snmp.*`             | object | SNMP credentials                                |
| `profile_id`         | int    | Profile ID to test (0–15)                       |
| `threshold_offset`   | int    | dB offset below required MER (quarter dB units) |
| `symbols_to_average` | int    | Number of symbols to average per subcarrier     |
| `required_avg_mer`   | int    | Required average MER (quarter dB units)         |

## Get Measurement Status

### 📡 Endpoint

**POST** `/docs/pnm/ds/ofdm/merMargin/getMeasurementStatistics`

Returns MER margin test status and results per OFDM profile.

### 📒 Request Body (JSON)

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "ip_address": "192.168.0.1",
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
```

### 📤 JSON Response Example

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Measurement Statistics for MER Margin",
  "results": {
    "DS_OFDM_MER_MARGIN": [
      {
        "index": 3,
        "channel_id": 3,
        "entry": {
          "docsPnmCmDsOfdmMerMarProfileId": 2,
          "docsPnmCmDsOfdmMerMarThrshldOffset": 2,
          "docsPnmCmDsOfdmMerMarMeasEnable": false,
          "docsPnmCmDsOfdmMerMarNumSymPerSubCarToAvg": 8,
          "docsPnmCmDsOfdmMerMarReqAvgMer": 360,
          "docsPnmCmDsOfdmMerMarNumSubCarBelowThrshld": 5,
          "docsPnmCmDsOfdmMerMarMeasuredAvgMer": 387,
          "docsPnmCmDsOfdmMerMarAvgMerMargin": 27,
          "docsPnmCmDsOfdmMerMarMeasStatus": 3
        }
      }
    ]
  }
}
```

### 📊 Response Field Breakdown

| Field                             | Type | Description                                                         |
| --------------------------------- | ---- | ------------------------------------------------------------------- |
| `profile_id`                      | int  | Modulation profile ID                                               |
| `threshold_offset`                | int  | Threshold offset below required MER                                 |
| `meas_enable`                     | bool | Whether measurement is active                                       |
| `symbols_to_average`              | int  | Number of symbols per subcarrier to average                         |
| `required_avg_mer`                | int  | Required average MER (quarter dB)                                   |
| `num_subcarriers_below_threshold` | int  | Subcarriers below MER threshold                                     |
| `measured_avg_mer`                | int  | Actual measured average MER (hundredth dB)                          |
| `avg_mer_margin`                  | int  | Difference between measured and required average MER (hundredth dB) |
| `meas_status`                     | int  | Measurement status code                                             |
