# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Module: common_endpoint_classes.schema.base_snmp
Defines SNMP configuration models for v2c and v3 settings.
"""

from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from pydantic.alias_generators import to_camel

from pypnm.config.system_config_settings import SystemConfigSettings as SCSC

class SNMPv2c(BaseModel):
    """
    SNMP v2c settings model.

    Attributes:
        community (str): Write community string. Must not be blank.
    """
    community: str = Field(default=SCSC.snmp_write_community, description=f"Write community string (default: {SCSC.snmp_write_community})")

    @field_validator("community")
    def community_not_blank(cls, v: str) -> str:
        """
        Validate that the community string is not blank.
        """
        if not v.strip():
            raise ValueError("SNMPv2c.community must not be blank")
        return v


class SNMPv3(BaseModel):
    """
    SNMP v3 settings model.

    Attributes:
        username (Optional[str]): Username; if omitted, system default is used.
        securityLevel (Literal["noAuthNoPriv","authNoPriv","authPriv"]): Required SNMPv3 security level.
        authProtocol (Optional[Literal["MD5","SHA"]]): Authentication protocol.
        authPassword (Optional[str]): Authentication password.
        privProtocol (Optional[Literal["DES","AES"]]): Privacy protocol.
        privPassword (Optional[str]): Privacy password.
    """
    username: Optional[str]                     = Field(default=None, description="Username; if omitted, system default is used")
    securityLevel: Literal["noAuthNoPriv","authNoPriv","authPriv"] = Field(default="noAuthNoPriv", description="SNMPv3 security level")
    authProtocol: Optional[Literal["MD5","SHA"]]    = Field(default="SHA", description="Authentication protocol")
    authPassword: Optional[str]                     = Field(default="password", description="Authentication password")
    privProtocol: Optional[Literal["DES","AES"]]    = Field(default="AES", description="Privacy protocol")
    privPassword: Optional[str]                     = Field(default="password", description="Privacy password")

    @model_validator(mode="after") # type: ignore
    def check_v3_fields(cls, model: "SNMPv3") -> "SNMPv3":
        """
        Ensure that authentication and privacy fields are present based on securityLevel.
        """
        lvl = model.securityLevel
        if lvl in ("authNoPriv","authPriv"):
            if not model.authProtocol or not model.authPassword:
                raise ValueError("authProtocol & authPassword are required for auth levels")
        if lvl == "authPriv":
            if not model.privProtocol or not model.privPassword:
                raise ValueError("privProtocol & privPassword are required for privacy level")
        return model


class SNMPConfig(BaseModel):
    """
    SNMP configuration model supporting both v2c and optional v3 settings.
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    snmp_v2c: SNMPv2c   = Field(default_factory=SNMPv2c, description="SNMP v2c settings")

    if SCSC.snmp_v3_enable:
        snmp_v3: SNMPv3     = Field(default_factory=SNMPv3, description="SNMP v3 settings")
