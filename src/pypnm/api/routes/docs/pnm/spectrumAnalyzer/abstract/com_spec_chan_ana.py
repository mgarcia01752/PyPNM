
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
CommonSpectumBwLut  = Dict[ChannelId, Tuple[StartFrequency, Union[CenterFrequency,PlcFrequency], EndFrequency]]

class CommonSpectrumChannelAnalyzer(ABC):
    def __init__(self, cm:CableModem) -> None:
        self._cm = cm
        self._pnm_test_type = DocsPnmCmCtlTest.SPECTRUM_ANALYZER
        self.logger = logging.getLogger(self.__class__.__name__)
        self.log_prefix = f"[{self.__class__.__name__}]"
        self._pnm_test_type = DocsPnmCmCtlTest.SPECTRUM_ANALYZER
        self._measurement_stat:Dict[ChannelId, List[DocsIf3CmSpectrumAnalysisEntry]] = {}

    @abstractmethod
    async def start(self) -> List[Tuple[ChannelId, MessageResponse]]:
        """
        Start the spectrum analyzer measurement on the cable modem.

        Returns
        -------
        List[Tuple[ChannelId, DocsIf3CmSpectrumAnalysisEntry]]
            A list of tuples containing channel identifiers and their corresponding
            message responses from the cable modem.
            
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
        pass
    
    async def getPnmMeasurementStatistics(self) -> Dict[ChannelId, List[DocsIf3CmSpectrumAnalysisEntry]]:
        """
        Get the PNM measurement statistics.

        Returns:
            Dict[ChannelId, List[DocsIf3CmSpectrumAnalysisEntry]]: _description_
        """
        return self._measurement_stat

    async def updatePnmMeasurementStatistics(self, channel_id:ChannelId) -> bool:
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

        if self._pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER:
            self._measurement_stat[channel_id] = await self._cm.getDocsIf3CmSpectrumAnalysisEntry()  

        elif self._pnm_test_type == DocsPnmCmCtlTest.SPECTRUM_ANALYZER_SNMP_AMP_DATA:
            self._measurement_stat[channel_id] = await self._cm.getDocsIf3CmSpectrumAnalysisEntry()           

        else:   
            self.logger.warning(f"{self.log_prefix} - Unknown PNM test type: {self._pnm_test_type}")

        return True
    
    async def is_snmp_ready(self) -> bool:
        """
        Asynchronously check if the cable modem is accessible via SNMP.

        Returns:
            bool: True if the modem responds to SNMP queries, False otherwise.
        """
        return await self._cm.is_snmp_reachable()
    
    @abstractmethod
    async def calculate_spectrum_bandwidth(self) -> CommonSpectumBwLut:
        """
        Compute start/center/end frequencies for each SC-QAM downstream channel.

        Returns:
            Mapping of ChannelId -> (start_hz, center_hz, end_hz).
            Uses half-width around center: start = center - width/2, end = center + width/2.
        """
        pass