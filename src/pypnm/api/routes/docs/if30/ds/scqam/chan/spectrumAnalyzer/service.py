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
from pypnm.docsis.cm_snmp_operation import SpectrumRetrievalType
from pypnm.docsis.data_type.DocsIfDownstreamChannel import DocsIfDownstreamChannelEntry
from pypnm.lib.inet import Inet
from pypnm.lib.types import ChannelId
from pypnm.pnm.data_type.pnm_test_types import DocsPnmCmCtlTest

StartFrequency      = int
CenterFrequency     = int
EndFrequency        = int
ScQamSpectrumBw     = Tuple[StartFrequency, CenterFrequency, EndFrequency]
ScQamSpectrumBwLut  = Dict[ChannelId, ScQamSpectrumBw]

class ScQamChanSpecAnalyzerService(CommonMeasureService):
    """
    Thin wrapper around :class:`CommonMeasureService` that configures and
    launches DOCSIS SC-QAM spectrum-analyzer captures for a given cable modem.
    """

    def __init__(
        self,
        cable_modem: CableModem,
        tftp_servers: Tuple[Inet, Inet] = PnmConfigManager.get_tftp_servers(),
        tftp_path: str = PnmConfigManager.get_tftp_path(),
    ):
        """
        Initialize the SC-QAM spectrum analyzer service.

        Args:
            cable_modem (CableModem): Target cable modem instance.
            *spectrum_capture_parameters (object): Extra positional options that are
                forwarded **verbatim** to ``CommonMeasureService.__init__``. In the
                common case this is a single :class:`SpecAnCapturePara` instance, but
                additional positional options are supported if your underlying
                ``CommonMeasureService`` accepts them.
            tftp_servers (Tuple[Inet, Inet], optional): (primary, secondary) TFTP servers
                used for capture file transfer. Defaults to
                ``PnmConfigManager.get_tftp_servers()``.
            tftp_path (str, optional): Remote TFTP directory/path where capture files
                are written. Defaults to ``PnmConfigManager.get_tftp_path()``.

        Notes:
            - This constructor **does not** interpret or validate the contents of
              ``*spectrum_capture_parameters``; they are passed through unchanged.
            - Typical usage passes one ``SpecAnCapturePara`` object:
              ``ScQamChanSpecAnalyzerService(cm, SpecAnCapturePara(...))``.

        Examples:
            Basic usage with one options object:

            >>> opts = SpecAnCapturePara(
            ...     inactivity_timeout=10,
            ...     first_segment_center_freq=579000000,
            ...     last_segment_center_freq=579000000,
            ...     segment_freq_span=6000000,
            ...     num_bins_per_segment=1024,
            ...     noise_bw=150,
            ...     window_function=WindowFunction.HANN,
            ...     num_averages=10,
            ...     spectrum_retrieval_type=SpectrumRetrievalType.FILE
            ... )
            >>> service = ScQamChanSpecAnalyzerService(cm, opts)
            >>> resp = await service.set_and_go()
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        super().__init__(
            DocsPnmCmCtlTest.SPECTRUM_ANALYZER,
            cable_modem,
            tftp_servers,
            tftp_path,
            cable_modem.getWriteCommunity(),)

class DsScQamChannelSpectrumAnalyzer:
    """
    Service to fetch DOCSIS SC-QAM downstream channel info and compute
    per-channel spectrum bandwidth tuples (start, center, end) in Hz, then
    trigger spectrum captures per channel.
    """

    def __init__(self, cable_modem: CableModem):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cm = cable_modem

    async def start(self) -> List[MessageResponse]:
        """
        Build capture parameters for each SC-QAM channel and run captures.
        """
        capture_parameters: List[SpecAnCapturePara] = []
        msg_responses: List[MessageResponse] = []

        bw_by_channel: ScQamSpectrumBwLut = await self.get_scqam_spectrum_bandwidth()

        # Keep it simple: one segment centered on the SC-QAM center, span = channel width.
        # Choose conservative defaults for bins/averages; tighten later as needed.
        num_bins_per_segment    = 256
        num_averages            = 10
        inactivity_timeout      = 10
        noise_bw                = 150
        segment_freq_span       = 1_000_000

        for chan_id, (start_hz, center_hz, end_hz) in bw_by_channel.items():

            self.logger.info(f'SC-QAM Mac: {self._cm.get_mac_address} - Channel-Settings: {chan_id}, {start_hz}, {center_hz}, {end_hz}')

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
            service = ScQamChanSpecAnalyzerService(self._cm)
            service.setSpectrumCaptureParameters(capture_parameter)
            msg_responses.append(await service.set_and_go())

        return msg_responses

    async def get_scqam_spectrum_bandwidth(self) -> ScQamSpectrumBwLut:
        """
        Compute start/center/end frequencies for each SC-QAM downstream channel.

        Returns:
            Mapping of ChannelId -> (start_hz, center_hz, end_hz).
            Uses half-width around center: start = center - width/2, end = center + width/2.
        """
        out: ScQamSpectrumBwLut = {}

        channels: List[DocsIfDownstreamChannelEntry] = await self._cm.getDocsIfDownstreamChannel()
        if not channels:
            self.logger.warning("No downstream SC-QAM channels returned from cable modem.")
            return out

        for channel in channels:
            cfreq   = channel.entry.docsIfDownChannelFrequency
            cwidth  = channel.entry.docsIfDownChannelWidth
            chan_id: ChannelId = cast(ChannelId, channel.entry.docsIfDownChannelId)

            if cfreq is None or cwidth is None or chan_id is None:
                self.logger.debug(
                    "Skipping channel with missing data: id=%s, freq=%s, width=%s",
                    chan_id, cfreq, cwidth
                )
                continue

            half_width: int = int(cwidth) // 2
            start: int = int(cfreq) - half_width
            end: int   = int(cfreq) + half_width

            out[chan_id] = (start, int(cfreq), end)

        return out
