# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Tuple
from api.routes.common.extended.common_measure_service import CommonMeasureService
from config.pnm_config_manager import PnmConfigManager
from docsis.cable_modem import CableModem
from lib.inet import Inet
from pnm.data_type.pnm_test_types import DocsPnmCmCtlTest

class CmDsOfdmChanEstCoefService(CommonMeasureService):
    """
    Service for executing the DOCSIS Downstream OFDM Channel Estimation Coefficient test.

    This service performs a Proactive Network Maintenance (PNM) test on a specified cable modem
    to retrieve OFDM channel estimation coefficients. These coefficients are used to evaluate
    the downstream channel's quality and identify impairments such as group delay,
    reflections, or echo paths.

    The test initiates a SNMP-triggered control procedure on the cable modem, stores the result
    in a file on the configured TFTP server, and retrieves and parses the output for reporting.

    Args:
        cable_modem (CableModem): Target cable modem on which to run the test.
        tftp_servers (Tuple[Inet, Inet], optional): Tuple of TFTP server IPs for file retrieval.
            Defaults to the configured primary/secondary TFTP servers.
        tftp_path (str, optional): Optional subdirectory path on the TFTP server for storing files.
            Defaults to the configured base path.
    """
    
    def __init__(self,
                 cable_modem: CableModem,
                 tftp_servers: Tuple[Inet, Inet] = PnmConfigManager.get_tftp_servers(),
                 tftp_path: str = PnmConfigManager.get_tftp_path()):
        super().__init__(
            DocsPnmCmCtlTest.DS_OFDM_CHAN_EST_COEF,
            cable_modem,
            tftp_servers,
            tftp_path,
            cable_modem.getWriteCommunity()
        )
        self.logger = logging.getLogger(self.__class__.__name__)
