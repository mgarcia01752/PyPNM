# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Tuple

from pypnm.api.routes.common.extended.common_measure_service import CommonMeasureService
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.schemas import SpectrumAnalyzerParameters
from pypnm.config.pnm_config_manager import PnmConfigManager
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
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
        spec_analyzer_para (SpectrumAnalyzerParameters): 
            Schema object containing all spectrum-analyzer-specific parameters:
                - inactivity_timeout (int): Timeout in seconds to wait before the spectrum analysis operation is considered failed due to inactivity (default: 100).
                - first_segment_center_freq (int): Frequency in Hz of the first segment center (default: 108_000_000).
                - last_segment_center_freq (int): Frequency in Hz of the last segment center (default: 1_002_000_000).
                - segment_freq_span (int): Frequency span in Hz of each segment (default: 1_000_000).
                - num_bins_per_segment (int): Number of FFT bins per segment (default: 256).
                - noise_bw (int): Equivalent noise bandwidth in kHz (default: 150).
                - window_function (WindowFunction): FFT window function applied during analysis (default: WindowFunction.HANN).
                - num_averages (int): Number of averages performed per segment (default: 1).
                - spectrum_retrieval_type (SpectrumRetrievalType): Specifies how spectrum data is retrieved (default: SpectrumRetrievalType.FILE).
        snmp_write_community (str, optional): SNMP community string with write access, obtained from the cable modem.
            Passed internally; not typically set manually.
    """

    def __init__(self,
        cable_modem: CableModem,
        tftp_servers: Tuple[Inet, Inet] = PnmConfigManager.get_tftp_servers(),
        tftp_path: str = PnmConfigManager.get_tftp_path(),*,
        spec_analyzer_para: SpectrumAnalyzerParameters,):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        inactivity_timeout = spec_analyzer_para.inactivity_timeout
        first_segment_center_freq = spec_analyzer_para.first_segment_center_freq
        last_segment_center_freq = spec_analyzer_para.last_segment_center_freq
        segment_freq_span = spec_analyzer_para.segment_freq_span
        num_bins_per_segment = spec_analyzer_para.num_bins_per_segment
        noise_bw = spec_analyzer_para.noise_bw
        window_function = spec_analyzer_para.window_function
        num_averages = spec_analyzer_para.num_averages
        spectrum_retrieval_type = spec_analyzer_para.spectrum_retrieval_type

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
            spectrum_retrieval_type=spectrum_retrieval_type,)
