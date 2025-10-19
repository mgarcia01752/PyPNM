# PNM Operations – Spectrum Analyzer

This API enables remote spectrum capture and signal inspection from a DOCSIS modem. It is designed for proactive diagnostics and RF analysis of the downstream OFDM path.

📌 **Important:** You must choose a start and end frequency that lie within the modem's configured diplexer band. Use the diplexer configuration endpoint to verify allowed frequency boundaries:

**POST:** `/docs/if31/system/diplexer`

👉 [API Guide – Diplexer Configuration](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/diplexer-configuration.md)

⚠️ **Notice:** A modem can only scan one direction at a time — either downstream or upstream. Attempting to scan both directions simultaneously is not supported.

## 📡 Endpoint

**POST** `/docs/pnm/ds/ofdm/spectrumAnalyzer/getMeasurement`

Performs a downstream OFDM spectrum capture from a DOCSIS cable modem. This operation converts raw spectrum amplitude data into a readable floating-point format for further signal processing, anomaly detection, and visualization.

## 📥 Request Body (JSON)

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
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
  "parameters": {
    "inactivity_timeout": 100,
    "first_segment_center_freq": 108000000,
    "last_segment_center_freq": 1002000000,
    "segment_freq_span": 1000000,
    "num_bins_per_segment": 256,
    "noise_bw": 150,
    "window_function": 1,
    "num_averages": 1,
    "spectrum_retrieval_type": 1
  }
}
```

### 🔑 Request Fields

| Field                                  | Type   | Description                                                    |
| -------------------------------------- | ------ | -------------------------------------------------------------- |
| `mac_address`                          | string | MAC address of the cable modem                                 |
| `ip_address`                           | string | IP address of the cable modem                                  |
| `snmp.snmpV2C.community`               | string | SNMPv2c community string                                       |
| `snmp.snmpV3.*`                        | string | SNMPv3 credentials and security settings                       |
| `parameters.inactivity_timeout`        | int    | Timeout before aborting idle spectrum acquisition              |
| `parameters.first_segment_center_freq` | int    | Start frequency (Hz) of the first spectrum segment             |
| `parameters.last_segment_center_freq`  | int    | End frequency (Hz) of the last spectrum segment                |
| `parameters.segment_freq_span`         | int    | Frequency span per segment (Hz)                                |
| `parameters.num_bins_per_segment`      | int    | Number of FFT bins per segment                                 |
| `parameters.noise_bw`                  | int    | Equivalent noise bandwidth                                     |
| `parameters.window_function`           | int    | Window function index (e.g., Hanning, Rectangular)             |
| `parameters.num_averages`              | int    | Number of averages per segment                                 |
| `parameters.spectrum_retrieval_type`   | int    | Retrieval type (e.g., 1 = capture & return raw and float data) |

## 📤 JSON Response

```json
{
  "mac_address": "a1:b2:c3:d4:e5:f6",
  "status": 0,
  "message": null,
  "data": {
    "data": [
      {
        "status": "SUCCESS",
        "Channel ID": 0,
        "MAC Address": "a1:b2:c3:d4:e5:f6",
        "First Segment Center Frequency": 300000000,
        "Last Segment Center Frequency": 900000000,
        "Segment Frequency Span": 1000000,
        "Number of Bins Per Segment": 256,
        "Equivalent Noise Bandwidth": 150,
        "Window Function": 1,
        "Bin Frequency Spacing": 3906.25,
        "Spectrum Analysis Data Length": 307712,
        "Spectrum Analysis Data": "<Spectrum-Data>:HEX", 
        "Number of Bin Segments": 256,
        "Amplitude Bin Segments Float": [
          [/* Segment 1 floats */],
          [/* Segment 2 floats */]
        ]
      }
    ]
  }
}
```

## 📊 Response Field Breakdown

| Field                            | Type   | Description                                         |
| -------------------------------- | ------ | --------------------------------------------------- |
| `status`                         | string | Status of the operation (e.g., SUCCESS, ERROR)      |
| `Channel ID`                     | int    | Channel ID of the OFDM measurement                  |
| `MAC Address`                    | string | MAC address of the modem                            |
| `First Segment Center Frequency` | int    | Center frequency (Hz) of the first spectrum segment |
| `Last Segment Center Frequency`  | int    | Center frequency (Hz) of the last spectrum segment  |
| `Segment Frequency Span`         | int    | Frequency range (Hz) per spectrum segment           |
| `Number of Bins Per Segment`     | int    | Number of frequency bins used in each segment       |
| `Equivalent Noise Bandwidth`     | int    | Filter bandwidth used during FFT measurement        |
| `Window Function`                | int    | FFT window type identifier (e.g., 1 = Hanning)      |
| `Bin Frequency Spacing`          | float  | Frequency spacing between each FFT bin (Hz)         |
| `Spectrum Analysis Data Length`  | int    | Total byte length of the raw spectrum data          |
| `Spectrum Analysis Data`         | string | Raw spectrum amplitude data in hexadecimal format   |
| `Number of Bin Segments`         | int    | Number of segments included in the spectrum capture |
| `Amplitude Bin Segments Float`   | array  | List of floating-point amplitude values per segment |

## 📝 Notes

* Raw spectrum data is preserved in `Spectrum Analysis Data` for future decoding.
* `Amplitude Bin Segments Float` is pre-processed for visualization and signal quality inspection.
* This data can be used to detect notches, roll-off, ingress noise, and other RF anomalies.
* Make sure the requested frequency range is within the modem’s diplexer capability using `/docs/if31/system/diplexer`.
* Modems cannot perform both upstream and downstream spectrum scans simultaneously.
