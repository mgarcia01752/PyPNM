
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Union
import logging

from pypnm.api.routes.common.extended.common_messaging_service import MessageResponse
from pypnm.api.routes.common.extended.common_process_service import DocsPnmCmCtlTest
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.pnm.DocsIf3CmSpectrumAnalysisEntry import DocsIf3CmSpectrumAnalysisEntry
from pypnm.lib.types import ChannelId, FrequencyHz

StartFrequency      = FrequencyHz
PlcFrequency        = FrequencyHz
EndFrequency        = FrequencyHz
CenterFrequency     = FrequencyHz
OfdmSpectrumBw      = Tuple[StartFrequency, PlcFrequency, EndFrequency]
OfdmSpectrumBwLut   = Dict[ChannelId, OfdmSpectrumBw]
ScQamSpectrumBw     = Tuple[StartFrequency, CenterFrequency, EndFrequency]
ScQamSpectrumBwLut  = Dict[ChannelId, ScQamSpectrumBw]
CommonSpectumBwLut  = Dict[ChannelId, Tuple[StartFrequency, Union[CenterFrequency, PlcFrequency], EndFrequency]]


class CommonSpectrumChannelAnalyzer(ABC):
    def __init__(self, cm: CableModem) -> None:
        self._cm = cm
        self._pnm_test_type = DocsPnmCmCtlTest.SPECTRUM_ANALYZER
        self.logger = logging.getLogger(self.__class__.__name__)
        self.log_prefix = f"[{self.__class__.__name__}]"
        self._pnm_test_type = DocsPnmCmCtlTest.SPECTRUM_ANALYZER
        self._measurement_stat: Dict[ChannelId, List[DocsIf3CmSpectrumAnalysisEntry]] = {}

    @abstractmethod
    async def start(self) -> List[Tuple[ChannelId, MessageResponse]]:
        """
        Start the spectrum analyzer measurement on the cable modem.

        Returns
        -------
        List[Tuple[ChannelId, MessageResponse]]
            A list of tuples containing channel identifiers and their corresponding
            message responses from the cable modem.

        Notes
        -----
        - Concrete implementations must configure capture parameters and trigger
          spectrum captures for each target channel.
        """
        pass

    async def getPnmMeasurementStatistics(self) -> Dict[ChannelId, List[DocsIf3CmSpectrumAnalysisEntry]]:
        """
        Return the raw PNM measurement statistics keyed by channel.

        Returns
        -------
        Dict[ChannelId, List[DocsIf3CmSpectrumAnalysisEntry]]
            Mapping of channel identifiers to their corresponding measurement
            entry lists.
        """
        return self._measurement_stat

    async def getPnmMeasurementStatisticsFlat(self) -> List[DocsIf3CmSpectrumAnalysisEntry]:
        """
        Return a flattened list of all PNM measurement entries across channels.

        This helper is intended for API layers that only need a single list of
        entries (for example, when serializing measurement statistics into a
        JSON payload without preserving per-channel grouping).

        Returns
        -------
        List[DocsIf3CmSpectrumAnalysisEntry]
            Flattened list of measurement entries aggregated from all channels.
        """
        entries: List[DocsIf3CmSpectrumAnalysisEntry] = []
        for channel_entries in self._measurement_stat.values():
            entries.extend(channel_entries)
        return entries

    async def updatePnmMeasurementStatistics(self, channel_id: ChannelId) -> bool:
        """
        Retrieve and store PNM measurement entries for the current `pnm_test_type`.

        Parameters
        ----------
        channel_id : ChannelId
            Channel identifier associated with the measurement update.

        Returns
        -------
        bool
            True if the measurement statistics were updated or a warning was
            logged; False is never returned but reserved for future logic.

        Notes
        -----
        - For spectrum analyzer test types, this method fetches
          DocsIf3CmSpectrumAnalysisEntry models from the cable modem and stores
          them under the given channel identifier.
        """
        if self._pnm_test_type in (
            DocsPnmCmCtlTest.SPECTRUM_ANALYZER,
            DocsPnmCmCtlTest.SPECTRUM_ANALYZER_SNMP_AMP_DATA,
        ):
            self._measurement_stat[channel_id] = await self._cm.getDocsIf3CmSpectrumAnalysisEntry()
        else:
            self.logger.warning(
                "%s - Unknown PNM test type: %s",
                self.log_prefix,
                self._pnm_test_type,
            )

        return True

    async def is_snmp_ready(self) -> bool:
        """
        Asynchronously check if the cable modem is accessible via SNMP.

        Returns
        -------
        bool
            True if the modem responds to SNMP queries, False otherwise.
        """
        return await self._cm.is_snmp_reachable()

    @abstractmethod
    async def calculate_spectrum_bandwidth(self) -> CommonSpectumBwLut:
        """
        Compute start/center/end frequencies for each downstream channel.

        Returns
        -------
        CommonSpectumBwLut
            Mapping of ChannelId -> (start_hz, center_or_plc_hz, end_hz).

        Notes
        -----
        - Concrete implementations must derive per-channel bandwidth tuples
          according to the modulation type (OFDM or SC-QAM).
        """
        pass
