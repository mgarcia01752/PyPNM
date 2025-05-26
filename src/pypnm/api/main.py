# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from api.utils.auto_load import auto_register_routers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title="PyPNM REST API",
    summary="Proactive Network Maintenance API for DOCSIS devices.",
    description="Python-based RESTful API to access, analyze, and visualize DOCSIS telemetry data.\n\n[PyPNM GitHub](https://github.com/mgarcia01752/PyPNM)",
    version="1.0.0"
)

app.add_middleware(GZipMiddleware, minimum_size=100_000)

# 🚀 Automatically include all routers
auto_register_routers(app)
