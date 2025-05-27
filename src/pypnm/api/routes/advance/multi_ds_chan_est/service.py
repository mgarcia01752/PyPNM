# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging

from pypnm.api.routes.advance.common.capture_service import AbstractCaptureService
from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.api.routes.docs.pnm.ds.ofdm.chan_est_coeff.service import CmDsOfdmChanEstCoefService
from pypnm.docsis.cable_modem import CableModem

class MultiChannelEstimationService(AbstractCaptureService):
    """
    Service to trigger a Cable Modem's ChannelEstimation capture via SNMP/TFTP and
    collect corresponding file-transfer transactions as CaptureSample objects.

    Each invocation of _capture_sample will:
      1. Send SNMP command to start ChannelEstimation capture and TFTP transfer.
      2. Await MessageResponse payload containing transaction entries.
      3. For each payload entry of type PNM_FILE_TRANSACTION with SUCCESS status:
         - Lookup the transaction record for filename retrieval.
         - Yield a CaptureSample(timestamp, transaction_id, filename).
      4. On SNMP/TFTP error or no valid entries, return a single CaptureSample
         with the appropriate error message.

    Inherited:
      - duration: total measurement duration in seconds.
      - interval: interval between captures in seconds.
    """
    def __init__(self, cm: CableModem, duration: float, interval: float):
        """
        Initialize the MultiChannelEstimationService.

        Args:
            cm: Configured CableModem instance for SNMP/TFTP operations.
            duration: Total duration (seconds) to run periodic captures.
            interval: Time (seconds) between successive captures.
        """
        super().__init__(duration, interval)
        self.cm = cm
        self.logger = logging.getLogger(__name__)

    async def _capture_message_response(self) -> MessageResponse:
        """
        Perform one ChannelEstimation capture cycle.

        Returns:
            A list of CaptureSample objects. On success, one per file-transfer
            transaction; on error, a single Sample with error filled.

        Error handling:
            - Catches exceptions from SNMP/TFTP invocation.
            - Validates payload type and entry contents.
        """
        try:
            msg_rsp: MessageResponse = await CmDsOfdmChanEstCoefService(self.cm).set_and_go()
            
        except Exception as exc:
            err_msg = f"Exception during ChannelEstimation SNMP/TFTP operation: {exc}"
            self.logger.error(err_msg, exc_info=True)
            return MessageResponse(ServiceStatusCode.DS_OFDM_CHAN_EST_NOT_AVAILABLE)

        if msg_rsp.status != ServiceStatusCode.SUCCESS:
            err_msg = f"SNMP/TFTP failure: status={msg_rsp.status}"
            self.logger.error(err_msg)
            return MessageResponse(ServiceStatusCode.DS_OFDM_CHAN_EST_NOT_AVAILABLE)
        
        return msg_rsp
