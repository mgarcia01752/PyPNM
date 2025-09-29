
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pypnm.config.pnm_config_manager import PnmConfigManager
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress
from pypnm.docsis.cm_snmp_operation import CmSnmpOperation
from pypnm.lib.ping import Ping

class CableModem(CmSnmpOperation):
    """
    Represents a Cable Modem device that extends SNMP operations.

    Provides access to the modem's MAC and IP addresses, and utility
    functions such as ping-based reachability and SNMP responsiveness checks.
    """

    inet: Inet

    def __init__(
        self,
        mac_address: MacAddress,
        inet: Inet,
        write_community: str = PnmConfigManager.get_write_community()):
        """
        Initialize the CableModem instance.

        Args:
            mac_address (MacAddress): The MAC address of the cable modem.
            inet (Inet): The IP address of the cable modem.
            write_community (str, optional): SNMP write community string. Defaults to the configured value.
        """
        super().__init__(inet=inet, write_community=write_community)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._mac_address: MacAddress = mac_address

    @property
    def get_mac_address(self) -> MacAddress:
        """
        Returns the MAC address of the cable modem.

        Returns:
            MacAddress: The cable modem's MAC address.
        """
        return self._mac_address

    @property
    def get_inet_address(self) -> str:
        """
        Returns the IP address of the cable modem as a string.

        Returns:
            str: The cable modem's IP address.
        """
        return str(self._inet)

    def is_ping_reachable(self) -> bool:
        """
        Checks whether the cable modem is reachable via ICMP ping.

        Returns:
            bool: True if the modem responds to ping, False otherwise.
        """
        return Ping.is_reachable(self.get_inet_address)

    async def is_snmp_reachable(self) -> bool:
        """
        Checks whether the cable modem is reachable via SNMP by requesting sysDescr.

        Returns:
            bool: True if SNMP communication is successful, False otherwise.
        """
        system_description = await self.getSysDescr()

        if not system_description:
            self.logger.debug(
                f"{self.__repr__()}- SNMP access failed"
            )
            return False

        return True

    def same_inet_version(self, other: Inet) -> bool:
        """
        Determines whether this modem's IP address and another Inet address are the same IP version.

        Args:
            other (Inet): Another Inet instance to compare.

        Returns:
            bool: True if both are either IPv4 or IPv6, False otherwise.

        Raises:
            TypeError: If 'other' is not an instance of Inet.
        """
        if not isinstance(other, Inet):
            raise TypeError(f"Expected 'Inet' instance, got {type(other).__name__}")
        return self._inet.same_inet_version(other)

    def __str__(self) -> str:
        """
        String representation of the cable modem.

        Returns:
            str: MAC and IP address representation.
        """
        return f"{self.get_mac_address}"
    
    def __repr__(self) -> str:
        """
        String representation of the cable modem.

        Returns:
            str: MAC and IP address representation.
        """
        return f"Mac: {self.__str__()} - Inet: {self.get_inet_address}"
        
