# PyPNM Network Topology and Usage Models

This document describes two common deployment topologies for PyPNM (Proactive Network Maintenance) and how PyPNM retrieves PNM (Proactive Network Maintenance) data from cable modems (CMs).

---

## Table of Contents

1. [Standalone Deployment](#standalone-deployment)  
2. [Spoke-and-Wheel Deployment](#spoke-and-wheel-deployment)

---

## 1. Standalone Deployment

In a standalone setup, a single PyPNM server handles both SNMP polling and PNM file retrieval without any intermediate agents.

### Components

- **PyPNM Server**  
  - Hosts the FastAPI backend, analysis engine, and (optional) web UI.  
  - Listens on UDP/161 for SNMP GET/SET to each CM.  
  - Runs a local file‐transfer service (typically TFTP) for CMs to upload PNM files.  
  - Stores raw and parsed PNM data under `/data/pnm/` and `/data/db/`.

- **Cable Modem (CM)**  
  - Supports DOCSIS 3.0 or DOCSIS 3.1 with PNM MIB extensions (spectrum, RxMER histogram, equalizer taps).  
  - Configured (via CMTS or DHCP) to send PNM files to the PyPNM server’s TFTP root directory (e.g., `/var/tftpboot/pnm/`).  
  - Responds to SNMP SET (to trigger measurement) and SNMP GET (to report status).

- **CMTS / CCAP**  
  - Issues PNM measurement commands to the CM (via SNMP SET).  
  - Provides TFTP server address to CM (through provisioning OID or DHCP).  

### Data Flow

1. **Trigger Measurement**  
   ```text
   Operator/API Client ──▶ PyPNM Server ──(SNMP SET)──▶ CM
````

* The operator (or automation) calls PyPNM’s REST endpoint (e.g., `POST /pnm/spectrum/start`).
* PyPNM issues `docsIf3CmSpectrumAnalysisTrigger` (DOCSIS 3.1 MIB) or `docsIfCmDsHistogramTrigger` (DOCSIS 3.0) as an SNMP SET to the CM.

2. **Measurement Execution & Upload**

   ```text
   CM ──(Measurement)──▶ (Stores data internally)  
   CM ──(TFTP PUT)──▶ PyPNM Server’s TFTP directory (/var/tftpboot/pnm/)
   ```

   * CM completes the spectrum/histogram measurement.
   * Once done, CM uploads the raw PNM file (binary or ASCII) via TFTP to the PyPNM server.

3. **SNMP Poll for Completion**

   ```text
   PyPNM Server ──(SNMP GET)──▶ CM
   ```

   * PyPNM polls `docsIf3CmSpectrumAnalysisMeasState` or `docsIf3CmSpectrumAnalysisMeasAmplitudeDataPresent`.
   * When “data ready” is signaled, PyPNM proceeds to file retrieval (if small metadata is fetched via SNMP GET).

4. **File Retrieval & Parsing**

   * PyPNM reads the uploaded file from its local TFTP folder.
   * Parsing modules (e.g., `CmSpectrumAnalysis`, `CmDsHistogramService`) extract frequency bins, amplitudes, MER buckets, equalizer taps, etc.
   * Parsed results are stored/share under `/data/db/` and visualizations (heatmaps, line graphs) are placed under `/output/`.

5. **Visualization & Alerts**

   * Operators view results in the PyPNM UI or dashboards.
   * Threshold violations (e.g., MER < 30 dB) generate alerts (email, SNMP traps, or webhooks).

> **Diagram Placeholder:**
> *(Standalone Deployment showing PyPNM server, SNMP link, CM, and TFTP service)*

---

## 2. Spoke-and-Wheel Deployment

In a spoke-and-wheel topology, a central PyPNM server (hub) remotely pulls PNM files from multiple TFTP servers at remote sites (spokes). There is no intermediary agent—PyPNM directly connects to each spoke to fetch completed files.

### Components

* **Hub (Central PyPNM Server)**

  * Hosts FastAPI backend, analysis engine, and (optional) UI.
  * Maintains SNMP connectivity (UDP/161) to every CM across sites.
  * Periodically polls each CM for PNM status and then pulls finished files from remote TFTP servers using TFTP, FTP, SFTP, or SCP.
  * Stores raw PNM files under `/data/pnm/{site}/{cm-mac}/` and parsed data under `/data/db/`.

* **Spoke (Remote TFTP Server)**

  * Deployed at each distribution hub or regional POP.
  * Receives PNM files from local CMs via TFTP (UDP/69).
  * Exposes a shared directory (e.g., `/var/tftpboot/pnm/`) where completed PNM files reside.
  * May also expose FTP, SFTP, or HTTP(S) endpoints for secure file retrieval.

* **PyPNM Remote Connect**

  * PyPNM’s retrieval subsystem runs fetch operations over:

    * **TFTP** (UDP/69)
    * **FTP / FTPS** (TCP/21, optionally TLS)
    * **SFTP / SCP** (SSH over TCP/22)
    * **HTTP(S)** (TCP/80/443)
  * Pulls files into `/data/pnm/{site}/{cm-mac}/`.

### Data Flow

1. **Trigger Measurement**

   ```text
   Operator/API Client ──▶ PyPNM Server ──(SNMP SET)──▶ CM
   ```

   * PyPNM calls `docsIf3CmSpectrumAnalysisTrigger` (or equivalent) on each CM.

2. **Local Upload (Spoke)**

   ```text
   CM ──(TFTP PUT)──▶ Spoke TFTP Server (/var/tftpboot/pnm/)
   ```

   * After measurement, CM uploads the PNM file to the nearest TFTP server at its local site.

3. **Remote Collection (PyPNM Fetch)**

   ```text
   PyPNM Server ──(TFTP/FTP/SFTP/SCP)──▶ Spoke TFTP Server
   ```

   * PyPNM polls each CM’s status OID (e.g., `docsIf3CmSpectrumAnalysisMeasState`) until “data ready.”
   * When ready, PyPNM launches a file‐transfer session to fetch the PNM file:

     1. **TFTP**: Direct TFTP GET from the spoke’s `/var/tftpboot/pnm/`.
     2. **FTP/FTPS**: If the spoke runs an FTP server, PyPNM logs in and downloads the file.
     3. **SFTP/SCP**: If SSH‐based file transfer is enabled, PyPNM uses key‐based or password authentication to copy files.
     4. **HTTP(S)**: If the spoke serves files via HTTP(S), PyPNM performs an HTTP GET.
   * Downloaded files are saved under `/data/pnm/{site}/{cm-mac}/` (e.g., `/data/pnm/NYC-POP-01/aa:bb:cc:dd:ee:ff/`).

4. **File Parsing & Storage**

   * Parsed data (frequency/amplitude, MER histogram buckets, equalizer tap coefficients) is written to `/data/db/{site}/{cm-mac}/`.
   * Visual outputs (heatmaps, line plots, histograms) are generated and saved under `/output/{site}/{cm-mac}/`.
   * Anomalies trigger alerts via email, SNMP trap, or webhook.

> **Diagram Placeholder:**
> *(Spoke-and-Wheel topology showing PyPNM hub, SNMP links to CMs, and TFTP servers at remote sites)*

---

## Protocols & Connectivity

* **SNMP (RFC 3411–3418)**

  * Use **SNMPv3** when possible (authentication/encryption). If SNMPv2c is used, confine it to a trusted management VLAN.
  * Key OIDs for DOCSIS 3.1 PNM:

    * `docsIf3CmSpectrumAnalysisTrigger` (SET)
    * `docsIf3CmSpectrumAnalysisMeasState` (GET)
    * `docsIf3CmSpectrumAnalysisMeasAmplitudeDataPresent` (GET)
  * Key OIDs for DOCSIS 3.0 RxMER histogram:

    * `docsIfCmDsHistogramTrigger`, `docsIfCmDsHistogramState`, etc.

* **File-Transfer Protocols**

  * **TFTP (RFC 1350)**: Default for cable modems. Unencrypted, UDP/69.
  * **FTP/FTPS (RFC 959 + TLS)**: Legacy; FTPS adds encryption.
  * **SFTP/SCP (SSH)**: Secure, uses SSH over TCP/22.
  * **HTTP(S) (RFC 7230–7235)**: Use HTTPS with valid TLS certificates for secure retrieval.

* **Network Access**

  * Hub must reach each CM on UDP/161 (SNMP) and each spoke on the chosen file‐transfer port (UDP/69 for TFTP, TCP/22 for SFTP, etc.).
  * Firewalls between hub and spokes should allow only the necessary ports and source IP (PyPNM server) to connect.

---

## Summary of Usage Models

| Deployment Model    | SNMP Polling | PNM File Upload Location     | File-Retrieval Method       | Comments                                       |
| ------------------- | ------------ | ---------------------------- | --------------------------- | ---------------------------------------------- |
| **Standalone**      | Hub → CM     | PyPNM Server’s local TFTP    | Local TFTP GET (same box)   | Simplest: one server does everything.          |
| **Spoke-and-Wheel** | Hub → CM     | Remote TFTP servers (spokes) | Hub pulls via TFTP/FTP/SFTP | Scales to multiple sites; hub aggregates data. |

---

> **Note:**
>
> * Ensure all SNMP traffic (especially SNMPv2c community strings) is confined to a secure management VLAN.
> * If using FTP or HTTP(S) for file retrieval, enforce strong authentication and TLS.
> * Use consistent naming conventions: include `site ID`, `CM MAC`, and `timestamp` in PNM filenames (e.g., `spectrum_aa_bb_cc_dd_ee_ff_20250604_151230.bin`).
> * Store files under a hierarchical path:
>
>   ```
>   /data/pnm/{site}/{cm-mac}/raw/
>   /data/db/{site}/{cm-mac}/parsed/
>   /output/{site}/{cm-mac}/visuals/
>   ```

```
```
