## 🧪 Cable Modem Diagnostic API Reference

### 🛠️ Single-Shot PNM Operations

This reference serves as the **single-shot FastAPI REST API landing point** for all major PNM (Proactive Network Maintenance) diagnostic operations. It consolidates the key FastAPI documentation pages for DOCSIS 3.0/3.1 cable modem monitoring, analysis, and reporting—designed for both on-demand and automated diagnostics workflows.

### 📁 Markdown Reference Index

| Markdown                                                         | Description                                  |
| ---------------------------------------------------------------- | -------------------------------------------- |
| [Diplexer Configuration](./diplexer-configuration.md)            | Diplexer system settings                     |
| [OFDM Channel Estimation](./ds/ofdm/channel-estimation.md)       | OFDM channel distortion/echo analysis        |
| [OFDM Constellation Display](./ds/ofdm/constellation-display.md) | Visual representation of modulation symbols  |
| [OFDM FEC Summary](./ds/ofdm/fec-summary.md)                     | OFDM Forward Error Correction analysis       |
| [OFDM Modulation Profile](./ds/ofdm/modulation-profile.md)       | Bit-loading per subcarrier and profile usage |
| [OFDM RxMER](./ds/ofdm/rxmer.md)                                 | Raw RxMER data, summary, and graphing        |
| [OFDM Channel Stats](./ds/ofdm/stats.md)                         | OFDM channel stats: frequency, power, MER    |
| [SC-QAM Downstream Stats](./ds/scqam/stats.md)                   | Downstream SC-QAM channel stats              |
| [Event Log](./event-log.md)                                      | CM Event log access                          |
| [MER Histogram](./histogram.md)                                  | Downstream histogram (MER/SNR distribution)  |
| [Reset Cable Modem](./reset-cm.md)                               | Remote cable modem reset                     |
| [Spectrum Analyzer](./spectrum-analyzer.md)                      | Downstream sweep capture                     |
| [System Description](./system-description.md)                    | SNMP system identity (sysDescr)              |
| [System Uptime](./up-time.md)                                    | Uptime from SNMP (sysUpTime)                 |
| [OFDMA Pre-Equalization](./us/ofdma/pre-equalization.md)         | Upstream OFDMA tap coefficient capture       |
| [OFDMA Channel Stats](./us/ofdma/stats.md)                       | OFDMA upstream channel stats                 |
| [SC-QAM Pre-Equalization](./us/scqam/chan/pre-equalization.md)   | SC-QAM upstream pre-equalization             |
| [SC-QAM Upstream Stats](./us/scqam/chan/stats.md)                | SC-QAM upstream stats                        |

---

### 📘 Overview

This API provides a comprehensive suite of diagnostic endpoints for Proactive Network Maintenance (PNM) in DOCSIS-based cable modem networks. These endpoints allow for real-time and historical data retrieval, signal quality assessment, and analysis of both upstream and downstream channels.

After starting the FastAPI service locally, visit [http://localhost:8000/docs](http://localhost:8000/docs) to explore the interactive Swagger documentation.

All endpoints use `POST` requests and accept JSON payloads containing a cable modem's MAC or IP address. Most responses include structured data and optionally visualizations or downloadable diagnostics.

---

<!-- The remainder of the index content stays unchanged -->
