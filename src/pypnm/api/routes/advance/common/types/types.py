
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import enum
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union
from pypnm.api.routes.common.classes.file_capture.types import TransactionId
from pypnm.docsis.cm_snmp_operation import SystemDescriptor
from pypnm.docsis.data_type.sysDescr import SystemDescriptorModel
from pypnm.lib.types import FileName, MacAddressStr

DeviceDetailsPayload = Union[
    SystemDescriptorModel,
    SystemDescriptor, str, Dict[str, Any],
    None,]

class EntryDict(TypedDict):
    transaction_id: str
    file_name: str
    file_type: str
    capture_time: int
    channel_id: Optional[int]
    device_details: DeviceDetailsPayload
    data: bytes
    mac_address: str

class Sort(enum.Enum):
    CHANNEL_ID      = enum.auto()
    ASCEND_EPOCH    = enum.auto()
    PNM_FILE_TYPE   = enum.auto()
    MAC_ADDRESS     = enum.auto()

TransactionFile = Tuple[TransactionId, FileName, bytes]
TransactionFileCollection = List[TransactionFile]
FlatIndex    = Dict[MacAddressStr, List[EntryDict]]
GroupedIndex = Dict[MacAddressStr, Dict[int, List[EntryDict]]]
SortOrder    = List[Sort]


