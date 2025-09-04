
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import re
import json
from dataclasses import dataclass
from typing import ClassVar, Dict

from pydantic import BaseModel

@dataclass(frozen=True)
class SystemDescriptor:
    """
    Parsed representation of a sysDescr string with fields:
      - hw_rev   : hardware revision
      - vendor   : device vendor
      - boot_rev : bootloader revision
      - sw_rev   : software revision
      - model    : device model

    Provides parsing, serialization, and an "empty" factory.
    """
    hw_rev: str
    vendor: str
    boot_rev: str
    sw_rev: str
    model: str
    is_empty:bool = False

    _PATTERN: ClassVar[re.Pattern] = re.compile(r"<<\s*(.*?)\s*>>")

    @classmethod
    def parse(cls, sys_descr: str) -> "SystemDescriptor":
        """
        Parse a sysDescr string of the form:
           <<HW_REV: xxx; VENDOR: xxx; BOOTR: xxx; SW_REV: xxx; MODEL: xxx>>
        Returns a SysDescr instance.
        """
        match = cls._PATTERN.search(sys_descr)
        if not match:
            raise ValueError(f"Invalid format, missing <<...>>: {sys_descr}")
        content = match.group(1)
        entries = [item.strip() for item in content.split(";") if item.strip()]
        data: Dict[str, str] = {}
        for entry in entries:
            if ':' not in entry:
                raise ValueError(f"Invalid field entry '{entry}' in sysDescr")
            key, val = [part.strip() for part in entry.split(':', 1)]
            data[key] = val
        try:
            return cls(
                hw_rev=data['HW_REV'],
                vendor=data['VENDOR'],
                boot_rev=data['BOOTR'],
                sw_rev=data['SW_REV'],
                model=data['MODEL'],
            )
        except KeyError as e:
            raise ValueError(f"Missing expected field {e.args[0]} in sysDescr: {sys_descr}")

    def to_dict(self) -> Dict[str, str]:
        """
        Serialize the SysDescr fields to a dict.
        """
        return {
            'HW_REV': self.hw_rev,
            'VENDOR': self.vendor,
            'BOOTR': self.boot_rev,
            'SW_REV': self.sw_rev,
            'MODEL': self.model,
        }

    def to_json(self) -> str:
        """
        Serialize the SysDescr fields to a JSON string.
        """
        return json.dumps(self.to_dict())

    @classmethod
    def load_from_dict(cls, data: Dict[str, str]) -> "SystemDescriptor":
        """
        Load a SysDescr from a dictionary.
        """
        return cls(
            hw_rev=data.get('HW_REV', ''),
            vendor=data.get('VENDOR', ''),
            boot_rev=data.get('BOOTR', ''),
            sw_rev=data.get('SW_REV', ''),
            model=data.get('MODEL', '')
        )
    
    @classmethod
    def empty(cls) -> "SystemDescriptor":
        """
        Return an empty SysDescr (all fields blank).
        """
        cls.is_empty = True
        return cls(hw_rev="", vendor="", boot_rev="", sw_rev="", model="")

    def __str__(self) -> str:
        """
        Return a string representation of the SysDescr.
        """
        return f"<< HW_REV: {self.hw_rev}; VENDOR: {self.vendor}; BOOTR: {self.boot_rev}; SW_REV: {self.sw_rev}; MODEL: {self.model} >>"

    def __hash__(self) -> int:
        return hash((self.hw_rev, self.vendor, self.boot_rev, self.sw_rev, self.model))

    def __repr__(self) -> str:
        return f"SystemDescriptor(hw_rev={self.hw_rev!r}, vendor={self.vendor!r}, boot_rev={self.boot_rev!r}, sw_rev={self.sw_rev!r}, model={self.model!r})"
    