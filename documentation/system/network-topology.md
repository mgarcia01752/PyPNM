# PyPNM Network Topology and Usage Models

This document outlines common deployment topologies for PyPNM (Proactive Network Maintenance) and explains how PyPNM retrieves and processes PNM data from cable modems (CMs).

## 📑 Table of Contents

1. [Standalone Deployment](#1-standalone-deployment)
2. [Spoke-and-Wheel Deployment](#2-spoke-and-wheel-deployment)
3. [Protocols & Connectivity](#protocols--connectivity)
4. [Summary of Usage Models](#summary-of-usage-models)

## 1. Standalone Deployment

In a standalone deployment, a single PyPNM server handles SNMP polling and file retrieval without intermediate file-relay agents.

### 🧩 Components

- **PyPNM Server**
  - Hosts the FastAPI backend, analysis engine, and optional UI.
  - Performs SNMP SET/GET operations to CMs.
  - Runs a local TFTP server to receive PNM files.
  - Stores raw and parsed data in `/data/pnm/` and `/data/db/`.

- **Cable Modem (CM)**
  - DOCSIS 3.0/3.1 with PNM MIB support.
  - Sends SNMP responses and uploads files to TFTP root (`/var/tftpboot/pnm/`).

- **CMTS / CCAP**
  - Issues SNMP triggers and provides the TFTP server IP to the CM.

### 🔁 Data Flow

1. **Trigger Measurement**

   ```text
   Operator/API ──▶ PyPNM ──(SNMP SET)──▶ CM
   ```
   * PyPNM calls SNMP SET to initiate the measurement (e.g., spectrum, histogram).

2. **Measurement & File Upload**

   ```text
   CM ──(TFTP PUT)──▶ PyPNM TFTP Server
   ```
   * CM runs the measurement and uploads the result.

3. **Polling for Completion**

   ```text
   PyPNM ──(SNMP GET)──▶ CM
   ```
   * PyPNM checks the CM’s state OIDs to determine when data is ready.

4. **File Retrieval & Parsing**
   * PyPNM reads from the TFTP directory, extracts frequency bins, MER, taps, etc.

5. **Visualization & Alerts**
   * Results are visualized in dashboards; alerts may be generated.

> **🖼️ Diagram Placeholder:** Standalone system with PyPNM + CM + TFTP

## 2. Spoke-and-Wheel Deployment

A central PyPNM server (hub) manages remote CMs at various sites (spokes) and fetches completed PNM files via network file-transfer.

### 🧩 Components

- **Hub (PyPNM Central Server)**
  - Connects via SNMP to all CMs.
  - Uses TFTP, FTP, SFTP, SCP, or HTTP to fetch PNM files from remote sites.

- **Spoke (Remote Site)**
  - Contains a TFTP server receiving CM uploads.
  - Exposes the file directory for PyPNM retrieval.

- **PyPNM Retrieval Engine**
  - Supports: TFTP, FTP/FTPS, SFTP/SCP, HTTP(S)
  - Downloads and organizes files under `/data/pnm/{site}/{cm-mac}/`

### 🔁 Data Flow

1. **Trigger Measurement**

   ```text
   Operator/API ──▶ PyPNM ──(SNMP SET)──▶ CM
   ```

2. **CM Uploads to Spoke TFTP**

   ```text
   CM ──(TFTP PUT)──▶ Spoke TFTP Server
   ```

3. **Remote Retrieval**

   ```text
   PyPNM ──(TFTP/SFTP/FTP/HTTP)──▶ Spoke Server
   ```

4. **Parse & Visualize**
   * Files are parsed, stored, and visualized as in standalone mode.

> **🖼️ Diagram Placeholder:** Hub connected to multiple remote sites

## Protocols & Connectivity

- **SNMP** (v2c/v3): Used to trigger measurements and read completion status.
- **File Transfer**:
  - **TFTP (UDP/69)**: Default protocol used by CMs.
  - **FTP/SFTP/SCP/HTTP**: Used by PyPNM to pull files from spokes.
- **Security Tips**:
  - Use SNMPv3 or isolate SNMPv2c in management VLANs.
  - Use SFTP or HTTPS for secure file transfers.

## Summary of Usage Models

| Model              | SNMP Path     | Upload Target           | Retrieval Method          | Notes                                       |
|-------------------|---------------|--------------------------|---------------------------|---------------------------------------------|
| **Standalone**    | PyPNM → CM    | Local TFTP (same box)    | Local read                | Simplified, all-in-one system.              |
| **Spoke-and-Wheel**| PyPNM → CM    | Remote TFTP at site      | Remote fetch via protocols| Scalable, centralized control.              |
