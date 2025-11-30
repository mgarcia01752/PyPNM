
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
import enum
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

from pypnm.docsis.data_type.sysDescr import SystemDescriptor, SystemDescriptorModel
from pypnm.lib.types import (
    CaptureTime,
    ChannelId,
    FileName,
    MacAddressStr,
    TransactionId,
)

DeviceDetailsPayload = Union[
    SystemDescriptorModel,
    SystemDescriptor, str, Dict[str, Any],
    None,]

class EntryDict(TypedDict):
    transaction_id: TransactionId
    file_name: FileName
    file_type: str
    capture_time: CaptureTime
    channel_id: Optional[ChannelId]
    device_details: DeviceDetailsPayload
    data: bytes
    mac_address: MacAddressStr

class Sort(enum.Enum):
    CHANNEL_ID      = enum.auto()
    ASCEND_EPOCH    = enum.auto()
    PNM_FILE_TYPE   = enum.auto()
    MAC_ADDRESS     = enum.auto()


TransactionFile             = Tuple[TransactionId, FileName, bytes]
TransactionFileCollection   = List[TransactionFile]
FlatIndex                   = Dict[MacAddressStr, List[EntryDict]]
GroupedIndex                = Dict[MacAddressStr, Dict[int, List[EntryDict]]]
SortOrder                   = List[Sort]
