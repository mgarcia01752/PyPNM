# PyPNM Network Topology and Usage Models

This document outlines common deployment topologies for PyPNM (Proactive Network Maintenance) and explains how PyPNM retrieves and processes PNM data from cable modems (CMs).

## Table of Contents

1. [Standalone Deployment](#1-standalone-deployment)
2. [Hub-and-Spoke Deployment](#2-hub-and-spoke-deployment)
3. [Protocols & Connectivity](#protocols--connectivity)
4. [Summary of Usage Models](#summary-of-usage-models)

## 1. Standalone Deployment

A single PyPNM host performs SNMP control and file retrieval. No intermediate file-relay services are required.

### Components

* **PyPNM Server**

  * Runs the FastAPI backend, analysis engine, and optional UI.
  * Performs SNMP GET/SET/WALK operations to CMs.
  * Can host a local TFTP service to receive PNM files.
  * Persists raw and derived artifacts under `.data/` (e.g., `.data/pnm/`, `.data/db/`).

* **Cable Modem (CM)**

  * DOCSIS 3.0/3.1 with PNM MIB support.
  * Responds to SNMP; uploads PNM files to the configured TFTP server.

* **CMTS / CCAP**

  * Provides RF plant and CM management connectivity.
  * (Optional) Supplies the TFTP server address via config provisioning.

### Data Flow

1. **Trigger measurement**

```
Operator/API --> PyPNM --(SNMP SET)--> CM
```

2. **Measurement & upload**

```
CM --(TFTP PUT)--> PyPNM (local TFTP)
```

3. **Completion polling**

```
PyPNM --(SNMP GET)--> CM (status OIDs)
```

4. **File ingest & parsing**

* PyPNM ingests files from the TFTP directory and parses payloads (e.g., RxMER, constellation, histograms).

5. **Visualization & alerts**

* Results are written to `.data/` subdirectories and surfaced via API/UI; alerting may be applied.

> Diagram placeholder: Single host (PyPNM) with CM and local TFTP.

## 2. Hub-and-Spoke Deployment

A central PyPNM server (hub) manages many remote sites (spokes). CMs at each site upload to a local file endpoint (typically TFTP). PyPNM fetches completed files over the WAN.

### Components

* **Hub (Central PyPNM)**

  * Issues SNMP control to all CMs across sites.
  * Retrieves PNM files from spoke file servers using TFTP, FTP/FTPS, SFTP/SCP, or HTTP(S).
  * Normalizes storage under `.data/pnm/{site}/{cm-mac}/`.

* **Spoke (Remote Site)**

  * Runs a TFTP (or equivalent) endpoint receiving CM uploads.
  * Exposes a network-accessible directory for PyPNM retrieval.

* **Retrieval Engine (PyPNM)**

  * Configurable per site/protocol (see system configuration).
  * Handles retries, timeouts, and directory placement.

### Data Flow

1. **Trigger measurement**

```
Operator/API --> PyPNM --(SNMP SET)--> CM (remote site)
```

2. **CM uploads to spoke file server**

```
CM --(TFTP PUT)--> Spoke TFTP
```

3. **Remote retrieval (hub pulls)**

```
PyPNM --(TFTP/SFTP/FTP/HTTP)--> Spoke
```

4. **Parse & visualize**

* Processing and visualization mirror the standalone model, but with site-scoped storage.

> Diagram placeholder: Central hub connected to multiple spokes (sites).

## Protocols & Connectivity

* **SNMP (v2c/v3)**

  * Control plane for measurements (start/stop/status) and telemetry reads.
  * Typical ports: UDP 161 (queries), UDP 162 (traps if used).

* **File transfer (data plane)**

  * **TFTP (UDP/69)**: Default CM upload path defined by DOCSIS PNM workflows.
  * **FTP/FTPS (TCP/21)**, **SFTP/SCP (TCP/22)**, **HTTP (TCP/80)**, **HTTPS (TCP/443)**: Pull methods PyPNM can use to fetch files from spokes.

* **Security guidance**

  * Prefer SNMPv3 where available; if using v2c, isolate on a management VLAN and restrict by ACL.
  * Use SFTP/HTTPS for WAN retrieval where possible.
  * Restrict TFTP exposure to internal segments and validate upload paths.

## Summary of Usage Models

| Model         | SNMP Path  | Upload Target          | Retrieval Method          | Characteristics                          |
| ------------- | ---------- | ---------------------- | ------------------------- | ---------------------------------------- |
| Standalone    | PyPNM → CM | Local TFTP (same host) | Local file ingest         | Simple, minimal moving parts.            |
| Hub-and-Spoke | PyPNM → CM | Spoke site file server | TFTP/FTP/SFTP/SCP/HTTP(S) | Scales across sites; centralized control |
