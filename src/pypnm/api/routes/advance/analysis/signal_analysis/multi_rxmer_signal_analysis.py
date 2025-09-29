# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from pydantic import BaseModel, Field

from pypnm.api.routes.advance.analysis.report.multi_analysis_rpt import MultiAnalysisRpt
from pypnm.api.routes.advance.common.capture_data_aggregator import CaptureDataAggregator
from pypnm.api.routes.advance.common.transactionsCollection import TransactionCollectionModel
from pypnm.api.routes.common.classes.collection.ds_modulation_profile_aggregator import DsModulationProfileAggregator
from pypnm.api.routes.common.classes.collection.ds_rxmer_aggregator import DsRxMerAggregator
from pypnm.api.routes.common.classes.collection.fec_summary_aggregator import FecSummaryAggregator
from pypnm.lib.constants import INVALID_CAPTURE_TIME
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.signal_processing.shan.shannon import Shannon
from pypnm.lib.types import ArrayLike, CaptureTime, ChannelId, FloatSeries, FrequencySeriesHz, IntSeries, MacAddressStr
from pypnm.pnm.lib.min_avg_max import MinAvgMax
from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pypnm.pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile
from pypnm.pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer, CmDsOfdmRxMerModel

# ---------------------------
# Result Models (Pydantic v2)
# ---------------------------

class MultiRxMerAnalysisType(Enum):
    MIN_AVG_MAX                = 0
    OFDM_PROFILE_PERFORMANCE_1 = 1
    RXMER_HEAT_MAP             = 2


class MultiRxMerAnalysisBaseModel(BaseModel):
    channel_id: ChannelId = Field(..., description="OFDM channel identifier for this result set.")
    frequency: FrequencySeriesHz = Field(..., description="Per-subcarrier frequency bins (Hz).")

class MinAvgMaxAnalysisModel(MultiRxMerAnalysisBaseModel):    
    min:       FloatSeries       = Field(..., description="Per-subcarrier minimum values.")
    avg:       FloatSeries       = Field(..., description="Per-subcarrier average values.")
    max:       FloatSeries       = Field(..., description="Per-subcarrier maximum values.")

class ProfileEntryModel(BaseModel):
    capture_time:   int       = Field(..., description="Epoch capture timestamp.")
    profile_index:  int       = Field(..., description="Modulation profile index for the capture.")
    profile_limits: IntSeries = Field(..., description="Per-subcarrier Shannon limits (bits/s/Hz) for the profile.")
    capacity_delta: IntSeries = Field(..., description="MER-limit minus profile-limit per subcarrier.")

class ChannelOfdmProfilePerfModel(MultiRxMerAnalysisBaseModel):
    avg_mer:            FloatSeries             = Field(..., description="Per-subcarrier average MER (dB).")
    mer_shannon_limits: IntSeries               = Field(..., description="Per-subcarrier Shannon limits derived from avg MER.")
    fec_summary_total:  Dict[str, int]          = Field(..., description="Aggregated FEC counters between first and last capture.")
    profiles:           List[ProfileEntryModel] = Field(..., description="Per-capture per-profile deltas/limits.")

class ChannelHeatMapModel(MultiRxMerAnalysisBaseModel):
    timestamps:  IntSeries               = Field(..., description="Capture timestamps (epoch) for rows of the heatmap.")
    subcarriers: List[Union[int, float]] = Field(..., description="Subcarrier indices or frequency bins for columns.")
    values:      List[List[float]]       = Field(..., description="Matrix: rows=captures, cols=subcarriers; MER values.")


MinAvgMaxMap            = Dict[ChannelId, MinAvgMaxAnalysisModel]
OfdmProfilePerfMap      = Dict[ChannelId, ChannelOfdmProfilePerfModel]
HeatMapMap              = Dict[ChannelId, ChannelHeatMapModel]
TemporalMapping         = Tuple[CaptureTime, Union[CmDsOfdmRxMer, CmDsOfdmFecSummary, CmDsOfdmModulationProfile]]
MultiRxMerAnalysisMap   = Union[MinAvgMaxMap, OfdmProfilePerfMap, HeatMapMap]

class MultiRxMerAnalysisResult(BaseModel):
    mac_address:    MacAddressStr
    analysis_type:  MultiRxMerAnalysisType
    data:           MultiRxMerAnalysisMap
    error:          Optional[str] = ""

# ---------------------------
# Analyzer (models built during processing; single CM)
# ---------------------------

class MultiRxMerSignalAnalysis(MultiAnalysisRpt):

    def __init__(self, capt_data_agg: CaptureDataAggregator, analysis_type: MultiRxMerAnalysisType) -> None:
        super().__init__(capt_data_agg)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.analysis_type = analysis_type
        self._model: Optional[MultiRxMerAnalysisResult] = None
        self._mac: Optional[str] = None

        self._sorted_temporal_mapping: List[TemporalMapping] = []
        self._analysis_map: MultiRxMerAnalysisMap = {}
        self._is_process:bool = False

    # -----------------------
    # Public API
    # -----------------------

    def to_model(self) -> MultiRxMerAnalysisResult:

        if not self._is_process:
            self._process()

        if self._model is not None:
            return self._model
        
        mac = self.getMacAddresses()

        if len(mac) > 1:
            self.logger.error(f'Found #({len(mac)}), Not Expection more than 1 MacAddress -> {mac}')
        
        mac = mac[0].to_mac_format()

        try:
            data = self._dispatch_build()
            self._model = MultiRxMerAnalysisResult(
                mac_address     =   mac,
                analysis_type   =   self.analysis_type,
                data            =   data,
            )

        except Exception as e:
            self.logger.error(f'Unable to create MultiRxMerAnalysisResult, reason: {e}')
            self._model = MultiRxMerAnalysisResult(
                mac_address     =   mac,
                analysis_type   =   self.analysis_type,
                data            =   None,
                error           =   str(e),
            )

        return self._model

    def to_dict(self) -> Dict[str, Any]:
        return self.to_model().model_dump()

    # -----------------------
    # Internals
    # -----------------------

    def _dispatch_build(self) -> MultiRxMerAnalysisMap:

        if self.analysis_type == MultiRxMerAnalysisType.MIN_AVG_MAX:
            return self._analyze_min_avg_max_models()
        
        if self.analysis_type == MultiRxMerAnalysisType.OFDM_PROFILE_PERFORMANCE_1:
            return self._analyze_ofdm_profile_perf_models()
        
        if self.analysis_type == MultiRxMerAnalysisType.RXMER_HEAT_MAP:
            return self._analyze_rxmer_heat_map_models()
        
        raise ValueError(f"Unsupported analysis type: {self.analysis_type}")

    #--------------------------------------------------------------------------
    #               Analyses (single MAC; return channel->model)
    #--------------------------------------------------------------------------
    def _analyze_min_avg_max_models(self) -> MinAvgMaxMap:
        """
        Aggregate per-subcarrier RxMER across time (by channel) using CmDsOfdmRxMerModel.

        For each CmDsOfdmRxMer object in `self._sorted_temporal_mapping`, this:
        - Converts to CmDsOfdmRxMerModel (`obj.to_model()`),
        - Collects `values` (FloatSeries) per `channel_id`,
        - Applies MinAvgMax across captures to produce per-index min/avg/max arrays.

        Returns
        -------
        MinAvgMaxMap
            Mapping of ChannelId -> MinAvgMaxModel (min/avg/max lists per subcarrier index).
        """
        self.logger.info('Building MinAvgMax Signal Analysis')

        chan_series: Dict[ChannelId, List[List[float]]] = {}
        chan_freq: Dict[ChannelId, FrequencySeriesHz] = {}
        mamap: MinAvgMaxMap = {}

        for _, obj in self._sorted_temporal_mapping:

            if not isinstance(obj, CmDsOfdmRxMer):
                self.logger.info('Not a CmDsOfdmRxMer Object, skipping')
                continue

            model: CmDsOfdmRxMerModel = obj.to_model()

            if model.channel_id not in chan_series:
                chan_series[model.channel_id] = []

            chan_series[model.channel_id].append(model.values)
            chan_freq[model.channel_id] = self._build_frequencies(model)

        for cid, series in chan_series.items():

            self.logger.debug(f'Building MinAvgMaxAnalysisModel for Channel: {cid}')
            frequencies = self._build_frequencies(chan_freq.get(cid))

            try:
                mam = MinAvgMax(series, precision=2)
                mam_model = mam.to_model()

                mamap[cid] = MinAvgMaxAnalysisModel(
                    channel_id  =   cid,
                    frequency   =   frequencies,
                    min         =   mam_model.min,
                    avg         =   mam_model.avg,
                    max         =   mam_model.max)

            except ValueError as e:
                self.logger.warning('MinAvgMax failed for channel %s: %s', str(cid), str(e))
                continue

        return mamap

    def _analyze_ofdm_profile_perf_models(self) -> OfdmProfilePerfMap:
        mac    = self._resolve_mac()
        ch_map = self._trans_collect.get_DEPRECATE()[mac]

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
                self._route_pnm_file(data_stream, ds_rxmer, ds_mod, fec_sum, prefix)

        models: OfdmProfilePerfMap = {}
        for ch_id in ds_rxmer.get_channel_ids():
            # NOTE: assuming aggregator exposes getMinAvgMax(ch_id)
            mam = ds_rxmer.getMinAvgMax(ch_id)  # If your method name differs, align here.

            # Shannon conversion path: ensure snr_to_limit accepts dB inputs or convert as needed.
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
                    cv = prof.get("carrier_values") if isinstance(profiles, list) and isinstance(prof, dict) else None
                    if not isinstance(cv, dict):
                        continue

                    shannon_vals = cv.get("shannon_limit")
                    if not isinstance(shannon_vals, list) or not shannon_vals:
                        continue

                    prof_limits = Shannon.snr_to_limit(shannon_vals)
                    capacity_delta = [m - p for p, m in zip(prof_limits, mer_bit_limits)]

                    entries.append(
                        ProfileEntryModel(
                            capture_time=ct,
                            profile_index=idx,
                            profile_limits=prof_limits,
                            capacity_delta=capacity_delta,
                        )
                    )

            models[cast(ChannelId, ch_id)] = ChannelOfdmProfilePerfModel(
                channel_id          =   cast(ChannelId, ch_id),
                avg_mer             =   mam.avg_values,
                mer_shannon_limits  =   mer_bit_limits,
                fec_summary_total   =   fec_totals,
                profiles            =   entries,
            )

        return models

    def _analyze_rxmer_heat_map_models(self) -> HeatMapMap:

        models: HeatMapMap = {}

        for ch_id, entries in ch_map.items():
            timestamps: List[int]       = []
            magnitudes: List[List[float]] = []
            freq_bins:  List[float]     = []

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

            models[cast(ChannelId, int(ch_id))] = ChannelHeatMapModel(
                channel_id=cast(ChannelId, int(ch_id)),
                timestamps=timestamps,
                subcarriers=freq_bins if freq_bins else list(range(len(magnitudes[0]))),
                values=magnitudes,
            )

        return models

    """Abstract Required methods"""

    def _process(self) -> None:
        """
        Process transactions into typed PNM objects and build a time-indexed view.

        Steps
        -----
        1) Fetch all TransactionCollectionModel items from the current TransactionCollection.
        2) Attempt to decode each payload (bytes) as one of:
            - CmDsOfdmRxMer
            - CmDsOfdmFecSummary
            - CmDsOfdmModulationProfile
            In that order; on failure, fall through to the next type.
        3) Store each successfully decoded object in a temporal mapping keyed
        by its capture_time (or INVALID_CAPTURE_TIME if missing).
        4) Produce a list `self._sorted_temporal_mapping` of (capture_time, obj) tuples,
        sorted by ascending capture_time, for downstream iteration.
        """
        self._is_process = True
        self.logger.info("Processing Multi-RxMER Analysis Report")

        # Convert Transactions to PNM RxMER Data
        tc = self.getTransactionCollection()
        tcms:List[TransactionCollectionModel] = tc.getTransactionCollectionModel()
        temporal_mapping:Dict[CaptureTime, Union[CmDsOfdmRxMer, CmDsOfdmFecSummary, CmDsOfdmModulationProfile]] = {}

        self.logger.info(f'TransactionCollectionModel Count: {len(tcms)}')

        # Groom data for general use due to various Analysis that is performed
        for tcm in tcms:

            try:
                dorm = CmDsOfdmRxMer(tcm.data)
                capture_time: CaptureTime = dorm.getPnmHeaderModel().pnm_header.capture_time or INVALID_CAPTURE_TIME
                temporal_mapping[capture_time] = dorm
                continue

            except Exception:
                self.logger.debug('PNM file is not compatible, skipping')

            try:
                dofs = CmDsOfdmFecSummary(tcm.data)
                capture_time: CaptureTime = dofs.getPnmHeaderModel().pnm_header.capture_time or INVALID_CAPTURE_TIME
                temporal_mapping[capture_time] = dofs
                continue

            except Exception:
                self.logger.debug('PNM file is not compatible, skipping')

            try:
                domp = CmDsOfdmModulationProfile(tcm.data)
                capture_time: CaptureTime = domp.getPnmHeaderModel().pnm_header.capture_time or INVALID_CAPTURE_TIME
                temporal_mapping[capture_time] = domp
                continue

            except Exception:
                self.logger.debug('PNM file is not compatible, skipping')

        # Create a sorted list of tuples based on capture_time (ascending)
        self._sorted_temporal_mapping = sorted(temporal_mapping.items(), key=lambda x: x[0])

        self.logger.info(
            f"Temporal mapping size={len(temporal_mapping)}, sorted entries={len(self._sorted_temporal_mapping)}")
        
        self._dispatch_build()

    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Build CSV outputs for supported analysis types.
        Currently implemented for MIN_AVG_MAX only.
        """
        self.logger.debug("Processing Multi-RxMER Analysis CSV Report")
        out: List[CSVManager] = []

        if self.analysis_type == MultiRxMerAnalysisType.MIN_AVG_MAX:
            model = self.to_model()
            data  = cast(MinAvgMaxMap, model.data)

            for ch_id, ch_model in data.items():
                csv_mgr:CSVManager = self.csv_manager_factory()

                # Convert frequency (Hz) → kHz for readability and to match labeling.
                freq_hz  = ch_model.frequency
                freq_khz = [f / 1_000.0 for f in freq_hz]

                csv_mgr.set_header(["channel_id", "frequency_khz", "min", "avg", "max"])

                for idx, f_khz in enumerate(freq_khz):
                    # Defensive indexing (lists should match by construction)
                    mn = ch_model.min[idx]  if idx < len(ch_model.min)  else None
                    av = ch_model.avg[idx]  if idx < len(ch_model.avg)  else None
                    mx = ch_model.max[idx]  if idx < len(ch_model.max)  else None
                    csv_mgr.insert_row([ch_id, f_khz, mn, av, mx])

                csv_fname = self.create_csv_fname(tags=['rxmer_min_avg_max', f'{ch_id}'])
                csv_mgr.set_path_fname(csv_fname)

                out.append(csv_mgr)

        return out

    def create_matplot(self, **kwargs) -> List[MatplotManager]:
        """
        Build MatPlot PNG outputs for supported analysis types.
        Currently implemented for MIN_AVG_MAX only.
        """
        self.logger.debug("Processing Multi-RxMER Analysis MatPlot Report")
        out: List[MatplotManager] = []

        if self.analysis_type == MultiRxMerAnalysisType.MIN_AVG_MAX:
            model = self.to_model()
            data  = cast(MinAvgMaxMap, model.data)

            for channel_id, ch_model in data.items():
                # Frequency (Hz) → kHz to match label
                freq_hz  = cast(ArrayLike, ch_model.frequency)
                freq_khz = cast(ArrayLike,[float(f) / 1_000.0 for f in cast(List[float], freq_hz)])

                mn  = cast(ArrayLike, ch_model.min)
                av  = cast(ArrayLike, ch_model.avg)
                mx  = cast(ArrayLike, ch_model.max)

                cfg = PlotConfig(
                    title=f"Min-Avg-Max RxMER Channel: {channel_id}",
                    x=freq_khz,              xlabel="Frequency (kHz)",
                    y_multi=[mn, av, mx],    y_multi_label=["Min", "Avg", "Max"],
                    grid=True, legend=True, transparent=False,
                )

                multi = self.create_png_fname(tags=[str(channel_id), "rxmer_min_avg_max"])
                self.logger.debug("Creating MatPlot: %s for channel: %s", multi, channel_id)

                mat_mgr = MatplotManager(default_cfg=cfg)
                mat_mgr.plot_multi_line(filename=multi)

                out.append(mat_mgr)

        else:
            self.logger.warning(f'STUB: To Be Implemented - Analysis Type: {self.analysis_type}')

        return out

    """Helpers"""

    def _build_frequencies(self, model: Union[CmDsOfdmRxMerModel, FrequencySeriesHz, None]) -> FrequencySeriesHz:
        """
        Build absolute subcarrier center frequencies (Hz) for the RxMER series.
        """
        if isinstance(model, list):
            return model
        if model is None:
            return []
            
        active_idx  = model.first_active_subcarrier_index
        spacing     = model.subcarrier_spacing
        freq_zero   = model.subcarrier_zero_frequency
        num_idx     = len(model.values)

        start_freq  = freq_zero + (spacing * active_idx)

        freqs: FrequencySeriesHz = [int(start_freq + (i * spacing)) for i in range(num_idx)]
        return freqs

