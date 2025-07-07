## 🧪 Cable Modem Diagnostic API Reference

### 🛠️ Single-Shot PNM Operations

This reference serves as the **single-shot FastAPI REST API landing point** for all major PNM (Proactive Network Maintenance) diagnostic operations. It consolidates the key FastAPI documentation pages for DOCSIS 3.0/3.1 cable modem monitoring, analysis, and reporting designed for both on-demand and automated diagnostics workflows.

#### 📡 Downstream (DS) Operations

| Markdown                                                         | Description                                    |
| ---------------------------------------------------------------- | ---------------------------------------------- |
| [OFDM Channel Estimation](./ds/ofdm/channel-estimation.md)       | OFDM channel distortion/echo analysis          |
| [OFDM Constellation Display](./ds/ofdm/constellation-display.md) | Visual representation of modulation symbols    |
| [OFDM FEC Summary](./ds/ofdm/fec-summary.md)                     | OFDM Forward Error Correction analysis         |
| [OFDM Modulation Profile](./ds/ofdm/modulation-profile.md)       | Bit-loading per subcarrier and profile usage   |
| [OFDM RxMER](./ds/ofdm/rxmer.md)                                 | Raw RxMER data, summary, and graphing          |
| [OFDM Channel Stats](./ds/ofdm/stats.md)                         | OFDM channel stats: frequency, power, MER      |
| [SC-QAM Downstream Stats](./ds/scqam/stats.md)                   | Downstream SC-QAM channel stats                |
| [Histogram](./histogram.md)                                      | Downstream power-level histogram               |
| [Spectrum Analyzer](./spectrum-analyzer.md)                      | Downstream sweep capture                       |

#### 📶 Upstream (US) Operations

| Markdown                                                       | Description                            |
| -------------------------------------------------------------- | -------------------------------------- |
| [OFDMA Pre-Equalization](./us/ofdma/pre-equalization.md)       | Upstream OFDMA tap coefficient capture |
| [OFDMA Channel Stats](./us/ofdma/stats.md)                     | OFDMA upstream channel stats           |
| [SC-QAM Pre-Equalization](./us/scqam/chan/pre-equalization.md) | SC-QAM upstream pre-equalization       |
| [SC-QAM Upstream Stats](./us/scqam/chan/stats.md)              | SC-QAM upstream stats                  |

#### 🧾 Cable Modem Functions

| Markdown                                              | Description                     |
| ----------------------------------------------------- | ------------------------------- |
| [Diplexer Configuration](./diplexer-configuration.md) | Diplexer system settings        |
| [Event Log](./event-log.md)                           | CM Event log access             |
| [Reset Cable Modem](./reset-cm.md)                    | Remote cable modem reset        |
| [System Description](./system-description.md)         | SNMP system identity (sysDescr) |
| [System Uptime](./up-time.md)                         | Uptime from SNMP (sysUpTime)    |

#### ⚙️ PyPNM System

| Markdown                                                 | Description                                      |
| -------------------------------------------------------- | ------------------------------------------------ |
| [System Configuration](./configuration.md)               | Retrieve or update PyPNM SNMP settings           |
| [System Log](../system/log.md)                           | Download PyPNM backend log file                  |
| [File Operations](../file_manager/file-manager.md)       | Search, retrieve, and analyze uploaded PNM files |

### 📘 Overview

This API provides a comprehensive suite of diagnostic endpoints for Proactive Network Maintenance (PNM) in DOCSIS-based cable modem networks. These endpoints allow for real-time and historical data retrieval, signal quality assessment, and analysis of both upstream and downstream channels.

After starting the FastAPI service locally, visit [http://localhost:8000/docs](http://localhost:8000/docs) to explore the interactive Swagger documentation.

All endpoints use `POST` requests and accept JSON payloads containing a cable modem's MAC or IP address. Most responses include structured data and optionally visualizations or downloadable diagnostics.

### PySNMP System Configuration

| Endpoint                | Description                                                                                                  |
|-------------------------|--------------------------------------------------------------------------------------------------------------|
| `POST /pypnm/system/config/get | Retrieve current system configuration. |
| `POST /pypnm/system/config/update | Update the system configuration. |

### 🖥️ System Information

| Endpoint                | Description                                                                                                  |
|-------------------------|--------------------------------------------------------------------------------------------------------------|
| `POST /system/sysdescr` | Retrieves the system description (`sysDescr`) of the cable modem, indicating hardware/software details.     |
| `POST /system/uptime`   | Retrieves the modem's uptime in seconds since the last reboot.                                               |

### 📄 Event Logs

| Endpoint                  | Description                                                                                                               |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------|
| `POST /docs/dev/eventLog` | Retrieves DOCSIS event logs, including critical errors (e.g., ranging failures, T3/T4 timeouts).                          |
| `POST /docs/dev/reset`    | Sends a reset command to the cable modem.                                                                                 |

### 📶 Interface & Channel Statistics

| Endpoint                                | Description                                                                                                     |
|-----------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `POST /docs/if31/system/diplexer`       | Retrieves diplexer settings that define frequency split between upstream and downstream.                       |
| `POST /docs/if31/ds/ofdm/profile/stats` | Returns OFDM profile usage stats including codewords, errors, and profile IDs.                                |
| `POST /docs/if31/ds/ofdm/chan/stats`    | Physical stats for OFDM downstream channels: channel ID, PLC power, center frequency.                         |
| `POST /docs/if31/us/ofdma/chan/stats`   | Retrieves OFDMA upstream channel data: transmit power, active subcarriers, symbol rates, etc.                 |
| `POST /docs/if30/ds/scqam/chan/stats`   | SC-QAM downstream signal quality: power levels, frequency, modulation.                                         |
| `POST /docs/if30/us/atdma/chan/stats`   | ATDMA upstream info: frequency, modulation, pre-equalization, power levels.                                    |
| `POST /docs/if30/us/atdma/chan/preEqualization`   | ATDMA upstream info: frequency, modulation, pre-equalization, power levels.                                    |

### 🔧 PNM: General Diagnostics

| Endpoint                                   | Description                                                                                                 |
|--------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `POST /docs/pnm/files`                     | Upload or retrieve PNM files for further analysis or visualization.                                         |
| `POST /docs/pnm/spectrumAnalyzer`          | Captures a downstream spectrum snapshot to identify ingress or interference.                                |
| `POST /docs/pnm/ds/histogram`              | Returns downstream SNR and MER histograms indicating signal quality distribution.                           |
| `POST /docs/pnm/ds/ofdm/rxMer`             | Retrieves RxMER (Receive MER) values across OFDM subcarriers.                                               |
| `POST /docs/pnm/ds/ofdm/constDisplay`      | Retrieves OFDM constellation data for visualization and noise analysis.                                     |
| `POST /docs/pnm/ds/ofdm/fecSummary`        | Summarizes FEC performance: corrected/uncorrected codewords and error correction health.                    |
| `POST /docs/pnm/ds/ofdm/chanEstimation`    | Retrieves downstream channel estimation data (impulse noise, group delay).                                  |
| `POST /docs/pnm/ds/ofdm/modulationProfile` | Returns modulation profile and subcarrier bit-loading info.                                                 |
| `POST /docs/pnm/us/ofdma/preEqualization`  | Gets upstream pre-equalization coefficients to assess plant impairments.                                    |
| `POST /docs/pnm/lld/latencyReport`         | Retrieves Low Latency DOCSIS metrics like queue delay and flow behavior.                                    |

### 📊 PNM: RxMER Measurements

| Endpoint                                      | Description                                                                                           |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `POST /docs/pnm/ds/ofdm/rxMer/getMeasurement` | Gets the latest RxMER snapshot per subcarrier.                                                        |
| `POST /docs/pnm/ds/ofdm/rxMer/getAnalysis`    | Generates visual plots (e.g., heatmap, line graph) of RxMER data.                                    |

### ⚙️ PNM: FEC Summary

| Endpoint                                           | Description                                                                                   |
|----------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `POST /docs/pnm/ds/ofdm/fecSummary/getMeasurment`  | Retrieves OFDM Forward Error Correction stats (corrected vs uncorrected codewords, profile).  |

### 📐 PNM: Channel Estimation

| Endpoint                                                       | Description                                                                                       |
|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `POST /docs/pnm/ds/ofdm/channelEstCoeff/getMeasurement`        | Fetch raw channel estimation coefficient data.                                                    |
| `POST /docs/pnm/ds/ofdm/channelEstCoeff/getAnalysis`           | Analyze channel distortion metrics (e.g., group delay, frequency response).                      |

### 🛰️ PNM: Constellation Display

| Endpoint                                             | Description                                                                 |
|------------------------------------------------------|-----------------------------------------------------------------------------|
| `POST /docs/pnm/ds/ofdm/constDisplay/getMeasurement` | Capture raw constellation symbols from cable modem.                         |
| `POST /docs/pnm/ds/ofdm/constDisplay/getAnalysis`    | Generate plots and detect modulation anomalies or impairments.              |

### 📡 PNM: Upstream Pre-Equalization

| Endpoint                                                                | Description                                                                  |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `POST /docs/pnm/us/ofdma/preEqualization/getMeasurement`               | Gets complex tap coefficients from upstream channel.                         |
| `POST /docs/pnm/us/ofdma/preEqualization/getAnalysis`                  | Derives metrics like magnitude, phase, and group delay from raw taps.        |

## PNM Advance Operation and Analysis

| Method | Endpoint                                 | Description                                      | Request Model           | Response Model                |
| ------ | ---------------------------------------- | ------------------------------------------------ | ----------------------- | ----------------------------- |
| POST   | `/advance/multiRxMer/start`              | Start a periodic RxMER capture                   | `MultiRxMerRequest`     | `MultiRxMerStartResponse`    |
| GET    | `/advance/multiRxMer/status/{op_id}`     | Get current state & sample count for this op     | path param `operation_id` | `MultiRxMerStatusResponse`   |
| GET    | `/advance/multiRxMer/results/{op_id}`    | Retrieve all timestamped transaction IDs & files | path param `operation_id` | `MultiRxMerResultsResponse`  |
| POST   | `/advance/multiRxMer/stop/{op_id}`       | Signal capture to stop after current iteration   | path param `operation_id` | `MultiRxMerStatusResponse`   |

### 📁 PNM: File Management

| Endpoint                          | Description                                                                                   |
|-----------------------------------|-----------------------------------------------------------------------------------------------|
| `POST /docs/pnm/files/searchFiles`   | |
| `POST /docs/pnm/files/getFiles`   | Lists all available PNM files by MAC address or filtering criteria.                           |
| `POST /docs/pnm/files/pushFile`   | Uploads a new PNM measurement file to the system.                                             |
| `POST /docs/pnm/files/getAnalysis`| Produces a visual output (e.g., spectrum or RxMER graph) from a selected PNM file.            |

### 🔁 Common Request Format

Most endpoints follow this JSON structure:

```json
{
  "mac_address": "a0:b1:c2:d3:e4:f5",
  "ip_address": "192.168.100.1"
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
````

* `mac_address`: Accepts formats like `aabbccddeeff`, `aabb.ccdd.eeff`, or `aa:bb:cc:dd:ee:ff`.
* `ip_address`: Supports both IPv4 and IPv6 addresses.

### 📚 DOCSIS MIB Support

This API is based on industry-standard **DOCSIS MIBs** including:

* [`DOCS-IF-MIB`](https://datatracker.ietf.org/doc/html/rfc4546) – Defines the core MIB objects for DOCSIS 1.x and 2.0 interfaces.
* [`DOCS-IF3-MIB`](https://mibs.cablelabs.com/MIBs/DOCSIS/DOCS-IF3-MIB-2025-02-20.txt) – Extends DOCSIS MIBs with additional objects introduced in DOCSIS 3.0.
* [`DOCS-IF31-MIB`](https://mibs.cablelabs.com/MIBs/DOCSIS/DOCS-IF31-MIB-2025-04-24.txt) – Defines objects for DOCSIS 3.1 cable modems, including OFDM channels.
* [`DOCS-PNM-MIB`](https://mibs.cablelabs.com/MIBs/DOCSIS/DOCS-PNM-MIB-2024-07-05.txt) – Specifies Proactive Network Maintenance (PNM) MIBs for DOCSIS devices.
* [`IETF Interfaces MIB`](https://datatracker.ietf.org/doc/html/rfc2863) – Standard MIB for network interface management across devices.

These MIBs define SNMP-accessible metrics used to assess modem performance, error correction, and signal health across the DOCSIS network.
