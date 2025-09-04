
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from time import sleep
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Union

from pypnm.api.routes.common.classes.common_endpoint_classes.schemas import PnmChannelEntryResponse
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpRequest, SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.if30.ds.scqam.chan.stats.schemas import CodewordErrorRateRequest
from pypnm.api.routes.docs.if30.ds.scqam.chan.stats.service import DsScQamChannelService

class DsScQamChannelRouter:
    """
    Router class to handle DOCSIS 3.0 Downstream SC-QAM Channel Statistics endpoints.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.router = APIRouter(
            prefix="/docs/if30/ds/scqam/chan",
            tags=["DOCSIS 3.0 Downstream SC-QAM Channel Stats"])
        
        self._add_routes()

    def _add_routes(self):

        @self.router.post("/stats", response_model=Union[List[PnmChannelEntryResponse], SnmpResponse])
        async def get_scqam_ds_channels(request: SnmpRequest) -> Union[List[PnmChannelEntryResponse], SnmpResponse]:
            """
            **DOCSIS 3.0 Downstream SC-QAM Channel Stats**

            Retrieves downstream SC-QAM channel configuration and signal quality metrics
            for a DOCSIS 3.0 modem, including modulation type, frequency, RxMER, power,
            and error counters.

            This endpoint is used for monitoring downstream health and identifying RF impairments
            such high uncorrectable error rates.

            [API Guide - Downstream SC-QAM Channel Stats](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/scqam/stats.md)

            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            self.logger.info(f"Retrieving DOCSIS 3.0 SC-QAM downstream channel stats for MAC: {mac}, IP: {ip}")
            status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip).run_precheck()
            
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac), status=status, message=msg)              
            
            service = DsScQamChannelService(mac_address=mac, ip_address=ip)
            
            data = await service.get_scqam_chan_entries()
            return JSONResponse(content=data)  # type: ignore

        @self.router.post("/codewordErrorRate", response_model=Union[List[PnmChannelEntryResponse], SnmpResponse])
        async def get_scqam_ds_channels_codeword_error_rate(request: CodewordErrorRateRequest) -> Union[List[PnmChannelEntryResponse], SnmpResponse]:
            """
            **Compute per-channel DOCSIS 3.0 SC-QAM codeword error rates over a sampling interval.**

            [API Guide - Downstream SC-QAM Channel Codeword Error Rate](https://github.com/mgarcia01752/PyPNM/blob/main/documentation/api/fast-api/single/ds/scqam/cw-error-rate.md)
            """
            mac = request.cable_modem.mac_address
            ip = request.cable_modem.ip_address
            time_elapse = float(request.sample_time_elapsed)

            self.logger.info(f"Retrieving DOCSIS 3.0 SC-QAM downstream channel codeword error rate for MAC: {mac}, IP: {ip}")

            status, msg = await CableModemServicePreCheck(mac_address=mac, ip_address=ip,
                                                          validate_scqam_exist = True).run_precheck()
            
            if status != ServiceStatusCode.SUCCESS:
                self.logger.error(msg)
                return SnmpResponse(mac_address=str(mac), status=status, message=msg)              
            
            service = DsScQamChannelService(mac_address=mac, ip_address=ip)
            cw_error_rate = await service.get_scqam_chan_codeword_error_rate(time_elapse)
            
            return SnmpResponse(
                mac_address=str(mac),
                status=ServiceStatusCode.SUCCESS,
                message="Successfully retrieved codeword error rate",
                results=cw_error_rate)

# Required for dynamic auto-registration
router = DsScQamChannelRouter().router
