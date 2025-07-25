# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum, auto
import logging
import re
from typing import Union

try:
    from pysnmp.proto.rfc1902 import OctetString
    
except ImportError:
    OctetString = None
class MacAddressFormat(Enum):
    FLAT = auto()      # e.g., '001a2b3c4d5e'
    CISCO = auto()     # e.g., '001a.2b3c.4d5e'
    COLON = auto()     # e.g., '00:1a:2b:3c:4d:5e'
    HYPHEN = auto()    # e.g., '00-1a-2b-3c-4d-5e'

class MacAddress:
    def __init__(self, mac_address: Union[str, bytes, bytearray, 'OctetString']) -> None:
        """
        Initialize a MacAddress object.

        Args:
            mac_address (str | bytes | bytearray | OctetString): MAC address input.

        Raises:
            ValueError: If the MAC address is invalid or improperly formatted.
            TypeError: If input type is unsupported.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        if OctetString is not None and isinstance(mac_address, OctetString):
            # Convert OctetString to bytes
            mac_address = bytes(mac_address)
        
        if isinstance(mac_address, (bytes, bytearray)):
            # Convert bytes to hex string
            mac_address = ''.join(f"{b:02x}" for b in mac_address)
        
        if isinstance(mac_address, str):
            # Remove 0x prefix if present
            if mac_address.lower().startswith("0x"):
                mac_address = mac_address[2:]

            # Remove common separators (., -, :, and spaces)
            mac_address = re.sub(r"[.\-:\s]", "", mac_address)

            # Validate length and hex characters
            if not re.fullmatch(r"[0-9a-fA-F]{12}", mac_address):
                raise ValueError(f"Invalid MAC address: {mac_address}. It should contain exactly 12 hexadecimal characters.")

            self._mac = mac_address.lower()
        else:
            raise TypeError(f"Unsupported type for mac_address: {type(mac_address).__name__}")

    @staticmethod
    def null() -> str:
        return "00:00:00:00:00:00"
    
    @property
    def mac_address(self) -> str:
        """
        Internal raw MAC address (no separators).

        Returns:
            str: 12-character hexadecimal MAC address.
        """
        return self._mac

    def __str__(self) -> str:
        """
        Return the MAC address in standard colon-separated format.

        Returns:
            str: The MAC address as XX:XX:XX:XX:XX:XX.
        """
        return ':'.join(self.mac_address[i:i+2] for i in range(0, len(self.mac_address), 2))

    def is_multicast(self) -> bool:
        """
        Check if the MAC address is multicast.

        Returns:
            bool: True if multicast, False otherwise.
        """
        return int(self.mac_address[0:2], 16) & 1 == 1

    def to_mac_format(self, fmt: MacAddressFormat = MacAddressFormat.FLAT) -> str:
        """
        Convert the MAC address to a specific string format.

        Args:
            fmt (MacAddressFormat): Desired output format.

        Returns:
            str: Formatted MAC address.
        """
        hex_str = self.mac_address

        if fmt == MacAddressFormat.FLAT:
            return hex_str
        elif fmt == MacAddressFormat.COLON:
            return ':'.join(hex_str[i:i+2] for i in range(0, 12, 2))
        elif fmt == MacAddressFormat.HYPHEN:
            return '-'.join(hex_str[i:i+2] for i in range(0, 12, 2))
        elif fmt == MacAddressFormat.CISCO:
            return f"{hex_str[:4]}.{hex_str[4:8]}.{hex_str[8:]}"
        else:
            raise ValueError(f"Unsupported MAC address format: {fmt}")
    
    @staticmethod
    def is_valid(mac_address: Union[str, bytes, bytearray, 'OctetString']) -> bool:
        """
        Static method to validate a MAC address.

        Args:
            mac_address (str | bytes | bytearray | OctetString): MAC address input.

        Returns:
            bool: True if valid, otherwise False.
        """
        try:
            MacAddress(mac_address)
            return True
        except (ValueError, TypeError):
            return False

