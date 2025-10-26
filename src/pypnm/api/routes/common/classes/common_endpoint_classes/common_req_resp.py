# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator

from pypnm.api.routes.advance.common.operation_state import OperationState
from pypnm.api.routes.common.classes.common_endpoint_classes.common.enum import AnalysisType, OutputType
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.system_config_settings import SystemConfigSettings
from pypnm.api.routes.common.classes.common_endpoint_classes.schema.base_snmp import SNMPConfig
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.matplot.manager import ThemeType
from pypnm.lib.types import IPv4Str, IPv6Str, InetAddressStr, MacAddressStr

# Default settings
default_mac: MacAddressStr   = SystemConfigSettings.default_mac_address
default_ip: InetAddressStr   = SystemConfigSettings.default_ip_address
default_tftp_ipv4: IPv4Str   = SystemConfigSettings.bulk_tftp_ip_v4
default_tftp_ipv6: IPv6Str   = SystemConfigSettings.bulk_tftp_ip_v6

# -----------------------------
# SNMP and TFTP Parameter Models
# -----------------------------

class TftpConfig(BaseModel):
    ipv4: Optional[IPv4Str] = Field(default=default_tftp_ipv4, description="TFTP server IPv4 address")
    ipv6: Optional[IPv6Str] = Field(default=default_tftp_ipv6, description="TFTP server IPv6 address")

class PnmParameters(BaseModel):
    tftp: TftpConfig = Field(default_factory=TftpConfig, description="TFTP configuration")
    

# -----------------------------
# Cable Modem Model
# -----------------------------

class CableModemPnmConfig(BaseModel):
    mac_address: MacAddressStr      = Field(default=default_mac, description="MAC address of the cable modem")
    ip_address: InetAddressStr      = Field(default=default_ip, description="Inet address of the cable modem")
    pnm_parameters: PnmParameters   = Field(description="PNM Parameters: TFTPServer")
    snmp: SNMPConfig                = Field(description="SNMP configuration")

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> MacAddressStr:
        try:
            return MacAddress(v).mac_address
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v}, reason: ({e})")

# -----------------------------
# Request & Response Models
# -----------------------------

class CommonMatPlotUiConfig(BaseModel):
    theme:ThemeType = Field(description="")

class CommonMatPlotConfigRequest(BaseModel):
    ui:CommonMatPlotUiConfig

class CommonFileRequest(BaseModel):
    cable_modem: CableModemPnmConfig

class CommonRequest(BaseModel):
    cable_modem: CableModemPnmConfig

class CommonAnalysisType(BaseModel):
    type: int = Field(description="Analysis type to perform")

class CommonSingleCaptureAnalysisType(BaseModel):
    type: AnalysisType              = Field(default=AnalysisType.BASIC, description="Analysis type to perform")
    output: CommonOutput            = Field(description="")
    plot:CommonMatPlotConfigRequest = Field(description="")

class CommonOutput(BaseModel):
    type: OutputType = Field(default=OutputType.JSON, description="")

class CommonMultiAnalysisRequest(BaseModel):
    cable_modem: CableModemPnmConfig
    analysis: CommonAnalysisType

class CommonAnalysisRequest(BaseModel):
    cable_modem: CableModemPnmConfig
    analysis: CommonAnalysisType
    output: CommonOutput = Field(description="Output type: JSON or file")

class CommonSingleCaptureAnalysisRequest(BaseModel):
    cable_modem: CableModemPnmConfig
    analysis: CommonSingleCaptureAnalysisType

class CommonResponse(BaseModel):
    mac_address: MacAddressStr                                      = Field(default=default_mac, description="MAC address of the cable modem")
    status: Optional[Union[ServiceStatusCode, OperationState, str]] = Field(default="success", description="Operation status")
    message: Optional[str]                                          = Field(default=None, description="Additional information or error details")

    @field_validator("mac_address")
    def validate_mac(cls, v: str) -> MacAddressStr:
        try:
            return MacAddress(v).mac_address
        except Exception as e:
            raise ValueError(f"Invalid MAC address: {v}, reason: ({e})")

class CommonAnalysisResponse(CommonResponse):
    """Basic analysis response model."""
    pass
