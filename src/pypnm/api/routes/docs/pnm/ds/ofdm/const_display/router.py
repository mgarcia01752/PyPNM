# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pathlib import Path
from typing import List, Union, cast

from fastapi import APIRouter, HTTPException

from pypnm.api.routes.basic.abstract.analysis_report import Analysis
from pypnm.api.routes.basic.constellation_display_analysis_report import ConstellationDisplayReport
from pypnm.api.routes.common.classes.analysis.analysis import AnalysisType
from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmAnalysisRequest, PnmAnalysisResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.const_display.schemas import PnmConstellationDisplayAnalysisRequest, PnmConstellationDisplayRequest, PnmConstellationDisplayResponse
from pypnm.api.routes.docs.pnm.ds.ofdm.const_display.service import CmDsOfdmConstDisplayService
from pypnm.api.routes.docs.pnm.files.service import FileType, PnmFileService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import PathLike


class ConstellationDisplayRouter:
    """
    Router implementation for handling DOCSIS 3.1 Downstream OFDM Constellation Display
    Proactive Network Maintenance (PNM) requests.

    This router provides a POST endpoint to trigger SNMP-based measurement collection
    from a target cable modem and return the processed constellation display data.
    """

    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        tags: List[str] = ["PNM Operations - Downstream OFDM Constellation Display"]
        self.base_endpoint = "/constellationDisplay"

        self.base_endpoint = self.base_endpoint.strip("/")
        self.router = APIRouter(prefix=prefix, tags=tags) # type: ignore
        self.logger = logging.getLogger(f"ConstellationDisplayRouter.{self.base_endpoint}")
        self._add_routes()
        
    def _add_routes(self):

        @self.router.post(f"/{self.base_endpoint}/getMeasurement", 
                          response_model=Union[PnmConstellationDisplayResponse,SnmpResponse])
        async def get_measurement(request: PnmConstellationDisplayRequest) -> Union[PnmConstellationDisplayResponse, SnmpResponse]:
            """
            **Capture Downstream OFDM Constellation Symbols**

            This endpoint retrieves complex I/Q sample data from a DOCSIS cable modem for visualizing
            downstream OFDM constellation displays. Ideal for modulation quality analysis and signal
            impairment diagnostics. Each response includes metadata and I/Q values per OFDM channel.

            ⚠️ Due to large payloads, it is recommended to use Postman or CLI tools (e.g., `curl`) rather than SwaggerUI.

            [API Guide - Capture Downstream OFDM Constellation Symbol](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/ofdm/constellation-display.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Starting Constellation Display measurement for MAC: {mac}, IP: {ip}, Modulation Order Offset: {request.modulation_order_offset}, Number of Sample Symbols: {request.number_sample_symbol}")

            try:
                cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
                
                status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(mac_address=str(mac), status=status, message=msg)                    
                
                modulation_order_offset = request.capture_settings.modulation_order_offset
                number_sample_symbol = request.capture_settings.number_sample_symbol

                service = CmDsOfdmConstDisplayService(
                    cable_modem=cm,
                    modulation_order_offset=modulation_order_offset,
                    number_sample_symbol=number_sample_symbol,)
                
                msg_rsp: MessageResponse = await service.set_and_go()

                if msg_rsp.status != ServiceStatusCode.SUCCESS:
                    self.logger.error(
                        f"[getMeasurement] Constellation Display failed with status: {msg_rsp.status.name}")
                    raise HTTPException(status_code=500, detail="Constellation Display SNMP execution failed")

                cps = CommonProcessService(msg_rsp)
                msg_rsp = cps.process()
                                
                return PnmConstellationDisplayResponse(
                    mac_address=request.cable_modem.mac_address,
                    status=msg_rsp.status,
                    data=msg_rsp.payload_to_dict(),)

            except HTTPException:
                raise

            except Exception as e:
                self.logger.exception(f"[getMeasurement] Error for MAC {request.cable_modem.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")

        @self.router.post(f"/{self.base_endpoint}/getAnalysis", 
                          response_model=Union[PnmAnalysisResponse, SnmpResponse])
        async def get_analysis(request: PnmConstellationDisplayAnalysisRequest):
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving Constellation Display Analysis for MAC: {mac}, IP: {ip}, Analysis Type: {request.analysis.type}")

            cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
            
            status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac), status=status, message=msg)
                         
            try:
                cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
                
                status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(mac_address=str(mac), status=status, message=msg)                    
                
                modulation_order_offset = request.capture_settings.modulation_order_offset
                number_sample_symbol = request.capture_settings.number_sample_symbol

                service = CmDsOfdmConstDisplayService(
                    cable_modem=cm,
                    modulation_order_offset=modulation_order_offset,
                    number_sample_symbol=number_sample_symbol,)
                
                msg_rsp: MessageResponse = await service.set_and_go()

                if msg_rsp.status != ServiceStatusCode.SUCCESS:
                    self.logger.error(
                        f"[getMeasurement] Constellation Display failed with status: {msg_rsp.status.name}")
                    raise HTTPException(status_code=500, detail="Constellation Display SNMP execution failed")

                cps = CommonProcessService(msg_rsp)
                msg_rsp = cps.process()

                analysis = Analysis(AnalysisType.BASIC, msg_rsp)

                if request.output.type == FileType.JSON.value:
                    return PnmAnalysisResponse(
                        mac_address=mac, 
                        status=ServiceStatusCode.SUCCESS, data=analysis.get_results())

                elif request.output.type == FileType.ARCHIVE.value:
                    
                    analysis_rpt = ConstellationDisplayReport(analysis)
                    rpt:Path = analysis_rpt.build_report()
                    return PnmFileService().get_file(FileType.ARCHIVE, rpt.name)

                else:
                    return PnmAnalysisResponse(
                        mac_address=mac,
                        status=ServiceStatusCode.INVALID_OUTPUT_TYPE, data={})
            
            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getAnalysis] Error for MAC {mac}")
                raise HTTPException(status_code=500, detail=f"Plot retrieval failed: {str(e)}")

        @self.router.post(f"/{self.base_endpoint}/getMeasurementStatistics", response_model=Union[SnmpResponse])
        async def get_measurement_statistics(request: SnmpRequest):
            """
            Returns high-level Constellation Display measurement statistics for a DOCSIS 3.1 cable modem.
            This includes modulation order, symbol capture config, and measurement state metadata.
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving Constellation Display Measurement Statistics for MAC: {mac}, IP: {ip}")

            try:

                cm = CableModem(mac_address=MacAddress(mac), inet=Inet(ip))
                
                status, msg = await CableModemServicePreCheck(cable_modem=cm, validate_ofdm_exist=True).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(mac_address=str(mac), status=status, message=msg)  

                service: CmDsOfdmConstDisplayService = CmDsOfdmConstDisplayService(cm)
                service_measure_stat = await service.get_pnm_measurement_statistics()

                return SnmpResponse(
                    mac_address=str(mac),
                    status=ServiceStatusCode.SUCCESS,
                    message="Measurement Statistics for OFDM Constellation Display",
                    results=service_measure_stat)

            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurementStatistics] Error for MAC {request.cable_modem.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement statistics retrieval failed: {str(e)}")


# Required for dynamic auto-registration
router = ConstellationDisplayRouter().router
