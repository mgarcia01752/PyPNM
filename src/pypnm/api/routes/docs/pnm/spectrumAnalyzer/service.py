
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List, Tuple, cast

from pypnm.api.routes.common.extended.common_measure_service import CommonMeasureService, MeasurementEntry
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.schemas import SpecAnCapturePara
from pypnm.config.pnm_config_manager import PnmConfigManager
from pypnm.docsis.cable_modem import CableModem
from pypnm.lib.inet import Inet
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest

from pypnm.api.routes.common.classes.analysis.analysis import WindowFunction
from pypnm.api.routes.common.extended.common_process_service import MessageResponse

from pypnm.docsis.cm_snmp_operation import (
    DocsIf31CmDsOfdmChanChannelEntry,
    SpectrumRetrievalType,
)

from pypnm.lib.types import ChannelId, FrequencyHz, SubcarrierIdx


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
        capture_parameters: SpecAnCapturePara,):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        super().__init__(
            DocsPnmCmCtlTest.SPECTRUM_ANALYZER,
            cable_modem,
            tftp_servers,
            tftp_path,
            cable_modem.getWriteCommunity(),)
        
        self.setSpectrumCaptureParameters(capture_parameters)

StartFrequency    = int
PlcFrequency      = int
EndFrequency      = int
OfdmSpectrumBw    = Tuple[StartFrequency, PlcFrequency, EndFrequency]
OfdmSpectrumBwLut = Dict[ChannelId, OfdmSpectrumBw]


class OfdmChanSpecAnalyzerService(CommonMeasureService):
    """
    A specialized service for configuring and launching DOCSIS OFDM spectrum analyzer captures.

    This is a thin wrapper over :class:`CommonMeasureService` that preconfigures
    parameters for spectrum analyzer testing of a specific cable modem.

    Parameters
    ----------
    cable_modem : CableModem
        The cable modem instance to be tested.

    tftp_servers : tuple[Inet, Inet], optional
        A tuple containing the primary and secondary TFTP servers used for capture
        file transfer.
        Defaults to values from :func:`PnmConfigManager.get_tftp_servers`.

    tftp_path : str, optional
        The remote TFTP directory/path where capture files will be written.
        Defaults to :func:`PnmConfigManager.get_tftp_path`.

    Notes
    -----
    - This class is intended to simplify Spectrum Analyzer test setup by using
      standard PNM TFTP configuration.
    - After initialization, you must still call
      :meth:`setSpectrumCaptureParameters` to define the specific capture
      behavior.
    - Once configured, execute the capture using :meth:`set_and_go`.

    Example
    -------
    >>> opts = SpecAnCapturePara(
    ...     inactivity_timeout=10,
    ...     first_segment_center_freq=579_000_000,
    ...     last_segment_center_freq=579_000_000,
    ...     segment_freq_span=6_000_000,
    ...     num_bins_per_segment=1024,
    ...     noise_bw=150,
    ...     window_function=WindowFunction.HANN,
    ...     num_averages=10,
    ...     spectrum_retrieval_type=SpectrumRetrievalType.FILE
    ... )
    >>> service = OfdmChanSpecAnalyzerService(cm)
    >>> service.setSpectrumCaptureParameters(opts)
    >>> response = await service.set_and_go()
    """

    def __init__(
        self,
        cable_modem: CableModem,
        tftp_servers: Tuple[Inet, Inet] = PnmConfigManager.get_tftp_servers(),
        tftp_path: str = PnmConfigManager.get_tftp_path(),
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(
            DocsPnmCmCtlTest.SPECTRUM_ANALYZER,
            cable_modem,
            tftp_servers,
            tftp_path,
            cable_modem.getWriteCommunity(),
        )


class DsOfdmChannelSpectrumAnalyzer:
    """
    A high-level service that coordinates downstream OFDM spectrum analysis.

    This class is responsible for:

    1. Retrieving downstream OFDM channel information from the cable modem.
    2. Computing per-channel spectrum bandwidth tuples
       (start, center, end frequencies).
    3. Building spectrum capture parameter objects and executing captures
       for each channel through :class:`OfdmChanSpecAnalyzerService`.

    Parameters
    ----------
    cable_modem : CableModem
        The cable modem instance whose downstream OFDM channels will be analyzed.
    """

    def __init__(self, cable_modem: CableModem, number_of_averages: int = 1):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cm:CableModem = cable_modem
        self._number_of_averages = number_of_averages
        self._pnm_test_type = DocsPnmCmCtlTest.SPECTRUM_ANALYZER
        self.log_prefix = f"DsOfdmChannelSpectrumAnalyzer - CM {self._cm.get_mac_address}"
        
    async def start(self) -> List[Tuple[ChannelId, MessageResponse]]:
        """
        Build capture parameters and run spectrum captures for each OFDM channel.

        This method iterates over the downstream OFDM channels,
        builds the capture configuration, and triggers spectrum analyzer
        captures for each channel.

        Returns
        -------
        list[MessageResponse]
            A list of responses from each spectrum analyzer capture run.

        Notes
        -----
        - By default, this method sets conservative capture parameters
          such as 256 bins per segment and a 30-second inactivity timeout.
        - The segment frequency span is automatically derived from the
          difference between the start and end frequencies of each channel.
        - A temporary early `break` is present after the first channel
          for testing purposes. Remove this once multi-channel capture
          is ready to be run in production.
        """

        channel_specCapture:List[Tuple[ChannelId, SpecAnCapturePara]] = []
        out:List[Tuple[ChannelId, MessageResponse]] = []

        # Compute the bandwidth mapping for all OFDM channels
        bw_by_channel: OfdmSpectrumBwLut = await self.get_ofdm_spectrum_bandwidth()

        # Default capture settings
        num_bins_per_segment    = 256
        number_of_averages      = self._number_of_averages
        inactivity_timeout      = 30
        noise_bw                = 150
        segment_freq_span       = 1_000_000

        for chan_id, (start_hz, plc_hz, end_hz) in bw_by_channel.items():
            self.logger.info(
                f"OFDM - Mac: {self._cm.get_mac_address} - "
                f"Channel Settings: {chan_id}, {start_hz}, {plc_hz}, {end_hz}"
            )

            capture_parameter = SpecAnCapturePara(
                inactivity_timeout          = inactivity_timeout,
                first_segment_center_freq   = FrequencyHz(start_hz),
                last_segment_center_freq    = FrequencyHz(end_hz),
                segment_freq_span           = FrequencyHz(segment_freq_span),
                num_bins_per_segment        = num_bins_per_segment,
                noise_bw                    = noise_bw,
                window_function             = WindowFunction.HANN,
                num_averages                = number_of_averages,
                spectrum_retrieval_type     = SpectrumRetrievalType.FILE,
            )

            self.logger.info(
                f"OFDM - Mac: {self._cm.get_mac_address} - "
                f"Capture Parameters: {capture_parameter.model_dump()}"
            )

            channel_specCapture.append((chan_id, capture_parameter))

        for chan_id, capture_parameter in channel_specCapture:
            service = OfdmChanSpecAnalyzerService(self._cm)
            service.setSpectrumCaptureParameters(capture_parameter)
            out.append((chan_id, await service.set_and_go()))

        return out

    async def get_ofdm_spectrum_bandwidth(self) -> OfdmSpectrumBwLut:
        """
        Compute the start, center, and end frequencies for each downstream OFDM channel.

        This method queries the cable modem to retrieve OFDM channel information
        and calculates the usable spectrum for each channel.

        Returns
        -------
        OfdmSpectrumBwLut
            A dictionary mapping each channel ID to a tuple of
            ``(start_frequency_hz, plc_frequency_hz, end_frequency_hz)``.

        Method
        ------
        - Uses the following DOCSIS 3.1 OFDM channel fields:
            * ``SubcarrierZeroFreq``
            * ``FirstActiveSubcarrierNum``
            * ``LastActiveSubcarrierNum``
            * ``SubcarrierSpacing``
            * ``PlcFreq``

        - Start Frequency Calculation:

            ``start = zero_freq + (first_active * subcarrier_spacing)``

        - End Frequency Calculation:

            ``end = zero_freq + ((last_active + 1) * subcarrier_spacing)``

        - Center frequency is simply the PLC frequency:

            ``center = plc_freq``

        Notes
        -----
        - The first active subcarrier index may vary depending on the CMTS
          and modem configuration.
        - Start and end values define the total occupied OFDM spectrum.
        """
        out: OfdmSpectrumBwLut = {}

        channels: List[DocsIf31CmDsOfdmChanChannelEntry] = await self._cm.getDocsIf31CmDsOfdmChanEntry()
        if not channels:
            self.logger.warning("No downstream OFDM channels returned from cable modem.")
            return out

        for channel in channels:
            entry = channel.entry

            zero_freq: FrequencyHz      = cast(FrequencyHz, entry.docsIf31CmDsOfdmChanSubcarrierZeroFreq)
            first_active: SubcarrierIdx = cast(SubcarrierIdx, entry.docsIf31CmDsOfdmChanFirstActiveSubcarrierNum)
            last_active: SubcarrierIdx  = cast(SubcarrierIdx, entry.docsIf31CmDsOfdmChanLastActiveSubcarrierNum)
            sub_spacing: FrequencyHz    = cast(FrequencyHz, entry.docsIf31CmDsOfdmChanSubcarrierSpacing)
            plc_freq: FrequencyHz       = cast(FrequencyHz, entry.docsIf31CmDsOfdmChanPlcFreq)
            chan_id: ChannelId          = cast(ChannelId, entry.docsIf31CmDsOfdmChanChannelId)

            if (chan_id is None or zero_freq is None or
                first_active is None or last_active is None or
                sub_spacing is None or plc_freq is None ):
                
                self.logger.info(
                    "Skipping channel with missing data: "
                    f"id={chan_id}, zero_freq={zero_freq}, first_active={first_active}, "
                    f"last_active={last_active}, spacing={sub_spacing}, plc_freq={plc_freq}")
                
                continue

            # For now, starting at zero_freq as per current implementation
            start_freq  = zero_freq + (first_active * sub_spacing)
            end_freq    = zero_freq + ((last_active + 1) * sub_spacing)

            out[chan_id] = (int(start_freq), int(plc_freq), int(end_freq))

            self.logger.info(
                "Computed OFDM channel frequencies: "
                f"ch_id={chan_id}, start={start_freq}, plc={plc_freq}, end={end_freq}, "
                f"first_active={first_active}, last_active={last_active}, spacing={sub_spacing}"
            )

        return out

    async def is_snmp_ready(self) -> bool:
        """
        Asynchronously check if the cable modem is accessible via SNMP.

        Returns:
            bool: True if the modem responds to SNMP queries, False otherwise.
        """
        return await self._cm.is_snmp_reachable()
    
    async def getPnmMeasurementStatistics(self) -> List[MeasurementEntry]:
        """
        Retrieve PNM measurement entries for the currently configured `pnm_test_type`.

        Returns
        -------
        List[MeasurementEntry]
            A (possibly empty) list of model instances corresponding to the active
            test type:

            - SPECTRUM_ANALYZER                 → List[DocsIf3CmSpectrumAnalysisEntry]
            - SPECTRUM_ANALYZER_SNMP_AMP_DATA   → List[DocsIf3CmSpectrumAnalysisEntry]

            For other (stub/unsupported) test types, an empty list is returned.

        Notes
        -----
        - This method performs no aggregation; it returns the raw per-entry models
          fetched from the cable modem for the selected measurement type.
        - For strict typing, concrete lists are cast to `List[MeasurementEntry]`
          at return points (because `List` is invariant in the type system).
        """
        entries: List[MeasurementEntry] = []

        if self._pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER:
            self.logger.debug(f"{self.log_prefix} - Running SPECTRUM_ANALYZER")
            concrete = await self._cm.getDocsIf3CmSpectrumAnalysisEntry()
            return cast(List[MeasurementEntry], concrete)   

        elif self._pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER_SNMP_AMP_DATA:
            self.logger.debug(f"{self.log_prefix} - Running SPECTRUM_ANALYZER_SNMP_AMP_DATA")
            concrete = await self._cm.getDocsIf3CmSpectrumAnalysisEntry()
            return cast(List[MeasurementEntry], concrete)            

        else:
            self.logger.warning(f"{self.log_prefix} - Unknown PNM test type: {self._pnm_test_type}")

        return entries