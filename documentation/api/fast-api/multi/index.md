## 📱 Multi-Capture API Index

Explore the PyPNM multi-capture workflows for DOCSIS cable modems. This index provides direct access to key API guides and advanced analysis tools for repeated measurements and diagnostics.

> 🔧 **Background**
> See the [Capture Operation Guide](capture-operation.md) for an overview of the capture infrastructure and lifecycle.

### 🚀 Multi-Capture Workflows

| **Workflow**                                                    | **Description**                                                                 |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| [🧽 **Multi-RxMER Capture**](multi-capture-rxmer.md)            | Periodic downstream OFDM RxMER sampling and analysis across multiple carriers.  |
| [🔬 **Multi-DS Channel Estimation**](multi-capture-chan-est.md) | Periodic downstream OFDM channel estimation coefficient captures and reporting. |


### 📊 Advanced Analysis Modules

| **Module**                                                                | **Description**                                                                       |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [📈 Group Delay Calculator](./analysis/group-delay-calculator.md)         | Computes group delay variations from channel estimates.                               |
| [🔥 Heatmap Anomalies](./analysis/heatmap-anonomies.md)                   | Identifies temporal and spatial RxMER deviations using heatmap inspection.            |
| [🎯 OFDM Performance 1:1](./analysis/multi-rxmer-ofdm-performance-1-1.md) | Evaluates per-subcarrier capacity vs profile on a 1:1 basis.                          |
| [🔍 OFDM Echo Detection](./analysis/ofdm-echo-detection.md)               | Detects echo distortions and impulse reflections in OFDM channels.                    |
| [⚡ Phase Slope LTE Detection](./analysis/phase-slope-lte-detection.md)    | Detects LTE-related slope patterns in phase data that indicate external interference. |
| [🔀 Phase Slope (Legacy)](./analysis/phase-slope-lete-detection-2.md)     | Legacy method for identifying slope-related anomalies in upstream phase data.         |
| [🧽 Phase Slope (General)](./analysis/phase-slope.md)                     | General-purpose slope analysis for both upstream and downstream channels.             |
| [🧮 Signal Statistics](./analysis/signal-statistics.md)                   | Extracts RMS, min/max, and statistical variance from signal snapshots.                |

### 📘 Each Guide Includes:

1. **Workflow Overview** – High-level description of the process
2. **Endpoint Stubs** – Example JSON requests and responses
3. **Usage Examples** – Common payloads and scenarios
4. **Implementation Notes** – Practical tips and caveats

🔗 **Get Started:** Choose the appropriate guide for your use case and begin integrating multi-capture functionality with the PyPNM API.
