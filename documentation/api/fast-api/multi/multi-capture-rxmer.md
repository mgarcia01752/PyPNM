## 📁 Table of Contents

* [Workflow Overview](#workflow-overview)
* [Endpoint Stubs](#endpoint-stubs)

  * [1. Start Capture](#1-start-capture)
  * [2. Status Check](#2-status-check)
  * [3. Download Measurements](#3-download-measurements)
  * [4. Stop Capture Early](#4-stop-capture-early)
  * [5. Analysis](#5-analysis)
* [Timing Details](#timing-details)

## Workflow Overview

1. **Start Capture** (`POST /advance/multiRxMer/start`)

   * Initiates a background RxMER capture session with a defined duration and sample interval.
   * Returns a `group_id` and `operation_id` that uniquely identify this capture workflow.

2. **Check Status** (`GET /advance/multiRxMer/status/{operation_id}`)

   * Polls the session state to retrieve how many samples have been collected and the remaining time.

3. **Download Results** (`GET /advance/multiRxMer/results/{operation_id}`)

   * Streams a ZIP archive of all captured PNM files for offline processing or archival.

4. **Stop Capture Early** (`DELETE /advance/multiRxMer/stop/{operation_id}`)

   * Signals the capture task to end after the current iteration.
   * Returns the final sample count and state (including any time remaining).

5. **Analysis** (`POST /advance/multiRxMer/analysis`)

   * Submits an `operation_id` and desired `analysis_type` to perform post-capture analytics.
   * Returns processed metrics (e.g., min/avg/max RxMER, heatmaps, or profile performance).

## Endpoint Stubs

### 1. Start Capture

**Note:** Choose the appropriate measure mode according to desired capture type:

* `mode = 0` for **continuous sampling** (needed for MIN\_AVG\_MAX and RXMER\_HEAT\_MAP analyses).
* `mode = 1` for **OFDM performance** captures (needed for OFDM\_PROFILE\_PERFORMANCE analysis).

**Request** (`MultiRxMerRequest` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "ip_address": "192.168.0.100",
  "snmp": {
    "snmpV2C": { "community": "public" },
    "snmpV3": {
      "username": "user",
      "securityLevel": "noAuthNoPriv",
      "authProtocol": "MD5",
      "authPassword": "password",
      "privProtocol": "DES",
      "privPassword": "password"
    }
  },
  "capture": {
    "parameters": {
      "measurement_duration": 60,
      "sample_interval": 10
    }
  },
  "measure": {
    "mode": 0
  }
}
```

* **Fields**

  * `mac_address` (string): MAC address of the cable modem.
  * `ip_address` (string): IPv4 or IPv6 address of the modem.
  * `snmp` (object): SNMP credentials—either `snmpV2C` or `snmpV3`.
  * `capture.parameters.measurement_duration` (integer, seconds): Total capture duration.
  * `capture.parameters.sample_interval` (integer, seconds): Interval between successive RxMER samples.
  * `measure.mode` (integer): Measurement mode (0 = continuous sampling, 1 = OFDM performance).

**Response** (`MultiRxMerStartResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "running",
  "message": null,
  "group_id": "3bd6f7c107ad465b",
  "operation_id": "4aca137c1e9d4eb6"
}
```

* **Fields**

  * `status`: Always `"running"` immediately after initiation.
  * `group_id` (string): Unique identifier for this capture group.
  * `operation_id` (string): Unique identifier for this specific capture operation.

*See the [Timing Details](#timing-details) for how `measurement_duration` and `sample_interval` affect workflow timing.*

### 2. Status Check

**Request**:

```
GET /advance/multiRxMer/status/{operation_id}
```

* Replace `{operation_id}` with the ID returned by the Start Capture endpoint.

**Response** (`MultiRxMerStatusResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "success",
  "message": null,
  "operation": {
    "operation_id": "35ecc8fb1b3c44bd",
    "state": "running",
    "collected": 2,
    "time_remaining": 50,
    "message": null
  }
}
```

* **Fields**

  * `operation.state` (string): One of `"running"`, `"completed"`, or `"stopped"`.
  * `operation.collected` (integer): Number of samples captured so far.
  * `operation.time_remaining` (integer, seconds): Approximate seconds left in this capture.
  * `operation.message` (string | null): Additional status info (e.g., partial failures).

*Refer to [Timing Details](#timing-details) for recommended polling intervals.*

### 3. Download Measurements

**Request**:

```
GET /advance/multiRxMer/results/{operation_id}
```

* `{operation_id}` must correspond to a completed or stopped capture.

**Response**:

* Content-Type: `application/zip`

* A ZIP archive containing:

  Zip Filename: multiRxMer\_\<mac\_address>*\<operation\_id>.zip
  PNM Measurement File Example: ds\_ofdm\_rxmer\_per\_subcar*\<mac\_address>*\<channel\_id>*<ephoc>.bin

  ```
  ds_ofdm_rxmer_per_subcar_aabbccddeeff_193_1751762613.bin
  ds_ofdm_rxmer_per_subcar_aabbccddeeff_194_1751762613.bin
  ds_ofdm_rxmer_per_subcar_aabbccddeeff_193_1751762613.bin
  ds_ofdm_rxmer_per_subcar_aabbccddeeff_194_1751762613.bin
  ...
  ```

* **Notes**

  * Each `.pnm` file corresponds to a snapshot captured at `sample_interval` increments.
  * The total number of files equals the number of samples (`operation.collected`).

### 4. Stop Capture Early

**Request**:

```
DELETE /advance/multiRxMer/stop/{operation_id}
```

* `{operation_id}`: The ID of an ongoing capture session.

**Response** (`MultiRxMerStatusResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": "stopped",
  "message": null,
  "operation": {
    "operation_id": "3e310a2296b24c78",
    "state": "stopped",
    "collected": 4,
    "time_remaining": 42,
    "message": null
  }
}
```

* **Fields**

  * `status`: Always `"stopped"` when the request is accepted.
  * `operation.collected`: Final count of captured samples.
  * `operation.time_remaining`: Remaining seconds at the time of stopping (may be nonzero if stopped mid-capture).

### 5. Analysis

**Note:** The available analysis results depend on the measurement mode selected during capture:

* If **continuous sampling** measure mode (mode = 0) was used, you can request:

  * `MIN_AVG_MAX` (analysis\_type = 0)
  * `RXMER_HEAT_MAP` (analysis\_type = 2)
* If **OFDM analysis** measure mode (mode = 1) was used, you can request:

  * `OFDM_PROFILE_PERFORMANCE` (analysis\_type = 1)

**Request** (`MultiRxMerAnalysisRequest` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "analysis": {
    "analysis_type": 0
  },
  "operation_id": "string"
}
```

* **Fields**

  * `analysis.analysis_type` (integer):

    * `0` = MIN\_AVG\_MAX (returns minimum, average, and maximum RxMER). Requires continuous sampling mode.
    * `1` = OFDM\_PROFILE\_PERFORMANCE (returns per-subcarrier performance). Requires OFDM analysis mode.
    * `2` = RXMER\_HEAT\_MAP (returns a time-by-frequency heatmap grid). Requires continuous sampling mode.
    * *(Additional types can be added in the future.)*
  * `operation_id`: ID of the completed capture session to analyze.

**Response** (`MultiRxMerAnalysisResponse` schema):

```json
{
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "status": 0,
  "message": "Analysis MIN_AVG_MAX completed for group 3fbc19a7fffe49c4",
  "data": {
    "min": 28.5,
    "avg": 31.2,
    "max": 33.8
  }
}
```

* **Fields**

  * `status` (integer):

    * `0` = success.
    * Nonzero = error (see `message`).
  * `message` (string): Concise confirmation or error description.
  * `data` (object): Varies by `analysis_type`.

    * For `MIN_AVG_MAX`: `{ "min": <float>, "avg": <float>, "max": <float> }`
    * For `OFDM_PROFILE_PERFORMANCE`: `{ "subcarrier_id": { "rxmer": <float>, "snr": <float>, ... }, ... }`
    * For `RXMER_HEAT_MAP`: `{ "timestamps": [<int>, ...], "frequencies": [<int>, ...], "heatmap": [[<float>, ...], ...] }`

> **Note:** Always use the schema definitions under `api/routes/advance/multi_rxmer/schemas.py` for precise field names, types, and allowed values.

## Timing Details

### 1. Start Capture Timing

* **`measurement_duration`** (in seconds) defines how long the background task will run.

  * Example: `measurement_duration: 60` means sampling will occur for one minute total.
* **`sample_interval`** (in seconds) specifies how frequently a new RxMER measurement is taken.

  * Example: if `sample_interval: 10`, then 6 samples will be taken over a 60-second duration.
* Once you call `POST /advance/multiRxMer/start`, the API immediately returns a `group_id` and `operation_id`, and the background thread begins waiting for the first sample.

### 2. Status Polling Recommendations

* Clients should query `GET /advance/multiRxMer/status/{operation_id}` only as often as necessary.
* **Recommended Poll Interval:**

  * At most once every `sample_interval` seconds (e.g., if `sample_interval = 10`, poll every 10 seconds).
  * Polling more frequently wastes resources; polling less frequently risks missing the “completed” transition.
* Each status response includes `time_remaining` (seconds). When `time_remaining == 0` and `state` changes to `"completed"`, no further polling is needed.

### 3. Download Results Timing

* Once a capture has `state: "completed"` or `"stopped"`, the ZIP archive is available instantly.
* The download speed depends on network bandwidth and the total PNM file size.
* Internal note: each PNM file is generated at the moment of sampling (asynchronously), so the archive simply bundles existing files; there is no additional processing delay.

### 4. Stop Capture Early Timing

* When `DELETE /advance/multiRxMer/stop/{operation_id}` is called:

  1. The background thread completes its current sampling iteration (if mid-sample).
  2. It writes the final PNM file for that iteration.
  3. It transitions `operation.state` to `"stopped"`.
* As a result, the reported `operation.time_remaining` may be slightly greater than zero if you stop mid-interval.
* Expected delay: up to `sample_interval` seconds before the capture thread acknowledges the stop and returns status.

### 5. Analysis Processing Time

* **MIN\_AVG\_MAX** (analysis\_type = 0):

  * Complexity: O(N) over the number of collected samples N.
  * On a 60-second run with 6 samples, processing completes in a few milliseconds.
* **OFDM\_PROFILE\_PERFORMANCE** (analysis\_type = 1):

  * Complexity: O(N × M) where M = number of subcarriers (e.g., 192 subcarriers for a 6 MHz OFDM channel).
  * Typical delay: under 100 ms for 6 samples × 192 subcarriers.
* **RXMER\_HEAT\_MAP** (analysis\_type = 2):

  * Complexity: O(N × M) to build the 2D array plus potential image rendering if returned as a graphic.
  * Typical delay: under 200 ms for moderate sample counts (<100) and standard channel widths.
* These are rough estimates—actual latency depends on server load and I/O.
* Clients should expect analysis responses to be nearly instantaneous (sub-second) for typical downstream-ofdm captures.
