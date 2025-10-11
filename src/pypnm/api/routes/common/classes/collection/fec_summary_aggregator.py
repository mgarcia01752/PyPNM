# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
from typing import Dict, List, Optional
from typing_extensions import override
from pydantic import BaseModel, Field

from pypnm.api.routes.common.classes.collection.abstract.multi_pnm_aggreator import (
    MultiPnmCollection, MultiPnmCollectionObject)
from pypnm.docsis.cm_snmp_operation import FecSummaryType
from pypnm.lib.types import ChannelId, TimeStamp
from pypnm.pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pypnm.pnm.process.CmDsOfdmModulationProfile import ProfileId


class CodewordSummaryTotalsModel(BaseModel):
    total_codewords: int    = Field(..., description="Total codewords observed")
    corrected: int          = Field(..., description="FEC-corrected codewords")
    uncorrectable: int      = Field(..., description="Uncorrectable codewords")


class ProfileSummaryTotalsModel(BaseModel):
    profile_id: ProfileId                 = Field(..., description="")
    summary: CodewordSummaryTotalsModel   = Field(..., description="")

class FecSummaryTotalsModel(BaseModel):
    start: TimeStamp                            = Field(..., description="")
    end: TimeStamp                              = Field(..., description="")   
    channel_id: ChannelId                       = Field(..., description="")
    summary: List[ProfileSummaryTotalsModel]   = Field(..., description="")

class TimeStampProfileCollectionModel(BaseModel):
    timestamp: TimeStamp                                    = Field(..., description="")
    profiles: Dict[ProfileId, ProfileSummaryTotalsModel]    = Field(..., description="")


TimeStampProfileCollection = Dict[TimeStamp, TimeStampProfileCollectionModel]


class FecSummaryAggregator(MultiPnmCollection):
    """
    Aggregates FEC summary data by channel directly in a master dictionary.

    Adds accept CmDsOfdmFecSummary service instances and merges their data
    into a nested dict: channel_id -> timestamp -> {profile_id -> totals}.

    After the first add, all subsequent summaries must share the same MAC address.
    """

    def __init__(self) -> None:
        """
        Initialize an empty master data store and unset MAC.
        """
        super().__init__(CmDsOfdmFecSummary)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._store_channel_timestamps: Dict[ChannelId, Dict[TimeStamp, TimeStampProfileCollectionModel]] = {}

    @override
    def add(self, obj: MultiPnmCollectionObject) -> None:
        """
        Add a CmDsOfdmFecSummary object and merge into the channel→timestamp→profiles store.

        Parameters
        ----------
        obj : MultiPnmCollectionObject
            Must be an instance of CmDsOfdmFecSummary.
        """
        if not isinstance(obj, CmDsOfdmFecSummary):
            raise TypeError(f"FecSummaryAggregator only accepts CmDsOfdmFecSummary instances, got {type(obj)}")
        super().add(obj)
        self.__update_channel_temporal_db(obj)

    def get_summary_type(self, channel_id: ChannelId) -> FecSummaryType:
        """
        Return the summary type for this channel.

        Parameters
        ----------
        channel_id : ChannelId
            Channel identifier.

        Returns
        -------
        FecSummaryType
            Summary granularity.
        """
        return FecSummaryType.TEN_MIN

    def get_profile_ids(self, channel_id: ChannelId) -> List[ProfileId]:
        """
        Return sorted list of profile IDs for a channel.

        Parameters
        ----------
        channel_id : ChannelId
            Channel identifier.

        Returns
        -------
        List[ProfileId]
            Sorted list of profile IDs available in the channel.
        """
        channel_store = self._store_channel_timestamps.get(channel_id)
        if not channel_store:
            return []
        s: set[ProfileId] = set()
        for bucket in channel_store.values():
            s.update(bucket.profiles.keys())
        return sorted(s, key=int)

    def get_timestamps(self, channel_id: ChannelId, profile_id: ProfileId) -> List[TimeStamp]:
        """Return sorted timestamps for which a profile has data in a channel.

        Parameters
        ----------
        channel_id : ChannelId
            Channel to inspect.
        profile_id : ProfileId
            Profile to filter within the channel.

        Returns
        -------
        List[TimeStamp]
            Ascending list of timestamps; empty if none.
        """
        channel_store = self._store_channel_timestamps.get(channel_id)
        if not channel_store:
            return []
        out: List[TimeStamp] = []
        for ts, bucket in channel_store.items():
            if profile_id in bucket.profiles:
                out.append(ts)
        out.sort()
        return out

    def has_entry(self, channel_id: ChannelId, profile_id: ProfileId, timestamp: TimeStamp) -> bool:
        """Test if a channel/profile has an entry at a specific timestamp.

        Parameters
        ----------
        channel_id : ChannelId
            Channel to inspect.
        profile_id : ProfileId
            Profile to check.
        timestamp : TimeStamp
            Exact timestamp key.

        Returns
        -------
        bool
            True if an entry exists, otherwise False.
        """
        channel_store = self._store_channel_timestamps.get(channel_id)
        if not channel_store:
            return False
        bucket = channel_store.get(timestamp)
        if not bucket:
            return False
        return profile_id in bucket.profiles

    def get_entry(self, channel_id: ChannelId, profile_id: ProfileId, timestamp: TimeStamp, closest_entry: int = 0) -> Optional[TimeStampProfileCollectionModel]:
        """Retrieve the TimeStampProfileCollectionModel at an exact or nearest timestamp containing the profile.

        Behavior
        --------
        If an exact match exists and contains the requested profile, return it. Otherwise, select the nearest
        timestamp that contains the profile according to `closest_entry`:
        - 0: floor (latest timestamp ≤ requested)
        - 1: ceiling (earliest timestamp ≥ requested)

        Parameters
        ----------
        channel_id : ChannelId
            Channel to search.
        profile_id : ProfileId
            Profile that must be present in the returned bucket.
        timestamp : TimeStamp
            Target timestamp.
        closest_entry : int, default 0
            0 for floor, 1 for ceiling.

        Returns
        -------
        Optional[TimeStampProfileCollectionModel]
            The bucket at the chosen timestamp, or None if not found.
        """
        channel_store = self._store_channel_timestamps.get(channel_id)
        if not channel_store:
            return None
        bucket = channel_store.get(timestamp)
        if bucket and profile_id in bucket.profiles:
            return bucket
        ts_list = self.get_timestamps(channel_id, profile_id)
        if not ts_list:
            return None
        if closest_entry == 0:
            candidates = [t for t in ts_list if t <= timestamp]
            if not candidates:
                return None
            ts_sel = max(candidates)
        else:
            candidates = [t for t in ts_list if t >= timestamp]
            if not candidates:
                return None
            ts_sel = min(candidates)
        return channel_store.get(ts_sel)

    def get_summary_totals(self, channel_id: ChannelId, start_time: TimeStamp, end_time: TimeStamp) -> FecSummaryTotalsModel:
        """Aggregate FEC summary counters per profile between two timestamps (inclusive).

        Parameters
        ----------
        channel_id : ChannelId
            Channel to summarize.
        start_time : TimeStamp
            Inclusive lower bound.
        end_time : TimeStamp
            Inclusive upper bound.

        Returns
        -------
        FecSummaryTotalsModel
            Aggregated summary per profile for the specified channel and time range.
        """
        channel_store = self._store_channel_timestamps.get(channel_id, {})
        if not channel_store:
            return FecSummaryTotalsModel(
                start       =   start_time,
                end         =   end_time,
                channel_id  =   channel_id,
                summary     =   [],
            )

        ts_range = [ts for ts in channel_store.keys() if start_time <= ts <= end_time]
        profile_totals: Dict[ProfileId, CodewordSummaryTotalsModel] = {}

        for ts in ts_range:
            bucket = channel_store[ts]
            for pid, entry in bucket.profiles.items():
                agg = profile_totals.get(pid)
                if agg is None:
                    profile_totals[pid] = CodewordSummaryTotalsModel(
                        total_codewords =   entry.summary.total_codewords,
                        corrected       =   entry.summary.corrected,
                        uncorrectable   =   entry.summary.uncorrectable,
                    )
                else:
                    agg.total_codewords += entry.summary.total_codewords
                    agg.corrected += entry.summary.corrected
                    agg.uncorrectable += entry.summary.uncorrectable

        summary_list: List[ProfileSummaryTotalsModel] = [
            ProfileSummaryTotalsModel(profile_id=pid, summary=totals)
            for pid, totals in profile_totals.items()
        ]

        return FecSummaryTotalsModel(
            start       =   start_time,
            end         =   end_time,
            channel_id  =   channel_id,
            summary     =   summary_list,
        )

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
            profile_id: ProfileId = ProfileId(profile_block.profile_id)
            entries = profile_block.codeword_entries
            for ts, total, corrected, uncorrectable in zip(
                entries.timestamp,
                entries.total_codewords,
                entries.corrected,
                entries.uncorrectable,
            ):
                ts_bucket = channel_store.get(ts)
                if ts_bucket is None:
                    ts_bucket = TimeStampProfileCollectionModel(timestamp=ts, profiles={})
                    channel_store[ts] = ts_bucket
                profiles_map = ts_bucket.profiles
                new_summary = CodewordSummaryTotalsModel(total_codewords=total, corrected=corrected, uncorrectable=uncorrectable)
                new_profile_totals = ProfileSummaryTotalsModel(profile_id=profile_id, summary=new_summary)
                existing = profiles_map.get(profile_id)
                if existing is not None:
                    if (
                        existing.summary.total_codewords != new_summary.total_codewords
                        or existing.summary.corrected != new_summary.corrected
                        or existing.summary.uncorrectable != new_summary.uncorrectable
                    ):
                        self.logger.debug(
                            "FEC overwrite: ch=%s ts=%s profile=%s old={total:%s corr:%s uncor:%s} -> new={total:%s corr:%s uncor:%s}",
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
