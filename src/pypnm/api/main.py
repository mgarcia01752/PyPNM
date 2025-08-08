# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import sys
import pathlib
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pypnm.api.utils.auto_load import RouterRegistrar
from pypnm.startup.startup import StartUp

project_root = pathlib.Path(__file__).resolve()
while project_root.name != "src" and project_root != project_root.parent:
    project_root = project_root.parent

if project_root.name == "src" and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

StartUp.initialize()

fast_api_description = """
**Proactive Network Maintenance (PNM) API for DOCSIS devices**

Python-based RESTful API for accessing, analyzing, and visualizing DOCSIS 3.1/4.0 PNM telemetry.

**PyPNM provides structured endpoints for:**
- Downstream and upstream OFDM/OFDMA diagnostics
- OFDM RxMER and Channel Estimation Analysis
- Modulation profile decoding and traffic stats
- FEC summary and profile-specific correction metrics
- Spectrum capture, constellation display, and pre-equalization
- TFTP/SNMP-based file retrieval and modem polling

Designed for integration into dashboards, automation pipelines, and engineering tools to assist with plant health monitoring, anomaly detection, and DOCSIS signal quality evaluation.

🔗 [**GitHub - PyPNM**](https://github.com/mgarcia01752/PyPNM)
"""

app = FastAPI(
    title="PyPNM REST API",
    version="0.1.0",
    description=fast_api_description,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",)

app.add_middleware(GZipMiddleware, minimum_size=100_000)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],)

RouterRegistrar().register(app)
