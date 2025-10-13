from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import numpy as np
from typing import List, Tuple, Optional, Literal, cast

from pypnm.lib.qam.code_generator.auto_gen_qam_lut import QamScale
from pypnm.lib.qam.qam_lut import QAM_SYMBOL_CODEWORD_LUT
from pypnm.lib.qam.types import (
    CodeWord, HardDecisionArray, SoftDecisionArray, LutDict,
    QamModulation, SymbolArray
)


class QamLutManager:
    """
    Manage QAM LUT access for hard-decision points, codeword mapping,
    and soft-decision scaling.

    Assumptions
    -----------
    - self.qam_lut[qam_mod.name] is a dict with at least:
        {
          "hard": HardDecisionArray,            # list of (I,Q)
          "code_words": { int: (I,Q), ... }     # codeword -> (I,Q)
          "scale_factor": float                 # normalization constant
        }
    """

    def __init__(self) -> None:
        self.qam_lut: LutDict = QAM_SYMBOL_CODEWORD_LUT

    # -------------------------------------------------------------------------
    # Core Accessors
    # -------------------------------------------------------------------------
    def get_hard_decisions(self, qam_mod: QamModulation) -> HardDecisionArray:
        """
        Return the constellation hard-decision points for the given modulation.
        """
        hd: HardDecisionArray = self.qam_lut[qam_mod.name.__str__()].get("hard", [])
        return hd

    def get_codeword_symbol(
        self,
        qam_mod: QamModulation,
        code_word: CodeWord,
        *,
        bit_order: Literal["msb", "lsb"] = "msb",
    ) -> SymbolArray:
        """
        Map a packed integer `code_word` to one or more constellation symbols.

        Supports MSB-first or LSB-first bit unpacking.
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
        n_syms = (total_bits + bits_per_symbol - 1) // bits_per_symbol

        symbols: SymbolArray = []

        if bit_order == "msb":
            pad = (bits_per_symbol - (total_bits % bits_per_symbol)) % bits_per_symbol
            value = code_word << pad
            total_bits += pad
            for i in range(n_syms):
                shift = total_bits - (i + 1) * bits_per_symbol
                cw = (value >> shift) & mask
                symbols.append(self._lookup_symbol(lut, cw))
        else:
            value = code_word
            for i in range(n_syms):
                cw = (value >> (i * bits_per_symbol)) & mask
                symbols.append(self._lookup_symbol(lut, cw))

        return symbols

    def get_scale_factor(self, qam_mod: QamModulation) -> QamScale:
        """
        Retrieve the modulation-specific scale factor used for normalization.
        """
        entry = self.qam_lut.get(qam_mod.name)
        return cast(QamScale, entry["scale_factor"])

    def scale_soft_decisions(
        self, qam_mod: QamModulation, soft: SoftDecisionArray
    ) -> SoftDecisionArray:
        """
        Scale soft-decision IQ points by the modulation-specific normalization factor.
        """
        if not soft:
            return []

        scale = float(self.get_scale_factor(qam_mod))
        a = np.asarray(soft, dtype=np.float64)
        if a.ndim != 2 or a.shape[1] != 2:
            raise ValueError(
                f"soft must be a sequence of (I, Q) pairs; got shape {a.shape}"
            )
        a = a * scale
        return [(float(re), float(im)) for re, im in a]

    # -------------------------------------------------------------------------
    # NEW METHOD 1: Reverse lookup (symbol → codeword)
    # -------------------------------------------------------------------------
    def get_symbol_codeword(
        self, qam_mod: QamModulation, symbol: Tuple[float, float]
    ) -> Optional[CodeWord]:
        """
        Reverse-map a constellation symbol `(I, Q)` to its corresponding codeword.

        Performs exact match first, then nearest-neighbor search if necessary.
        """
        entry = self.qam_lut.get(qam_mod.name)
        if not entry or "code_words" not in entry:
            raise ValueError(f"No LUT 'code_words' found for {qam_mod.name}")

        lut = entry["code_words"]
        if not lut:
            return None

        i_in, q_in = float(symbol[0]), float(symbol[1])
        for codeword, (i_ref, q_ref) in lut.items():
            if i_in == i_ref and q_in == q_ref:
                return codeword

        # Fallback: nearest neighbor in Euclidean space
        ref_points = np.array(list(lut.values()), dtype=np.float64)
        code_keys = np.array(list(lut.keys()), dtype=np.int32)
        deltas = ref_points - np.array([i_in, q_in])
        dist_sq = np.sum(deltas**2, axis=1)
        nearest_idx = int(np.argmin(dist_sq))
        min_dist = float(np.sqrt(dist_sq[nearest_idx]))

        tol = np.mean(np.diff(np.unique(ref_points.flatten()))) * 0.05
        if min_dist <= tol:
            return int(code_keys[nearest_idx])
        return None

    # -------------------------------------------------------------------------
    # NEW METHOD 2: Auto-detect modulation order
    # -------------------------------------------------------------------------
    def infer_modulation_order(
        self, samples: SymbolArray, threshold: float = 0.15
    ) -> QamModulation:
        """
        Infer the most probable QAM modulation order from constellation samples.

        Uses cluster counting and spacing analysis to approximate known orders.
        """
        if not samples:
            return QamModulation.UNKNOWN

        pts = np.asarray(samples, dtype=np.float64)
        if pts.ndim != 2 or pts.shape[1] != 2:
            raise ValueError(f"Invalid sample shape {pts.shape}; expected Nx2 array")

        norm = np.mean(np.sqrt(np.sum(pts**2, axis=1)))
        if norm <= 0:
            return QamModulation.UNKNOWN
        pts /= norm

        grid = np.round(pts / threshold) * threshold
        unique_clusters = len(np.unique(grid, axis=0))

        mapping = {
            2:      QamModulation.QAM_2,
            4:      QamModulation.QAM_4,
            8:      QamModulation.QAM_8,
            16:     QamModulation.QAM_16,
            32:     QamModulation.QAM_32,
            64:     QamModulation.QAM_64,
            128:    QamModulation.QAM_128,
            256:    QamModulation.QAM_256,
            512:    QamModulation.QAM_512,
            1024:   QamModulation.QAM_1024,
            2048:   QamModulation.QAM_2048,
            4096:   QamModulation.QAM_4096,
            8192:   QamModulation.QAM_8192,
            16384:  QamModulation.QAM_16384,
            32768:  QamModulation.QAM_32768,
            65536:  QamModulation.QAM_65536,
        }


        best_match = min(mapping.items(), key=lambda kv: abs(unique_clusters - kv[0]))
        est_mod = best_match[1]
        expected_points = best_match[0]
        diff_ratio = abs(unique_clusters - expected_points) / expected_points

        if diff_ratio > 0.25:
            return QamModulation.UNKNOWN
        return est_mod

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def _infer_bits_per_symbol(keys_sorted: List[int]) -> int:
        """
        Infer bits-per-symbol from LUT keys.

        Prefers dense keyspaces [0 .. 2^k - 1].
        """
        if not keys_sorted:
            raise ValueError("Cannot infer bits/symbol from empty key set")

        m = len(keys_sorted)
        max_key = keys_sorted[-1]

        if (m & (m - 1)) == 0 and keys_sorted[0] == 0 and max_key == m - 1:
            return (m - 1).bit_length()

        return max(1, max_key.bit_length())

    @staticmethod
    def _lookup_symbol(lut: dict, cw: int):
        """
        Safe LUT lookup with a clear error if a codeword isn't present.
        """
        try:
            return lut[cw]
        except KeyError:
            raise KeyError(f"Codeword {cw} not found in LUT")
