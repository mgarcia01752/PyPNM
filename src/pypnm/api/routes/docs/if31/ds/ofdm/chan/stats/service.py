
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List
from pypnm.docsis.cable_modem import CableModem, InetAddressStr
from pypnm.docsis.data_type.DocsIf31CmDsOfdmChanEntry import DocsIf31CmDsOfdmChanEntry
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress, MacAddressStr

class DsOfdmChannelService:

    def __init__(self, mac_address: MacAddressStr, ip_address: InetAddressStr):
        self.cm = CableModem(MacAddress(mac_address), Inet(ip_address))
        self.logger = logging.getLogger("DsOfdmChannelService")

    async def get_ofdm_chan_entries(self) -> List[Dict]:
        """
        Retrieves and populates all OFDM downstream channel entries.

        Returns:
            List[dict]: List of dictionaries with `index`, `channel_id`, and `entry` keys.
        """
        entries: List[DocsIf31CmDsOfdmChanEntry] = await self.cm.getDocsIf31CmDsOfdmChanEntry()

        if not entries:
            self.logger.warning("No OFDM channel entries retrieved from the cable modem.")
            return []

        result = []
        for entry in entries:
            try:
                result.append(entry.model_dump())
            except ValueError as e:
                self.logger.warning(f"Skipping incomplete entry at index {entry.index}: {e}")
                continue
        
        if not result:
            self.logger.warning("No valid OFDM channel entries found.")

        return result
