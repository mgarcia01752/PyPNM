# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
from enum import Enum

from typing import Dict
from pypnm.lib.types import Complex

CodeWord = int
CodeWordLut = Dict[CodeWord, Complex]

class QamModulation(Enum):
    """Enumeration of supported QAM modulation orders."""
    UNKNOWN     = 0
    QAM_2       = 2
    QAM_4       = 4
    QAM_8       = 8
    QAM_16      = 16
    QAM_32      = 32
    QAM_64      = 64
    QAM_128     = 128
    QAM_256     = 256
    QAM_512     = 512
    QAM_1024    = 1024
    QAM_2048    = 2048
    QAM_4096    = 4096
    QAM_8192    = 8192
    QAM_16384   = 16384
    QAM_32768   = 32768
    QAM_65536   = 65536

    @classmethod
    def from_value(cls, value: int) -> "QamModulation":
        """Return the enum from its integer order (e.g., 64 -> QAM_64)."""
        return cls(value)

    def __str__(self) -> str:
        """Return lowercase name like 'qam_64'."""
        return f"qam_{self.value}"