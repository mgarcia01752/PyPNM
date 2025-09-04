
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator

from pypnm.api.routes.advance.common.operation_state import OperationState
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.api.routes.common.classes.common_endpoint_classes.schema.base_snmp import SNMPConfig
from pypnm.lib.mac_address import MacAddress

# Default settings
default_mac = SystemConfigSettings.default_mac_address
default_ip = SystemConfigSettings.default_ip_address
default_tftp_ipv4 = SystemConfigSettings.bulk_tftp_ip_v4
default_tftp_ipv6 = SystemConfigSettings.bulk_tftp_ip_v6

# -----------------------------
# SNMP and TFTP Parameter Models
# -----------------------------

class TftpConfig(BaseModel):
    ipv4: Optional[str] = Field(default=default_tftp_ipv4, description="TFTP server IPv4 address")
    ipv6: Optional[str] = Field(default=default_tftp_ipv6, description="TFTP server IPv6 address")

class PnmParameters(BaseModel):
    tftp: TftpConfig = Field(default_factory=TftpConfig, description="TFTP configuration")
    snmp: SNMPConfig = Field(description="SNMP configuration")

# -----------------------------
# Cable Modem Model
# -----------------------------

class CableModemConfig(BaseModel):
    mac_address: str = Field(default=default_mac, description="MAC address of the cable modem")
    ip_address: str = Field(default=default_ip, description="IP address of the cable modem")
    pnm_parameters: PnmParameters = Field(description="PNM Parameters including SNMP and TFTP")

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> str:
        try:
            return str(MacAddress(v))
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v} ({e})")

# -----------------------------
# Request & Response Models
# -----------------------------

class CommonFileRequest(BaseModel):
    cable_modem: CableModemConfig

class CommonRequest(BaseModel):
    cable_modem: CableModemConfig

class CommonAnalysisType(BaseModel):
    type: int = Field(description="Analysis type to perform")

class CommonOutput(BaseModel):
    type: int = Field(default=0, description="Report output type: 0 = JSON, 1 = CSV file")

class CommonMultiAnalysisRequest(BaseModel):
    cable_modem: CableModemConfig
    analysis: CommonAnalysisType

class CommonAnalysisRequest(BaseModel):
    cable_modem: CableModemConfig
    analysis: CommonAnalysisType
    output: CommonOutput = Field(description="Output type: JSON or file")

class CommonResponse(BaseModel):
    mac_address: str = Field(default=default_mac, description="MAC address of the cable modem")
    status: Optional[Union[ServiceStatusCode, OperationState, str]] = Field(default="success", description="Operation status")
    message: Optional[str] = Field(default=None, description="Additional information or error details")

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> str:
        try:
            return str(MacAddress(v))
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v} ({e})")

class CommonAnalysisResponse(CommonResponse):
    """Basic analysis response model."""
    pass
