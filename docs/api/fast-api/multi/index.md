# Multi-Capture API Index

Explore The PyPNM Multi-Capture Workflows For DOCSIS Cable Modems. This Index Provides Direct Access To Key API Guides And Advanced Analysis Tools For Repeated Measurements And Diagnostics.

> **Background**
> See the [Capture Operation Guide](capture-operation.md) for an overview of the capture infrastructure and lifecycle.

## Multi-Capture Workflows

| **Workflow**                                                 | **Description**                                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| **[Multi-RxMER Capture](multi-capture-rxmer.md)**            | Periodic downstream OFDM RxMER sampling and analysis across multiple carriers.  |
| **[Multi-DS Channel Estimation](multi-capture-chan-est.md)** | Periodic downstream OFDM channel-estimation coefficient captures and reporting. |

## Advanced Analysis Modules

| **Module**                                                             | **Description**                                                                       |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [Multi-RxMER-MinAvgMax](./analysis/multi-rxmer-min-avg-max.md)         | Computes minimum, average, and maximum RxMER values across multiple captures.         |
| [Multi-ChanEst-MinAvgMax](./analysis/multi-chanest-min-avg-max.md)     | Computes minimum, average, and maximum channel estimation across captures.|
| [Group Delay Calculator](./analysis/group-delay-calculator.md)         | Computes group delay variations from channel estimates.                               |
| [OFDM Performance 1:1](./analysis/multi-rxmer-ofdm-performance-part-1.md) | Evaluates per-subcarrier capacity vs profile on a 1:1 basis.                       |
| [OFDM Echo Detection](./analysis/ofdm-echo-detection.md)               | Detects echo distortions and impulse reflections in OFDM channels.                    |
| [Phase Slope LTE Detection](./analysis/phase-slope-lte-detection.md)   | Detects LTE-related slope patterns in phase data that indicate external interference. |
| [Signal Statistics](./analysis/signal-statistics.md)                   | Extracts RMS, min/max, and statistical variance from signal snapshots.                |

### Each Guide Includes

1. **Workflow Overview** – High-level description of the process
2. **Endpoint Stubs** – Example JSON requests and responses
3. **Usage Examples** – Common payloads and scenarios
4. **Implementation Notes** – Practical tips and caveats

**Get Started:** Choose The Appropriate Guide For Your Use Case And Begin Integrating Multi-Capture Functionality With The PyPNM API.
