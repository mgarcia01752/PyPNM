# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Dict, List
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.ClabsDocsisVersion import ClabsDocsisVersion
from pypnm.docsis.data_type.DocsFddCmFddCapabilities import DocsFddCmFddBandEdgeCapabilities
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class FddDiplexerBandEdgeCapabilityService:
    """
    Service class for retrieving the diplexer band edge capabilities of a DOCSIS 4.0
    cable modem operating in FDD mode.

    This service fetches the following capabilities via SNMP:
    - Upstream upper band edge capability
    - Downstream lower band edge capability
    - Downstream upper band edge capability

    These values indicate the supported extended frequency spectrum limits as reported
    in the modem's SNMP MIBs (e.g., `docsFddDiplexerUsUpperBandEdgeCapability`, etc.).
    """

    def __init__(self, mac_address: str, ip_address: str):
        """
        Initialize the service using a modem's MAC and IP address.

        Args:
            mac_address (str): The MAC address of the target cable modem.
            ip_address (str): The IP address of the target cable modem.
        """
        self.cm = CableModem(mac_address=MacAddress(mac_address), inet=Inet(ip_address))

    def isDocsis40(self) -> bool:
        if self.cm.getDocsisBaseCapability() != ClabsDocsisVersion.DOCSIS_40:
            return False
        return True
    
    async def getFddDiplexerBandEdgeCapabilityEntries(self) -> List[Dict]:
        """
        Retrieve and populate the FDD diplexer band edge capabilities from the modem.

        This method:
        1. Walks the SNMP capability tables to obtain valid indices.
        2. Constructs DocsFddCmFddBandEdgeCapabilities objects for each.
        3. Starts SNMP population of each capability instance.
        4. Returns the structured results as a list of dictionaries.

        Returns:
            List[Dict]: A list of populated band edge capability entries.
        """
        fdd_band_edge_list: List[DocsFddCmFddBandEdgeCapabilities] = \
            await self.cm.getDocsFddCmFddBandEdgeCapabilities(create_and_start=False)

        entries: List[Dict] = []

        for fdd_band_edge in fdd_band_edge_list:
            if await fdd_band_edge.start():
                entries.append(fdd_band_edge.to_dict())

        return entries
