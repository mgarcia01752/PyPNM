
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Any, Dict, List, cast
from struct import Struct, iter_unpack

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from pypnm.lib.constants import INVALID_CHANNEL_ID
from pypnm.lib.qam.types import CodeWordArray
from pypnm.lib.types import CaptureTime, ChannelId, FloatSeries, MacAddressStr, TimeStamp
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader, PnmHeaderParameters
from pypnm.lib.mac_address import MacAddress




# -------- Struct formats (network/big-endian) --------
SUMMARY_HDR = Struct('!B6sBB')   # channel_id, mac(6), summary_type, num_profiles
PROFILE_HDR = Struct('!BH')      # profile_id, number_of_sets
SET_FMT = '!I3I'                 # timestamp, total_codewords, corrected_codewords, uncorrectable_codewords
SET_REC = Struct(SET_FMT)        # for .size and consistency


class OfdmFecSumCodeWordEntryModel(BaseModel):
    """
    Parallel arrays holding per-interval codeword statistics for a single OFDM profile.

    Notes
    -----
    - All lists must be the same length (aligned time buckets).
    - `timestamp` values are Unix epoch seconds for each aggregation window.
    """
    timestamp: List[TimeStamp]      = Field(..., description="Unix timestamps (seconds) for each aggregation interval")
    total_codewords: CodeWordArray  = Field(..., description="Total codewords observed in each interval")
    corrected: CodeWordArray        = Field(..., description="FEC-corrected codewords per interval")
    uncorrectable: CodeWordArray    = Field(..., description="Uncorrectable codewords per interval")

    @model_validator(mode="after")
    def _validate_lengths(self):
        n = len(self.timestamp)
        if not (len(self.total_codewords) == len(self.corrected) == len(self.uncorrectable) == n):
            raise ValueError("timestamp, total_codewords, corrected, uncorrectable must have equal lengths")
        return self


class OfdmFecSumDataModel(BaseModel):
    """
    FEC summary dataset for a single OFDM modulation profile.
    """
    profile_id: int                                = Field(..., description="OFDM modulation profile identifier")
    number_of_sets: int                            = Field(..., description="Number of time-ordered codeword statistic sets")
    codeword_entries: OfdmFecSumCodeWordEntryModel = Field(..., description="Per-interval codeword stats (parallel arrays)")

    @model_validator(mode="after")
    def _validate_number_of_sets(self):
        if self.number_of_sets != len(self.codeword_entries.timestamp):
            raise ValueError(f"number_of_sets={self.number_of_sets} does not match entries={len(self.codeword_entries.timestamp)}")
        return self


class CmDsOfdmFecSummaryModel(BaseModel):
    """
    Canonical model for DOCSIS downstream OFDM FEC summary.

    Notes
    -----
    - `summary_type` indicates the aggregation window/type (e.g., you noted `2` = 24-hour interval).
    - `num_profiles` is the count of profile blocks in this payload.
    - `fec_summary_data` contains one entry per profile.
    """
    model_config = ConfigDict(populate_by_name=True)

    pnm_header: PnmHeaderParameters                 = Field(..., description="PNM header metadata for this capture")
    channel_id: ChannelId                           = Field(INVALID_CHANNEL_ID, description="Downstream channel ID")
    mac_address: MacAddressStr                      = Field(default_factory=MacAddress.null, description="Cable modem MAC address")
    summary_type: int                               = Field(..., description="Aggregation type/window code (implementation-defined; e.g., 2 = 24-hour)")
    num_profiles: int                               = Field(..., description="Number of OFDM profiles reported in this summary")
    fec_summary_data: List[OfdmFecSumDataModel]     = Field(..., description="Per-profile FEC summary datasets")

    @computed_field
    @property
    def summary_type_label(self) -> str:
        """
        Human-friendly label for `summary_type`. Extend as needed.
        """
        mapping = {
            2: "24-hour interval",
            # 1: "10-minute interval",  # add mappings as you formalize them
        }
        return mapping.get(self.summary_type, f"unknown({self.summary_type})")


class CmDsOfdmFecSummary(PnmHeader):
    """
    Parser/adapter for DOCSIS **Downstream OFDM FEC Summary** payloads.

    Responsibilities
    ----------------
    1) Validate the PNM file type as `OFDM_FEC_SUMMARY`.
    2) Unpack the summary header and iterate per-profile blocks.
    3) For each profile, parse `number_of_sets` entries of timestamp/total/corrected/uncorrectable.
    4) Materialize a `CmDsOfdmFecSummaryModel` with structured results.

    Binary layout (network byte order, big-endian)
    ----------------------------------------------
    Summary header (`!B6sBB`):
      - B   : channel_id
      - 6s  : mac_address (raw 6 bytes)
      - B   : summary_type (aggregation code)
      - B   : num_profiles

    Per-profile header (`!BH`):
      - B   : profile_id
      - H   : number_of_sets

    Codeword set (repeated `number_of_sets` times; `!I3I`):
      - I   : timestamp (epoch seconds)
      - 3I  : total_codewords, corrected_codewords, uncorrectable_codewords
    """

    def __init__(self, binary_data: bytes):
        """
        Initialize and immediately parse a FEC summary blob.

        Parameters
        ----------
        binary_data : bytes
            Raw PNM buffer containing a DS OFDM FEC summary.
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        self._channel_id: ChannelId
        self._mac_address: MacAddressStr
        self._summary_type: int
        self._num_profiles: int
        self._model: CmDsOfdmFecSummaryModel

        self.__process()

    def __process(self) -> None:
        """
        Parse the binary FEC summary and build the model.

        Raises
        ------
        ValueError
            If the PNM file type is not `OFDM_FEC_SUMMARY` or buffer is too short.
        """
        # 1) File-type validation
        if self.get_pnm_file_type() != PnmFileType.OFDM_FEC_SUMMARY:
            expected = PnmFileType.OFDM_FEC_SUMMARY.get_pnm_cann()
            got = self.get_pnm_file_type().get_pnm_cann()
            raise ValueError(f"PNM file stream is not OFDM FEC Summary type: expected {expected}, got {got}")

        mv = memoryview(self.pnm_data)

        # 2) Summary header
        if len(mv) < SUMMARY_HDR.size:
            raise ValueError(f"Insufficient data for FEC summary header: need {SUMMARY_HDR.size}, have {len(mv)}")

        channel_id, mac_raw, summary_type, num_profiles = SUMMARY_HDR.unpack(mv[:SUMMARY_HDR.size])
        self.logger.debug(f"FEC Summary Header Data: {bytes(mv[:SUMMARY_HDR.size]).hex()}")

        self._channel_id = channel_id
        self._mac_address = mac_raw.hex(':')  # AA:BB:CC:DD:EE:FF
        self._summary_type = summary_type
        self._num_profiles = num_profiles

        # 3) Profiles loop
        pos = SUMMARY_HDR.size
        profile_entries: List[OfdmFecSumDataModel] = []

        for profile_index in range(self._num_profiles):
            # Ensure we have a full profile header
            if len(mv) < pos + PROFILE_HDR.size:
                self.logger.error(f"Truncated profile header at index {profile_index} (pos={pos}, need={PROFILE_HDR.size}, have={len(mv)-pos})")
                break

            profile_id, number_of_sets = PROFILE_HDR.unpack(mv[pos:pos + PROFILE_HDR.size])
            pos += PROFILE_HDR.size

            self.logger.debug(f"Profile {profile_id} declares {number_of_sets} set(s)")

            # Compute maximum sets that fit in the remaining buffer
            remaining = len(mv) - pos
            max_sets = remaining // SET_REC.size
            requested_sets = number_of_sets
            if number_of_sets > max_sets:
                self.logger.warning(
                    f"Profile {profile_id}: truncating sets from {requested_sets} to {max_sets} "
                    f"(remaining={remaining} bytes, record={SET_REC.size} bytes)"
                )
                number_of_sets = max_sets

            # Slice the exact bytes for this profile's sets and iterate without manual index math
            set_bytes_len = number_of_sets * SET_REC.size
            sets_slice = mv[pos:pos + set_bytes_len]

            ts: FloatSeries = []
            tc: FloatSeries = []
            cc: FloatSeries = []
            uc: FloatSeries = []

            for timestamp, total, corrected, uncorrectable in iter_unpack(SET_FMT, sets_slice):
                self.logger.debug(f"Profile {profile_id} Set: ts={timestamp}, total={total}, corrected={corrected}, uncorrectable={uncorrectable}")
                ts.append(timestamp)
                tc.append(total)
                cc.append(corrected)
                uc.append(uncorrectable)

            pos += set_bytes_len

            cwe_model = OfdmFecSumCodeWordEntryModel(
                timestamp       =   ts,
                total_codewords =   tc,
                corrected       =   cc,
                uncorrectable   =   uc,
            )

            profile_entry = OfdmFecSumDataModel(
                profile_id          =   profile_id,
                number_of_sets      =   number_of_sets,
                codeword_entries    =   cwe_model,
            )
            profile_entries.append(profile_entry)

        if len(profile_entries) != self._num_profiles:
            self.logger.debug(
                f"Parsed {len(profile_entries)} profile(s), header declared {self._num_profiles}")

        # Get the first timestamp for reference/logging
        first_timestamp: CaptureTime = cast(CaptureTime, profile_entries[0].codeword_entries.timestamp[0])
 
        if not self.override_capture_time(first_timestamp):
            self.logger.error(f'Unable to update CaptureTime from {self._capture_time} -> {first_timestamp}')

        # 4) Build the pydantic model
        self._model = CmDsOfdmFecSummaryModel (
            pnm_header      = self.getPnmHeaderParameterModel(),
            channel_id      = self._channel_id,
            mac_address     = self._mac_address,
            summary_type    = self._summary_type,
            num_profiles    = self._num_profiles,
            fec_summary_data=profile_entries,)

    def to_model(self) -> CmDsOfdmFecSummaryModel:
        """Return the structured pydantic model for the parsed FEC summary."""
        return self._model

    def to_dict(self, header_only: bool = False) -> Dict[str, Any]:
        return self.to_model().model_dump()