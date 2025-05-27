# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
import logging
from abc import ABC, abstractmethod
from typing import List, Union
from fastapi import APIRouter, HTTPException

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisRequest, PnmAnalysisResponse, PnmMeasurementResponse, PnmRequest
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse


class BaseFastApiRouter(ABC):

    def __init__(self, prefix: str, tags: List[str|Enum], base_endpoint: str):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{base_endpoint}")
        self.base_endpoint = base_endpoint.strip("/")

class PnmFastApiRouter(ABC):
    """
    Abstract base router class for defining standardized FastAPI endpoints related to 
    Proactive Network Maintenance (PNM).

    Subclasses must implement core logic for:
    - get_measurement_logic
    - get_files_logic
    - get_analysis_logic
    """

    def __init__(self, prefix: str, tags: List[str|Enum], base_endpoint: str):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{base_endpoint}")
        self._base_endpoint = base_endpoint.strip("/")
        self._add_routes()

    def _add_routes(self):
        @self.router.post(f"/{self._base_endpoint}/getMeasurement", response_model=Union[PnmMeasurementResponse, SnmpResponse])
        async def get_measurement(request: PnmRequest):
            try:
                return await self.get_measurement_logic(request)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurement] Error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")

        @self.router.post(f"/{self._base_endpoint}/getAnalysis", response_model=Union[PnmAnalysisResponse, SnmpResponse], response_model_exclude_unset=True)
        async def get_analysis(request: PnmAnalysisRequest):
            try:
                return await self.get_analysis_logic(request)
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getPlot] Error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Plot retrieval failed: {str(e)}")

    @abstractmethod
    async def get_measurement_logic(self, request: PnmRequest) -> Union[PnmMeasurementResponse, SnmpResponse]:
        """Subclasses must implement this to provide measurement data.
        
        Example:
        
        self.logger.info(f"Retrieving RxMER measurement for MAC {request.mac_address}")
        
        data = {
            "measurement": [35.2, 34.8, 36.0],  # Example RxMER values in dB
        }
        return PnmMeasurementResponse(status=ServiceStatusCode.SUCCESS, 
                                      mac_address=MacAddress(request.mac_address), 
                                      measurement=data)
        
        """
        pass

    @abstractmethod
    async def get_analysis_logic(self, request: PnmAnalysisRequest) -> Union[PnmAnalysisResponse, SnmpResponse]:
        """Subclasses must implement this to provide plotting data.
        
        Example:
        
        self.logger.info(f"Generating RxMER plot data for MAC {request.mac_address}")
        
        # Placeholder plotting data
        plot_data = {
            "labels": ["SC0", "SC1", "SC2"],
            "values": [35.2, 34.8, 36.0]
        }
        return PnmPlotResponse(status=ServiceStatusCode.SUCCESS, 
                               mac_address=MacAddress(request.mac_address), 
                               plot_data=plot_data)      
        
        """
        pass
