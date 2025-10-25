# SPDX-License-Identifier: MIT

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import pytest

from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef

DATA_DIR = Path(__file__).parent / "_data"
CE_PATH = DATA_DIR / "channel_estimation.bin"
NON_CE_PATH = DATA_DIR / "rxmer.bin"  # negative test: valid PNM but wrong type

MAC_RE = re.compile(r"^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$")


def _looks_like_pair_seq(x) -> bool:
    """Accept either complex values or [re, im] pairs."""
    if isinstance(x, complex):
        return True
    if isinstance(x, (list, tuple)) and len(x) == 2:
        return all(isinstance(v, (int, float)) for v in x)
    return False


@pytest.fixture(scope="session")
def ce_bytes() -> bytes:
    return CE_PATH.read_bytes()


@pytest.mark.pnm
def test_ce_parses_and_model_shape(ce_bytes):
    ce = CmDsOfdmChanEstimateCoef(ce_bytes).to_model()

    # Basic header fields present
    assert isinstance(ce.channel_id, int)
    assert MAC_RE.match(ce.mac_address)

    # Subcarrier metadata sane
    assert isinstance(ce.subcarrier_spacing, int) and ce.subcarrier_spacing > 0
    assert isinstance(ce.first_active_subcarrier_index, int) and ce.first_active_subcarrier_index >= 0

    # Data length is raw bytes; must be multiple of 4 (2B real + 2B imag)
    assert ce.data_length % 4 == 0

    # Number of complex points = data_length/4
    num_points = ce.data_length // 4
    assert isinstance(ce.values, list) and len(ce.values) == num_points

    # Units
    assert ce.value_units == "complex"

    # OBW equals (#points) * spacing
    assert ce.occupied_channel_bandwidth == num_points * ce.subcarrier_spacing


@pytest.mark.pnm
def test_ce_coeff_rounding_and_raw_access(ce_bytes):
    parser = CmDsOfdmChanEstimateCoef(ce_bytes)

    rounded = parser.get_coefficients("rounded")
    assert isinstance(rounded, list) and all(_looks_like_pair_seq(v) for v in rounded)

    raw = parser.get_coefficients("raw")
    # Raw may be list[complex] (current impl) — accept both shapes
    assert isinstance(raw, list) and len(raw) == len(rounded)
    assert all(_looks_like_pair_seq(v) for v in raw) or all(isinstance(v, complex) for v in raw)


@pytest.mark.pnm
def test_ce_serialization_roundtrip(ce_bytes):
    parser = CmDsOfdmChanEstimateCoef(ce_bytes)

    d = parser.to_dict()
    j = parser.to_json()

    parsed = json.loads(j)
    # Top-level keys must match dict export
    assert set(parsed.keys()) == set(d.keys())


@pytest.mark.pnm
def test_non_ce_file_rejected():
    with pytest.raises(ValueError):
        _ = CmDsOfdmChanEstimateCoef(NON_CE_PATH.read_bytes())
