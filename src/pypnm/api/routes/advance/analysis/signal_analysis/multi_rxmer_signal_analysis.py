# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

from pypnm.api.routes.advance.common.pnm_collection import PnmCollection
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.collection.ds_modulation_profile_aggregator import DsModulationProfileAggregator
from pypnm.api.routes.common.classes.collection.ds_rxmer_aggregator import DsRxMerAggregator
from pypnm.api.routes.common.classes.collection.fec_summary_aggregator import FecSummaryAggregator
from pypnm.lib.signal_processing.shan.shannon import Shannon
from pypnm.lib.types import FloatSeries, FrequencySeriesHz, IntSeries
from pypnm.pnm.lib.min_avg_max import MinAvgMax
from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pypnm.pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile
from pypnm.pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


# ---------------------------
# Result Models (Pydantic v2)
# ---------------------------

class MultiRxMerAnalysisType(Enum):
    MIN_AVG_MAX                = 0
    OFDM_PROFILE_PERFORMANCE_1 = 1
    RXMER_HEAT_MAP             = 2


class MultiRxMerAnalysisBaseModel(BaseModel):
    channel_id: int = Field(..., description="OFDM channel identifier for this result set.")


class MinAvgMaxModel(MultiRxMerAnalysisBaseModel):
    frequency: FrequencySeriesHz = Field(..., description="Per-subcarrier frequency bins (Hz).")
    min:       FloatSeries       = Field(..., description="Per-subcarrier minimum values.")
    avg:       FloatSeries       = Field(..., description="Per-subcarrier average values.")
    max:       FloatSeries       = Field(..., description="Per-subcarrier maximum values.")


class ProfileEntryModel(BaseModel):
    capture_time:   int       = Field(..., description="Epoch capture timestamp.")
    profile_index:  int       = Field(..., description="Modulation profile index for the capture.")
    profile_limits: IntSeries = Field(..., description="Per-subcarrier Shannon limits (bits/s/Hz) for the profile.")
    capacity_delta: IntSeries = Field(..., description="MER-limit minus profile-limit per subcarrier.")


class ChannelOfdmProfilePerfModel(MultiRxMerAnalysisBaseModel):
    avg_mer:            FloatSeries            = Field(..., description="Per-subcarrier average MER (dB).")
    mer_shannon_limits: IntSeries              = Field(..., description="Per-subcarrier Shannon limits derived from avg MER.")
    fec_summary_total:  Dict[str, int]         = Field(..., description="Aggregated FEC counters between first and last capture.")
    profiles:           List[ProfileEntryModel]= Field(..., description="Per-capture per-profile deltas/limits.")


class ChannelHeatMapModel(MultiRxMerAnalysisBaseModel):
    timestamps:  IntSeries               = Field(..., description="Capture timestamps (epoch) for rows of the heatmap.")
    subcarriers: List[Union[int, float]] = Field(..., description="Subcarrier indices or frequency bins for columns.")
    values:      List[List[float]]       = Field(..., description="Matrix: rows=captures, cols=subcarriers; MER values.")


# channel_id -> model
MinAvgMaxMap       = Dict[int, MinAvgMaxModel]
OfdmProfilePerfMap = Dict[int, ChannelOfdmProfilePerfModel]
HeatMapMap         = Dict[int, ChannelHeatMapModel]


class MultiRxMerAnalysisResult(BaseModel):
    mac_address: str
    analysis_type: MultiRxMerAnalysisType
    data: Union[MinAvgMaxMap, OfdmProfilePerfMap, HeatMapMap, None] = None
    error: Optional[str] = None


# ---------------------------
# Analyzer (models built during processing; single CM)
# ---------------------------

class MultiRxMerSignalAnalysis:
    """
    Single-CM Multi-RxMER analyses. Models are built during processing.
    `to_model()` returns the cached model.
    """

    def __init__(self, collection: PnmCollection, analysis_type: MultiRxMerAnalysisType) -> None:
        self.logger        = logging.getLogger(self.__class__.__name__)
        self.collection    = collection
        self.analysis_type = analysis_type
        self._model: Optional[MultiRxMerAnalysisResult] = None
        self._mac: Optional[str] = None

    # -----------------------
    # Public API
    # -----------------------

    def to_model(self) -> MultiRxMerAnalysisResult:
        if self._model is not None:
            return self._model
        try:
            mac = self._resolve_mac()
            data = self._dispatch_build()
            self._model = MultiRxMerAnalysisResult(mac_address=mac, analysis_type=self.analysis_type, data=data)
        except Exception as e:
            mac = self._mac or "00:00:00:00:00:00"
            self._model = MultiRxMerAnalysisResult(mac_address=mac, analysis_type=self.analysis_type, data=None, error=str(e))
        return self._model

    def to_dict(self) -> Dict[str, Any]:
        return self.to_model().model_dump()

    # -----------------------
    # Internals
    # -----------------------

    def _resolve_mac(self) -> str:
        if self._mac:
            return self._mac
        nested = self.collection.get()  # expected shape: { mac: { channel_id: [entries...] } }
        if not nested:
            raise ValueError("No data in collection.")
        macs = list(nested.keys())
        if len(macs) != 1:
            raise ValueError(f"Expected a single MAC, found {len(macs)}: {macs}")
        self._mac = macs[0]
        return self._mac

    def _dispatch_build(self) -> Union[MinAvgMaxMap, OfdmProfilePerfMap, HeatMapMap]:
        if self.analysis_type == MultiRxMerAnalysisType.MIN_AVG_MAX:
            return self._analyze_min_avg_max_models()
        if self.analysis_type == MultiRxMerAnalysisType.OFDM_PROFILE_PERFORMANCE_1:
            return self._analyze_ofdm_profile_perf_models()
        if self.analysis_type == MultiRxMerAnalysisType.RXMER_HEAT_MAP:
            return self._analyze_rxmer_heat_map_models()
        raise ValueError(f"Unsupported analysis type: {self.analysis_type}")

    # -----------------------
    # Helpers
    # -----------------------

    def _parse_rxmer_series(self, entry: Dict[str, Any]) -> Optional[Tuple[List[float], List[float], int]]:
        data_stream = entry.get("data")
        if data_stream is None:
            return None
        try:
            dorm = CmDsOfdmRxMer(data_stream)
            hdr  = dorm.to_dict()
            res  = Analysis.basic_analysis_rxmer(hdr)

            cv = getattr(res, "carrier_values", None)
            if cv is not None:
                mags, freqs = cv.magnitude, cv.frequency
            else:
                mags  = res.get("magnitude") or res.get("carrier_values", {}).get("magnitude", [])
                freqs = res.get("frequency") or res.get("carrier_values", {}).get("frequency", [])
            if not mags:
                return None

            ts = hdr.get("pnm_header", {}).get("capture_time", 0)
            return mags, (freqs or []), ts
        except Exception:
            return None

    def _route_pnm_file(
        self,
        data_stream: bytes,
        rxmer: DsRxMerAggregator,
        modprof: DsModulationProfileAggregator,
        fecsum: FecSummaryAggregator,
        log_prefix: str,
    ) -> None:
        try:
            file_type: PnmFileType = PnmHeader(data_stream).get_pnm_file_type()  # type: ignore
        except Exception as e:
            self.logger.error(f"{log_prefix} - PNM header parse failed: {e}")
            return

        if file_type == PnmFileType.RECEIVE_MODULATION_ERROR_RATIO:
            self.logger.debug(f"{log_prefix} - {file_type.name} Found"); rxmer.add(CmDsOfdmRxMer(data_stream)); return
        if file_type == PnmFileType.OFDM_MODULATION_PROFILE:
            self.logger.debug(f"{log_prefix} - {file_type.name} Found"); modprof.add(CmDsOfdmModulationProfile(data_stream)); return
        if file_type == PnmFileType.OFDM_FEC_SUMMARY:
            self.logger.debug(f"{log_prefix} - {file_type.name} Found"); fecsum.add(CmDsOfdmFecSummary(data_stream)); return

        self.logger.warning(f"{log_prefix} - Unexpected PNM file: {file_type.name}, skipping")

    # -----------------------
    # Analyses (single MAC; return channel->model)
    # -----------------------

    def _analyze_min_avg_max_models(self) -> MinAvgMaxMap:
        mac = self._resolve_mac()
        ch_map = self.collection.get()[mac]

        channel_amplitudes: Dict[int, List[List[float]]] = {}
        channel_frequencies: Dict[int, List[float]] = {}

        for ch_id, entries in ch_map.items():
            for entry in entries:
                parsed = self._parse_rxmer_series(entry)
                if not parsed:
                    continue
                mags, freqs, _ = parsed
                channel_amplitudes.setdefault(ch_id, []).append(mags)
                if ch_id not in channel_frequencies and freqs:
                    channel_frequencies[ch_id] = freqs

        models: MinAvgMaxMap = {}
        for ch_id, series in channel_amplitudes.items():
            try:
                calc = MinAvgMax(series).to_dict()
                models[ch_id] = MinAvgMaxModel(
                    channel_id=ch_id,
                    frequency=channel_frequencies.get(ch_id, []),
                    min=calc.get("min", []),
                    avg=calc.get("avg", []),
                    max=calc.get("max", []),
                )
            except ValueError as ve:
                self.logger.error(f"[{mac}][ch={ch_id}] MinAvgMax computation failed: {ve}")
        return models

    def _analyze_ofdm_profile_perf_models(self) -> OfdmProfilePerfMap:
        mac = self._resolve_mac()
        ch_map = self.collection.get()[mac]

        ds_rxmer = DsRxMerAggregator()
        ds_mod   = DsModulationProfileAggregator()
        fec_sum  = FecSummaryAggregator()

        for ch_id, entries in ch_map.items():
            prefix = f"[{mac}][ch={ch_id}]"
            for entry in entries:
                data_stream = entry.get("data")
                if data_stream is None:
                    self.logger.error(f"{prefix} - No DataStream Found")
                    continue
                self._route_pnm_file(data_stream, ds_rxmer, ds_mod, fec_sum, f"[{mac}]")

        models: OfdmProfilePerfMap = {}
        for ch_id in ds_rxmer.get_channel_ids():
            mam = ds_rxmer.getMinAvgMin(ch_id)
            mer_bit_limits: List[int] = Shannon.snr_to_limit(mam.avg_values)

            capture_times = ds_rxmer.get_capture_times(ch_id)
            if not capture_times:
                self.logger.warning(f"[{mac}][ch={ch_id}] No captures for channel, skipping")
                continue

            start_time, end_time = capture_times[0], capture_times[-1]
            fec_totals = fec_sum.get_summary_totals(ch_id, start_time, end_time)

            entries: List[ProfileEntryModel] = []
            for ct in capture_times:
                result = ds_mod.basic_analysis(ch_id, ct)
                profiles = result.get("profiles", []) if isinstance(result, dict) else result
                if not isinstance(profiles, list):
                    continue

                for idx, prof in enumerate(profiles):
                    cv = prof.get("carrier_values")
                    if not isinstance(cv, dict):
                        continue
                    shannon_vals = cv.get("shannon_limit")
                    if not isinstance(shannon_vals, list) or not shannon_vals:
                        continue

                    prof_limits = Shannon.snr_to_limit(shannon_vals)
                    capacity_delta = [m - p for p, m in zip(prof_limits, mer_bit_limits)]
                    entries.append(ProfileEntryModel(
                        capture_time=ct,
                        profile_index=idx,
                        profile_limits=prof_limits,
                        capacity_delta=capacity_delta,
                    ))

            models[ch_id] = ChannelOfdmProfilePerfModel(
                channel_id=ch_id,
                avg_mer=mam.avg_values,
                mer_shannon_limits=mer_bit_limits,
                fec_summary_total=fec_totals,
                profiles=entries,
            )
        return models

    def _analyze_rxmer_heat_map_models(self) -> HeatMapMap:
        mac = self._resolve_mac()
        ch_map = self.collection.get()[mac]

        models: HeatMapMap = {}
        for ch_id, entries in ch_map.items():
            timestamps: List[int] = []
            magnitudes: List[List[float]] = []
            freq_bins: List[float] = []

            for entry in entries:
                parsed = self._parse_rxmer_series(entry)
                if not parsed:
                    continue
                mags, freqs, ts = parsed
                timestamps.append(ts)
                magnitudes.append(mags)
                if not freq_bins and freqs:
                    freq_bins = freqs

            if not magnitudes:
                continue

            models[ch_id] = ChannelHeatMapModel(
                channel_id=ch_id,
                timestamps=timestamps,
                subcarriers=freq_bins if freq_bins else list(range(len(magnitudes[0]))),
                values=magnitudes,
            )
        return models
