
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

__skip_autoregister__ = True

from enum import Enum
import logging
from abc import ABC, abstractmethod
from typing import List
from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.schema.base_connect_request import BaseDeviceConnectRequest
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import (
    SnmpAnalysisRequest, SnmpAnalysisResponse, SnmpResponse)

class SnmpFastApiRouter(ABC):
    """
    Abstract base router class for defining standardized FastAPI endpoints related to 
    Proactive Network Maintenance (PNM).

    Subclasses must implement core logic for:
    - get_measurement_logic
    - get_analysis_logic
    """

    def __init__(self, prefix: str, tags: List[str|Enum], base_endpoint: str):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{base_endpoint}")
        self._base_endpoint = base_endpoint.strip("/")
        self._add_routes()

    def _add_routes(self):
        @self.router.post(f"/{self._base_endpoint}/getMeasurement", response_model=SnmpResponse)
        async def get_measurement(request: BaseDeviceConnectRequest):
            try:
                return await self.get_measurement_logic(request)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurement] Error for MAC {request.cable_modem.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")

        @self.router.post(f"/{self._base_endpoint}/getAnalysis", response_model=SnmpAnalysisResponse)
        async def get_analysis(request: SnmpAnalysisRequest):
            try:
                return await self.get_analysis_logic(request)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getPlot] Error for MAC {request.cable_modem.mac_address}")
                raise HTTPException(status_code=500, detail=f"Plot retrieval failed: {str(e)}")

    @abstractmethod
    async def get_measurement_logic(self, request: BaseDeviceConnectRequest) -> SnmpResponse:
        """Subclasses must implement this to provide measurement data.
        
        Example:
        
        self.logger.info(f"Retrieving RxMER measurement for MAC {request.cable_modem.mac_address}")
        
        data = {
            "measurement": [35.2, 34.8, 36.0],  # Example RxMER values in dB
        }
        return PnmMeasurementResponse(status=ServiceStatusCode.SUCCESS, 
                                      mac_address=MacAddress(request.cable_modem.mac_address), 
                                      measurement=data)
        
        """
        pass

    @abstractmethod
    async def get_analysis_logic(self, request: SnmpAnalysisRequest) -> SnmpAnalysisResponse:
        """Subclasses must implement this to provide plotting data.
        
        Example:
        
        self.logger.info(f"Generating RxMER plot data for MAC {request.cable_modem.mac_address}")
        
        # Placeholder plotting data
        plot_data = {
            "labels": ["SC0", "SC1", "SC2"],
            "values": [35.2, 34.8, 36.0]
        }
        return PnmPlotResponse(status=ServiceStatusCode.SUCCESS, 
                               mac_address=MacAddress(request.cable_modem.mac_address), 
                               plot_data=plot_data)      
        
        """
        pass
