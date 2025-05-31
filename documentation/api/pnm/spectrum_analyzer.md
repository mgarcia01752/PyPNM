# Spectrum Analyzer API Documentation

*Please provide the MAC address of the target cable modem when invoking these endpoints.*

This API provides endpoints for performing measurements and analysis related to spectrum analysis for cable modems in a DOCSIS network.

---

### Endpoints Overview

| Endpoint                                                 | Description                                                                                   |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `POST /docs/pnm/ds/ofdm/spectrumAnalyzer/getMeasurement` | Initiate and retrieve raw spectrum analysis data for a specified cable modem.                 |
| `POST /docs/pnm/ds/ofdm/spectrumAnalyzer/getAnalysis`    | Perform detailed analysis of spectrum data, including magnitude and group delay calculations. |

---

## 1. POST `/docs/pnm/ds/ofdm/spectrumAnalyzer/getMeasurement`

**Request Payload:**

```json
{
  "mac_address": "aabb.ccdd.eeff",      
  "ip_address": "string",
  "snmp": {
    "snmpV2C": {
      "community": "string"
    },
    "snmpV3": {
      "username": "string",
      "securityLevel": "string",
      "authProtocol": "string",
      "authPassword": "string",
      "privProtocol": "string",
      "privPassword": "string"
    }
  },
  "parameters": {
    "inactivity_timeout": 100,
    "first_segment_center_freq": 300000000,
    "last_segment_center_freq": 900000000,
    "segment_freq_span": 1000000,
    "num_bins_per_segment": 256,
    "noise_bw": 150,
    "window_function": 1,
    "num_averages": 1,
    "spectrum_retrieval_type": 1
  }
}
```

* **`mac_address`**: MAC address of the target cable modem (e.g., `aabb.ccdd.eeff`).
* **`ip_address`**: IP address of the target cable modem (e.g., `172.20.63.12`).
* **`snmp`**: Either SNMP v2c or v3 credentials:

  * **`snmpV2C`**:

    * `community`: SNMP v2c write community string.
  * **`snmpV3`**:

    * `username`: SNMPv3 username.
    * `securityLevel`: One of `noAuthNoPriv`, `authNoPriv`, `authPriv`.
    * `authProtocol`: SNMPv3 auth protocol (e.g., `MD5`, `SHA`).
    * `authPassword`: SNMPv3 authentication password.
    * `privProtocol`: SNMPv3 privacy protocol (e.g., `DES`, `AES`).
    * `privPassword`: SNMPv3 privacy password.
* **`parameters`**: Spectrum Analyzer settings:

  * `inactivity_timeout`: Timeout in seconds for inactivity (default: 100).
  * `first_segment_center_freq`: First segment center frequency in Hz (e.g., 300 MHz).
  * `last_segment_center_freq`: Last segment center frequency in Hz (e.g., 900 MHz).
  * `segment_freq_span`: Frequency span of each segment in Hz (e.g., 1 MHz).
  * `num_bins_per_segment`: Number of FFT bins per segment (default: 256).
  * `noise_bw`: Equivalent noise bandwidth in kHz (default: 150).
  * `window_function`: FFT window function ID (e.g., `1` for HANN).
  * `num_averages`: Number of averages per segment (default: 1).
  * `spectrum_retrieval_type`: Retrieval method (1 = FILE via TFTP, 2 = SNMP).

**Response Example:**

```json
{
  "mac_address": "aabb.ccdd.eeff",
  "status": 0,
  "message": null,
  "data": {
    "frequency_bins": [
      {"frequency": 300000000, "magnitude_dB": -32.1, "group_delay": 1.2e-8},
      {"frequency": 301000000, "magnitude_dB": -31.5, "group_delay": 1.3e-8},
      ...
    ],
    "metadata": {
      "num_bins": 256,
      "start_frequency": 300000000,
      "end_frequency": 900000000,
      "window_function": 1,
      "noise_bw": 150
    }
  }
}
```

* **`frequency_bins`**: Array of objects each containing frequency (Hz), magnitude in dB, and group delay (seconds).
* **`metadata`**: Additional test parameters and settings used.

---

## 2. POST `/docs/pnm/ds/ofdm/spectrumAnalyzer/getAnalysis`

**Request Payload:**

```json
{
  "mac_address": "aabb.ccdd.eeff",
  "ip_address": "string",
  "snmp": {
    "snmpV2C": {"community": "string"},
    "snmpV3": {
      "username": "string",
      "securityLevel": "string",
      "authProtocol": "string",
      "authPassword": "string",
      "privProtocol": "string",
      "privPassword": "string"
    }
  },
  "parameters": {
    "inactivity_timeout": 100,
    "first_segment_center_freq": 300000000,
    "last_segment_center_freq": 900000000,
    "segment_freq_span": 1000000,
    "num_bins_per_segment": 256,
    "noise_bw": 150,
    "window_function": 1,
    "num_averages": 1,
    "spectrum_retrieval_type": 1
  }
}
```

* Same fields as the `getMeasurement` endpoint.

**Response Example:**

```json
{
  "mac_address": "aabb.ccdd.eeff",
  "status": 0,
  "message": null,
  "data": {
    "analysis_header": "header-info-string",
    "summary": {
      "average_magnitude_dB": -30.5,
      "max_magnitude_dB": -28.2,
      "min_magnitude_dB": -35.1,
      "average_group_delay": 1.25e-8
    },
    "detailed_bins": [
      {"frequency": 300000000, "magnitude_dB": -32.1, "group_delay": 1.2e-8},
      {"frequency": 301000000, "magnitude_dB": -31.5, "group_delay": 1.3e-8},
      ...
    ]
  }
}
```

* **`analysis_header`**: String providing context or metadata about the analysis.
* **`summary`**: Aggregate metrics calculated over all bins.
* **`detailed_bins`**: Same structure as in `getMeasurement` response, with frequency, magnitude, and group delay.

---

## 3. Window Function Types

When configuring spectrum analysis, the `window_function` parameter selects the DFT window applied to the time-domain samples. Each window trades off main-lobe width versus side-lobe level:

| ID | Name             | Description                                                            |
| -- | ---------------- | ---------------------------------------------------------------------- |
| 0  | OTHER            | Unspecified or device-specific windowing.                              |
| 1  | HANN             | Hann window – reduces side lobes, suitable for most use cases.         |
| 2  | BLACKMAN\_HARRIS | High dynamic range window with very low spectral leakage.              |
| 3  | RECTANGULAR      | No windowing; equivalent to raw DFT, maximum resolution, high leakage. |
| 4  | HAMMING          | Similar to Hann but with slightly different tapering.                  |
| 5  | FLAT\_TOP        | Flattens the top of the main lobe – good for accurate amplitude.       |
| 6  | GAUSSIAN         | Gaussian-shaped window; parameterized by standard deviation.           |
| 7  | CHEBYSHEV        | Minimizes main-lobe width for a given side-lobe level.                 |
