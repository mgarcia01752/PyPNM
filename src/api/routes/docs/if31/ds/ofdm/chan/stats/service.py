# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List
from docsis.cable_modem import CableModem
from docsis.data_type.DocsIf31CmDsOfdmChanEntry import DocsIf31CmDsOfdmChanEntry
from lib.inet import Inet
from lib.mac_address import MacAddress


class DsOfdmChannelService:

    def __init__(self, mac_address: str, ip_address: str):
        self.cm = CableModem(mac_address=MacAddress(mac_address), inet=Inet(ip_address))
        self.logger = logging.getLogger("DsOfdmChannelService")

    async def get_ofdm_chan_entries(self) -> List[Dict]:
        """
        Retrieves and populates all OFDM downstream channel entries.

        Returns:
            List[dict]: List of dictionaries with `index`, `channel_id`, and `entry` keys.
        """
        entries: List[DocsIf31CmDsOfdmChanEntry] = await self.cm.getDocsIf31CmDsOfdmChanEntry()

        result = []
        for entry in entries:
            try:
                result.append(entry.to_dict())
            except ValueError as e:
                self.logger.warning(f"Skipping incomplete entry at index {entry.index}: {e}")
                continue

        return result
