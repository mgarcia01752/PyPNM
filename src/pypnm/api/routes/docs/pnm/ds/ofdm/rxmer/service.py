# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Tuple
from api.routes.common.extended.common_measure_service import CommonMeasureService
from config.pnm_config_manager import PnmConfigManager
from lib.inet import Inet

from docsis.cable_modem import CableModem
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest

class CmDsOfdmRxMerService(CommonMeasureService):
    """
    Service class for executing DOCSIS 3.1 downstream OFDM RxMER (Receive Modulation Error Ratio)
    measurements on a cable modem.

    This class wraps the necessary logic for configuring and triggering the
    DS-OFDM-RxMER-Per-Subcarrier test defined by the PNM framework. It determines the 
    appropriate TFTP server address based on IP version compatibility with the cable modem
    and utilizes SNMP to configure the modem's bulk data collection behavior.

    Attributes:
        logger (logging.Logger): Logger instance for diagnostic logging specific to this service.
    """

    def __init__(self,
                 cable_modem: CableModem,
                 tftp_servers: Tuple[Inet, Inet] = PnmConfigManager.get_tftp_servers(),
                 tftp_path: str = PnmConfigManager.get_tftp_path()):
        """
        Initializes the RxMER service with the provided cable modem and TFTP configuration.

        Args:
            cable_modem (CableModem): The target cable modem instance for which RxMER is to be measured.
            tftp_servers (Tuple[Inet, Inet], optional): Tuple of (IPv4, IPv6) TFTP server addresses.
                Defaults to the values loaded from PnmConfigManager.
            tftp_path (str, optional): Remote directory path on the TFTP server where data will be stored.
                Defaults to the value from PnmConfigManager.
        """
        super().__init__(
            DocsPnmCmCtlTest.DS_OFDM_RXMER_PER_SUBCAR,
            cable_modem,
            tftp_servers,
            tftp_path,
            cable_modem.getWriteCommunity()
        )
        self.logger = logging.getLogger(self.__class__.__name__)
