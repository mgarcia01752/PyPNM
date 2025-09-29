# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import struct
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from pypnm.lib.types import CaptureTime
from pypnm.pnm.process.pnm_file_type import PnmFileType

class PnmHeaderParameters(BaseModel):
    """Typed fields parsed from a PNM header."""

    file_type: Optional[str]            = Field(None, description="PNM file type identifier (e.g., 'PNN')")
    file_type_version: Optional[int]    = Field(None, description="Numeric version of the file type (e.g., 10 for PNN10)")
    major_version: Optional[int]        = Field(None, description="Major version of the PNM format")
    minor_version: Optional[int]        = Field(None, description="Minor version of the PNM format")
    capture_time:CaptureTime            = Field(description="Capture timestamp as epoch seconds since 1970-01-01")


class PnmHeaderModel(BaseModel):
    """Model wrapper for PNM header parameters."""
    pnm_header: PnmHeaderParameters


class PnmHeader:
    """
    Parser for PNM headers.

    Formats
    -------
    - Special (little-endian) when byte_array[3] == 8:
        '<3sBBB'  -> file_type(3s), file_type_num(u8), major(u8), minor(u8)
        (no capture_time)
    - Standard (big-endian/network) otherwise:
        '!3sBBBI' -> file_type(3s), file_type_num(u8), major(u8), minor(u8), capture_time(u32)
    """

    _FMT_LE: str = "<3sBBB"   # special case (no capture_time)
    _FMT_BE: str = "!3sBBBI"  # standard (with capture_time)

    def __init__(self, byte_array: bytes) -> None:
        """
        Initialize and parse a PNM header from raw bytes.

        Args:
            byte_array: Raw file bytes starting at the PNM header.
        """
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

        self._pnmheader_model: PnmHeaderModel
        self._parameters: PnmHeaderParameters
        self._file_type: Optional[bytes] = None
        self._file_type_num: Optional[int] = None
        self._major_version: Optional[int] = None
        self._minor_version: Optional[int] = None
        self._capture_time: Optional[int] = None
        self.pnm_data: bytes = b""

        self.__parse_header(byte_array)
        self.__build_pnm_header_model()

    def __parse_header(self, byte_array: bytes) -> None:
        """
        Internal: parse header fields and slice payload.

        Raises:
            ValueError: If byte_array is too short to contain a header.
        """
        if not isinstance(byte_array, (bytes, bytearray)) or len(byte_array) < 4:
            raise ValueError("byte_array must be bytes-like and at least 4 bytes long")

        special: int = struct.unpack("<B", byte_array[3:4])[0]

        if special == 8:
            fmt = self._FMT_LE
            size = struct.calcsize(fmt)
            if len(byte_array) < size:
                raise ValueError("insufficient bytes for little-endian header")
            self._file_type, self._file_type_num, self._major_version, self._minor_version = struct.unpack(
                fmt, byte_array[:size]
            )
        else:
            fmt = self._FMT_BE
            size = struct.calcsize(fmt)
            if len(byte_array) < size:
                raise ValueError("insufficient bytes for big-endian header")
            (
                self._file_type,
                self._file_type_num,
                self._major_version,
                self._minor_version,
                self._capture_time,
            ) = struct.unpack(fmt, byte_array[:size])

        self.pnm_data = bytes(byte_array[size:])

    def __build_pnm_header_model(self):
        self._parameters = PnmHeaderParameters(
            file_type           =   self._file_type.decode("utf-8").strip() if self._file_type else None,
            file_type_version   =   self._file_type_num,
            major_version       =   self._major_version,
            minor_version       =   self._minor_version,
            capture_time        =   self._capture_time,
        )
        self._pnmheader_model = PnmHeaderModel(pnm_header=self._parameters)
    
    def getPnmHeaderModel(self) -> PnmHeaderModel:
        """
        Build a Pydantic model representing the parsed header.

        Returns:
            PnmHeaderModel: Structured header model.
        """
        return self._pnmheader_model
    
    def getPnmHeaderParameterModel(self) -> PnmHeaderParameters:
        return self._parameters

    def _to_dict(self, header_only: bool = False) -> Dict[str, Any]:
        """
        Serialize the header using Pydantic's model_dump.

        Args:
            header_only: When True, omit payload hex.

        Returns:
            Dict[str, Any]: {"pnm_header": {...}} plus optional "data".
        """
        out: Dict[str, Any] = self.getPnmHeaderModel().model_dump(exclude_none=True)
        if not header_only:
            out["data"] = self.pnm_data.hex()
        return out

    def getPnmHeader(self, header_only: bool = False) -> Dict[str, Any]:
        """
        Public getter maintained for backward compatibility.

        Args:
            header_only: When True, omit payload hex.

        Returns:
            Dict[str, Any]: Header dictionary.
        """
        return self._to_dict(header_only)

    def get_pnm_file_type(self) -> Optional[PnmFileType]:
        """
        Map parsed (file_type + version) to a PnmFileType enum, if known.

        Returns:
            Optional[PnmFileType]: Matching enum or None if unrecognized.
        """
        if self._file_type and self._file_type_num is not None:
            pnm_id: str = f"{self._file_type.decode('utf-8').strip()}{self._file_type_num}"
            for t in PnmFileType:
                if t.value == pnm_id:
                    return t
        return None

    @classmethod
    def from_bytes(cls, data: bytes) -> "PnmHeader":
        """
        Alternate constructor.

        Args:
            data: Raw bytes.

        Returns:
            PnmHeader: Parsed instance.
        """
        return cls(data)
