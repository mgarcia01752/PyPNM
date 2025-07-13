# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List

from pypnm.docsis.cable_modem import CableModem

class CmDsOfdmMerMarginService:
    """
    Service class for handling Downstream OFDM MER Margin measurement operations.

    This class wraps methods to:
    - Trigger MER Margin measurement on the cable modem
    - Retrieve measurement statistics and results
    """

    def __init__(self, cable_modem: CableModem):
        """
        Initialize the MER Margin service.

        Args:
            cable_modem (CableModem): The cable modem instance to operate on.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cable_modem = cable_modem

    async def set(self) -> None:
        """
        Initiates the MER Margin measurement on the cable modem.

        NOTE: Implementation pending—will configure SNMP set values for trigger params.
        """
        pass  # TODO: Implement SNMP set logic for trigger

    async def getMeasurementStatus(self) -> Dict[str, List[Dict]]:
        """
        Retrieves MER Margin measurement entries from the cable modem.

        Returns:
            Dict[str, List[Dict]]: A dictionary containing a list of MER Margin entries,
            keyed by "DS_MER_MARGIN".
        """
        try:
            entries = await self.cable_modem.getDocsPnmCmDsOfdmMerMarEntry()
            return {"DS_MER_MARGIN": [e.model_dump() for e in entries]}
        
        except Exception as e:
            self.logger.exception("Failed to retrieve MER Margin entries")
            return {"DS_MER_MARGIN": []}
