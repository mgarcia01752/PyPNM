from __future__ import annotations

# SPDX-License-Identifier: MIT

import numpy as np
from typing import List, Tuple, Optional, Literal, cast

from pypnm.lib.qam.code_generator.auto_gen_qam_lut import QamScale
from pypnm.lib.qam.qam_lut import QAM_SYMBOL_CODEWORD_LUT
from pypnm.lib.qam.types import (
    CodeWord, HardDecisionArray, SoftDecisionArray, LutDict,
    QamModulation, SymbolArray
)


class QamLutManager:
    """Accessor/utility for QAM constellation LUTs (hard points, codewords, scaling)."""

    def __init__(self) -> None:
        """Initialize the manager with the global QAM LUT."""
        self.qam_lut: LutDict = QAM_SYMBOL_CODEWORD_LUT

    def _lut_key(self, qam_mod: QamModulation) -> str:
        """Return the LUT key string for a modulation enum.

        Args:
            qam_mod: Modulation order enum.

        Returns:
            String key used in the LUT (e.g., "QAM_256").
        """
        return str(qam_mod.name)

    def get_hard_decisions(self, qam_mod: QamModulation) -> HardDecisionArray:
        """Return the hard-decision constellation points for a modulation.

        Args:
            qam_mod: Modulation order enum.

        Returns:
            List of (I, Q) tuples.
        """
        key = self._lut_key(qam_mod)
        return self.qam_lut[key].get("hard", [])

    def get_codeword_symbol(
        self,
        qam_mod: QamModulation,
        code_word: CodeWord,
        *,
        bit_order: Literal["msb", "lsb"] = "msb",
    ) -> SymbolArray:
        """Map a packed integer codeword to one or more constellation symbols.

        For multi-symbol payloads, bits are split into chunks of size
        bits-per-symbol in MSB-first or LSB-first order.

        Args:
            qam_mod: Modulation order enum.
            code_word: Packed bits representing one or more symbols.
            bit_order: "msb" for most-significant chunk first, "lsb" for least-significant.

        Returns:
            List of (I, Q) tuples (one per symbol).

        Raises:
            ValueError: Missing or malformed LUT.
            KeyError: A sliced codeword is not present in the LUT.
        """
        key = self._lut_key(qam_mod)
        entry = self.qam_lut.get(key)
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
            s = bin(code_word)[2:]
            total_bits_padded = n_syms * bits_per_symbol
            if len(s) < total_bits_padded:
                s = "0" * (total_bits_padded - len(s)) + s
            for i in range(n_syms):
                chunk = s[i * bits_per_symbol : (i + 1) * bits_per_symbol]
                cw = int(chunk, 2)
                symbols.append(self._lookup_symbol(lut, cw))
        else:
            value = code_word
            for i in range(n_syms):
                cw = (value >> (i * bits_per_symbol)) & mask
                symbols.append(self._lookup_symbol(lut, cw))

        return symbols

    def get_scale_factor(self, qam_mod: QamModulation) -> QamScale:
        """Return the LUT-defined normalization scale factor.

        Args:
            qam_mod: Modulation order enum.

        Returns:
            Scale factor as float-like.
        """
        key = self._lut_key(qam_mod)
        entry = self.qam_lut.get(key)
        return cast(QamScale, entry["scale_factor"])

    def scale_soft_decisions(
        self, qam_mod: QamModulation, soft: SoftDecisionArray
    ) -> SoftDecisionArray:
        """Scale soft-decision points by the modulation-specific factor.

        Args:
            qam_mod: Modulation order enum.
            soft: Sequence of (I, Q) pairs.

        Returns:
            Normalized (I, Q) pairs.

        Raises:
            ValueError: Soft array is not shape (N, 2).
        """
        if not soft:
            return []
        scale = float(self.get_scale_factor(qam_mod))
        a = np.asarray(soft, dtype=np.float64)
        if a.ndim != 2 or a.shape[1] != 2:
            raise ValueError(f"soft must be a sequence of (I, Q) pairs; got shape {a.shape}")
        a = a * scale
        return [(float(re), float(im)) for re, im in a]

    def get_symbol_codeword(
        self, qam_mod: QamModulation, symbol: Tuple[float, float]
    ) -> Optional[CodeWord]:
        """Reverse map a constellation point to its codeword.

        Tries exact match, then nearest neighbor with a small tolerance.

        Args:
            qam_mod: Modulation order enum.
            symbol: (I, Q) point.

        Returns:
            Codeword if found, else None.

        Raises:
            ValueError: Missing or malformed LUT.
        """
        key = self._lut_key(qam_mod)
        entry = self.qam_lut.get(key)
        if not entry or "code_words" not in entry:
            raise ValueError(f"No LUT 'code_words' found for {qam_mod.name}")

        lut = entry["code_words"]
        if not lut:
            return None

        i_in, q_in = float(symbol[0]), float(symbol[1])
        for codeword, (i_ref, q_ref) in lut.items():
            if i_in == i_ref and q_in == q_ref:
                return codeword

        ref_points = np.array(list(lut.values()), dtype=np.float64)
        code_keys = np.array(list(lut.keys()), dtype=np.int32)
        deltas = ref_points - np.array([i_in, q_in])
        dist_sq = np.sum(deltas**2, axis=1)
        nearest_idx = int(np.argmin(dist_sq))
        min_dist = float(np.sqrt(dist_sq[nearest_idx]))

        flat = np.unique(ref_points.flatten())
        if flat.size >= 2:
            spacing = np.mean(np.diff(flat))
            tol = spacing * 0.05
        else:
            tol = 0.0

        if min_dist <= tol:
            return int(code_keys[nearest_idx])
        return None

    def infer_modulation_order(
        self, samples: SymbolArray, threshold: float = 0.15
    ) -> QamModulation:
        """Heuristically infer the QAM order from constellation samples.

        Normalizes radius, snaps to a coarse grid, counts clusters, and chooses
        the known order with closest point count. Returns UNKNOWN on mismatch.

        Args:
            samples: Constellation samples [(I, Q), ...].
            threshold: Grid step after normalization.

        Returns:
            Estimated QamModulation value (or UNKNOWN).
        """
        if not samples:
            return QamModulation.UNKNOWN

        pts = np.asarray(samples, dtype=np.float64)
        if pts.ndim != 2 or pts.shape[1] != 2:
            return QamModulation.UNKNOWN

        norms = np.sqrt(np.sum(pts**2, axis=1))
        m = float(np.mean(norms)) if norms.size else 0.0
        if not np.isfinite(m) or m <= 0.0:
            return QamModulation.UNKNOWN
        pts = pts / m

        grid = np.round(pts / threshold) * threshold
        unique_clusters = int(len(np.unique(grid, axis=0)))

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

        closest_order, est_mod = min(
            mapping.items(), key=lambda kv: abs(unique_clusters - kv[0])
        )

        diff_ratio = abs(unique_clusters - closest_order) / float(closest_order)
        if diff_ratio > 0.25:
            return QamModulation.UNKNOWN
        return est_mod

    @staticmethod
    def _infer_bits_per_symbol(keys_sorted: List[int]) -> int:
        """Infer bits-per-symbol from LUT codeword keys.

        Prefers dense key spaces [0 .. 2**k - 1]; otherwise uses the bit length
        of the largest key.

        Args:
            keys_sorted: Sorted list of codeword integers.

        Returns:
            Bits per symbol.

        Raises:
            ValueError: Empty key list.
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
        """Return (I, Q) for a codeword or raise a clear KeyError.

        Args:
            lut: Mapping codeword -> (I, Q).
            cw: Codeword to resolve.

        Returns:
            (I, Q) tuple.

        Raises:
            KeyError: Codeword not in LUT.
        """
        try:
            return lut[cw]
        except KeyError:
            raise KeyError(f"Codeword {cw} not found in LUT")
