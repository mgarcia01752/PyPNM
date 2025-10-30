# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import pytest

from pypnm.pnm.lib.fixed_point_decoder import (
    FixedPointDecoder,
    IntegerBits,
    FractionalBits,
)

def _q(a: int, b: int):
    return (IntegerBits(a), FractionalBits(b))

def _frac_bits(q) -> int:
    # q = (IntegerBits, FractionalBits) → cast to plain int
    return int(q[1])

def _pack_q_pair(re: float, im: float, q, *, signed: bool = True) -> bytes:
    """Encode one complex sample (little-endian) for generic Q(a,b) with 16-bit components."""
    scale = 2 ** _frac_bits(q)

    def to_u16(v: float) -> int:
        n = int(round(v * scale))
        if signed:
            return n & 0xFFFF  # two's complement wrapping into 16 bits
        return max(0, min(0xFFFF, n))

    re_u = to_u16(re)
    im_u = to_u16(im)
    return re_u.to_bytes(2, "little", signed=False) + im_u.to_bytes(2, "little", signed=False)


def test_decode_fixed_point_signed_q1_14_basic() -> None:
    # Q(1,14) => total bits = 16 (byte-aligned)
    q = _q(1, 14)
    # +1.0 -> 0x4000
    assert FixedPointDecoder.decode_fixed_point(0x4000, q, signed=True) == pytest.approx(1.0)
    # +0.25 -> 0x1000
    assert FixedPointDecoder.decode_fixed_point(0x1000, q, signed=True) == pytest.approx(0.25)
    # -1.0  -> 0xC000 in two's complement
    assert FixedPointDecoder.decode_fixed_point(0xC000, q, signed=True) == pytest.approx(-1.0)
    # -0.5  -> 0xE000
    assert FixedPointDecoder.decode_fixed_point(0xE000, q, signed=True) == pytest.approx(-0.5)


def test_decode_fixed_point_unsigned_q1_14() -> None:
    q = _q(1, 14)
    # No two's-complement adjustment when signed=False
    # 0x7FFF / 2^14 ≈ 1.999939
    val = FixedPointDecoder.decode_fixed_point(0x7FFF, q, signed=False)
    assert val == pytest.approx(0x7FFF / (2 ** 14))


def test_decode_fixed_point_rejects_non_byte_aligned() -> None:
    # Q(1,15) => total bits = 17 (not multiple of 8) should be rejected in complex decoder
    q_bad = _q(1, 15)

    # Single value path still computes (it doesn't enforce alignment), but complex decoder should fail.
    assert FixedPointDecoder.decode_fixed_point(0x1, q_bad, signed=True) == pytest.approx(1 / (2 ** 15))

    # Now ensure decode_complex_data raises
    with pytest.raises(ValueError, match="must be a multiple of 8"):
        FixedPointDecoder.decode_complex_data(b"\x00" * 8, q_bad, signed=True)


def test_decode_complex_data_q1_14_two_samples_signed() -> None:
    q = _q(1, 14)
    # Build two samples: (1.0, -0.5) and (0.25, 0.0)
    blob = b"".join([
        _pack_q_pair(1.0, -0.5, q, signed=True),
        _pack_q_pair(0.25, 0.0, q, signed=True),
    ])
    out = FixedPointDecoder.decode_complex_data(blob, q, signed=True)
    assert isinstance(out, list)
    assert len(out) == 2
    assert out[0].real == pytest.approx(1.0)
    assert out[0].imag == pytest.approx(-0.5)
    assert out[1].real == pytest.approx(0.25)
    assert out[1].imag == pytest.approx(0.0)


def test_decode_complex_data_invalid_length() -> None:
    q = _q(1, 14)  # 16 bits per component, 4 bytes per complex
    with pytest.raises(ValueError, match="data length must be a multiple of the complex number size"):
        FixedPointDecoder.decode_complex_data(b"\x00\x01\x02", q, signed=True)  # 3 bytes (invalid)


def test_decode_complex_data_unsigned_mode() -> None:
    q = _q(1, 14)
    # In unsigned mode, high-bit values are interpreted as large positives (no two's complement)
    # Use raw ints: 0x7FFF (~1.99994) for real, 0x2000 (0.5) for imag
    blob = (0x7FFF).to_bytes(2, "little") + (0x2000).to_bytes(2, "little")
    vals = FixedPointDecoder.decode_complex_data(blob, q, signed=False)
    assert len(vals) == 1
    re, im = vals[0].real, vals[0].imag
    assert re == pytest.approx(0x7FFF / (2 ** 14))
    assert im == pytest.approx(0.5)


def test_decode_complex_data_multiple_samples_roundtrip_like() -> None:
    q = _q(1, 14)
    samples = [(0.0, 0.0), (0.5, 0.5), (-0.75, 0.25), (1.0, -1.0)]
    blob = b"".join(_pack_q_pair(r, i, q) for (r, i) in samples)
    out = FixedPointDecoder.decode_complex_data(blob, q, signed=True)
    assert len(out) == len(samples)
    for got, exp in zip(out, samples):
        assert got.real == pytest.approx(exp[0], abs=1e-4)
        assert got.imag == pytest.approx(exp[1], abs=1e-4)
