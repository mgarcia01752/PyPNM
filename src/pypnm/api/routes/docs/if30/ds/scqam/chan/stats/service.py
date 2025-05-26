# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Dict, List
from docsis.cable_modem import CableModem
from docsis.data_type import DocsIfDownstreamChannel
from lib.inet import Inet
from lib.mac_address import MacAddress

class DsScQamChannelService:
    """
    Service class for retrieving SC-QAM (Single Carrier Quadrature Amplitude Modulation)
    downstream channel entries from a DOCSIS cable modem.

    This class encapsulates logic to interact with a cable modem using its MAC and IP address,
    and extract downstream channel metrics such as frequency, power, SNR, and modulation type.
    """

    def __init__(self, mac_address: str, ip_address: str):
        """
        Initialize the service with a target cable modem's MAC and IP address.

        Args:
            mac_address (str): MAC address of the cable modem.
            ip_address (str): IP address of the cable modem.
        """
        self.cm = CableModem(mac_address=MacAddress(mac_address), inet=Inet(ip_address))

    async def get_scqam_chan_entries(self) -> List[Dict]:
        """
        Retrieve and process DOCSIS SC-QAM downstream channel entries.

        Returns:
            List[Dict]: A list of dictionaries representing successfully retrieved 
                        and populated SC-QAM downstream channel entries.
        """
        ds_channel_list: List[DocsIfDownstreamChannel] = await self.cm.getDocsIfDownstreamChannel()
        result: List[Dict] = []

        for ds_channel in ds_channel_list:
            success = await ds_channel.start()
            if success and ds_channel.docsIfDownChannelId is not None:
                result.append(ds_channel.to_dict())

        return result
