# PNM Operations – Downstream OFDM Constellation Display

This API provides access to raw constellation symbols captured from DOCSIS 3.1 downstream OFDM channels, enabling visual inspection of I/Q (in-phase and quadrature) data. The constellation display is a cornerstone of RF diagnostics—it reveals the actual symbol behavior at the demodulator and can highlight impairments such as phase noise, amplitude distortion, ingress, or burst noise.

By capturing and plotting these samples as a scatter plot, network operators can immediately assess modulation clarity, clustering, and the presence of impairments. This is particularly valuable when diagnosing subtle or transient RF issues that might not manifest in standard metrics like RxMER or FEC.

Due to the volume of data returned, this endpoint is best consumed via Postman, CLI tools, or automation scripts rather than SwaggerUI. The capture supports per-channel modulation information, subcarrier mapping, and sampling configuration for precise control and reproducibility.

## 🔊 Endpoint

**POST** `/docs/pnm/ds/ofdm/constellationDisplay/getMeasurement`

Captures downstream OFDM constellation symbols from a DOCSIS cable modem for visualization as a scatter plot (I/Q points). Due to the volume of data returned, **Postman or CLI tools are recommended** over SwaggerUI.

## 📅 Request Body (JSON)

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
  "modulation_order_offset": 0,
  "number_sample_symbol": 8192
}
```

### 🔑 Request Fields

| Field                     | Type   | Description                                        |
| ------------------------- | ------ | -------------------------------------------------- |
| `mac_address`             | string | MAC address of the cable modem                     |
| `ip_address`              | string | IP address of the cable modem                      |
| `snmp.snmpV2C.community`  | string | SNMPv2c community string                           |
| `snmp.snmpV3.*`           | string | SNMPv3 credentials and security options            |
| `modulation_order_offset` | int    | Modulation offset (profile-based modulation shift) |
| `number_sample_symbol`    | int    | Number of I/Q samples to retrieve (e.g., 8192)     |

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
        "pnm_header": {
          "file_type": "PNN",
          "file_type_version": 3,
          "major_version": 1,
          "minor_version": 0,
          "capture_time": 1751825651
        },
        "channel_id": 197,
        "mac_address": "a1:b2:c3:d4:e5:f6",
        "subcarrier_zero_frequency": 1217600000,
        "actual_modulation_order": "qam16",
        "num_sample_symbols": 8192,
        "subcarrier_spacing": 50000,
        "sample_length": 32768,
        "value_units": "[Real(I), Imaginary(Q)]",
        "values": [
          [2.8161, -0.9989],
          [3.1241,  0.2345],
          ...
        ]
      }
    ]
  }
}
```

## 📊 Response Field Breakdown

| Field                       | Type   | Description                                                |
| --------------------------- | ------ | ---------------------------------------------------------- |
| `status`                    | string | Status of the constellation capture (e.g., SUCCESS)        |
| `pnm_header.*`              | object | Metadata about the capture format, version, and timestamp  |
| `channel_id`                | int    | Downstream channel ID                                      |
| `mac_address`               | string | MAC address of the modem                                   |
| `subcarrier_zero_frequency` | int    | Base subcarrier frequency (Hz)                             |
| `actual_modulation_order`   | string | OFDM modulation type (e.g., `qam16`, `qam1024`, `qam4096`) |
| `num_sample_symbols`        | int    | Number of constellation sample points                      |
| `subcarrier_spacing`        | int    | Frequency spacing between subcarriers (Hz)                 |
| `sample_length`             | int    | Total data length (samples × 2)                            |
| `value_units`               | string | Units of the sample values (I/Q format)                    |
| `values`                    | array  | List of I/Q sample pairs representing constellation points |

## 📈 Visualization

* Data from `values` can be plotted as I (x-axis) vs Q (y-axis) for a **scatter plot**.
* Ideal clusters represent good modulation; noise and spread may indicate impairment.

## 📃 Notes

* Large payloads are not suitable for SwaggerUI. Use Postman, `curl`, or Python clients.
* Useful for evaluating demodulation performance and diagnosing OFDM reception impairments.
* ⚠️ There may be **multiple OFDM channels** returned in the `data` array. Each entry corresponds to a distinct downstream OFDM channel.
