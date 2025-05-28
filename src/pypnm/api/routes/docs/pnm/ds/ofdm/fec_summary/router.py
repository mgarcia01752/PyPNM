# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import List, Union
from fastapi import APIRouter, HTTPException
from pypnm.api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse
from pypnm.api.routes.common.classes.operation.cable_modem_precheck import CableModemServicePreCheck
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import CommonProcessService
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.fec_summary.schemas import PnmFecSummaryRequest, PnmFecSummaryResponse
from pypnm.api.routes.docs.pnm.ds.ofdm.fec_summary.service import CmDsOfdmFecSummaryService
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.cm_snmp_operation import FecSummaryType
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class FecSummaryRouter:
    """
    Concrete implementation of PnmFastApiRouter for handling Fec Summary-related requests.
    """
    def __init__(self):
        prefix = "/docs/pnm/ds/ofdm"
        tags:List[str] = ["PNM Operations - Downstream OFDM FEC Summary"]
        base_endpoint = "/fecSummary"

        self.base_endpoint = base_endpoint.strip("/")
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.logger = logging.getLogger(f"FecSummaryRouter.{self.base_endpoint}")

        @self.router.post(f"/{self.base_endpoint}/getMeasurement", response_model=Union[PnmFecSummaryResponse, SnmpResponse])
        async def get_measurement(request: PnmFecSummaryRequest):
            try:
                self.logger.info(f'Mac: {request.mac_address}, Inet: {request.ip_address}, FEC Summary: {request.fec_summary_type}')

                cm = CableModem(mac_address=MacAddress(request.mac_address), inet=Inet(request.ip_address))

                status, msg = await CableModemServicePreCheck(mac_address=request.mac_address, 
                                                        ip_address=request.ip_address).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.mac_address),
                        status=status,
                        message=msg
                    )               
            
                fec_type = FecSummaryType.from_value(int(request.fec_summary_type))

                service = CmDsOfdmFecSummaryService(cable_modem=cm, fec_summary_type=fec_type)
                msg_rsp: MessageResponse = await service.set_and_go()

                if msg_rsp.status != ServiceStatusCode.SUCCESS:
                    self.logger.error(f"[getMeasurement] FEC Summary failed with status: {msg_rsp.status.name}")
                    raise HTTPException(status_code=500, detail="FEC summary SNMP execution failed")

                cps = CommonProcessService(msg_rsp)
                msg_rsp = cps.process()

                return PnmFecSummaryResponse(
                    mac_address=request.mac_address,
                    status=msg_rsp.status,
                    data=msg_rsp.payload_to_dict()
                )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurement] Error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")


# ✅ Required for dynamic auto-registration
router = FecSummaryRouter().router
