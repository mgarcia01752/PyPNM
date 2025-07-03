# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from pypnm.api.routes.advance.common.operation_state import OperationState
from pypnm.api.routes.common.classes.common_endpoint_classes.schema.base_snmp import SNMPConfig
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.lib.mac_address import MacAddress

default_mac = SystemConfigSettings.default_mac_address
default_ip = SystemConfigSettings.default_ip_address

class CommonFileRequest(BaseModel):
    """
    Standard file request model for PNM FastAPI endpoints.

    Attributes:
        mac_address (str): MAC address of the cable modem (default from config).
    """
    mac_address: str = Field(default_mac, description="MAC address of the cable modem")
    
class CommonRequest(BaseModel):
    """
    Standard request model for PNM FastAPI endpoints.

    Attributes:
        mac_address (str): MAC address of the cable modem (default from config).
        ip_address (str): IP address of the cable modem (default from config).
    """
    mac_address: str = Field(default_mac, description="MAC address of the cable modem")
    ip_address: str = Field(default_ip, description="IP address of the cable modem")
    snmp:SNMPConfig = Field(description="SNMP (Default: v2c)")

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> str:
        """
        Validates and normalizes the MAC address using the custom MacAddress class.

        Args:
            v (str): The MAC address as a string.

        Returns:
            str: The normalized MAC address.

        Raises:
            ValueError: If the input is not a valid MAC address.
        """
        try:
            mac = MacAddress(v)
            return str(mac)
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v} ({e})")

class CommonResponse(BaseModel):
    """
    Standard response model for PNM FastAPI endpoints.

    Attributes:
        mac_address (str): MAC address of the cable modem (validated and normalized, default from config).
        status (Optional[ServiceStatusCode | OperationState | str]): Result status of the operation (default: "success").
        message (Optional[str]): Additional information or error details.
    """
    mac_address: str = Field(default_mac, description="MAC address of the cable modem")
    status: Optional[ServiceStatusCode | OperationState | str] = Field(
        default="success", description="Status of the operation (e.g., 'success', 'error')"
    )
    message: Optional[str] = Field(
        default=None, description="Additional information or error message"
    )

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> str:
        """
        Validates and normalizes the MAC address using the custom MacAddress class.

        Args:
            v (str): The MAC address as a string.

        Returns:
            str: The normalized MAC address.

        Raises:
            ValueError: If the input is not a valid MAC address.
        """
        try:
            mac = MacAddress(v)
            return str(mac)
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v} ({e})")

class CommonAnalysisType(BaseModel):
    type:int = Field(description="Analysis to perform")

class CommonOutput(BaseModel):
    """
    Args:
    
    Field:
        type:
            0 : JSON
            1 : CSV FILE 
    """
    type:int = Field(default=0, description="Report Output Type")

class CommonMultiAnalysisRequest(BaseModel):
    mac_address: str = Field(default_mac, description="MAC address of the cable modem")
    analysis: CommonAnalysisType

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> str:
        """
        Validates and normalizes the MAC address using the custom MacAddress class.

        Args:
            v (str): The MAC address as a string.

        Returns:
            str: The normalized MAC address.

        Raises:
            ValueError: If the input is not a valid MAC address.
        """
        try:
            mac = MacAddress(v)
            return str(mac)
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v} ({e})")

class CommonAnalysisRequest(BaseModel):
    """
    Basic Analysis Requst, assuming that Data was captured
    """
    mac_address: str = Field(default_mac, description="MAC address of the cable modem")
    ip_address: str = Field(default_ip, description="IP address of the cable modem")
    snmp:SNMPConfig = Field(description="SNMP (Default: v2c)")
    analysis: CommonAnalysisType
    output:CommonOutput = Field(description="Output Type REST or File")

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> str:
        """
        Validates and normalizes the MAC address using the custom MacAddress class.

        Args:
            v (str): The MAC address as a string.

        Returns:
            str: The normalized MAC address.

        Raises:
            ValueError: If the input is not a valid MAC address.
        """
        try:
            mac = MacAddress(v)
            return str(mac)
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v} ({e})")
    
class CommonAnalysisResponse(CommonResponse):
    """
    Basic Analysis Responseust
    """
