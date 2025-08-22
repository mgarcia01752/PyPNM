# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Iterable

from pypnm.lib.qam.types import QamModulation, SymbolArray

class CodeWordGenerator:
    """
    Generate codewords for QAM modulation schemes.
    """

    def __init__(self):
        pass

    def generate(self, qam_mod:QamModulation , num_of_symbols: int) -> SymbolArray:
        """
        Generate codewords based on the specified bits per symbol.
        """
        bits_per_symbol = qam_mod.get_bit_per_symbol()
        max_codeword = (1 << bits_per_symbol) - 1
        

    def prbs(self, byte_length:int=1) -> Iterable[int]:
        """
        Generate a pseudo-random bit sequence (PRBS) of the specified byte length.
        """
        # Simple PRBS generator using a linear feedback shift register (LFSR)
        lfsr = 0b10101010101010101010101010101010  # Example seed
        for _ in range(byte_length * 8):
            lsb = lfsr & 1
            yield lsb
            # Feedback polynomial: x^8 + x^6 + x^5 + x^4 + 1
            lfsr = (lfsr >> 1) ^ (-(lsb) & 0b10110111)
