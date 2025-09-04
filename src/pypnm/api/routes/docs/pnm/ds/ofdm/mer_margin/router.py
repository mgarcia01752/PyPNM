
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from ipaddress import ip_interface
import logging
from typing import Dict, List, Union
from fastapi import APIRouter
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
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(f"RxMerMarginRouter.{self.base_endpoint}")

        self._add_routes()

    def _add_routes(self):
        
        @self.router.post(f"/{self.base_endpoint}/getMeasurementTemplate", 
                          response_model=Union[SnmpResponse])
        async def get_measurement_template(request: PnmRequest) -> Union[SnmpResponse]:
            """
            📘 [API Guide - MER Margin Measurement Template](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/mer-margin.md#get-measurement-template)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving MER Margin measurement template for MAC: {mac}, IP: {ip}")

            cm = CableModem(mac_address=MacAddress(mac),inet=Inet(ip))

            status, msg = await CableModemServicePreCheck(cable_modem=cm,validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(mac),
                    status=status, message=msg)

            service = CmDsOfdmMerMarginService(cm)
            template:Dict[str, List[Dict]] = await service.getMeasurementTemplate()

            return SnmpResponse(
                mac_address=str(mac),
                status=ServiceStatusCode.SUCCESS,
                message="MER Margin test triggered successfully",
                results=template)
                
        @self.router.post(f"/{self.base_endpoint}/getMeasurement", 
                          response_model=Union[SnmpResponse])
        async def get_measurement(request: PnmMerMarginRequest) -> Union[SnmpResponse]:
            """
            Initiates a MER Margin test on a specified OFDM channel/profile.

            Triggers the modem to calculate MER margin statistics against a given modulation profile.
            This test measures subcarrier MER against required profile thresholds and computes available MER margin.

            [API Guide - MER Margin Measurement](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/mer-margin.md#get-measurement)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Initiating MER Margin measurement for MAC: {mac}, IP: {ip}, Profile ID: {request.mer_margin.profile_id}")            

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))

            status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(mac),
                    status=status, message=msg)

            service = CmDsOfdmMerMarginService(cm)
            await service.set(request.mer_margin)

            return SnmpResponse(
                mac_address=str(request.cable_modem.mac_address),
                status=ServiceStatusCode.SUCCESS,
                message="MER Margin test triggered successfully")

        @self.router.post(f"/{self.base_endpoint}/getAnalysis", 
                          response_model=Union[PnmAnalysisResponse, SnmpResponse])
        async def get_analysis(request: PnmMerMarginRequest):
            """
            Retrieves the MER Margin analysis results from the cable modem.

            This endpoint provides values for:
            - Measured Average MER
            - Required Average MER
            - Number of subcarriers below threshold
            - MER Margin (dB)

            [API Guide - MER Margin Analysis](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/mer-margin.md#get-analysis)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving MER Margin analysis for MAC: {mac}, IP: {ip}, Profile ID: {request.mer_margin.profile_id}")

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))

            status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac),status=status, message=msg)

            service = CmDsOfdmMerMarginService(cm)
            return await service.get_analysis()

        @self.router.post(f"/{self.base_endpoint}/getMeasurementStatistics", 
                          response_model=Union[SnmpResponse])
        async def get_measurement_statistics(request: PnmRequest):
            """
            Returns current MER Margin measurement configuration and status.

            This includes:
            - Trigger status
            - Profile ID and threshold configuration
            - Measurement enable flag
            - Symbol averaging parameters

            [API Guide - MER Margin Measurement Configuration and Status](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/mer-margin.md#get-measurement-statistics)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Fetching MER Margin measurement statistics for MAC: {mac}, IP: {ip}")            

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))

            status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()

            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(
                    mac_address=str(mac),
                    status=status, message=msg)

            service = CmDsOfdmMerMarginService(cm)
            results = await service.getMeasurementStatus()

            return SnmpResponse(
                mac_address=str(mac),
                status=ServiceStatusCode.SUCCESS,
                message="Measurement Statistics for MER Margin",
                results=results)

# Required for dynamic auto-registration
router = RxMerMarginRouter().router
