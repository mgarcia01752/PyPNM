# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from typing import Optional
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest
from pypnm.pnm.process.pnm_file_type import PnmFileType


class PnmFileTypeMapper:
    """
    Provides bidirectional mapping between DocsPnmCmCtlTest and PnmFileType enums.
    """

    _test_to_file_type = {
        DocsPnmCmCtlTest.SPECTRUM_ANALYZER: PnmFileType.SPECTRUM_ANALYSIS,
        DocsPnmCmCtlTest.DS_OFDM_SYMBOL_CAPTURE: PnmFileType.SYMBOL_CAPTURE,
        DocsPnmCmCtlTest.DS_OFDM_CHAN_EST_COEF: PnmFileType.OFDM_CHANNEL_ESTIMATE_COEFFICIENT,
        DocsPnmCmCtlTest.DS_CONSTELLATION_DISP: PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY,
        DocsPnmCmCtlTest.DS_OFDM_RXMER_PER_SUBCAR: PnmFileType.RECEIVE_MODULATION_ERROR_RATIO,
        DocsPnmCmCtlTest.DS_HISTOGRAM: PnmFileType.DOWNSTREAM_HISTOGRAM,
        DocsPnmCmCtlTest.US_PRE_EQUALIZER_COEF: PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS,
        DocsPnmCmCtlTest.DS_OFDM_MODULATION_PROFILE: PnmFileType.OFDM_MODULATION_PROFILE,
        DocsPnmCmCtlTest.LATENCY_REPORT: PnmFileType.LATENCY_REPORT,
    }

    # Automatically invert the mapping
    _file_type_to_test = {v: k for k, v in _test_to_file_type.items()}

    @classmethod
    def get_file_type(cls, test: DocsPnmCmCtlTest) -> Optional[PnmFileType]:
        return cls._test_to_file_type.get(test)

    @classmethod
    def get_test_type(cls, file_type: PnmFileType) -> Optional[DocsPnmCmCtlTest]:
        return cls._file_type_to_test.get(file_type)
