# Single Capture Operations

Endpoints that perform one-shot capture or query against a single device.

## Simple Network Management Protocol (SNMP)

### Downstream (DS)

| Page                                              | Description                     |
|---------------------------------------------------|---------------------------------|
| [OFDM Profile Stats](ds/ofdm/stats.md)            | Frequency, power, MER.          |
| [SC-QAM CW error rate](ds/scqam/cw-error-rate.md) | Continuous-wave error rate.     |
| [SC-QAM stats](ds/scqam/stats.md)                 | Downstream SC-QAM stats.        |

### Upstream (US)

| Page                                                        | Description                     |
|-------------------------------------------------------------|---------------------------------|
| [OFDMA stats](us/ofdma/stats.md)                            | OFDMA upstream channel stats.   |
| [SC-QAM pre-equalization](us/scqam/chan/pre-equalization.md) | SC-QAM upstream pre-EQ.         |
| [SC-QAM stats](us/scqam/chan/stats.md)                      | SC-QAM upstream stats.          |

### Frequency division duplex (FDD)

| Page                                                                           | Description                     |
|--------------------------------------------------------------------------------|---------------------------------|
| [Diplexer band-edge capability](fdd/fdd-diplexer-band-edge-cap.md)             | Supported diplexer range.       |
| [Diplexer configuration (system)](fdd/fdd-system-diplexer-configuration.md)    | System diplexer settings.       |

### Cable modem functions

| Page                                        | Description                     |
|---------------------------------------------|---------------------------------|
| [Diplexer configuration](diplexer-configuration.md)          | Device diplexer settings.       |
| [DOCSIS base configuration](docsis-base-configuration.md)    | Base configuration view.        |
| [Event log](event-log.md)                                    | Cable modem event log.          |
| [Reset cable modem](reset-cm.md)                             | Remote reset.                   |
| [System description](system-description.md)                  | `sysDescr` identity.            |
| [System uptime](up-time.md)                                  | `sysUpTime` in seconds.         |

## Proactive Network Maintenance (PNM)

### Downstream (DS)

| Page                                                      | Description                     |
|-----------------------------------------------------------|---------------------------------|
| [OFDM RxMER](ds/ofdm/rxmer.md)                            | Raw RxMER, summaries, plots.    |
| [OFDM MER margin](ds/ofdm/mer-margin.md)                  | OFDM MER margin utilities.      |
| [OFDM channel estimation](ds/ofdm/channel-estimation.md)  | Channel distortion/echo analysis. |
| [OFDM constellation display](ds/ofdm/constellation-display.md) | Visual modulation symbols. |
| [OFDM FEC summary](ds/ofdm/fec-summary.md)                | Forward error correction summary. |
| [OFDM modulation profile](ds/ofdm/modulation-profile.md)  | Bit-loading and profile usage.  |
| [Histogram](histogram.md)                                 | Downstream power-level histogram. |
| [Spectrum analyzer](spectrum-analyzer.md)                 | Downstream sweep capture.       |

### Upstream (US)

| Page                                               | Description                     |
|----------------------------------------------------|---------------------------------|
| [OFDMA pre-equalization](us/ofdma/pre-equalization.md) | Upstream tap coefficients. |

### Interface

| Page                                   | Description                     |
|----------------------------------------|---------------------------------|
| [PNM interface stats](pnm/interface/stats.md) | PNM interface-level statistics. |
