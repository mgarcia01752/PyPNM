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
from pypnm.api.routes.advance.analysis.signal_analysis.multi_rxmer_signal_analysis import MultiAnalysisRpt
from pypnm.api.routes.advance.common.capture_data_aggregator import CaptureDataAggregator
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.log_files import LogFile
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.types import ChannelId, FloatSeries, FrequencySeriesHz, ComplexArray, ComplexSeries
from pypnm.lib.utils import TimeUnit, Utils
from pypnm.pnm.lib.min_avg_max import MinAvgMax
from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef


# ──────────────────────────────────────────────────────────────
# Aliases
# ──────────────────────────────────────────────────────────────
ChannelAmplitudeMap = Dict[ChannelId, List[FloatSeries]]
ChannelFrequencyMap = Dict[ChannelId, FrequencySeriesHz]
ChannelComplexMap = Dict[ChannelId, List[ComplexArray]]
ChannelObwMap = Dict[ChannelId, float]
ChannelComplexSeriesMap = Dict[ChannelId, List[ComplexSeries]]


# ──────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────
class MinAvgMaxModel(BaseModel):
    channel_id: ChannelId = Field(..., description="OFDM downstream channel ID")
    frequency: FrequencySeriesHz = Field(..., description="Subcarrier frequency bins (Hz)")
    min: FloatSeries = Field(..., description="Minimum amplitude (dB) per subcarrier")
    avg: FloatSeries = Field(..., description="Average amplitude (dB) per subcarrier")
    max: FloatSeries = Field(..., description="Maximum amplitude (dB) per subcarrier")


class GroupDelayAnalysisModel(BaseModel):
    channel_id: ChannelId = Field(..., description="OFDM downstream channel ID")
    frequency: FrequencySeriesHz = Field(..., description="Subcarrier frequency bins (Hz)")
    group_delay_us: FloatSeries = Field(..., description="Per-subcarrier group delay (µs)")


class LteDetectionModel(BaseModel):
    channel_id: ChannelId   = Field(..., description="OFDM downstream channel ID")
    anomalies: FloatSeries  = Field(..., description="Detected LTE interference magnitudes/indices")
    threshold: float        = Field(..., description="Group-delay ripple threshold")
    bin_widths: FloatSeries = Field(..., description="Bin widths used for segmentation (Hz)")


class EchoDetectionPhaseSlopeModel(BaseModel):
    channel_id: ChannelId           = Field(..., description="OFDM downstream channel ID")
    slope_profile: FloatSeries      = Field(..., description="Phase-slope values (radians/Hz)")
    frequency: FrequencySeriesHz    = Field(..., description="Subcarrier frequency bins (Hz)")


class EchoDetectionIfftModel(BaseModel):
    channel_id: ChannelId           = Field(..., description="OFDM downstream channel ID")
    impulse_response: FloatSeries   = Field(..., description="Impulse-response magnitude vs delay")
    sample_rate: float              = Field(..., description="Sample rate used for IFFT (Hz)")


class MultiChanEstimationResult(BaseModel):
    analysis_type: str = Field(..., description="Name of executed analysis type")
    results: List[
        Union[
            MinAvgMaxModel,
            GroupDelayAnalysisModel,
            LteDetectionModel,
            EchoDetectionPhaseSlopeModel,
            EchoDetectionIfftModel,
        ]
    ] = Field(default_factory=list, description="List of per-channel analysis results")
    error: Optional[str] = Field(default=None, description="Error message if analysis failed")

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)


# ──────────────────────────────────────────────────────────────
# Enum
# ──────────────────────────────────────────────────────────────
class MultiChanEstimationAnalysisType(Enum):
    MIN_AVG_MAX                 = 0
    GROUP_DELAY                 = 1
    LTE_DETECTION_PHASE_SLOPE   = 2
    ECHO_DETECTION_PHASE_SLOPE  = 3
    ECHO_DETECTION_IFFT         = 4


# ──────────────────────────────────────────────────────────────
# Main Class
# ──────────────────────────────────────────────────────────────
class MultiChanEstimationSignalAnalysis(MultiAnalysisRpt):
    """Performs signal-quality analyses on grouped Multi-ChannelEstimation captures."""

    def __init__(self, capt_data_agg: CaptureDataAggregator, analysis_type: MultiChanEstimationAnalysisType) -> None:
        super().__init__(capt_data_agg)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._analysis_type = analysis_type
        self._results: Optional[MultiChanEstimationResult] = None

    # ──────────────────────────────────────────────────────────
    # Internals
    # ──────────────────────────────────────────────────────────
    def _log_result(self, tag: str, mac: str, data: List[BaseModel]) -> None:
        fname = f"{tag}_{mac}_{Utils.time_stamp(TimeUnit.NANOSECONDS)}.dict"
        for r in data:
            LogFile().write(fname, r)

    def _process(self):
        if self._results is None:
            self._results = self.__process()

    def __process(self) -> MultiChanEstimationResult:
        mac = self.getMacAddresses()[0]
        self.logger.info(f"[_process] {self._analysis_type.name} for MAC={mac}")

        match self._analysis_type:
            case MultiChanEstimationAnalysisType.MIN_AVG_MAX:
                data = self._analyze_min_avg_max()
            case MultiChanEstimationAnalysisType.GROUP_DELAY:
                data = self._analyze_group_delay()
            case MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE:
                data = self._analyze_lte_detection()
            case MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE:
                data = self._analyze_echo_detection_phase_slope()
            case MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT:
                data = self._analyze_echo_detection_ifft()
            case _:
                raise ValueError(f"Unsupported analysis type: {self._analysis_type}")

        self._log_result(self._analysis_type.name, str(mac), data)
        return MultiChanEstimationResult(analysis_type=self._analysis_type.name, results=data)

    def to_model(self) -> MultiChanEstimationResult:
        if self._results is None:
            try:
                self._results = self.__process()
            except Exception as e:
                return MultiChanEstimationResult(
                    analysis_type   =   self._analysis_type.name,
                    results         =   [],
                    error           =   str(e),)
        return self._results

    # ──────────────────────────────────────────────────────────
    # CSV
    # ──────────────────────────────────────────────────────────
    def create_csv(self, **kwargs) -> List[CSVManager]:
        csvs: List[CSVManager] = []
        model = self.to_model()

        for r in model.results:
            csv = CSVManager()

            match self._analysis_type:
                # ───────────────────────────────
                case MultiChanEstimationAnalysisType.MIN_AVG_MAX:
                    if not isinstance(r, MinAvgMaxModel): 
                        continue
                    csv.set_header(["Frequency (Hz)", "Min (dB)", "Avg (dB)", "Max (dB)"])
                    for f, mn, av, mx in zip(r.frequency, r.min, r.avg, r.max):
                        csv.insert_row([f, mn, av, mx])
                    csv.set_path_fname(self.create_csv_fname(tags=[f"ch{r.channel_id}", "minavgmax"]))
                    csv.write()
                    csvs.append(csv)

                # ───────────────────────────────
                case MultiChanEstimationAnalysisType.GROUP_DELAY:
                    if not isinstance(r, GroupDelayAnalysisModel): 
                        continue
                    csv.set_header(["Frequency (Hz)", "Group Delay (µs)"])
                    for f, gd in zip(r.frequency, r.group_delay_us):
                        csv.insert_row([f, gd])
                    csv.set_path_fname(self.create_csv_fname(tags=[f"ch{r.channel_id}", "groupdelay"]))
                    csv.write()
                    csvs.append(csv)

                # ───────────────────────────────
                case MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE:
                    if not isinstance(r, LteDetectionModel): 
                        continue
                    csv.set_header(["Bin Width (Hz)", "Anomaly Magnitude"])
                    for bw, anom in zip(r.bin_widths, r.anomalies):
                        csv.insert_row([bw, anom])
                    csv.insert_row(["Threshold", r.threshold])
                    csv.set_path_fname(self.create_csv_fname(tags=[f"ch{r.channel_id}", "lte-detect"]))
                    csv.write()
                    csvs.append(csv)

                # ───────────────────────────────
                case MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE:
                    if not isinstance(r, EchoDetectionPhaseSlopeModel): 
                        continue
                    csv.set_header(["Frequency (Hz)", "Phase Slope (rad/Hz)"])
                    for f, s in zip(r.frequency, r.slope_profile):
                        csv.insert_row([f, s])
                    csv.set_path_fname(self.create_csv_fname(tags=[f"ch{r.channel_id}", "echo-slope"]))
                    csv.write()
                    csvs.append(csv)

                # ───────────────────────────────
                case MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT:
                    if not isinstance(r, EchoDetectionIfftModel): 
                        continue
                    csv.set_header(["Sample Index", "Amplitude"])
                    for i, amp in enumerate(r.impulse_response):
                        csv.insert_row([i, amp])
                    csv.insert_row(["Sample Rate (Hz)", r.sample_rate])
                    csv.set_path_fname(self.create_csv_fname(tags=[f"ch{r.channel_id}", "echo-ifft"]))
                    csv.write()
                    csvs.append(csv)

        return csvs
    
    # ──────────────────────────────────────────────────────────
    # Matplot
    # ──────────────────────────────────────────────────────────
    def create_matplot(self, **kwargs) -> List[MatplotManager]:
        plots: List[MatplotManager] = []
        model = self.to_model()

        match self._analysis_type:
            case MultiChanEstimationAnalysisType.MIN_AVG_MAX:
                for r in model.results:
                    if not isinstance(r, MinAvgMaxModel):
                        continue
                    cfg = PlotConfig(
                        x=r.frequency,
                        y_multi=[r.min, r.avg, r.max],
                        y_multi_label=["Min", "Avg", "Max"],
                        xlabel="Subcarrier Frequency (Hz)",
                        ylabel="Amplitude (dB)",
                        title=f"Channel {r.channel_id} — Min/Average/Max Amplitude",
                        grid=True, legend=True, theme="dark")
                    mp = MatplotManager(default_cfg=cfg)
                    mp.plot_multi_line(self.create_png_fname(tags=[f"ch{r.channel_id}", "minavgmax"]))
                    plots.append(mp)

            case MultiChanEstimationAnalysisType.GROUP_DELAY:
                for r in model.results:
                    if not isinstance(r, GroupDelayAnalysisModel):
                        continue
                    cfg = PlotConfig(
                        x=r.frequency, y=r.group_delay_us,
                        xlabel="Subcarrier Frequency (Hz)",
                        ylabel="Group Delay (µs)",
                        title=f"Channel {r.channel_id} — Group Delay",
                        grid=True, legend=False, theme="dark")
                    mp = MatplotManager(default_cfg=cfg)
                    mp.plot_line(self.create_png_fname(tags=[f"ch{r.channel_id}", "groupdelay"]))
                    plots.append(mp)

            case MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE:
                for r in model.results:
                    if not isinstance(r, LteDetectionModel):
                        continue
                    cfg = PlotConfig(
                        x=r.bin_widths, y=r.anomalies,
                        xlabel="Frequency Bin Width (Hz)",
                        ylabel="Anomaly Magnitude",
                        title=f"Channel {r.channel_id} — LTE Detection (Threshold={r.threshold:.2e})",
                        grid=True, legend=False, theme="dark")
                    mp = MatplotManager(default_cfg=cfg)
                    mp.plot_bar(r.bin_widths, r.anomalies,
                                self.create_png_fname(tags=[f"ch{r.channel_id}", "lte-detect"]))
                    plots.append(mp)

            case MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE:
                for r in model.results:
                    if not isinstance(r, EchoDetectionPhaseSlopeModel):
                        continue
                    cfg = PlotConfig(
                        x=r.frequency, y=r.slope_profile,
                        xlabel="Subcarrier Frequency (Hz)",
                        ylabel="Phase Slope (rad/Hz)",
                        title=f"Channel {r.channel_id} — Echo Detection (Phase Slope)",
                        grid=True, legend=False, theme="dark")
                    mp = MatplotManager(default_cfg=cfg)
                    mp.plot_line(self.create_png_fname(tags=[f"ch{r.channel_id}", "echo-slope"]))
                    plots.append(mp)

            case MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT:
                for r in model.results:
                    if not isinstance(r, EchoDetectionIfftModel):
                        continue
                    cfg = PlotConfig(
                        x=list(range(len(r.impulse_response))), y=r.impulse_response,
                        xlabel="Sample Index",
                        ylabel="Amplitude (Linear Units)",
                        title=f"Channel {r.channel_id} — Echo Detection (IFFT Impulse Response)",
                        grid=True, legend=False, theme="dark")
                    mp = MatplotManager(default_cfg=cfg)
                    mp.plot_line(self.create_png_fname(tags=[f"ch{r.channel_id}", "echo-ifft"]))
                    plots.append(mp)

        return plots

    # ──────────────────────────────────────────────────────────
    # Analysis Methods
    # ──────────────────────────────────────────────────────────
    def _analyze_min_avg_max(self) -> List[MinAvgMaxModel]:
        amplitudes, freqs = {}, {}
        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                model = CmDsOfdmChanEstimateCoef(tcm.data).to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)
                ch = ChannelId(result.channel_id)
                if result.carrier_values.magnitudes:
                    amplitudes.setdefault(ch, []).append(result.carrier_values.magnitudes)
                freqs[ch] = result.carrier_values.frequency
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] MIN_AVG_MAX parse failed: {e}")
        return [
            MinAvgMaxModel(channel_id=ch, frequency=freqs.get(ch, []), **MinAvgMax(amps).to_dict())
            for ch, amps in amplitudes.items()
        ]

    def _analyze_group_delay(self) -> List[GroupDelayAnalysisModel]:
        channel_data, freqs = {}, {}
        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                model = CmDsOfdmChanEstimateCoef(tcm.data).to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)
                ch = ChannelId(result.channel_id)
                channel_data.setdefault(ch, []).append(result.carrier_values.complex)
                freqs[ch] = result.carrier_values.frequency
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] GROUP_DELAY parse failed: {e}")
        out = []
        for ch, cplx in channel_data.items():
            gd = GroupDelayCalculator(cplx, freqs[ch]).to_dict()
            out.append(GroupDelayAnalysisModel(channel_id=ch, frequency=gd.get("freqs", []), group_delay_us=gd.get("tau_us", [])))
        return out

    def _analyze_lte_detection(self) -> List[LteDetectionModel]:
        channel_data, freqs, threshold, bin_widths = {}, {}, 1e-9, [1e6, 5e5, 1e5]
        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                model = CmDsOfdmChanEstimateCoef(tcm.data).to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)
                ch = ChannelId(result.channel_id)
                channel_data.setdefault(ch, []).append(result.carrier_values.complex)
                freqs[ch] = result.carrier_values.frequency
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] LTE_DETECTION_PHASE_SLOPE parse failed: {e}")
        out = []
        for ch, cplx in channel_data.items():
            res = GroupDelayAnomalyDetector(cplx, freqs[ch]).run(bin_widths=bin_widths, threshold=threshold)
            out.append(LteDetectionModel(channel_id=ch, anomalies=res.get("anomalies", []), threshold=threshold, bin_widths=bin_widths))
        return out

    def _analyze_echo_detection_phase_slope(self) -> List[EchoDetectionPhaseSlopeModel]:
        channel_data, freqs = {}, {}
        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                model = CmDsOfdmChanEstimateCoef(tcm.data).to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)
                ch = ChannelId(result.channel_id)
                channel_data.setdefault(ch, []).append(result.carrier_values.complex)
                freqs[ch] = result.carrier_values.frequency
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] ECHO_DETECTION_PHASE_SLOPE parse failed: {e}")
        out = []
        for ch, cplx in channel_data.items():
            slope = PhaseSlopeEchoDetector(cplx, freqs[ch]).to_dict()
            out.append(EchoDetectionPhaseSlopeModel(channel_id=ch, slope_profile=slope.get("slope_profile", []), frequency=slope.get("frequency", [])))
        return out

    def _analyze_echo_detection_ifft(self) -> List[EchoDetectionIfftModel]:
        channel_data, obw = {}, {}
        for tcm in self._trans_collect.getTransactionCollectionModel():
            try:
                model = CmDsOfdmChanEstimateCoef(tcm.data).to_model()
                result = Analysis.basic_analysis_ds_chan_est_from_model(model)
                ch = ChannelId(result.channel_id)
                channel_data.setdefault(ch, []).append(result.carrier_values.complex)
                obw[ch] = result.carrier_values.occupied_channel_bandwidth
            except Exception as e:
                self.logger.error(f"[file={tcm.filename}] ECHO_DETECTION_IFFT parse failed: {e}")
        out = []
        for ch, cplx in channel_data.items():
            bw = obw.get(ch, 0)
            if not bw:
                continue
            ifft = IfftEchoDetector(cplx, sample_rate=float(bw)).to_dict()
            out.append(EchoDetectionIfftModel(
                    channel_id          =   ch, 
                    impulse_response    =   ifft.get("impulse_response", []), 
                    sample_rate         =   float(bw)))
        return out
