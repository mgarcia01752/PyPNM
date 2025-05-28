# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Tuple
from pypnm.config.config_manager import ConfigManager
from pypnm.lib.inet import Inet

class PnmConfigManager:
    """
    Static utility class for accessing PNM-related configuration values.
    Provides access to TFTP server addresses, SNMP community strings, and file paths.
    """

    _config = ConfigManager()
    _tftp_v4 = _config.get("PnmBulkDataTransfer", "tftp", "ip_v4")
    _tftp_v6 = _config.get("PnmBulkDataTransfer", "tftp", "ip_v6")
    _write_community = _config.get("SNMP", "write_community")
    _tftp_path = _config.get("PnmBulkDataTransfer", "tftp", "remote_dir")
    _save_dir = _config.get("PnmFileRetrieval", "save_dir")

    @classmethod
    def reload(cls):
        """
        Reloads all configuration values from the source configuration.
        Call this if the underlying configuration file changes and you want updated values.
        """
        cls._config.reload()
        cls._tftp_v4 = cls._config.get("PnmBulkDataTransfer", "tftp", "ip_v4")
        cls._tftp_v6 = cls._config.get("PnmBulkDataTransfer", "tftp", "ip_v6")
        cls._write_community = cls._config.get("SNMP", "write_community")
        cls._tftp_path = cls._config.get("PnmBulkDataTransfer", "tftp", "remote_dir")
        cls._save_dir = cls._config.get("PnmFileRetrieval", "save_dir")

    @staticmethod
    def get_save_dir() -> str:
        '''
        Returns:
            Directory of the saved PNM capture files
        '''
        PnmConfigManager.reload()
        return PnmConfigManager._save_dir

    @staticmethod
    def get_tftpv4() -> Inet:
        """
        Returns the IPv4 address of the TFTP server as an Inet object.

        Returns:
            Inet: The TFTP server's IPv4 address.
        """
        return Inet(PnmConfigManager._tftp_v4)

    @staticmethod
    def get_tftpv6() -> Inet:
        """
        Returns the IPv6 address of the TFTP server as an Inet object.

        Returns:
            Inet: The TFTP server's IPv6 address.
        """
        return Inet(PnmConfigManager._tftp_v6)

    @staticmethod
    def get_tftp_servers() -> Tuple[Inet, Inet]:
        """
        Retrieves the TFTP server IP addresses (both IPv4 and IPv6) as a tuple of `Inet` objects.

        Returns:
            Tuple[Inet, Inet]: A tuple containing the IPv4 and IPv6 Inet instances respectively.
        """
        return Inet(PnmConfigManager._tftp_v4), Inet(PnmConfigManager._tftp_v6)

    @staticmethod
    def get_write_community() -> str:
        """
        Returns the SNMP write community string.

        Returns:
            str: The SNMP write community.
        """
        return PnmConfigManager._write_community

    @staticmethod
    def get_tftp_path() -> str:
        """
        Returns the configured remote directory path for TFTP transfers.

        Returns:
            str: The TFTP server's remote directory path.
        """
        return PnmConfigManager._tftp_path
