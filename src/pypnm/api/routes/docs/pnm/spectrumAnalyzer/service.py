# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Tuple
from pypnm.api.routes.common.extended.common_measure_service import CommonMeasureService
from pypnm.config.pnm_config_manager import PnmConfigManager
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.pnm.data_type.DocsIf3CmSpectrumAnalysisCtrlCmd import SpectrumRetrievalType, WindowFunction
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest

class CmSpectrumAnalysisService(CommonMeasureService):
    """
    Service class for managing CM Spectrum Analysis operations.

    This service runs the spectrum analyzer test on a specified cable modem,
    handling all relevant SNMP and TFTP parameters with sensible defaults.

    Parameters:
        cable_modem (CableModem): The target cable modem instance on which to run the test.
        tftp_servers (Tuple[Inet, Inet], optional): Tuple of IP addresses of the TFTP servers used for storing/retrieving result files.
            Defaults to the configured TFTP servers via `PnmConfigManager.get_tftp_servers()`.
        tftp_path (str, optional): Directory path on the TFTP server where output files are stored.
            Defaults to the configured path via `PnmConfigManager.get_tftp_path()`.
        inactivity_timeout (int, optional): Timeout in seconds to wait before the spectrum analysis operation is considered failed due to inactivity.
            Defaults to 100 seconds.
        first_segment_center_freq (int, optional): Frequency in Hz of the first segment center.
            Defaults to 108,000,000 Hz (108 MHz).
        last_segment_center_freq (int, optional): Frequency in Hz of the last segment center.
            Defaults to 1,002,000,000 Hz (1002 MHz).
        segment_freq_span (int, optional): Frequency span in Hz of each segment.
            Defaults to 1,000,000 Hz (1 MHz).
        num_bins_per_segment (int, optional): Number of FFT bins per segment.
            Defaults to 256.
        noise_bw (int, optional): Equivalent noise bandwidth in kHz.
            Defaults to 150 kHz.
        window_function (WindowFunction, optional): FFT window function applied during analysis.
            Defaults to `WindowFunction.HANN`.
        num_averages (int, optional): Number of averages performed per segment.
            Defaults to 1.
        spectrum_retrieval_type (SpectrumRetrievalType, optional): Specifies how spectrum data is retrieved (e.g., via file or SNMP).
            Defaults to `SpectrumRetrievalType.FILE`.
        snmp_write_community (str, optional): SNMP community string with write access, obtained from the cable modem.
            Passed internally; not typically set manually.
    """

    def __init__(self,
        cable_modem: CableModem,
        tftp_servers: Tuple[Inet, Inet] = PnmConfigManager.get_tftp_servers(),
        tftp_path: str = PnmConfigManager.get_tftp_path(),
        *,
        inactivity_timeout: int = 100,
        first_segment_center_freq: int = 108_000_000,
        last_segment_center_freq: int = 1_002_000_000,
        segment_freq_span: int = 1000000,
        num_bins_per_segment: int = 256,
        noise_bw: int = 150,
        window_function: WindowFunction = WindowFunction.HANN,
        num_averages: int = 1,
        spectrum_retrieval_type: SpectrumRetrievalType = SpectrumRetrievalType.FILE,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(
            DocsPnmCmCtlTest.SPECTRUM_ANALYZER,
            cable_modem,
            tftp_servers,
            tftp_path,
            cable_modem.getWriteCommunity(),
            inactivity_timeout=inactivity_timeout,
            first_segment_center_freq=first_segment_center_freq,
            last_segment_center_freq=last_segment_center_freq,
            segment_freq_span=segment_freq_span,
            num_bins_per_segment=num_bins_per_segment,
            noise_bw=noise_bw,
            window_function=window_function,
            num_averages=num_averages,
            spectrum_retrieval_type=spectrum_retrieval_type,
        )
