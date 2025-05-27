# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator

from pypnm.api.routes.advance.common.operation_state import OperationState
from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.config.config_common import SystemConfigCommonSettings as SCSC
from pypnm.lib.mac_address import MacAddress


class BaseDeviceResponse(BaseModel):
    """
    Standard response model for all PNM FastAPI endpoints.

    Attributes:
        mac_address (str): Validated and normalized MAC address of the cable modem.
        status (ServiceStatusCode | OperationState | str): Result status of the operation.
        message (str, optional): Additional information or error details.

    Usage:
        ```python
        >>> BaseResponse()
        BaseResponse(mac_address="00:11:22:33:44:55", status="success", message=None)

        >>> BaseResponse(status=ServiceStatusCode.ERROR, message="Modem not found")
        ```
    """
    
    mac_address: str = Field(
        default=SCSC.default_mac_address,
        description="MAC address of the cable modem, validated and normalized"
    )
    status: Union[ServiceStatusCode, OperationState, str] = Field(
        default="success",
        description="Status of the operation (e.g., 'success', 'error')"
    )
    message: Optional[str] = Field(
        default=None,
        description="Additional informational or error message"
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