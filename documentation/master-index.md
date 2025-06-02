# PyPNM WiKi

Welcome to the PyPNM documentation. Use this master index to navigate through all guides, API references, examples, and system docs.

## 📚 API Reference

### DOCSIS Device Endpoints
- [Event Log](api/dev/eventLog.md)
- [Reset](api/dev/reset.md)

### FastAPI Reference
- [FastAPI Overview](api/fast-api/index.md)

#### • Multi-Snapshot Analysis
- [Overview](api/fast-api/multi/index.md)
- **Analysis**
  - [Group Delay Calculator](api/fast-api/multi/analysis/group-delay-calculator.md)
  - [Heatmap Anomalies](api/fast-api/multi/analysis/heatmap-anonomies.md)
  - [OFDM Performance 1:1](api/fast-api/multi/analysis/multi-rxmer-ofdm-performance-1-1.md)
  - [OFDM Echo Detection](api/fast-api/multi/analysis/ofdm-echo-detection.md)
  - [Phase Slope LTE Detection](api/fast-api/multi/analysis/phase-slope-lte-detection.md)
  - [Phase Slope (Legacy)](api/fast-api/multi/analysis/phase-slope-lete-detection-2.md)
  - [Phase Slope (General)](api/fast-api/multi/analysis/phase-slope.md)
  - [Signal Statistics](api/fast-api/multi/analysis/signal-statistics.md)
- [Capture Operation](api/fast-api/multi/capture-operation.md)
- [Multi-Capture Channel Estimation](api/fast-api/multi/multi-capture-chan-est.md)
- [Multi-Capture RxMER](api/fast-api/multi/multi-capture-rxmer.md)

#### • Single-Snapshot Endpoints
- [Single Snapshot Overview](api/fast-api/single/index.md)

#### • Status Codes
- [FastAPI Status Codes](api/fast-api/status/fast-api-status-codes.md)

### DOCSIS 3.0
- [Downstream SCQAM Channel Stats](api/if30/ds/scqam/chan/stats.md)
- [Upstream ATDMA Channel Stats](api/if30/us/atdma/chan/stats.md)

### DOCSIS 3.1
- [System Diplexer](api/if31/diplex.md)
- **Downstream OFDM**
  - [Channel Stats](api/if31/ds/ofdm/channel/stats.md)
  - [Profile Stats](api/if31/ds/ofdm/profile/stats.md)

### PNM Data Parsers

- [Spectrum Analyzer](api/pnm/spectrum_analyzer.md)
- [Channel Estimation Coefficients](api/pnm/chan_est_coef.md)
- [Constellation Display](api/pnm/const_displap.md)
- [FEC Summary](api/pnm/fec_summary.md)
- [Histogram](api/pnm/histogram.md)
- [RxMER](api/pnm/rxmer.md)
- [US OFDMA Pre-EQ](api/pnm/us_ofdma_pre_eq.md)

### Python Helpers

- [Python API Index](api/python/index.md)
  - [SNMPv2c](api/python/snmp/snmp-v2c.md)
  - [System Config](api/python/system_config/system_config.md)

## 💾 DOCSIS Background

- [DOCSIS Overview](docsis/index.md)

## 🛠 Examples

- [Example Scripts](examples/index.md)

## ⚙️ System & Setup

- [Generate SSL Certificates](system/generate-ssl-certificates.md)
- [System Configuration](system/system_config.md)
