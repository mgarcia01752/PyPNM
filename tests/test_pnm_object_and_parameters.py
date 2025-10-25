# SPDX-License-Identifier: MIT
# Copyright (c) 2025

from __future__ import annotations

from pathlib import Path

import pytest

from pypnm.pnm.process.pnm_parameter import PnmObjectAndParameters

DATA_DIR = Path(__file__).parent / "_data"

# Map test files to whether we expect support (i.e., a concrete parser is implemented)
CASES = [
    ("channel_estimation.bin", True),   # CmDsOfdmChanEstimateCoef
    ("const_display.bin",      True),   # CmDsConstDispMeas
    ("fec_summary.bin",        True),   # CmDsOfdmFecSummary
    ("modulation_profile.bin", True),   # CmDsOfdmModulationProfile
    ("rxmer.bin",              True),   # CmDsOfdmRxMer
    ("histogram.bin",          False),  # NotImplemented in dispatcher
    ("spectrum_analyzer.bin",  False),  # NotImplemented in dispatcher
]

@pytest.mark.pnm
@pytest.mark.parametrize("fname,supported", CASES)
def test_pnm_object_and_parameters_dispatch(fname: str, supported: bool):
    blob = (DATA_DIR / fname).read_bytes()
    obj = PnmObjectAndParameters(blob).to_dict()

    # Always include a file_type string
    assert isinstance(obj.get("file_type"), str) and len(obj["file_type"]) >= 3

    if supported:
        # Should NOT include 'error'
        assert "error" not in obj, f"Unexpected error for {fname}: {obj.get('error')}"
        # Core fields should be present (may be None for some types, but these should exist)
        for key in (
            "capture_time",
            "channel_id",
            "mac_address",
            "subcarrier_zero_frequency",
            "first_active_subcarrier_index",
            "subcarrier_spacing",
        ):
            assert key in obj

        # Light sanity checks when present
        ch = obj.get("channel_id")
        if isinstance(ch, int):
            assert ch >= 0

        sp = obj.get("subcarrier_spacing")
        if isinstance(sp, int):
            assert sp >= 0

        # MAC format sanity if present
        mac = obj.get("mac_address")
        if isinstance(mac, str):
            # allow “xx:xx:..” or uppercase
            parts = mac.split(":")
            if all(len(p) == 2 for p in parts):
                assert all(0 <= int(p, 16) <= 0xFF for p in parts)

    else:
        # Unsupported handlers should surface an error string
        assert "error" in obj and isinstance(obj["error"], str) and obj["error"], f"No error reported for unsupported {fname}"
