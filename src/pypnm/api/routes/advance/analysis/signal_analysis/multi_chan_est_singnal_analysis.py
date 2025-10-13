# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from enum import Enum
from typing import List, Optional, Union, Dict

from pydantic import BaseModel, Field

from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.ifft import IfftEchoDetector
from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.phase_slope import PhaseSlopeEchoDetector
from pypnm.api.routes.advance.analysis.signal_analysis.detection.lte.phase_slope_lte_detection import GroupDelayAnomalyDetector
from pypnm.api.routes.advance.analysis.signal_analysis.group_delay_calculator import GroupDelayCalculator
from pypnm.api.routes.advance.common.capture_data_aggregator import CaptureDataAggregator
from pypnm.api.routes.advance.common.transactionsCollection import TransactionCollection, TransactionCollectionModel
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.file_capture.types import GroupId
from pypnm.lib.log_files import LogFile
from pypnm.lib.types import (
    ChannelId, FloatSeries, FrequencySeriesHz, ComplexArray, ComplexSeries, MacAddressStr,)
from pypnm.lib.utils import TimeUnit, Utils
from pypnm.pnm.lib.min_avg_max import MinAvgMax
from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef


# ---------------------------------------------------------------------
# Aggregated multi-capture type aliases
# ---------------------------------------------------------------------
ChannelAmplitudeMap       = Dict[ChannelId, List[FloatSeries]]
ChannelFrequencyMap       = Dict[ChannelId, FrequencySeriesHz]
ChannelComplexMap         = Dict[ChannelId, List[ComplexArray]]
ChannelObwMap             = Dict[ChannelId, float]
ChannelComplexSeriesMap   = Dict[ChannelId, List[ComplexSeries]]


# ---------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------
class MinAvgMaxModel(BaseModel):
    """Statistical amplitude summary for a single channel."""
    channel_id: ChannelId           = Field(..., description="OFDM downstream channel ID")
    frequency: FrequencySeriesHz    = Field(..., description="Subcarrier frequency bins (Hz)")
    min: FloatSeries                = Field(..., description="Minimum amplitude (dB) across captures per subcarrier")
    avg: FloatSeries                = Field(..., description="Average amplitude (dB) across captures per subcarrier")
    max: FloatSeries                = Field(..., description="Maximum amplitude (dB) across captures per subcarrier")


class GroupDelayAnalysisModel(BaseModel):
    """Group-delay metrics derived from phase slope of channel-estimation coefficients."""
    channel_id: ChannelId           = Field(..., description="OFDM downstream channel ID")
    frequency: FrequencySeriesHz    = Field(..., description="Subcarrier frequency bins (Hz)")
    group_delay_us: FloatSeries     = Field(..., description="Per-subcarrier group delay (microseconds)")


class LteDetectionModel(BaseModel):
    """LTE interference detection using group-delay ripple anomalies."""
    channel_id: ChannelId           = Field(..., description="OFDM downstream channel ID")
    anomalies: FloatSeries          = Field(..., description="Detected LTE interference amplitudes or anomaly indices")
    threshold: float                = Field(..., description="Group-delay ripple threshold (seconds or equivalent)")
    bin_widths: FloatSeries         = Field(..., description="Frequency bin widths used for anomaly segmentation (Hz)")


class EchoDetectionPhaseSlopeModel(BaseModel):
    """Echo detection based on discontinuities in the channel phase slope."""
    channel_id: ChannelId           = Field(..., description="OFDM downstream channel ID")
    slope_profile: FloatSeries      = Field(..., description="Phase-slope values across subcarriers (radians/Hz)")
    frequency: FrequencySeriesHz    = Field(..., description="Subcarrier frequency bins (Hz)")


class EchoDetectionIfftModel(BaseModel):
    """Echo detection based on inverse FFT of the complex channel impulse response."""
    channel_id: ChannelId           = Field(..., description="OFDM downstream channel ID")
    impulse_response: FloatSeries   = Field(..., description="Magnitude of impulse response vs delay (linear units)")
    sample_rate: float              = Field(..., description="Sample rate used for IFFT reconstruction (Hz)")


class MultiChanEstimationResult(BaseModel):
    """Unified result model for multi-channel estimation analysis."""
    analysis_type: str              = Field(..., description="Name of the executed analysis type")
    results: List[
        Union[
            MinAvgMaxModel,
            GroupDelayAnalysisModel,
            LteDetectionModel,
            EchoDetectionPhaseSlopeModel,
            EchoDetectionIfftModel,
        ]
    ]                               = Field(default_factory=list, description="List of per-channel analysis results")
    error: Optional[str]            = Field(default=None, description="Error message if analysis failed")

    def to_json(self, indent: int = 2) -> str:
        """Return the result as a JSON string."""
        return self.model_dump_json(indent=indent)


# ---------------------------------------------------------------------
# Analysis Executor
# ---------------------------------------------------------------------
class MultiChanEstimationAnalysisType(Enum):
    """Signal analysis routines for Multi-Channel-Estimation data."""
    MIN_AVG_MAX                    = 0
    GROUP_DELAY                    = 1
    LTE_DETECTION_PHASE_SLOPE      = 2
    ECHO_DETECTION_PHASE_SLOPE     = 3
    ECHO_DETECTION_IFFT            = 4


class MultiChanEstimationSignalAnalysis:
    """Performs signal-quality analyses on grouped Multi-Channel-Estimation captures."""

    def __init__(self, capture_group_id: GroupId, analysis_type: MultiChanEstimationAnalysisType) -> None:
        self.logger                 = logging.getLogger(self.__class__.__name__)
        self._capture_group_id      = capture_group_id
        self._analysis_type         = analysis_type
        self._results: Optional[MultiChanEstimationResult] = None

        # Initialize the aggregator for this capture group
        self._aggregator             = CaptureDataAggregator(capture_group_id)
        self._trans_collect:TransactionCollection = self._aggregator.collect()

    def _process(self) -> MultiChanEstimationResult:

        self.logger.info(f'[_process] {self._analysis_type.name} for MacAddress: {self.get_mac_address()}')

        if self._analysis_type == MultiChanEstimationAnalysisType.MIN_AVG_MAX:
            data = self._analyze_min_avg_max()
        elif self._analysis_type == MultiChanEstimationAnalysisType.GROUP_DELAY:
            data = self._analyze_group_delay()
        elif self._analysis_type == MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE:
            data = self._analyze_lte_detection()
        elif self._analysis_type == MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE:
            data = self._analyze_echo_detection_phase_slope()
        elif self._analysis_type == MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT:
            data = self._analyze_echo_detection_ifft()
        else:
            raise ValueError(f"Unsupported analysis type: {self._analysis_type}")
        
        fname = f'{self._analysis_type.name}_{self.get_mac_address()}_{Utils.time_stamp(TimeUnit.NANOSECONDS)}.dict'
        for _ in data:
            LogFile().write(fname, _)

        return MultiChanEstimationResult(analysis_type=self._analysis_type.name, results=data)

    def get_mac_address(self) -> MacAddressStr:

        if len(self._trans_collect.getMacAddresses()) > 1:
            self.logger.warning(f'Unexpected number of MacAddresses Found: total: {len(self._trans_collect.getMacAddresses())}')

        return self._trans_collect.getMacAddresses()[0].mac_address


    def to_model(self) -> MultiChanEstimationResult:
        """Run the analysis and return a structured model."""
        if self._results is None:
            try:
                self._results = self._process()
            except Exception as e:
                return MultiChanEstimationResult(
                    analysis_type   =   self._analysis_type.name, 
                    results         =   [], 
                    error           =   str(e))
        return self._results

    # -----------------------------------------------------------------
    # MIN / AVG / MAX
    # -----------------------------------------------------------------
    def _analyze_min_avg_max(self) -> List[MinAvgMaxModel]:

        amplitudes: ChannelAmplitudeMap = {}
        freqs: ChannelFrequencyMap = {}

        # Iterate TransactionCollection models (typed)
        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                data_bytes = tcm.data
                ocef = CmDsOfdmChanEstimateCoef(data_bytes)
                model = ocef.to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)

                ch_id = ChannelId(result.channel_id)
                mags = result.carrier_values.magnitudes
                freqs[ch_id] = result.carrier_values.frequency
                if mags:
                    amplitudes.setdefault(ch_id, []).append(mags)
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] MIN_AVG_MAX parse failed: {e}")
                continue

        out: List[MinAvgMaxModel] = []
        for ch_id, amp_lists in amplitudes.items():
            calc = MinAvgMax(amp_lists)
            stats = calc.to_dict()
            out.append(
                MinAvgMaxModel(
                    channel_id  =   ch_id,
                    frequency   =   freqs.get(ch_id, []),
                    min         =   stats["min"],
                    avg         =   stats["avg"],
                    max         =   stats["max"],))
        return out

    # -----------------------------------------------------------------
    # GROUP DELAY
    # -----------------------------------------------------------------
    def _analyze_group_delay(self) -> List[GroupDelayAnalysisModel]:
        channel_data: ChannelComplexMap = {}
        freqs_map: ChannelFrequencyMap = {}

        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                ocef = CmDsOfdmChanEstimateCoef(tcm.data)
                model = ocef.to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)

                ch_id = ChannelId(result.channel_id)
                channel_data.setdefault(ch_id, []).append(result.carrier_values.complex)
                freqs_map[ch_id] = result.carrier_values.frequency
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] GROUP_DELAY parse failed: {e}")
                continue

        results: List[GroupDelayAnalysisModel] = []
        for ch_id, complex_lists in channel_data.items():
            calc = GroupDelayCalculator(complex_lists, freqs_map[ch_id])
            gd = calc.to_dict()
            results.append(
                GroupDelayAnalysisModel(
                    channel_id      =   ch_id,
                    frequency       =   gd.get("freqs", []),
                    group_delay_us  =   gd.get("tau_us", []),))
        return results

    # -----------------------------------------------------------------
    # LTE DETECTION
    # -----------------------------------------------------------------
    def _analyze_lte_detection(self) -> List[LteDetectionModel]:
        channel_data: ChannelComplexMap = {}
        freqs_map: ChannelFrequencyMap = {}
        threshold = 1e-9
        bin_widths = [1e6, 5e5, 1e5]

        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                ocef = CmDsOfdmChanEstimateCoef(tcm.data)
                model = ocef.to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)

                ch_id = ChannelId(result.channel_id)
                channel_data.setdefault(ch_id, []).append(result.carrier_values.complex)
                freqs_map[ch_id] = result.carrier_values.frequency
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] LTE_DETECTION_PHASE_SLOPE parse failed: {e}")
                continue

        out: List[LteDetectionModel] = []
        for ch_id, complex_lists in channel_data.items():
            calc = GroupDelayAnomalyDetector(complex_lists, freqs_map[ch_id])
            res = calc.run(bin_widths=bin_widths, threshold=threshold)
            out.append(
                LteDetectionModel(
                    channel_id      =   ch_id,
                    anomalies       =   res.get("anomalies", []),
                    threshold       =   threshold,
                    bin_widths      =   bin_widths,))
        return out

    # -----------------------------------------------------------------
    # ECHO DETECTION (Phase Slope)
    # -----------------------------------------------------------------
    def _analyze_echo_detection_phase_slope(self) -> List[EchoDetectionPhaseSlopeModel]:
        channel_data: ChannelComplexMap = {}
        freqs_map: ChannelFrequencyMap = {}

        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                ocef = CmDsOfdmChanEstimateCoef(tcm.data)
                model = ocef.to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)

                ch_id = ChannelId(result.channel_id)
                channel_data.setdefault(ch_id, []).append(result.carrier_values.complex)
                freqs_map[ch_id] = result.carrier_values.frequency
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] ECHO_DETECTION_PHASE_SLOPE parse failed: {e}")
                continue

        out: List[EchoDetectionPhaseSlopeModel] = []
        for ch_id, complex_lists in channel_data.items():
            calc = PhaseSlopeEchoDetector(complex_lists, freqs_map[ch_id])
            slope_data = calc.to_dict()
            out.append(
                EchoDetectionPhaseSlopeModel(
                    channel_id      =   ch_id,
                    slope_profile   =   slope_data.get("slope_profile", []),
                    frequency       =   slope_data.get("frequency", []),))
        return out

    # -----------------------------------------------------------------
    # ECHO DETECTION (IFFT)
    # -----------------------------------------------------------------
    def _analyze_echo_detection_ifft(self) -> List[EchoDetectionIfftModel]:
        channel_data: ChannelComplexMap = {}
        obw_map: ChannelObwMap = {}

        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                ocef = CmDsOfdmChanEstimateCoef(tcm.data)
                model = ocef.to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)

                ch_id = ChannelId(result.channel_id)
                channel_data.setdefault(ch_id, []).append(result.carrier_values.complex)
                obw_map[ch_id] = result.carrier_values.occupied_channel_bandwidth
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] ECHO_DETECTION_IFFT parse failed: {e}")
                continue

        out: List[EchoDetectionIfftModel] = []
        for ch_id, complex_lists in channel_data.items():
            obw = obw_map.get(ch_id, 0)
            if not obw:
                continue
            calc = IfftEchoDetector(complex_lists, sample_rate=float(obw))
            ifft_res = calc.to_dict()
            out.append(
                EchoDetectionIfftModel(
                    channel_id      =   ch_id,
                    impulse_response=   ifft_res.get("impulse_response", []),
                    sample_rate     =   float(obw),))
        return out
