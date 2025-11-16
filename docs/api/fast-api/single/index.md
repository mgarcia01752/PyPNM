# Single Capture Operations

Endpoints that perform one-shot capture or query against a single device.

## Simple Network Management Protocol (SNMP)

### Downstream (DS)

|  Reference                                        | Description                             |
|---------------------------------------------------|-----------------------------------------|
| [OFDM Channel Statistics](ds/ofdm//channel-stats.md)      | Physical Channel Statistics     |
| [OFDM Profile Statistics](ds/ofdm/profile-stats.md)       | Profile Codeword Statistics     |
| [SC-QAM Channel Statistics](ds/scqam/channel-stats.md)    | Physical Channel Statistics     |
| [SC-QAM CW Error Rate](ds/scqam/cw-error-rate.md)         | Codeword Error Statistics       |

### Upstream (US)

|  Reference                                                  | Description                         |
|-------------------------------------------------------------|-------------------------------------|
| [OFDMA Channel Statistics](us/ofdma/stats.md)               | OFDMA Channel Statistics            |
| [ATDMA Pre-Equalization](us/atdma/chan/pre-equalization.md) | ATDMA Pre-Equalization              |
| [ATDMA Channel Statistics](us/atdma/chan/stats.md)          | ATDMA Channel Statistics            |

### DOCSIS Frequency Division Duplex (FDD)

|  Reference                                                                     | Description                    |
|--------------------------------------------------------------------------------|--------------------------------|
| [Diplexer band-edge capability](fdd/fdd-diplexer-band-edge-cap.md)             | Supported diplexer range       |
| [Diplexer configuration (system)](fdd/fdd-system-diplexer-configuration.md)    | System diplexer settings       |

### DOCSIS Full Duplex (FDX)

|  Reference                                                                     | Description                  |
|--------------------------------------------------------------------------------|------------------------------|
| [Diplexer band-edge capability](fdd/fdd-diplexer-band-edge-cap.md)             | Supported diplexer range     |
| [Diplexer configuration (system)](fdd/fdd-system-diplexer-configuration.md)    | System diplexer settings     |

### Cable Modem Functions and Interfaces

|  Reference                                                    | Description                       |
|---------------------------------------------------------------|-----------------------------------|
| [Diplexer Configuration](diplexer-configuration.md)           | Device diplexer settings          |
| [DOCSIS Base Configuration](docsis-base-configuration.md)     | Base configuration view           |
| [Event Log](event-log.md)                                     | Cable modem event log             |
| [Reset Cable Modem](reset-cm.md)                              | Remote reset                      |
| [System Description](system-description.md)                   | `sysDescr` identity               |
| [System Uptime](up-time.md)                                   | `sysUpTime` in seconds            |
| [Interface Statistics](pnm/interface/stats.md)                | Interface-level statistics        |

## Proactive Network Maintenance (PNM)

### Downstream (DS)

|  Reference                                                        | Description                       |
|-------------------------------------------------------------------|-----------------------------------|
| [OFDM RxMER](ds/ofdm/rxmer.md)                                    | Raw RxMER, summaries, plots       |
| [OFDM MER Margin](ds/ofdm/mer-margin.md)                          | OFDM MER margin utilities         |
| [OFDM Channel-Estimation](ds/ofdm/channel-estimation.md)          | Channel distortion/echo analysis  |
| [OFDM Constellation Display](ds/ofdm/constellation-display.md)    | Visual modulation symbols    |
| [OFDM FEC Summary](ds/ofdm/fec-summary.md)                        | Forward error correction summary  |
| [OFDM Modulation Profile](ds/ofdm/modulation-profile.md)          | Bit-loading and profile usage     |
| [Histogram](ds/histogram.md)                                      | Downstream power-level histogram  |

### Upstream (US)

|  Reference                                         | Description                      |
|----------------------------------------------------|----------------------------------|
| [OFDMA Pre-Equalization](us/ofdma/pre-equalization.md) | Upstream tap coefficients    |

## Spectrum Analysis

|  Reference                                | Description                           |
|-------------------------------------------|---------------------------------------|
| [Spectrum Analyzer](spectrum-analyzer.md) | Spectrum Capture                      |
| [DOCSIS 3.0 SC-QAM](spectrum-analyzer.md) | Downstream PerChannel SCQAM Capture   |
| [DOCSIS 3.1 OFDM](spectrum-analyzer.md)   | Downstream PerChannel OFDM Capture    |

