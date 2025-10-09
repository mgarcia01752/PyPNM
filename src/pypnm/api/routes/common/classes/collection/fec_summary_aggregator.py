# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging

from typing import Any, Dict, List
from typing_extensions import override

from pydantic import BaseModel, Field

from pypnm.api.routes.common.classes.collection.abstract.multi_pnm_aggreator import MultiPnmCollection, MultiPnmCollectionObject
from pypnm.docsis.cm_snmp_operation import FecSummaryType
from pypnm.lib.types import ChannelId, TimeStamp
from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pypnm.pnm.process.CmDsOfdmModulationProfile import ProfileId


class CodewordSummaryTotalsModel(BaseModel):
    total_codewords: int    = Field(..., description="Total codewords observed")
    corrected: int          = Field(..., description="FEC-corrected codewords")
    uncorrectable: int      = Field(..., description="Uncorrectable codewords")

class ProfileSummaryTotalsModel(BaseModel):
    profile_id: ProfileId               = Field(..., description="")
    summary: CodewordSummaryTotalsModel = Field(..., description="")

class TimeStampProfileCollectionModel(BaseModel):
    timestamp: TimeStamp                                    = Field(..., description="")
    profiles: Dict[ProfileId, ProfileSummaryTotalsModel]    = Field(..., description="")

TimeStampProfileCollection = Dict[TimeStamp, TimeStampProfileCollectionModel]
    
class FecSummaryTotalsModel(BaseModel):
    start:TimeStamp         = Field(description="")
    end: TimeStamp          = Field(description="")
    summary:CodewordSummaryTotalsModel


class FecSummaryAggregator(MultiPnmCollection):
    """
    Aggregates FEC summary data by channel directly in a master dictionary.

    Adds accept CmDsOfdmFecSummary service instances and merges their data
    into a nested dict: channel_id -> profile_id -> timestamp -> entry.

    After the first add, all subsequent summaries must share the same MAC address.
    """
    def __init__(self):
        """
        Initialize an empty master data store and unset MAC.
        """
        super().__init__(CmDsOfdmFecSummary)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._store_channel_timestamps:Dict[ChannelId, Dict[TimeStamp, TimeStampProfileCollectionModel]] = {}
    
    @override
    def add(self, obj: MultiPnmCollectionObject) -> None:
        if not isinstance(obj, CmDsOfdmFecSummary):
            raise TypeError(f"FecSummaryAggregator only accepts CmDsOfdmFecSummary instances, got {type(obj)}")
        super().add(obj)

        self.__update_channel_temporal_db(obj)


    def get_summary_type(self, channel_id: ChannelId) -> FecSummaryType:
        return FecSummaryType.TEN_MIN

    def get_profile_ids(self, channel_id: ChannelId) -> List[ProfileId]:
        """Return sorted list of profile IDs for a channel."""
        return []

    def get_timestamps(self, channel_id: ChannelId, profile_id: ProfileId) -> List[TimeStamp]:
        """Return sorted list of timestamps for a given channel and profile."""
        return []

    def has_entry(self, channel_id: ChannelId, profile_id: ProfileId, timestamp: TimeStamp) -> bool:
        """Check existence of data for channel/profile/timestamp."""
        return False

    def get_entry(self, channel_id: ChannelId, profile_id: ProfileId, timestamp: TimeStamp, closest_entry: int = 0) -> Dict[str, Any]:
        """
        Retrieve entry for channel/profile/timestamp.
        closest_entry : 0 = floor ; 1 = ceiling
        """
        pass

    def get_summary_totals(self, channel_id: ChannelId, start_time: TimeStamp, end_time: TimeStamp) -> FecSummaryTotalsModel:
        """
        Aggregate FEC summary counters per profile between two timestamps (inclusive).

        Args:
            channel_id: ID of the channel to summarize.
            start_time: Lower bound timestamp (inclusive).
            end_time: Upper bound timestamp (inclusive).

        """
        pass

    def __update_channel_temporal_db(self, obj: CmDsOfdmFecSummary) -> None:
        """
        Merge one CmDsOfdmFecSummary parse into the channel→timestamp→profiles store.

        Policy
        ------
        - Idempotent per (channel_id, profile_id, timestamp).
        - If an entry already exists for the same key and values differ,
        last-writer wins (overwrite) and emit a debug log.
        """
        model = obj.to_model()

        channel_id = model.channel_id
        channel_store = self._store_channel_timestamps.setdefault(channel_id, {})

        for profile_block in model.fec_summary_data:
            profile_id:ProfileId = ProfileId(profile_block.profile_id)
            entries = profile_block.codeword_entries

            for ts, total, corrected, uncorrectable in zip(
                entries.timestamp,
                entries.total_codewords,
                entries.corrected,
                entries.uncorrectable,
            ):
                ts_bucket = channel_store.get(ts)
                if ts_bucket is None:
                    ts_bucket = TimeStampProfileCollectionModel(
                        timestamp   =   ts,
                        profiles    =   {}
                    )
                    channel_store[ts] = ts_bucket

                profiles_map = ts_bucket.profiles

                new_summary = CodewordSummaryTotalsModel(
                    total_codewords =   total,
                    corrected       =   corrected,
                    uncorrectable   =   uncorrectable,
                )
                new_profile_totals = ProfileSummaryTotalsModel(
                    profile_id  =   profile_id,
                    summary     =   new_summary,
                )

                existing = profiles_map.get(profile_id)
                if existing is not None:
                    if (
                        existing.summary.total_codewords != new_summary.total_codewords or
                        existing.summary.corrected != new_summary.corrected or
                        existing.summary.uncorrectable != new_summary.uncorrectable
                    ):
                        self.logger.debug(
                            "FEC overwrite: ch=%s ts=%s profile=%s "
                            "old={total:%s corr:%s uncor:%s} -> new={total:%s corr:%s uncor:%s}",
                            channel_id,
                            ts,
                            profile_id,
                            existing.summary.total_codewords,
                            existing.summary.corrected,
                            existing.summary.uncorrectable,
                            new_summary.total_codewords,
                            new_summary.corrected,
                            new_summary.uncorrectable,
                        )

                profiles_map[profile_id] = new_profile_totals

