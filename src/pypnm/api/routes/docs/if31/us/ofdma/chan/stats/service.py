
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.DocsIf31CmUsOfdmaChanEntry import DocsIf31CmUsOfdmaChanEntry
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress

class UsOfdmChannelService:
    def __init__(self, mac_address: str, ip_address: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cm = CableModem(mac_address=MacAddress(mac_address), inet=Inet(ip_address))

    async def get_ofdma_chan_entries(self) -> List[Dict]:
        """
        Retrieves and populates all OFDMA upstream channel entries.

        Returns:
            List[dict]: List of dictionaries with `index`, `channel_id`, and `entry` keys.
        """
        entries: List[DocsIf31CmUsOfdmaChanEntry] = await self.cm.getDocsIf31CmUsOfdmaChanEntry()

        result = []
        for entry in entries:
            try:
                result.append(entry.model_dump())
            except Exception as e:
                self.logger.warning(f"Skipping invalid entry at index {entry.index}: {e}")
                continue

        return result
