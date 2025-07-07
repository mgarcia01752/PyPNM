# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging

from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.DocsFddCmFddSystemCfgState import DocsFddCmFddSystemCfgState
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

logger = logging.getLogger(__name__)

class FddDiplexerConfigService:
    """
    Service for retrieving DOCSIS 4.0 FDD diplexer configuration state from a cable modem.

    """
    MHZ: int = 1_000_000

    @staticmethod
    async def fetch_fdd_diplexer_config(mac_address: str, ip_address: str) -> DocsFddCmFddSystemCfgState:
        """
.
        """
        logger.info(f"Fetching diplexer config for {mac_address}@{ip_address}")

        cm = CableModem(
            mac_address=MacAddress(mac_address),
            inet=Inet(ip_address))
        
        state: DocsFddCmFddSystemCfgState = await cm.getDocsFddCmFddSystemCfgState()
        if state is None:
            logger.error("Diplexer configuration returned None")
            raise RuntimeError("Failed to retrieve diplexer configuration")
       
        return state
        


