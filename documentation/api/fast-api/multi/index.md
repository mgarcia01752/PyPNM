## Multi-Capture API Index

* **Capture Operation Overview** — [Capture Operation Guide](capture-operation.md)

This directory contains two related multi-capture workflows for DOCSIS cable modems. Use the guides below to explore each API’s endpoints and usage patterns.

| Workflow                        | Description                                                                     | Link                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Multi-RxMER Capture**         | Periodic downstream OFDM RxMER sampling and analysis across multiple carriers.  | [Multi-RxMER API Guide](multi-capture-rxmer.md)                           |
| **Multi-DS Channel Estimation** | Periodic downstream OFDM channel estimation coefficient captures and reporting. | [Multi-DS Channel Estimation Guide](multi-capture-chan-est.md)             |

**Analysis**
  - [Group Delay Calculator](./analysis/group-delay-calculator.md)
  - [Heatmap Anomalies](./analysis/heatmap-anonomies.md)
  - [OFDM Performance 1:1](./analysis/multi-rxmer-ofdm-performance-1-1.md)
  - [OFDM Echo Detection](./analysis/ofdm-echo-detection.md)
  - [Phase Slope LTE Detection](./analysis/phase-slope-lte-detection.md)
  - [Phase Slope (Legacy)](./analysis/phase-slope-lete-detection-2.md)
  - [Phase Slope (General)](./analysis/phase-slope.md)
  - [Signal Statistics](./analysis/signal-statistics.md)

Each guide includes:

1. **Workflow Overview** – high-level sequence of operations.  
2. **Endpoint Stubs** – sample requests and responses.  
3. **Usage Examples** – typical JSON payloads.  
4. **Notes** – tips and common pitfalls.

Select the guide matching your use case to get started with multi-capture operations via the PyPNM API.
