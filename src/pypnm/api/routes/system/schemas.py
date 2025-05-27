# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Module: common_endpoint_classes.schema.sys

Defines request and response models for system SNMP operations (sysDescr and sysUpTime).
"""
from api.routes.common.classes.common_endpoint_classes.schema.base_connect_request import BaseDeviceConnectRequest
from api.routes.common.classes.common_endpoint_classes.snmp.schemas import SnmpResponse

class SysRequest(BaseDeviceConnectRequest):
    """
    Request model for SNMP system operations.

    Inherits:
        mac_address (str): MAC address of the cable modem.
        ip_address (str): IP address of the cable modem.
        snmp (SNMPConfig): SNMP configuration block.

    Usage:
        ```python
        req = SysRequest(
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.100",
            snmp={
                "snmpV2c": {"community": "public"},
                "snmpV3": {"username": "user", "securityLevel": "noAuthNoPriv"}
            }
        )
        ```
    """
    # No additional fields; uses base connection parameters.

class SysDescrResponse(SnmpResponse):
    ''''''
    
class SysUpTimeResponse(SnmpResponse):
    """
    Response model for SNMP `sysUpTime` query.

    The `results` field is a dictionary containing the `uptime` key with a human-readable string.
    """

