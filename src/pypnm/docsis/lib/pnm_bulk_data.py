
from __future__ import annotations

import ipaddress

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
from dataclasses import dataclass
from typing import Optional


@dataclass
class DocsPnmBulkDataGroup:
    docsPnmBulkDestIpAddrType: Optional[int]    # e.g., 1 for IPv4, 2 for IPv6
    docsPnmBulkDestIpAddr: Optional[str]        # string form of IP address
    docsPnmBulkDestPath: Optional[str]          # path as a string (URL or file path)
    docsPnmBulkUploadControl: Optional[int]     # control flag or enum

    docsPnmBulkFileName: Optional[str]          # name of the file
    docsPnmBulkFileControl: Optional[int]       # control flag or enum
    docsPnmBulkFileUploadStatus: Optional[int]  # status flag or enum

    def __post_init__(self):
        if self.docsPnmBulkDestIpAddr:
            try:
                ipaddress.ip_address(self.docsPnmBulkDestIpAddr)
            except ValueError:
                raise ValueError(f"Invalid IP address: {self.docsPnmBulkDestIpAddr}")

@dataclass
class DocsPnmBulkFileEntry:
    index: int
    docsPnmBulkFileName: Optional[str] = None
    docsPnmBulkFileControl: Optional[int] = None
    docsPnmBulkFileUploadStatus: Optional[int] = None
