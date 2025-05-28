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
from pypnm.api.routes.docs.pnm.ds.histogram.schemas import PnmHistogramRequest, PnmHistogramResponse
from pypnm.api.routes.docs.pnm.ds.histogram.service import CmDsHistogramService
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class DsHistogramRouter:
    """
    Router for handling DOCSIS Downstream Histogram PNM (Proactive Network Maintenance) operations.

    This router defines the API endpoint for triggering a downstream histogram measurement on a
    cable modem using SNMP and retrieving the results from a TFTP server.

    Endpoint:
        POST /docs/pnm/ds/histogram/getMeasurement

    Request:
        - `mac_address`: MAC address of the target cable modem.
        - `ip_address`: IP address of the target cable modem.
        - `sample_duration`: Duration in seconds for histogram sampling.

    Response:
        - `mac_address`: Echoed MAC address from the request.
        - `status`: Status code indicating success or failure.
        - `data`: Parsed histogram measurement results (if successful).
    """

    def __init__(self):
        prefix = "/docs/pnm/ds"
        tags: List[str] = ["PNM Operations - Downstream Histogram"]
        base_endpoint = "/histogram"

        self.base_endpoint = base_endpoint.strip("/")
        self.router = APIRouter(prefix=prefix, tags=tags) # type: ignore
        self.logger = logging.getLogger(f"DsHistogramRouter.{self.base_endpoint}")

        @self.router.post(f"/{self.base_endpoint}/getMeasurement", response_model=Union[PnmHistogramResponse, SnmpResponse])
        async def get_measurement(request: PnmHistogramRequest):
            """
            Initiates a downstream histogram measurement on a target cable modem.

            Uses SNMP to trigger a measurement and TFTP to retrieve the result file.
            Processes the output and returns it in structured format.

            Args:
                request (PnmHistogramRequest): Contains MAC address, IP address, and sample duration.

            Returns:
                PnmHistogramResponse: Status and processed measurement results.

            Raises:
                HTTPException: If SNMP or processing fails.
            """
            try:
                self.logger.info(
                    f"[getMeasurement] Mac: {request.mac_address}, "
                    f"Inet: {request.ip_address}, Sample Duration: {request.sample_duration}"
                )

                cm = CableModem(
                    mac_address=MacAddress(request.mac_address),
                    inet=Inet(request.ip_address)
                )

                status, msg = await CableModemServicePreCheck(cable_modem=cm).run_precheck()
                if status != ServiceStatusCode.SUCCESS:
                    self.logger.error(msg)
                    return SnmpResponse(
                        mac_address=str(request.mac_address),
                        status=status,
                        message=msg
                    )    

                service = CmDsHistogramService(
                    cable_modem=cm,
                    sample_duration=int(request.sample_duration)
                )
                msg_rsp: MessageResponse = await service.set_and_go()

                if msg_rsp.status != ServiceStatusCode.SUCCESS:
                    self.logger.error(f"[getMeasurement] Histogram failed with status: {msg_rsp.status.name}")
                    raise HTTPException(status_code=500, detail="Downstream Histogram SNMP execution failed")

                cps = CommonProcessService(msg_rsp)
                msg_rsp = cps.process()

                return PnmHistogramResponse(
                    mac_address=request.mac_address,
                    status=msg_rsp.status,
                    data=msg_rsp.payload_to_dict()
                )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.exception(f"[getMeasurement] Unexpected error for MAC {request.mac_address}")
                raise HTTPException(status_code=500, detail=f"Measurement retrieval failed: {str(e)}")

# ✅ Required for dynamic auto-registration
router = DsHistogramRouter().router
