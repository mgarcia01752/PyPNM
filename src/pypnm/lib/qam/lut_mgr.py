
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from pypnm.lib.qam.code_generator.auto_gen_qam_lut import QamScale
from pypnm.lib.qam.qam_lut import QAM_SYMBOL_CODEWORD_LUT
from typing import List, Literal, cast

from pypnm.lib.qam.types import (
    CodeWord, HardDecisionArray, SoftDecisionArray, LutDict, QamModulation, SymbolArray)

class QamLutManager:
    """
    Manage QAM LUT access for hard-decision points and codeword→symbol mapping.

    Assumptions
    -----------
    - self.qam_lut[qam_mod.name] is a dict with at least:
        {
          "hard": HardDecisionArray,            # list of (I,Q)
          "code_words": { int: (I,Q), ... }     # codeword -> (I,Q)
        }
    - 'code_words' keys ideally form a dense range [0 .. 2^k - 1] so that
      k = bits-per-symbol can be inferred unambiguously.
    """

    def __init__(self) -> None:
        self.qam_lut: LutDict = QAM_SYMBOL_CODEWORD_LUT

    def get_hard_decisions(self, qam_mod: QamModulation) -> HardDecisionArray:
        """
        Return the constellation hard-decision points for the given modulation.

        Parameters
        ----------
        qam_mod : QamModulation

        Returns
        -------
        HardDecisionArray
            List of (I, Q) tuples for the modulation's constellation.
        """
        hd:HardDecisionArray = self.qam_lut[qam_mod.name.__str__()].get('hard', [])
        return hd

    def get_codeword_symbol(self, qam_mod: QamModulation,
        code_word: CodeWord,
        *,
        bit_order: Literal["msb", "lsb"] = "msb",) -> SymbolArray:
        """
        Map a packed integer `code_word` to one or more constellation symbols.

        If `code_word` encodes more than one symbol (i.e., more than k bits,
        where k = bits-per-symbol inferred from the LUT), it is split into k-bit
        chunks and each chunk is mapped to its (I, Q) point in stream order.

        Parameters
        ----------
        qam_mod : QamModulation
            Target modulation (selects the LUT slice).
        code_word : int
            Packed bits to map. May contain 1 or multiple k-bit symbols.
        bit_order : {"msb", "lsb"}, default "msb"
            How to chunk the packed integer:
              - "msb": take the highest-order k bits first (network/MSB-first).
              - "lsb": take the lowest-order k bits first.

        Returns
        -------
        SymbolArray
            A list of (I, Q) tuples corresponding to the decoded symbols.

        Raises
        ------
        KeyError
            If any k-bit chunk does not exist in the LUT.
        ValueError
            If the LUT is missing or malformed for the given modulation.
        """
        entry = self.qam_lut.get(qam_mod.name)
        if not entry or "code_words" not in entry:
            raise ValueError(f"Missing 'code_words' LUT for {qam_mod.name}")

        lut = entry["code_words"]
        if not isinstance(lut, dict) or not lut:
            raise ValueError(f"Empty or invalid 'code_words' LUT for {qam_mod.name}")

        keys_sorted = sorted(lut.keys())
        bits_per_symbol = self._infer_bits_per_symbol(keys_sorted)

        mask = (1 << bits_per_symbol) - 1
        total_bits = max(1, code_word.bit_length())

        # Number of full symbols contained in the packed integer
        n_syms = (total_bits + bits_per_symbol - 1) // bits_per_symbol

        symbols: SymbolArray = []

        if bit_order == "msb":
            # Left-pad to align to a multiple of k bits, then peel from the top
            pad = (bits_per_symbol - (total_bits % bits_per_symbol)) % bits_per_symbol
            value = code_word << pad
            total_bits += pad
            for i in range(n_syms):
                shift = total_bits - (i + 1) * bits_per_symbol
                cw = (value >> shift) & mask
                symbols.append(self._lookup_symbol(lut, cw))
        else:
            # LSB-first: peel k bits at a time from the right
            value = code_word
            for i in range(n_syms):
                cw = (value >> (i * bits_per_symbol)) & mask
                symbols.append(self._lookup_symbol(lut, cw))

        return symbols

    def get_scale_factor(self,qam_mod: QamModulation) -> QamScale:
        entry = self.qam_lut.get(qam_mod.name)
        return cast(QamScale, entry['scale_factor'])

    def scale_soft_decisions(self, qam_mod: QamModulation, soft: SoftDecisionArray) -> SoftDecisionArray:
        """
        Scale soft-decision IQ points by the modulation-specific factor.

        Parameters
        ----------
        qam_mod : QamModulation
            Modulation used to derive the scale factor.
        soft : SoftDecisionArray
            List of (I, Q) float pairs.

        Returns
        -------
        SoftDecisionArray
            New list with each pair scaled by `scale`.
        """
        if not soft:
            return []
        
        scale = float(self.get_scale_factor(qam_mod))

        a = np.asarray(soft, dtype=np.float64)
        if a.ndim != 2 or a.shape[1] != 2:
            raise ValueError(f"soft must be a sequence of (I, Q) pairs; got shape {a.shape}")
        a = a * scale
        return [(float(re), float(im)) for re, im in a]

    # ----------------------------
    # Helpers
    # ----------------------------
    @staticmethod
    def _infer_bits_per_symbol(keys_sorted: List[int]) -> int:
        """
        Infer bits-per-symbol from LUT keys.

        Prefer the dense case: keys == [0 .. 2^k - 1].
        Otherwise, fall back to bit_length(max_key).
        """
        if not keys_sorted:
            raise ValueError("Cannot infer bits/symbol from empty key set")

        m = len(keys_sorted)
        max_key = keys_sorted[-1]

        # Dense power-of-two keyspace?
        if (m & (m - 1)) == 0 and keys_sorted[0] == 0 and max_key == m - 1:
            return (m - 1).bit_length()

        # Fallback: enough bits to represent the largest key
        return max(1, max_key.bit_length())

    @staticmethod
    def _lookup_symbol(lut: dict, cw: int):
        """
        Safe LUT lookup with a clear error if a codeword isn't present.
        """
        try:
            return lut[cw]
        except KeyError:
            raise KeyError(f"Codeword {cw} not found in LUT")  # re-raise with context



