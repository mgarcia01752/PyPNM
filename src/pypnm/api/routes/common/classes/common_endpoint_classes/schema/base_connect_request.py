# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from ipaddress import ip_address
from pydantic import BaseModel, Field, ConfigDict, field_validator
from api.routes.common.classes.common_endpoint_classes.schema.base_snmp import SNMPConfig
from config.config_common import SystemConfigCommonSettings as SCSC
from lib.mac_address import MacAddress


class BaseDeviceConnectRequest(BaseModel):
    """
    Request model for connecting to a cable modem using SNMP.

    Attributes:
        mac_address (str): Validated and normalized MAC address of the cable modem.
            Defaults to the system-configured value from SystemConfigCommonSettings.
        ip_address (str): Validated and normalized IP address of the cable modem.
            Defaults to the system-configured value from SystemConfigCommonSettings.
        snmp (SNMPConfig): SNMP configuration block containing v2c and v3 settings.

    Usage:
        ```python
        >>> req = BaseDeviceConnectRequest(
        ...     mac_address="00-11-22-33-44-55",
        ...     ip_address="192.168.1.100",
        ...     snmp=SNMPConfig(
        ...         snmp_v2c={"community": "public"},
        ...         snmp_v3={
        ...             "username": "user",
        ...             "securityLevel": "authPriv",
        ...             "authProtocol": "SHA",
        ...             "authPassword": "pass",
        ...             "privProtocol": "AES",
        ...             "privPassword": "privpass"
        ...         }
        ...     )
        >>> req.mac_address
        "00:11:22:33:44:55"
        >>> req.ip_address
        "192.168.1.100"
        ```
    """
    # Enable assignment-time validation via ConfigDict (Pydantic v2)
    model_config = ConfigDict(
        validate_assignment=True
    )

    mac_address: str = Field(
        default=SCSC.default_mac_address,
        description="MAC address of the cable modem, validated via MACValidator mixin"
    )
    
    ip_address: str = Field(
        default=SCSC.default_ip_address,
        description="IP address of the cable modem, validated via IPValidator mixin"
    )
    
    snmp: SNMPConfig = Field(
        ...,  # explicit required field
        description="SNMP configuration block containing v2c and v3 settings"
    )

    @field_validator("mac_address", mode="before")
    def _normalize_mac(cls, v: str) -> str:
        """
        Normalize and validate a raw MAC address string before assignment.

        Args:
            v (str): Raw MAC address input.

        Returns:
            str: Canonical MAC address (e.g., "00:11:22:33:44:55").

        Raises:
            ValueError: If the provided MAC is invalid.
        """
        try:
            return str(MacAddress(v))
        except Exception as e:
            raise ValueError(f"Invalid MAC address {v!r}: {e}")
        
    @field_validator("ip_address")
    def _validate_ip(cls, v: str) -> str:
        """
        Validate and normalize a raw IP address string.

        Args:
            v (str): Raw IP address input.

        Returns:
            str: Canonical IP address (e.g., "192.168.1.100").

        Raises:
            ValueError: If the provided IP is invalid.
        """
        try:
            return str(ip_address(v))
        except ValueError:
            raise ValueError(f"Invalid IP address {v!r}")