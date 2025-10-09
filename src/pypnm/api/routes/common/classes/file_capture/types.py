# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from typing import Any, Dict, NewType

from pydantic import BaseModel, Field

from pypnm.docsis.cable_modem import MacAddress
from pypnm.docsis.cm_snmp_operation import SystemDescriptor
from pypnm.docsis.data_type.sysDescr import SystemDescriptorModel
from pypnm.lib.types import FileName, MacAddressStr, TimestampSec

GroupId             = NewType("GroupId", str)
TransactionId       = NewType("TransactionId", str)

Record              = Dict[str, Any]
TransactionRecord   = Dict[TransactionId, Record]

class DeviceDetailsModel(BaseModel):
    system_description: SystemDescriptorModel = Field(..., description="Parsed system descriptor")

class TransactionRecordModel(BaseModel):
    transaction_id: TransactionId       = Field(..., description="16-char transaction ID")
    timestamp: TimestampSec             = Field(..., description="Epoch seconds")
    mac_address: MacAddressStr          = Field(..., description="Cable modem MAC address")
    pnm_test_type: str                  = Field(..., description="PNM test type")
    filename: FileName                  = Field(..., description="Capture filename")
    device_details: DeviceDetailsModel  = Field(..., description="Device details container")

    @classmethod
    def null(cls) -> "TransactionRecordModel":
        return cls(
            transaction_id  =   TransactionId(""),
            timestamp       =   TimestampSec(0),
            mac_address     =   MacAddressStr(MacAddress.null()),
            pnm_test_type   =   "",
            filename        =   FileName(""),
            device_details=DeviceDetailsModel(system_description=SystemDescriptor.empty().to_model()),
        )