# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import sys
import pathlib
import logging
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pypnm.api.utils.auto_load import auto_register_routers

project_root = pathlib.Path(__file__).resolve()
while project_root.name != "src" and project_root != project_root.parent:
    project_root = project_root.parent

if project_root.name == "src" and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# --- 🚀 FastAPI App Initialization ---
app = FastAPI(
    title="PyPNM REST API",
    version="1.0.0",
    summary="Proactive Network Maintenance API for DOCSIS devices.",
    description=(
        "Python-based RESTful API to access, analyze, and visualize DOCSIS telemetry data.\n\n"
        "[PyPNM GitHub](https://github.com/mgarcia01752/PyPNM)"
    ),
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(GZipMiddleware, minimum_size=100_000)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🔍 Auto-Register All Routers ---
auto_register_routers(app)
