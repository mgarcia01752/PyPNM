# PyPNM MultiRxMer MIN\_AVG\_MAX Result

This document outlines the structure and meaning of the JSON returned by the `POST /advance/multiRxMer/analysis` endpoint when `analysis_type = 0` (MIN\_AVG\_MAX).

## 🔄 Top-Level Response

| Field        | Type    | Description                             |
| ------------ | ------- | --------------------------------------- |
| mac\_address | string  | MAC address of the modem being analyzed |
| status       | integer | Status code (0 = success)               |
| message      | string  | Descriptive status message              |
| data         | object  | Dictionary keyed by OFDM Channel ID     |

## 🔁 Channel Breakdown (`data.<channel_id>`) — Repeated for N channels

Each key in the `data` object corresponds to one OFDM channel. The value is an object with RxMER statistics:

### 📈 Measurement Arrays

| Field     | Type     | Description                                 |
| --------- | -------- | ------------------------------------------- |
| min       | float\[] | Per-subcarrier minimum RxMER values         |
| avg       | float\[] | Per-subcarrier average RxMER values         |
| max       | float\[] | Per-subcarrier maximum RxMER values         |
| frequency | float\[] | Frequency values (Hz or MHz) per subcarrier |
| precision | integer  | Decimal places of precision                 |

### 📊 Signal Statistics (`signal_statistics`)

Each of the three measurement series (`min`, `avg`, `max`) includes statistical summaries:

#### ➕ Common Stats Format

| Metric               | Type    | Description                              |
| -------------------- | ------- | ---------------------------------------- |
| mean                 | float   | Mean value of the series                 |
| median               | float   | Median value                             |
| std                  | float   | Standard deviation                       |
| variance             | float   | Variance                                 |
| power                | float   | Signal power                             |
| peak\_to\_peak       | float   | Max - Min of signal                      |
| mean\_abs\_deviation | float   | Mean absolute deviation                  |
| skewness             | float   | Skewness of the distribution             |
| kurtosis             | float   | Kurtosis of the distribution             |
| crest\_factor        | float   | Crest factor = peak amplitude / RMS      |
| zero\_crossing\_rate | float   | Frequency of zero crossings (normalized) |
| zero\_crossings      | integer | Raw count of zero crossings              |

> ⚠️ Each measurement (`min`, `avg`, `max`) contains its own set of stats.

## 🧠 Example Skeleton

### 📦 JSON Structure Supporting Multiple Channels

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Analysis MIN_AVG_MAX completed for group <group_id>",
  "data": {
    "<channel_id_1>": {
      "min": [/* float */],
      "avg": [/* float */],
      "max": [/* float */],
      "frequency": [/* float */],
      "precision": 2,
      "signal_statistics": {
        "min": {
          "mean": 0.0,
          "median": 0.0,
          "std": 0.0,
          "variance": 0.0,
          "power": 0.0,
          "peak_to_peak": 0.0,
          "mean_abs_deviation": 0.0,
          "skewness": 0.0,
          "kurtosis": 0.0,
          "crest_factor": 0.0,
          "zero_crossing_rate": 0.0,
          "zero_crossings": 0
        },
        "avg": {
          "mean": 0.0,
          "median": 0.0,
          "std": 0.0,
          "variance": 0.0,
          "power": 0.0,
          "peak_to_peak": 0.0,
          "mean_abs_deviation": 0.0,
          "skewness": 0.0,
          "kurtosis": 0.0,
          "crest_factor": 0.0,
          "zero_crossing_rate": 0.0,
          "zero_crossings": 0
        },
        "max": {
          "mean": 0.0,
          "median": 0.0,
          "std": 0.0,
          "variance": 0.0,
          "power": 0.0,
          "peak_to_peak": 0.0,
          "mean_abs_deviation": 0.0,
          "skewness": 0.0,
          "kurtosis": 0.0,
          "crest_factor": 0.0,
          "zero_crossing_rate": 0.0,
          "zero_crossings": 0
        }
      }
    },
    "<channel_id_2>": {
      /* same structure as channel_id_1 */
    }
  }
}
```

## 📝 Notes

* The `data` field may contain multiple channel objects, each keyed by its OFDM channel ID.
* All measurement arrays (`min`, `avg`, `max`, `frequency`) are expected to be of equal length.
* Precision is provided for display/rounding guidance.
* All statistics are calculated **per channel**.

---

> 📂 For full field definitions, refer to: `api/routes/advance/multi_rxmer/schemas.py`
