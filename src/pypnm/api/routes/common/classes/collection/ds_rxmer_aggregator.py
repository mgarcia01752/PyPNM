from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Any, List, Optional, overload
from typing_extensions import override
from pydantic import BaseModel, Field, model_validator
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.api.routes.common.classes.collection.abstract.multi_pnm_aggreator import MultiPnmCollection, MultiPnmCollectionObject
from pypnm.lib.mac_address import MacAddress
from pypnm.lib.types import CaptureTime, ChannelId, FrequencySeriesHz, MacAddressStr, MagnitudeSeries, Sequence
from pypnm.pnm.lib.min_avg_max import MinAvgMax, MinAvgMaxModel
from pypnm.pnm.parser.CmDsOfdmRxMer import CmDsOfdmRxMer

class RxMerCaptureModel(BaseModel):
    capture_time: CaptureTime    = Field(..., ge=0, description="Epoch seconds.")
    channel_id: ChannelId        = Field(..., ge=0, description="OFDM channel id.")
    mac_address: MacAddressStr   = Field(default=MacAddress.null(), description="Normalized MAC (e.g., 00:1a:2b:3c:4d:5e).")
    frequency: FrequencySeriesHz = Field(..., description="Per-subcarrier center frequencies (Hz).")
    values: MagnitudeSeries      = Field(..., description="Per-subcarrier RxMER values (dB).")

    @model_validator(mode="after")
    def _check_lengths(self) -> "RxMerCaptureModel":
        if not self.frequency or not self.values:
            raise ValueError("`frequency` and `values` must be non-empty.")
        if len(self.frequency) != len(self.values):
            raise ValueError(f"Length mismatch: frequency={len(self.frequency)} vs values={len(self.values)}.")
        return self

class DsRxMerAggregator(MultiPnmCollection):
    """
    Aggregates RxMER captures by channel and timestamp.

    Notes
    -----
    - All ingested entries are validated into `RxMerCaptureModel` instances.
    - Enforces a single MAC address across all captures.
    - Provides convenience accessors for:
        • Channel IDs present.
        • Capture timestamps per channel.
        • Frequency arrays.
        • Min/Avg/Max summary statistics via `MinAvgMax`.
        • Basic RxMER analysis via `Analysis` helpers.
    """

    def __init__(self) -> None:
        super().__init__(CmDsOfdmRxMer)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._mac_address: MacAddressStr = MacAddress.null()

    @override
    def add(self, obj: MultiPnmCollectionObject) -> None:
        if not isinstance(obj, CmDsOfdmRxMer):
            raise TypeError(f"DsRxMerAggregator only accepts CmDsOfdmRxMer instances, got {type(obj)}")
        super().add(obj)

    def get_min_avg_max(self, channel_id: ChannelId, precision: int = 2) -> MinAvgMaxModel:
        """
        Compute Min/Avg/Max statistics for RxMER values in a channel.

        Returns
        -------
        MinAvgMaxModel
            Structured model containing min/avg/max arrays and aggregate stats.
        """

        captures: Sequence[tuple[CaptureTime, CmDsOfdmRxMer]] = self.get(channel_id=channel_id)
        mags:List[MagnitudeSeries] = []

        for capture_time, dorm in captures:
            values = dorm.get_rxmer_values()
            self.logger.debug(f'Calculating MinAvgMaxChannel=({channel_id}) - CaptureTime=({capture_time}) - Getting RxMER ValueCount=({len(values)})')
            mags.append(values)

        return MinAvgMax(mags, precision=precision).to_model()

    def get_frequencies(self, channel_id: ChannelId) -> FrequencySeriesHz:
        captures: Sequence[tuple[CaptureTime, CmDsOfdmRxMer]] = self.get(channel_id=channel_id)
        _, obj = captures[0]
        return obj.get_frequencies()

    @overload
    def get_basic_analysis(self) -> Any: ...
    @overload
    def get_basic_analysis(self, channel_id: ChannelId) -> Any: ...
    @overload
    def get_basic_analysis(self, channel_id: ChannelId, capture_time: CaptureTime) -> Any: ...

    def get_basic_analysis(self, channel_id: Optional[ChannelId] = None, capture_time: Optional[CaptureTime] = None) -> Any:
        """
        Perform basic RxMER analysis using `Analysis.basic_analysis_rxmer`.

        Behavior
        --------
        - No arguments: analyze all `CmDsOfdmRxMer` captures across all channels and timestamps.
        - `channel_id` only: analyze all `CmDsOfdmRxMer` captures for the specified channel
        (results gathered in ascending `capture_time` order).
        - `channel_id` + `capture_time`: analyze the single capture at that key, if present.

        Parameters
        ----------
        channel_id : ChannelId | None
            Target channel to analyze. If None, analyzes all channels.
        capture_time : CaptureTime | None
            Timestamp within `channel_id`. If None, analyzes all captures within the channel.

        Returns
        -------
        Any
            Whatever `Analysis.basic_analysis_rxmer` returns (implementation-defined).
            Returns `None` if no matching `CmDsOfdmRxMer` captures are found.

        Notes
        -----
        - Only `CmDsOfdmRxMer` objects are considered; other capture types are ignored.
        - Each capture is converted via `.to_model().model_dump()` prior to analysis to ensure
        a stable, serializable payload for the analysis function.
        """
        captures: List[CmDsOfdmRxMer] = []
        if channel_id is None:
            for ch_map in self._store.values():
                for _, obj in ch_map.items():
                    if isinstance(obj, CmDsOfdmRxMer):
                        captures.append(obj)
        else:
            if capture_time is None:
                for _, obj in sorted(self._store.get(channel_id, {}).items(), key=lambda kv: kv[0]):
                    if isinstance(obj, CmDsOfdmRxMer):
                        captures.append(obj)
            else:
                obj = self.get(channel_id, capture_time)
                if isinstance(obj, CmDsOfdmRxMer):
                    captures.append(obj)
        if not captures:
            return None
        payload = [m.model_dump() for m in (o.to_model() for o in captures)]
        return Analysis.basic_analysis_rxmer(payload)


