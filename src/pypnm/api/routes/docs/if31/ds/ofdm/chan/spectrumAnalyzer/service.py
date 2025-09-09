from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Dict, List, Tuple, cast

from pypnm.api.routes.common.classes.analysis.analysis import WindowFunction
from pypnm.api.routes.common.extended.common_measure_service import CommonMeasureService
from pypnm.api.routes.common.extended.common_process_service import MessageResponse
from pypnm.api.routes.docs.pnm.spectrumAnalyzer.schemas import SpecAnCapturePara
from pypnm.config.pnm_config_manager import PnmConfigManager
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.cm_snmp_operation import (
    DocsIf31CmDsOfdmChanChannelEntry,
    SpectrumRetrievalType,
)
from pypnm.lib.inet import Inet
from pypnm.lib.types import ChannelId
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest


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

    def __init__(self, cable_modem: CableModem):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cm = cable_modem

    async def start(self) -> List[MessageResponse]:
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
        capture_parameters: List[SpecAnCapturePara] = []
        msg_responses: List[MessageResponse] = []

        # Compute the bandwidth mapping for all OFDM channels
        bw_by_channel: OfdmSpectrumBwLut = await self.get_ofdm_spectrum_bandwidth()

        # Default capture settings
        num_bins_per_segment = 256
        num_averages = 1
        inactivity_timeout = 30
        noise_bw = 150
        segment_freq_span = 1_000_000  # Overwritten per channel

        for chan_id, (start_hz, plc_hz, end_hz) in bw_by_channel.items():
            self.logger.info(
                f"OFDM - Mac: {self._cm.get_mac_address} - "
                f"Channel Settings: {chan_id}, {start_hz}, {plc_hz}, {end_hz}"
            )

            segment_freq_span = end_hz - start_hz

            capture_parameter = SpecAnCapturePara(
                inactivity_timeout          = inactivity_timeout,
                first_segment_center_freq   = start_hz,
                last_segment_center_freq    = end_hz,
                segment_freq_span           = segment_freq_span,
                num_bins_per_segment        = num_bins_per_segment,
                noise_bw                    = noise_bw,
                window_function             = WindowFunction.HANN,
                num_averages                = num_averages,
                spectrum_retrieval_type     = SpectrumRetrievalType.FILE,
            )
            capture_parameters.append(capture_parameter)

        for capture_parameter in capture_parameters:
            service = OfdmChanSpecAnalyzerService(self._cm)
            service.setSpectrumCaptureParameters(capture_parameter)
            msg_responses.append(await service.set_and_go())

        return msg_responses

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

            zero_freq       = entry.docsIf31CmDsOfdmChanSubcarrierZeroFreq
            first_active    = entry.docsIf31CmDsOfdmChanFirstActiveSubcarrierNum
            last_active     = entry.docsIf31CmDsOfdmChanLastActiveSubcarrierNum
            sub_spacing     = entry.docsIf31CmDsOfdmChanSubcarrierSpacing
            plc_freq        = entry.docsIf31CmDsOfdmChanPlcFreq
            chan_id: ChannelId = cast(ChannelId, entry.docsIf31CmDsOfdmChanChannelId)

            if (chan_id is None or zero_freq is None or
                first_active is None or last_active is None or
                sub_spacing is None or plc_freq is None ):
                
                self.logger.debug(
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
                f"id={chan_id}, start={start_freq}, center={plc_freq}, end={end_freq}, "
                f"first_active={first_active}, last_active={last_active}, spacing={sub_spacing}"
            )

        return out
