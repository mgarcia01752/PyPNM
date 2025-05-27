# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from pypnm.config.config_manager import ConfigManager


class SystemConfigCommonSettings:
    """Loads common defaults from system config at import time."""
    _cfg = ConfigManager()
    snmp_v2_write_comm: str   = _cfg.get("SNMP", "write_community")
    default_mac_address: str   = _cfg.get("FastApiRequestDefault", "mac_address")
    default_ip_address: str    = _cfg.get("FastApiRequestDefault", "ip_address")
