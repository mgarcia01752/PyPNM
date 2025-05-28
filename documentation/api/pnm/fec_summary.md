
# DOCSIS PNM - Downstream OFDM FEC Summary

This API retrieves Forward Error Correction (FEC) summary data for downstream OFDM channels from a cable modem using SNMP and TFTP mechanisms.

---

## 🔗 Endpoint

**POST** `/docs/pnm/ds/ofdm/fecSummary/getMeasurement`

---

## 📥 Request Body

### Schema: `PnmFecSummaryRequest`

```json
{
  "mac_address": "aabb.ccdd.eeff",
  "ip_address": "192.168.100.1",
  "fec_summary_type": 2
}
```

| Field           | Type   | Description                                 |
|----------------|--------|---------------------------------------------|
| mac_address    | string | MAC address of the cable modem              |
| ip_address     | string | IP address of the cable modem               |
| fec_summary_type | int  | Type of summary: `2` (10-min), `3` (24-hr)  |

---

## 📤 Response

### Schema: `PnmFecSummaryResponse`

```json
{
  "mac_address": "00:50:f1:12:dc:c3",
  "status": 0,
  "message": null,
  "data": {
    "data": [
      {
        "status": "SUCCESS",
        "channel_id": 34,
        "mac_address": "00:50:f1:12:dc:c3",
        "summary_type": 2,
        "num_profiles": 5,
        "fec_summary_data": [
          {
            "profile_id": 255,
            "number_of_sets": 600,
            "codeword_entries": [
              {
                "timestamp": 8439,
                "total_codewords": 44445,
                "corrected_codewords": 0,
                "uncorrectable_codewords": 0
              },{...}
            ]
          },
          {
            "profile_id": 0,
            "number_of_sets": 600,
            "codeword_entries": [
              {
                "timestamp": 8439,
                "total_codewords": 44445,
                "corrected_codewords": 0,
                "uncorrectable_codewords": 0
              },{...}
            ]
          },
        ]
      }
    ]
  }
}
````

---

## 🔍 Field Descriptions

### Top-Level

| Field        | Type   | Description                        |
| ------------ | ------ | ---------------------------------- |
| mac\_address | string | MAC address of the modem queried   |
| status       | int    | Status code from service execution |
| message      | string | Optional message or error text     |
| data         | object | Contains FEC measurement results   |

---

### `data.data[]` (per channel result)

| Field              | Type   | Description                           |
| ------------------ | ------ | ------------------------------------- |
| status             | string | "SUCCESS" or error message            |
| channel\_id        | int    | OFDM channel ID                       |
| mac\_address       | string | Cable modem MAC                       |
| summary\_type      | int    | 2 for 10-min, 3 for 24-hour summary   |
| num\_profiles      | int    | Number of modulation profiles present |
| fec\_summary\_data | array  | List of FEC summaries per profile     |

---

### `fec_summary_data[]` (per profile)

| Field             | Type  | Description                                |
| ----------------- | ----- | ------------------------------------------ |
| profile\_id       | int   | Profile ID (e.g., 255 for unknown/default) |
| number\_of\_sets  | int   | Number of measurement sets (600 or 1440)   |
| codeword\_entries | array | Codeword stats per measurement timestamp   |

---

### `codeword_entries[]`

| Field                    | Type | Description                                  |
| ------------------------ | ---- | -------------------------------------------- |
| timestamp                | int  | Relative timestamp (counter or second-based) |
| total\_codewords         | int  | Total number of codewords                    |
| corrected\_codewords     | int  | Number of codewords corrected by FEC         |
| uncorrectable\_codewords | int  | Codewords uncorrectable even after FEC       |

---

## ✅ Notes

* `summary_type = 2` → 10-minute test (600 samples)
* `summary_type = 3` → 24-hour test (1440 samples)
* Each `codeword_entry` corresponds to a periodic snapshot during the test window.
