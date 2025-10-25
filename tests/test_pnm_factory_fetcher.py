# SPDX-License-Identifier: MIT
# Copyright (c) 2025

from __future__ import annotations

from pathlib import Path
from struct import pack

import pytest

from pypnm.pnm.process.fetch_pnm_process import PnmFileTypeObjectFetcher
from pypnm.pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer
from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef
from pypnm.pnm.process.CmDsConstDispMeas import CmDsConstDispMeas
from pypnm.pnm.process.CmDsHist import CmDsHist
from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pypnm.pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile
from pypnm.pnm.process.CmSpectrumAnalysis import CmSpectrumAnalysis

DATA_DIR = Path(__file__).parent / "_data"

@pytest.mark.pnm
@pytest.mark.parametrize(
    "filename, expected_cls",
    [
        ("rxmer.bin", CmDsOfdmRxMer),
        ("channel_estimation.bin", CmDsOfdmChanEstimateCoef),
        ("const_display.bin", CmDsConstDispMeas),
        ("histogram.bin", CmDsHist),
        ("fec_summary.bin", CmDsOfdmFecSummary),
        ("modulation_profile.bin", CmDsOfdmModulationProfile),
        ("spectrum_analyzer.bin", CmSpectrumAnalysis),
    ],
)
def test_factory_returns_correct_parser(filename, expected_cls):
    blob = (DATA_DIR / filename).read_bytes()
    parser = PnmFileTypeObjectFetcher(blob).get_parser()
    assert isinstance(parser, expected_cls)
    # Smoketest that the parser can materialize a model/dict without exceptions
    assert hasattr(parser, "to_model") or hasattr(parser, "to_dict")
    if hasattr(parser, "to_model"):
        _ = parser.to_model()
    else:
        _ = parser.to_dict()


@pytest.mark.pnm
def test_factory_unknown_type_raises_value_error():
    """
    Build a minimal, valid-looking PNM header with an unknown 3-char type ("PNX")
    so the factory cannot map it to a known parser.
    Header format (standard): '!3sBBBI'
    """
    # file_type="PNX", file_type_num=5, major=1, minor=0, capture_time=0
    header = pack("!3sBBBI", b"PNX", 5, 1, 0, 0)
    with pytest.raises(ValueError):
        PnmFileTypeObjectFetcher(header)
