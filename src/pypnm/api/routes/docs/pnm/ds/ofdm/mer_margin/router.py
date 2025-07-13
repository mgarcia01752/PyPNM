# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Union
from fastapi import APIRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.router import PnmFastApiRouter
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import (
    PnmAnalysisResponse, PnmRequest)
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.mer_margin.schemas import PnmMerMarginRequest
from pypnm.api.routes.docs.pnm.ds.ofdm.mer_margin.service import CmDsOfdmMerMarginService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class RxMerMarginRouter:
    """
    FastAPI Router for DOCSIS 3.1 Downstream OFDM MER Margin operations.

    This router handles the following operations for MER Margin:
    - Triggering measurement (`getMeasurement`)
    - Fetching measurement results (`getAnalysis`)
    - Fetching measurement configuration/status (`getMeasurementStatistics`)
    """

    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        tags = ["PNM Operations - Downstream OFDM MER Margin"]
        self.base_endpoint = "merMargin"

        self.router = APIRouter(prefix=prefix, tags=tags)  # type: ignore
        self.logger = logging.getLogger(f"RxMerMarginRouter.{self.base_endpoint}")

        self._add_routes()

    def _add_routes(self):
        @self.router.post(f"/{self.base_endpoint}/getMeasurement", response_model=Union[SnmpResponse])
        async def get_measurement(request: PnmMerMarginRequest) -> Union[SnmpResponse]:
            """
            🎯 Initiates a MER Margin test on a specified OFDM channel/profile.

            Triggers the modem to calculate MER margin statistics against a given modulation profile.
            This test measures subcarrier MER against required profile thresholds and computes available MER margin.

            📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/mer-margin.md#getmeasurement)
            """
            self.logger.info(f"Retrieving MER Margin measurement for MAC: {request.mac_address}")

            cm = CableModem(mac_address=MacAddress(request.mac_address), inet=Inet(request.ip_address))

            status, msg = await CableModemServicePreCheck(
                cable_modem=cm,
                validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status, message=msg)

            service = CmDsOfdmMerMarginService(cm)
            await service.set(request.mer_margin)

            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=ServiceStatusCode.SUCCESS,
                message="MER Margin test triggered successfully")

        @self.router.post(f"/{self.base_endpoint}/getAnalysis", response_model=Union[PnmAnalysisResponse, SnmpResponse])
        async def get_analysis(request: PnmMerMarginRequest):
            """
            📊 Retrieves the MER Margin analysis results from the cable modem.

            This endpoint provides values for:
            - Measured Average MER
            - Required Average MER
            - Number of subcarriers below threshold
            - MER Margin (dB)

            📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/mer-margin.md#getanalysis)
            """
            self.logger.info(f"Retrieving MER Margin analysis for MAC: {request.mac_address}")

            cm = CableModem(mac_address=MacAddress(request.mac_address), inet=Inet(request.ip_address))

            status, msg = await CableModemServicePreCheck(
                cable_modem=cm,
                validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status, message=msg)

            service = CmDsOfdmMerMarginService(cm)
            return await service.get_analysis()

        @self.router.post(f"/{self.base_endpoint}/getMeasurementStatistics", response_model=Union[SnmpResponse])
        async def get_statistics(request: PnmRequest):
            """
            📋 Returns current MER Margin measurement configuration and status.

            This includes:
            - Trigger status
            - Profile ID and threshold configuration
            - Measurement enable flag
            - Symbol averaging parameters

            📘 [API Guide](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/mer-margin.md#getmeasurementstatistics)
            """
            self.logger.info(f"Fetching MER Margin measurement statistics for MAC: {request.mac_address}")

            cm = CableModem(mac_address=MacAddress(request.mac_address), inet=Inet(request.ip_address))

            status, msg = await CableModemServicePreCheck(
                cable_modem=cm,
                validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(request.mac_address),
                    status=status, message=msg)

            service = CmDsOfdmMerMarginService(cm)
            results = await service.get()

            return SnmpResponse(
                mac_address=str(request.mac_address),
                status=ServiceStatusCode.SUCCESS,
                message="Measurement Statistics for MER Margin",
                results=results)


# ✅ Required for dynamic auto-registration
router = RxMerMarginRouter().router
