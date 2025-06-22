# Proactive Network Maintenance (PNM) Downstream OFDM Channel Estimation API

This API provides endpoints for performing measurements and analysis related to downstream OFDM channel estimation coefficients for cable modems in a DOCSIS network.

### Endpoints Overview

| Endpoint                                                       | Description                                                 |
| -------------------------------------------------------------- | ----------------------------------------------------------- |
| `POST /docs/pnm/ds/ofdm/channelEstCoeff/getMeasurement`        | Initiate and retrieve raw channel estimation coefficient data for a specified cable modem.  |
| `POST /docs/pnm/ds/ofdm/channelEstCoeff/getAnalysis`           | Perform detailed analysis of channel estimation data, including magnitude and group delay calculations. |
| `POST /docs/pnm/ds/ofdm/channelEstCoeff/getFiles`              | Retrieve related raw output files from TFTP server for offline inspection.                  |

## 1. POST `/docs/pnm/ds/ofdm/channelEstCoeff/getMeasurement`

**Request Payload:**

```json
{
  "mac_address": "string",
  "ip_address": "string"
}
````

* `mac_address`: MAC address of the target cable modem.
* `ip_address`: IP address of the target cable modem.

**Response Example:**

```json
{
  "mac_address": "00:50:f1:12:dc:c3",
  "status": 0,
  "message": null,
  "data": {
    "channel_id": 34,
    "coefficients": [
      {"real": 0.123, "imag": -0.456, "timestamp": 12345},
      {"real": 0.234, "imag": -0.567, "timestamp": 12346},
      ...
    ],
    "metadata": {
      "subcarrier_spacing": 429000,
      "active_subcarrier_index": 512,
      "zero_frequency": 55200000
    }
  }
}
```

## 2. POST `/docs/pnm/ds/ofdm/channelEstCoeff/getAnalysis`

Performs detailed analysis of downstream OFDM channel estimation data for a given cable modem.

**Request Payload:**

```json
{
  "mac_address": "string",
  "ip_address": "string",
  "analysis_type": 0
}
```

* `mac_address`: MAC address of the cable modem under test.
* `ip_address`: IP address of the cable modem.
* `analysis_type`: Integer code specifying type of analysis (0 = basic channel estimation analysis).

**Response Example:**

```json
{
  "mac_address": "00:50:f1:12:dc:c3",
  "status": 0,
  "message": null,
  "data": {
    "pnm_header": "header-info-string",
    "channel_id": 34,
    "magnitude_unit": "dB",
    "complex_unit": "[Real, Imaginary]",
    "frequency_unit": "Hz",
    "carrier_values": {
      "carrier_count": 1024,
      "frequency": [55200000, 55629000, 56058000, ...],
      "magnitude": [-32.1, -30.5, -31.7, ...],
      "group_delay": [1.2e-8, 1.3e-8, 1.1e-8, ...],
      "complex": [
        [0.123, -0.456],
        [0.234, -0.567],
        ...
      ]
    }
  }
}
```

### Analysis Method Details

* **Magnitude Calculation:**
  The magnitude for each subcarrier is computed from its complex channel coefficient $H(f) = R + jI$ as:

  $$
  \text{magnitude} = \sqrt{R^2 + I^2}
  $$

  and converted to decibels (dB) via:

  $$
  \text{magnitude\_dB} = 20 \times \log_{10}(\text{magnitude})
  $$

* **Group Delay Calculation:**
  The group delay $\tau_g(f)$ is estimated by unwrapping the phase $\phi(f)$ of $H(f)$ and differentiating with respect to frequency:

  $$
  \phi(f) = \text{unwrap}(\arg(H(f)))
  $$

  $$
  \tau_g(f) = - \frac{d\phi(f)}{df}
  $$

  This indicates frequency-dependent delays in the channel response, useful for diagnosing impairments like echoes or group delay distortions.

---

## 3. POST `/docs/pnm/ds/ofdm/channelEstCoeff/getFiles`

**Request Payload:**

```json
{
  "mac_address": "string",
  "ip_address": "string"
}
```

* `mac_address`: MAC address of the cable modem.
* `ip_address`: IP address of the cable modem.

**Description:**

Fetches raw output files related to the channel estimation coefficients test from the configured TFTP server for offline or detailed inspection.

# Notes

* All endpoints require authentication headers as configured.
* IP and MAC addresses must be valid and reachable within the network.
* Analysis results depend on successful measurement retrieval and data integrity.
