# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List,  TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.constants import INVALID_CHANNEL_ID, INVALID_PROFILE_ID
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.types import FloatSeries, FrequencySeriesHz, IntSeries, StringArray


class ModulationProfileModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    profile_id: int = Field(..., description="Profile identifier")
    modulation: List[str] = Field(default_factory=list, description="Per-carrier modulation label (e.g., 'QAM256')")
    bits_per_symbol: List[int] = Field(default_factory=list, description="Per-carrier bits per symbol (derived or provided)")
    shannon_min_mer: List[float] = Field(default_factory=list, description="Per-carrier minimum MER per Shannon (dB)")


class ModulationProfileParameters(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    profiles: List[ModulationProfileModel] = Field(default_factory=list, description="All profiles for a channel")


class ModulationProfileAnalysis(CommonAnalysis):
    parameters: ModulationProfileParameters = Field(..., description="Modulation profile parameters")


class ModulationProfileReport(AnalysisReport):
    FNAME_TAG: str = "modulationprofile"

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("ModulationProfileReport")
        self._results: Dict[int, ModulationProfileAnalysis] = {}

    def create_csv(self, **kwargs: Any) -> List[CSVManager]:
        """
        Stream validated models into CSVs. Assumes `_process()` already enforced.
        Emits one CSV per channel/profile pair.
        """
        csv_mgr_list: List[CSVManager] = []
        any_models = False

        for common_model in self.get_common_analysis_model():
            any_models = True
            model = cast(ModulationProfileAnalysis, common_model)
            channel_id: int = int(model.channel_id)
            freq: FrequencySeriesHz = cast(FrequencySeriesHz, model.raw_x)

            if not freq:
                self.logger.warning(f"Channel {channel_id} has empty frequency array; skipping CSV.")
                continue

            try:
                header: List[str] = ["ChannelID", "ProfileID", "Frequency_Hz", "Modulation", "BitsPerSymbol", "ShannonMinMER_dB"]

                for profile in model.parameters.profiles:
                    csv_mgr: CSVManager = self.csv_manager_factory()
                    csv_mgr.set_header(header)

                    csv_fname = self.create_csv_fname(tags=[str(channel_id), str(profile.profile_id), self.FNAME_TAG])
                    csv_mgr.set_path_fname(csv_fname)

                    n = len(freq)
                    mod = self._align_len(profile.modulation, n, fill="UNKNOWN")
                    bps = self._align_len(profile.bits_per_symbol, n, fill=0)
                    mer = self._align_len(profile.shannon_min_mer, n, fill=float("nan"))

                    rows_written = 0
                    for i in range(n):
                        csv_mgr.insert_row([channel_id, profile.profile_id, freq[i], mod[i], int(bps[i]), float(mer[i])])
                        rows_written += 1

                    self.logger.info(f"CSV rows for channel {channel_id} profile {profile.profile_id}: {rows_written}")
                    self.logger.info(f"CSV created for channel {channel_id}: {csv_fname} (rows={csv_mgr.get_row_count()})")

                    csv_mgr_list.append(csv_mgr)

            except Exception as exc:
                self.logger.exception(f"Failed to create CSV for channel {channel_id}: {exc}", exc_info=True)

        if not any_models:
            self.logger.info("No analysis data available; no CSVs created.")

        return csv_mgr_list

    def create_matplot(self, **kwargs: Any) -> List[MatplotManager]:
        """
        Generate per-channel plots, one set per profile:
          1) Bits-per-symbol vs. Frequency
          2) Shannon Min MER vs. Frequency
          3) Modulation order (M-QAM) vs. Frequency
        """
        out: List[MatplotManager] = []

        for common_model in self.get_common_analysis_model():
            model = cast(ModulationProfileAnalysis, common_model)
            channel_id: int = int(model.channel_id)
            freq: FrequencySeriesHz = cast(FrequencySeriesHz, model.raw_x)

            if not freq:
                self.logger.warning(f"Channel {channel_id} has empty frequency array; skipping plots.")
                continue

            for profile in model.parameters.profiles:
                profile_id: int = profile.profile_id
                try:
                    bpsym: IntSeries = self._align_len(profile.bits_per_symbol, len(freq), fill=0)
                    min_mer: FloatSeries = self._align_len(profile.shannon_min_mer, len(freq), fill=float("nan"))
                    mod_lbls: StringArray = self._align_len(profile.modulation, len(freq), fill="UNKNOWN")
                    mod_order: List[int] = [self._derive_qam_order(lbl) for lbl in mod_lbls]
                except Exception as exc:
                    self.logger.exception(f"Failed to align arrays for channel {channel_id} profile {profile_id}: {exc}", exc_info=True)
                    continue

                try:
                    bps_cfg = PlotConfig(title=f"Bits-Per-Symbol vs Frequency — OFDM Ch {channel_id} - ProfileID: {profile_id}", x=freq, xlabel="Frequency (Hz)", y=bpsym, ylabel="Bits-Per-Symbol", grid=True, legend=True, transparent=False)
                    png_fname = self.create_png_fname(tags=[str(channel_id), str(profile_id), "bps", self.FNAME_TAG])
                    self.logger.info(f"Creating Bits-Per-Symbol plot: {png_fname} for channel: {channel_id}")
                    mplot_mgr = MatplotManager(default_cfg=bps_cfg)
                    mplot_mgr.plot_line(filename=png_fname)
                    out.append(mplot_mgr)
                except Exception as exc:
                    self.logger.exception(f"Failed to create Bits-Per-Symbol plot for channel {channel_id} profile {profile_id}: {exc}", exc_info=True)

                try:
                    mer_cfg = PlotConfig(title=f"Shannon Min MER vs Frequency — OFDM Ch {channel_id} - ProfileID: {profile_id}", x=freq, xlabel="Frequency (Hz)", y=min_mer, ylabel="Shannon Min MER (dB)", grid=True, legend=True, transparent=False)
                    png_fname = self.create_png_fname(tags=[str(channel_id), str(profile_id), "shannon", self.FNAME_TAG])
                    self.logger.info(f"Creating Shannon Min MER plot: {png_fname} for channel: {channel_id}")
                    mplot_mgr = MatplotManager(default_cfg=mer_cfg)
                    mplot_mgr.plot_line(filename=png_fname)
                    out.append(mplot_mgr)
                except Exception as exc:
                    self.logger.exception(f"Failed to create Shannon Min MER plot for channel {channel_id} profile {profile_id}: {exc}", exc_info=True)

                try:
                    mod_cfg = PlotConfig(title=f"Modulation Order vs Frequency — OFDM Ch {channel_id} - ProfileID: {profile_id}", x=freq, xlabel="Frequency (Hz)", y=mod_order, ylabel="Modulation Order (M in M-QAM)", grid=True, legend=True, transparent=False)
                    png_fname = self.create_png_fname(tags=[str(channel_id), str(profile_id), "modulation", self.FNAME_TAG])
                    self.logger.info(f"Creating Modulation Order plot: {png_fname} for channel: {channel_id}")
                    mplot_mgr = MatplotManager(default_cfg=mod_cfg)
                    mplot_mgr.plot_line(filename=png_fname)
                    out.append(mplot_mgr)
                except Exception as exc:
                    self.logger.exception(f"Failed to create Modulation Order plot for channel {channel_id} profile {profile_id}: {exc}", exc_info=True)

        return out

    def _process(self) -> None:
        """
        Expected per-item shape (keys are case-sensitive):

        {
          "device_details": {...},
          "pnm_header": {...},
          "mac_address": "...",
          "channel_id": int,
          "frequency_unit": "Hz",
          "shannon_limit_unit": "dB",
          "profiles": [
            {
              "profile_id": int,
              "carrier_values": {
                "frequency": [...],           # List[float] (Hz)
                "modulation": [...],          # List[str]  (e.g., 'QAM256')
                "bits_per_symbol": [...],     # Optional[List[int]]
                "shannon_min_mer": [...]      # List[float] (dB)
              }
            },
            ...
          ]
        }
        """
        data_list: List[Dict[str, Any]] = self.get_analysis_data() or []

        for idx, data in enumerate(data_list):
            try:
                channel_id = int(data.get("channel_id", INVALID_CHANNEL_ID))
                profiles_in: List[Dict[str, Any]] = data.get("profiles", [])

                freq_array: FrequencySeriesHz = []
                profile_models: List[ModulationProfileModel] = []

                for profile_entry in profiles_in:
                    cv: Dict[str, Any] = profile_entry.get("carrier_values", {})
                    profile_id: int = int(profile_entry.get("profile_id", INVALID_PROFILE_ID))

                    freq: List[float] = list(map(float, cv.get("frequency", []) or []))
                    mod: List[str] = list(map(str, cv.get("modulation", []) or []))
                    bps: List[int] = list(map(int, cv.get("bits_per_symbol", []) or []))
                    mer: List[float] = list(map(float, cv.get("shannon_min_mer", []) or []))

                    if not bps and mod:
                        bps = [self._derive_bits_per_symbol(m) for m in mod]

                    if not freq_array and freq:
                        freq_array = freq

                    n = len(freq_array) if freq_array else len(freq)
                    if n:
                        mod = self._align_len(mod, n, fill="UNKNOWN")
                        bps = self._align_len(bps, n, fill=0)
                        mer = self._align_len(mer, n, fill=float("nan"))

                    profile_models.append(ModulationProfileModel(profile_id=profile_id, modulation=mod, bits_per_symbol=bps, shannon_min_mer=mer))

                params = ModulationProfileParameters(profiles=profile_models)

                model = ModulationProfileAnalysis(channel_id=channel_id, raw_x=freq_array, raw_y=[0.0], parameters=params)

                self.register_common_analysis_model(channel_id, model)

            except Exception as exc:
                self.logger.exception(f"Failed to process Modulation Profile item {idx}: {exc}", exc_info=True)

    T = TypeVar("T")

    @staticmethod
    def _align_len(seq: Iterable[T] | List[T], n: int, *, fill: T) -> List[T]:
        """
        Force a sequence to length n using truncation or padding with `fill`.
        """
        lst = list(seq) if not isinstance(seq, list) else seq
        if n <= 0:
            return []
        if len(lst) >= n:
            return lst[:n]
        return lst + [fill] * (n - len(lst))

    @staticmethod
    def _derive_bits_per_symbol(mod_label: str) -> int:
        """
        Best-effort mapping from modulation label to bits/symbol. Accepts forms like 'QAM256', 'QAM-256', '256QAM', 'qam1024', etc.
        """
        if not mod_label:
            return 0
        s = mod_label.strip().upper().replace("-", "").replace("_", "")
        digits = "".join(ch for ch in s if ch.isdigit())
        if not digits:
            return 0
        try:
            order = int(digits)
            from math import log2, isfinite
            val = log2(order)
            return int(val) if isfinite(val) else 0
        except Exception:
            return 0

    @staticmethod
    def _derive_qam_order(mod_label: str) -> int:
        """
        Parse modulation label to return QAM order M (e.g., 'QAM256' -> 256). If the label is missing digits, returns 0.
        """
        if not mod_label:
            return 0
        s = mod_label.strip().upper().replace("-", "").replace("_", "")
        digits = "".join(ch for ch in s if ch.isdigit())
        if not digits:
            return 0
        try:
            return int(digits)
        except Exception:
            return 0
