
### 📄 `pnm_us_ofdma_preEqualization.md`

````markdown
# 📡 Proactive Network Maintenance (PNM) – Upstream OFDMA Pre-Equalization

These endpoints provide visibility into the cable modem's upstream OFDMA pre-equalization data. The pre-equalization coefficients and derived metrics are vital for diagnosing impairments like group delay, micro-reflections, and in-channel frequency response issues.

---

## 🔁 Endpoint Summary

| Endpoint                                                                 | Description                                                                 |
|--------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `POST /docs/pnm/us/ofdma/preEqualization/getMeasurement`                | Retrieves raw complex pre-equalization tap data for upstream OFDMA channels |
| `POST /docs/pnm/us/ofdma/preEqualization/getAnalysis`                   | Computes derived metrics such as magnitude, phase, and group delay          |
| `POST /docs/pnm/us/ofdma/preEqualization/getFiles`                      | Downloads raw pre-equalization data files (e.g., from TFTP/SFTP)            |

---

## 📥 `POST /docs/pnm/us/ofdma/preEqualization/getMeasurement`

### Description

Fetches raw complex pre-equalization coefficients for upstream OFDMA channels. These tap values are directly read from the cable modem and represent [real, imaginary] complex pairs for each subcarrier or tap index.

### Request Body

```json
{
  "ip_address": "192.168.100.1",
  "mac_address": "00:11:22:33:44:55"
}
````

| Field         | Type   | Required | Description                           |
| ------------- | ------ | -------- | ------------------------------------- |
| `ip_address`  | string | ✅        | IP address of the cable modem         |
| `mac_address` | string | ✅        | MAC address of the target cable modem |

### Success Response `200 OK`

```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-05-16T14:32:45Z",
    "upstream_channel_id": 2,
    "cm_mac_address": "00:11:22:33:44:55",
    "cmts_mac_address": "00:aa:bb:cc:dd:ee",
    "subcarrier_zero_frequency": 20500000,
    "first_active_subcarrier_index": 30,
    "subcarrier_spacing": 25000,
    "value_length": 128,
    "value_unit": "[Real, Imaginary]",
    "values": [
      [0.98, -0.12],
      [0.95, -0.20],
      [0.88, -0.35]
    ]
  }
}
```

---

## 📊 `POST /docs/pnm/us/ofdma/preEqualization/getAnalysis`

### Description

Returns derived metrics from the raw pre-equalization data, including magnitude, group delay, and tap quality metrics. This analysis is useful for visualizing modem performance and identifying plant-related distortions.

### Request Body

```json
{
  "ip_address": "192.168.100.1",
  "mac_address": "00:11:22:33:44:55"
}
```

### Success Response `200 OK`

```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-05-16T14:32:45Z",
    "group_delay_us": [0.0, 0.2, 0.4, 0.3, 0.1],
    "magnitude_db": [-0.5, -0.3, -0.7, -1.2],
    "tap_energy_profile": [0.9, 0.5, 0.3, 0.1],
    "summary": {
      "dominant_tap_index": 0,
      "pre_cursor_energy": 0.2,
      "post_cursor_energy": 0.8,
      "noise_floor_db": -35
    }
  }
}
```

---

## 📁 `POST /docs/pnm/us/ofdma/preEqualization/getFiles`

### Description

Retrieves raw data files generated during measurement (such as binary coefficient dumps or processed CSVs). Files may be retrieved from the modem directly or from an intermediate TFTP/SFTP/HTTP server.

### Request Body

```json
{
  "ip_address": "192.168.100.1",
  "mac_address": "00:11:22:33:44:55",
  "file_type": "RAW_BINARY"
}
```

| Field         | Type   | Required | Description                                        |
| ------------- | ------ | -------- | -------------------------------------------------- |
| `ip_address`  | string | ✅        | IP address of the cable modem                      |
| `mac_address` | string | ✅        | MAC address of the cable modem                     |
| `file_type`   | string | ✅        | Type of file requested (`RAW_BINARY`, `CSV`, etc.) |

### Success Response `200 OK`

```json
{
  "status": "success",
  "data": {
    "file_name": "preEqData-00_11_22_33_44_55.raw",
    "download_url": "http://<host>/download/preEqData-00_11_22_33_44_55.raw"
  }
}
```

---

## ⚙️ Notes

* All endpoints are `POST` and require both `ip_address` and `mac_address`.
* Taps are decoded from fixed-point format into floating-point complex values.
* The `getAnalysis` endpoint is optional but recommended for visualization dashboards.
* The `getFiles` endpoint supports integration with external file processing or long-term storage.
* For accurate results, ensure the modem is online and reachable via SNMP.

---

## 🧪 Example Usage

```bash
curl -X POST http://<host>/docs/pnm/us/ofdma/preEqualization/getMeasurement \
     -H "Content-Type: application/json" \
     -d '{"ip_address": "192.168.100.1", "mac_address": "00:11:22:33:44:55"}'
```
