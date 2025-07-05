# Python API Measurement Types

This section introduces the core PNM measurement types available via the PyPNM Python API. Each measurement class parses a raw PNM binary file into a structured Python `dict` or JSON-like object. Downstream, you can convert that output into frequency vs. amplitude spectra, time-domain traces, or statistical summaries depending on the file type.

---

## How It Works

1. **Measurement Capture** — PNM files are created via live SNMP/TFTP operations.
   Example: [RxMER Measurement Capture](../../../examples/pnm/cm-pnm-ds-ofdm-rxmer.py)
2. **Load a PNM file** — Use the appropriate parser class (e.g., `CmDsOfdmRxMer`).
3. **Parse to structured data** — The parser returns a `dict` or Pydantic model with raw counters, arrays, and metadata.
4. **Post-process** — Convert arrays into NumPy, Pandas, or other formats for visualization (frequency vs. amplitude, time-series plots, histograms, heatmaps).

Chain these steps in scripts, dashboards, or Jupyter notebooks for custom analytics.

---

## Class Hierarchy UML

```text
    +-------------+        
    |   PNMFile   |        
    |   (bytes)   |        
    +-------------+        
           |               
           | inherits      
           v               
    +-------------+        
    | PnmHeader   |        
    +-------------+        
           |               
           | used by       
           v               
    +-------------+        
    | PnmParser   |        
    +-------------+        
```

* **PNMFile**: A Python `bytes` or byte-stream representing raw PNM capture data.
* [**PnmHeader**](../../../src/pypnm/pnm/process/pnm_header.py): Parses and holds header metadata extracted from the byte-stream.
* [**PnmFileType**](../../../src/pypnm/pnm/process/pnm_file_type.py): Check PNM Header against PNM FileTypes.
* **PnmParser**: Consumes the header and payload to produce structured measurement data.
---

## Output Format

All PNM parser classes produce their results as a Python `dict` or JSON-like structure. You can directly serialize this output to JSON or convert into NumPy/Pandas for further analysis. Typical top-level keys include:

* **metadata**: header fields such as version, capture time, file type
* **data**: numerical arrays (amplitude, frequency bins, I/Q samples, counters)
* **device\_details**: optional modem sysDescr or context fields

Use `json.dumps(parser_output)` to emit JSON, or access fields via standard dict operations.

---

## 🎯 Measurement Types (Parsers)

| Measurement Type              | Parser Class                                                                       | Description                                                                           | Status |
| ----------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | :----: |
| **OFDM Symbol Capture**       | [CmSymbolCapture](../../../src/pypnm/pnm/process/CmSymbolCapture.py)               | Extracts raw OFDM symbol waveforms for time-domain and IQ analysis.                   | CMTS Dependend    |
| **OFDM RxMER**                | [CmDsOfdmRxMer](../../../src/pypnm/pnm/process/CmDsOfdmRxMer.py)                   | Computes modulation error ratio per subcarrier; useful for carrier health heatmaps.   | ✅     |
| **OFDM FEC Summary**          | [CmDsOfdmFecSummary](../../../src/pypnm/pnm/process/CmDsOfdmFecSummary.py)         | Aggregates FEC counters for reliability metrics over time.                            | ✅     |
| **Spectrum Analysis**         | [CmSpectrumAnalysis](../../../src/pypnm/pnm/process/CmSpectrumAnalysis.py)         | Captures power spectral density snapshots in the frequency domain.                    | ✅     |
| **Channel Estimation**        | [CmDsOfdmChanEstimateCoef](../../../src/pypnm/pnm/process/CmDsOfdmChanEstimateCoef.py) | Retrieves equalizer tap coefficients for channel impulse response estimation.         | ✅     |
| **Modulation Profile**        | [CmDsOfdmModulationProfile](../../../src/pypnm/pnm/process/CmDsOfdmModulationProfile.py) | Shows modulation orders configured on each subcarrier.                                | ✅     |
| **Constellation Display**     | [CmDsConstDispMeas](../../../src/pypnm/pnm/process/CmDsConstDispMeas.py)           | Provides IQ scatter data for symbol constellation visualization.                      | ✅     |
| **Downstream Histogram**      | [CmDsHist](../../../src/pypnm/pnm/process/CmDsHist.py)                             | Outputs ADC histograms for detecting compression, clipping, or noise characteristics. | ✅     |
| **Upstream Pre-Equalization** | [CmUsPreEq](../../../src/pypnm/pnm/process/CmUsPreEq.py)                           | Parses pre-equalizer tap data for upstream OFDMA carriers.                            | ✅     |
| **ATDMA Pre-Equalization**    | [DocsEqualizerData](../../../src/pypnm/pnm/data_type/DocsEqualizerData.py)           | Parses legacy ATDMA equalizer taps for upstream DOCSIS channels.                      | ✅     |
| **Latency Reporting**         | [CmLatencyRpt](../../../src/pypnm/pnm/process/CmLatencyRpt.py)                     | Reports one-way delay and jitter statistics from PNM captures.                        | TBD    |

---

## Fetch and Process via a Service

Use higher-level service wrappers to automate PNM file retrieval and parsing:

* [RxMER Service Example](../../../src/pypnm/examples/service/cm-service-set-ds-rxmer.py)

### Main Service Calls

1. **`CmDsOfdmRxMerService.set_and_go()`** — initiates the RxMER capture.
2. **`CommonProcessService.process()`** — parses returned PNM payloads into JSON-ready structures.
3. **`FileProcessor.write_file()`** — saves each parsed result to disk as a timestamped JSON file.

---

## Background Staging & Manifesting

* Captures run in the background, triggering TFTP uploads of PNM files into the configured `data/pnm` directory.
* A concurrent background task creates a transition JSON manifest listing each captured file path and metadata.
* Downstream consumers can read this manifest to automatically discover and process new files without manual directory polling.

---

## Manifest Transaction Example

Each capture operation produces a manifest entry keyed by its operation ID. Example:

```json
{
  "2ee6138bbc1b3c3d": {
    "timestamp": 1748280294,
    "mac_address": "aa:bb:cc:dd:ee:ff",
    "pnm_test_type": "DS_OFDM_RXMER_PER_SUBCAR",
    "filename": "ds_ofdm_rxmer_per_subcar_aa:bb:cc:dd:ee:ff_34_1748280294.bin",
    "device_details": {
      "sys_descr": {
        "HW_REV": "1.0",
        "VENDOR": "LANCity",
        "BOOTR": "NONE",
        "SW_REV": "1.0.0.0",
        "MODEL": "LCPET-3"
      }
    }
  }
}
```

* **Key**: Operation ID (`2ee6138bbc1b3c3d`).
* **Fields**:

  * `timestamp`: Unix epoch of capture.
  * `pnm_test_type`: PNM measurement type identifier.
  * `filename`: Name of the TFTP-uploaded file in `data/pnm`.
  * `device_details.sys_descr`: Cable modem metadata for context.

> **Tip:** Use the manifest for automated, real-time data pipelines and dashboards without manual directory scanning.
