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
from pypnm.docsis.cm_snmp_operation import (DocsIf31CmDsOfdmChanChannelEntry,SpectrumRetrievalType,)
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
    Configure and launch DOCSIS OFDM spectrum-analyzer captures for a cable modem.

    This is a thin wrapper over :class:`CommonMeasureService` specialized for the
    Spectrum Analyzer test type.

    Parameters
    ----------
    cable_modem : CableModem
        Target cable modem instance.
    tftp_servers : tuple[Inet, Inet], optional
        (primary, secondary) TFTP servers for file transfer. Defaults to
        :func:`PnmConfigManager.get_tftp_servers`.
    tftp_path : str, optional
        Remote TFTP directory where capture files are written. Defaults to
        :func:`PnmConfigManager.get_tftp_path`.

    Notes
    -----
    - This constructor only wires up the Spectrum Analyzer test and standard
      transfer settings. Set capture parameters later via
      :meth:`setSpectrumCaptureParameters`.
    - Typical usage:

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
      >>> svc = OfdmChanSpecAnalyzerService(cm)
      >>> svc.setSpectrumCaptureParameters(opts)
      >>> resp = await svc.set_and_go()
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
    Orchestrates per-channel OFDM spectrum captures for a given cable modem.

    Responsibilities
    ----------------
    1) Fetch downstream OFDM channel descriptors.
    2) Compute per-channel spectrum bandwidth tuples ``(start, center, end)`` in Hz.
    3) Build spectrum capture parameters and execute captures via
       :class:`OfdmChanSpecAnalyzerService`.

    Parameters
    ----------
    cable_modem : CableModem
        Target cable modem instance.
    """

    def __init__(self, cable_modem: CableModem):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._cm = cable_modem

    async def start(self) -> List[MessageResponse]:
        """
        Build capture parameters for each OFDM channel and run captures.

        Returns
        -------
        list[MessageResponse]
            Responses from each spectrum-analyzer capture invocation.

        Notes
        -----
        - Uses a single-segment strategy centered across the full channel width
          (``segment_freq_span = end - start``).
        - Temporary early break is present by design (marked in logs); remove
          when ready to iterate all channels.
        """
        capture_parameters: List[SpecAnCapturePara] = []
        msg_responses: List[MessageResponse] = []

        bw_by_channel: OfdmSpectrumBwLut = await self.get_ofdm_spectrum_bandwidth()

        num_bins_per_segment = 256
        num_averages = 1
        inactivity_timeout = 30
        noise_bw = 150
        segment_freq_span = 1_000_000

        attemps: int = 0  # as in original code
        for chan_id, (start_hz, plc_hz, end_hz) in bw_by_channel.items():
            self.logger.info(
                f"OFDM - Mac: {self._cm.get_mac_address} - "
                f"Channel-Settings: {chan_id}, {start_hz}, {plc_hz}, {end_hz}"
            )

            segment_freq_span = end_hz - start_hz

            capture_parameter = SpecAnCapturePara(
                inactivity_timeout          =   inactivity_timeout,
                first_segment_center_freq   =   start_hz,
                last_segment_center_freq    =   end_hz,
                segment_freq_span           =   segment_freq_span,
                num_bins_per_segment        =   num_bins_per_segment,
                noise_bw                    =   noise_bw,
                window_function             =   WindowFunction.HANN,
                num_averages                =   num_averages,
                spectrum_retrieval_type     =   SpectrumRetrievalType.FILE,
            )
            capture_parameters.append(capture_parameter)

            if attemps == 0:
                self.logger.info("+++++++++++++TEMPORARY+++++++++++++ TAKE ME OUT")
                break
            attemps += 1

        for capture_parameter in capture_parameters:
            service = OfdmChanSpecAnalyzerService(self._cm)
            service.setSpectrumCaptureParameters(capture_parameter)
            msg_responses.append(await service.set_and_go())

        return msg_responses

    async def get_ofdm_spectrum_bandwidth(self) -> OfdmSpectrumBwLut:
        """
        Compute per-channel OFDM spectrum bounds.

        Returns
        -------
        OfdmSpectrumBwLut
            Mapping of ``ChannelId -> (start_hz, center_hz, end_hz)``.

        Method
        ------
        - Uses the DOCSIS 3.1 OFDM channel entry fields:
          ``SubcarrierZeroFreq``, ``FirstActiveSubcarrierNum``,
          ``LastActiveSubcarrierNum``, ``SubcarrierSpacing``, and ``PlcFreq``.
        - Start frequency:
          ``start = zero_freq + (first_active * subcarrier_spacing)``
        - End frequency (inclusive index):
          ``end   = zero_freq + ((last_active + 1) * subcarrier_spacing)``
        - Center is the PLC frequency: ``center = plc_freq``.
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

            if (
                chan_id is None
                or zero_freq is None
                or first_active is None
                or last_active is None
                or sub_spacing is None
                or plc_freq is None
            ):
                self.logger.debug(
                    "Skipping channel with missing data: "
                    f"id={chan_id}, zero_freq={zero_freq}, first_active={first_active}, "
                    f"last_active={last_active}, spacing={sub_spacing}, plc_freq={plc_freq}"
                )
                continue

            # start_freq = zero_freq + (first_active * sub_spacing)
            start_freq = zero_freq
            end_freq = zero_freq + ((last_active + 1) * sub_spacing)

            out[chan_id] = (int(start_freq), int(plc_freq), int(end_freq))

            self.logger.info(
                "Computed OFDM channel frequencies: "
                f"id={chan_id}, start={start_freq}, center={plc_freq}, end={end_freq}, "
                f"first_active={first_active}, last_active={last_active}, spacing={sub_spacing}"
            )

        return out
