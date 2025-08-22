# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia
from enum import IntEnum
import math
from typing import Dict, List, Mapping, Union
from pypnm.lib.types import Complex

LutDict = Mapping[str, Mapping[str, object]]
CodeWord = Union[int]
CodeWordArray = List[CodeWord]
QamSymbol = Complex
CodeWordLut = Dict[CodeWord, QamSymbol]
QamSymCwLut = Dict[str, CodeWordLut]
HardDecisionArray = List[QamSymbol]
SymbolArray = List[QamSymbol]

class QamModulation(IntEnum):
    """Enumeration of supported QAM modulation orders."""

    UNKNOWN = 0
    QAM_2 = 2
    QAM_4 = 4
    QAM_8 = 8
    QAM_16 = 16
    QAM_32 = 32
    QAM_64 = 64
    QAM_128 = 128
    QAM_256 = 256
    QAM_512 = 512
    QAM_1024 = 1024
    QAM_2048 = 2048
    QAM_4096 = 4096
    QAM_8192 = 8192
    QAM_16384 = 16384
    QAM_32768 = 32768
    QAM_65536 = 65536

    @classmethod
    def from_value(cls, value: int) -> "QamModulation":
        """Return the enum from its integer order (e.g., 64 -> QAM_64)."""
        return cls(value)

    def get_bit_per_symbol(self) -> int:
        """Return the number of bits per symbol for the modulation scheme."""
        return int(math.log2(self.value))

    def __str__(self) -> str:
        """Return lowercase name like 'qam_64'."""
        return f"qam_{self.value}"


__all__ = [
    "LutDict",
    "CodeWord",
    "QamSymbol",
    "CodeWordLut",
    "QamSymCwLut",
    "HardDecisionArray",
    "SymbolArray",
    "QamModulation",
]
