# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Tuple
from pypnm.config.pnm_config_manager import PnmConfigManager
from pypnm.lib.inet import Inet

from pypnm.docsis.cable_modem import CableModem
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest

class CmDsOfdmMerMarginService():
    """
    """

    def __init__(self, cable_modem: CableModem):
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
            cable_modem,tftp_servers,
            tftp_path,cable_modem.getWriteCommunity())
        self.logger = logging.getLogger(self.__class__.__name__)
