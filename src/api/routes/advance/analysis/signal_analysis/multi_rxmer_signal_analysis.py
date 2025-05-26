# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
import json
import logging
import time
from typing import Any, Dict, List, Optional

from api.routes.advance.common.pnm_collection import PnmCollection
from api.routes.common.classes.analysis.analysis import Analysis
from api.routes.common.classes.collection.ds_modulation_profile_aggregator import DsModulationProfileAggregator
from api.routes.common.classes.collection.ds_rxmer_aggregator import DsRxMerAggregator
from api.routes.common.classes.collection.fec_summary_aggregator import FecSummaryAggregator
from lib.shannon.shannon import Shannon
from pnm.lib.min_avg_max import MinAvgMax
from pnm.process.CmDsOfdmFecSummary import CmDsOfdmFecSummary
from pnm.process.CmDsOfdmModulationProfile import CmDsOfdmModulationProfile
from pnm.process.CmDsOfdmRxMer import CmDsOfdmRxMer
from pnm.process.pnm_file_type import PnmFileType
from pnm.process.pnm_header import PnmHeader

class MultiRxMerAnalysisType(Enum):
    """
    Signal analysis routines for Multi-RxMER data.
    """
    MIN_AVG_MAX = 0
    OFDM_PROFILE_PERFORMANCE_1 = 1
    RXMER_HEAT_MAP = 2


class MultiRxMerSignalAnalysis:
    """
    Performs signal-quality analyses on grouped Multi-RxMER captures.
    """

    def __init__(self,
                 collection: PnmCollection,
                 analysis_type: MultiRxMerAnalysisType
    ) -> None:
        """
        Args:
            collection: Indexed captures by MAC and channel.
            analysis_type: Type of analysis to run.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.collection = collection
        self.analysis_type = analysis_type
        self.results: Optional[Any] = None

    def _process(self) -> Any:
        """
        Dispatch to the selected analysis routine.

        Returns:
            Analysis result structure.

        Raises:
            ValueError: If analysis_type is unsupported.
        """
        if self.analysis_type == MultiRxMerAnalysisType.MIN_AVG_MAX:
            return self._analyze_min_avg_max()
        elif self.analysis_type == MultiRxMerAnalysisType.OFDM_PROFILE_PERFORMANCE_1:
            return self._analyze_ofdm_profile_performance_1()
        elif self.analysis_type == MultiRxMerAnalysisType.RXMER_HEAT_MAP:
            return self._analyze_rxmer_heat_map()
        else:
            raise ValueError(f"Unsupported analysis type: {self.analysis_type}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Run the analysis (if not done) and return a JSON-serializable dict.

        Always returns:
        {
            "analysis_type": <name>,
            "data": <_process() result or None>,
            "error": <error msg if it failed>
        }
        """
        # Lazily run the analysis
        if self.results is None:
            try:
                self.results = self._process()
            except Exception as e:
                return {
                    "analysis_type": self.analysis_type.name,
                    "data": None,
                    "error": str(e)
                }

        # By here, self.results may be any type—dict, list, int, etc.
        return {
            "analysis_type": self.analysis_type.name,
            "data": self.results
        }

    def _analyze_min_avg_max(self) -> Dict[int, Dict[str, List[float]]]:
        """
        Aggregate per-capture MER magnitude series by channel,
        then compute per-subcarrier min/avg/max using MinAvgMax.

        Assumes self.collection.get() returns:
            {
              mac_address: {
                  channel_id: [ entry_dict, ... ],
                  ...
              },
              ...
            }

        Returns:
            {
              channel_id: {
                  "frequency": [...],
                  "min": [...],
                  "avg": [...],
                  "max": [...],
              },
              ...
            }
        """
        channel_amplitudes: Dict[int, List[List[float]]] = {}
        channel_frequencies: Dict[int, List[float]] = {}

        nested = self.collection.get()
        for mac, channel_map in nested.items():
            for channel_id, entries in channel_map.items():
                for entry in entries:
                    data_stream = entry.get("data")
                    if data_stream is None:
                        continue
                    try:
                        # Parse RxMER sample and extract analysis
                        dorm = CmDsOfdmRxMer(data_stream)
                        measurement = dorm.to_dict()
                        result = Analysis.basic_analysis_rxmer(measurement)

                        # Extract magnitude list
                        mags = result.get("magnitude")
                        if not isinstance(mags, list):
                            mags = result.get("carrier_values", {}).get("magnitude", [])

                        # Extract frequency list
                        freqs = result.get("frequency")
                        if not isinstance(freqs, list):
                            freqs = result.get("carrier_values", {}).get("frequency", [])

                        if not mags:
                            self.logger.warning(
                                f"[{mac}][ch={channel_id}] No valid magnitudes, skipping"
                            )
                            continue

                    except Exception as e:
                        self.logger.error(
                            f"[{mac}][ch={channel_id}] RxMER parse failed: {e}"
                        )
                        continue

                    channel_amplitudes.setdefault(channel_id, []).append(mags)
                    # Store frequency bins once
                    if channel_id not in channel_frequencies and freqs:
                        channel_frequencies[channel_id] = freqs

        # Compute stats per channel and attach frequencies
        stats: Dict[int, Dict[str, List[float]]] = {}
        for channel_id, amp_lists in channel_amplitudes.items():
            try:
                calc = MinAvgMax(amp_lists)
                channel_stat = calc.to_dict()
                channel_stat["frequency"] = channel_frequencies.get(channel_id, [])
                stats[channel_id] = channel_stat
            except ValueError as ve:
                self.logger.error(
                    f"[ch={channel_id}] MinAvgMax computation failed: {ve}"
                )

        return stats

    def _analyze_ofdm_profile_performance_1(self) -> Dict[int, Dict[str, Any]]:
        """
            OFDM_PROFILE_MEASUREMENT_1
            --------------------------    
            * Calculate the Avg RxMER of the series
            * Calculate Shannon for each subcarrier
            * Compare each modualtion profile against the RxMER Average
            * Calculate the percentage of subcarries that are outside a given profile
            * Provide total FEC Stats for each profile over the time of the capture.
            op = e7a3468d602442b8        
        """
        stats: Dict[int, Dict[str, Any]] = {}
        
        dsRxMerAggregator = DsRxMerAggregator()
        dsModProfileAggregator =  DsModulationProfileAggregator()
        fecSummaryAggregator = FecSummaryAggregator()
        
        # Collection of Data
        nested = self.collection.get()
        for mac, channel_map in nested.items():
            for channel_id, entries in channel_map.items():
                for entry in entries:
                    
                    data_stream = entry.get("data")
                    if data_stream is None:
                        self.logger.error(f'[{mac}][ch={channel_id}] - No DataStream Found')
                        continue
                    try:
                        
                        file_type:PnmFileType = PnmHeader(data_stream).get_pnm_file_type() # type: ignore
                        if not file_type:
                            self.logger.error(f'Unknown PNM File Type ')
                            continue 
                                                   
                        if file_type == PnmFileType.RECEIVE_MODULATION_ERROR_RATIO:                            
                            self.logger.debug(f'[{mac}][ch={channel_id}] - {file_type.name} Found')
                            dsRxMerAggregator.add(CmDsOfdmRxMer(data_stream))
                                                        
                        elif file_type == PnmFileType.OFDM_MODULATION_PROFILE:
                            self.logger.debug(f'[{mac}][ch={channel_id}] - {file_type.name} Found')
                            dsModProfileAggregator.add(CmDsOfdmModulationProfile(data_stream))
                            
                        elif file_type == PnmFileType.OFDM_FEC_SUMMARY:
                            self.logger.debug(f'[{mac}][ch={channel_id}] - {file_type.name} Found')
                            fecSummaryAggregator.add(CmDsOfdmFecSummary(data_stream))
                                              
                        else:
                            self.logger.warning(f'Unexpected PNM file: {file_type.name}, skipping')
                            continue
                            
                    except Exception as e:
                        self.logger.error(
                            f"[{mac}][ch={channel_id}] - PNM file parse failed: {e}")
                        continue
        
        self.logger.info(f'Starting Processing OFDM_1')
        stats = self._PROCESS_ofdm_profile_performance_1(dsRxMerAggregator,dsModProfileAggregator,fecSummaryAggregator)
           
        return stats        

    def _PROCESS_ofdm_profile_performance_1(
        self,
        rxMerAgg: DsRxMerAggregator,
        modProfAgg: DsModulationProfileAggregator,
        fecSumAgg: FecSummaryAggregator
    ) -> Dict[int, Dict[str, Any]]:
        """
        Process Data:
        -------------
        - Take the AVG MER and compute the per-subcarrier Shannon limit.
        - Compare that to the modulation-profile Shannon limits to get a delta.
        - For each channel, collect:
        • mer_limits: List[float] - Shannon limits from MER
        • fec_summary: Dict[str, int] - aggregated FEC counters between first & last captures
        • profiles: List of per-capture/per-profile dicts with deltas, etc.
        """
        stats: Dict[int, Dict[str, Any]] = {}

        for channel_id in rxMerAgg.get_channel_ids():
            self.logger.debug(f"Processing channel {channel_id}")
            
            # 1) Get Shannon limits (bit/hz) from average MER
            mam = rxMerAgg.getMinAvgMin(channel_id)
            mer_bit_limits: List[int] = Shannon.snr_to_limit(mam.avg_values)

            # 2) Fetch all capture times for this channel
            capture_times = rxMerAgg.get_capture_times(channel_id)
            if not capture_times:
                self.logger.warning(f"No captures for channel {channel_id}, skipping")
                continue
            self.logger.info(f"Channel: {channel_id} - CaptureTimeCount: {len(capture_times)}")
            
            # 3) Sum FEC counters between first and last capture By Channel and Profile
            start_time, end_time = capture_times[0], capture_times[-1]
            self.logger.info(f"Channel: {channel_id} - [CaptureStartTime: {start_time}::CaptureEndTime: {end_time}]")
            fec_summary_totals = fecSumAgg.get_summary_totals(channel_id, start_time, end_time)

            # 4) Build per-profile entries
            profile_entries: List[Dict[str, Any]] = []
            for ct in capture_times:
                self.logger.debug(f"Channel {channel_id} - Capture @ {ct}")

                # Run analysis for this channel and capture time
                analysis_result = modProfAgg.basic_analysis(channel_id, ct)

                # Extract profiles list from result
                if isinstance(analysis_result, dict):
                    profiles = analysis_result.get("profiles", [])
                else:
                    profiles = analysis_result

                if not isinstance(profiles, list):
                    raise TypeError(f"Expected profiles list, got {type(profiles).__name__!r}")

                for idx, profile in enumerate(profiles):
                    # Drill into the nested carrier_values dict
                    carrier_values = profile.get("carrier_values")
                    if not isinstance(carrier_values, dict):
                        self.logger.warning(f"Profile {idx} missing 'carrier_values'; skipping")
                        continue

                    # Get the shannon_limit list
                    values = carrier_values.get("shannon_limit")
                    if not values or not isinstance(values, list):
                        raise KeyError(f"Missing or invalid 'shannon_limit' for profile {idx} at {ct}")

                    # Compute per-subcarrier limits
                    profile_bit_limits = Shannon.snr_to_limit(values)

                    # Log a sample of the results
                    self.logger.debug(f"Profile {idx} limits (first 5): {profile_bit_limits[:5]}")
                    self.logger.debug(f"MER limits   (first 5): {mer_bit_limits[:5]}")

                    # Compute Capacity Delta for each subcarrier (+ delta (good) - delta (bad))
                    capacity_delta = [m - p for p, m in zip(profile_bit_limits, mer_bit_limits)]
                    profile_entries.append({
                        "capture_time":   ct,
                        "profile_index":  idx,
                        "profile_limits": profile_bit_limits,
                        "capacity_delta": capacity_delta,
                    })

            # 5) Assemble channel stats
            stats[channel_id] = {
                "avg_mer": mam.avg_values,
                "mer_shannon_limits": mer_bit_limits,
                "fec_summary_total": fec_summary_totals,
                "profiles": profile_entries,
            }

        return stats

    def _analyze_rxmer_heat_map(self) -> Dict[int, Dict[str, Any]]:
        """
        Build a heat-map data cube of subcarrier MER vs. time for each channel.

        Returns:
            {
              channel_id: {
                "timestamps": [t0, t1, …],          # one per capture iteration
                "subcarriers": [f0, f1, …],         # frequency bins or subcarrier indices
                "values": [                         # list of magnitude arrays
                  [m0_0, m0_1, …],                   # capture 0
                  [m1_0, m1_1, …],                   # capture 1
                  …
                ]
              },
              …
            }
        """
        nested = self.collection.get()
        heatmap_data: Dict[int, Dict[str, Any]] = {}

        for mac, channel_map in nested.items():
            for channel_id, entries in channel_map.items():
                timestamps: List[int] = []
                magnitudes: List[List[float]] = []
                freq_bins: List[float] = []

                for entry in entries:
                    data_stream = entry.get("data")
                    if data_stream is None:
                        continue
                    try:
                        # 1) parse bytes → header + payload
                        dorm = CmDsOfdmRxMer(data_stream)
                        hdr = dorm.to_dict()
                        
                        # 2) run basic_analysis to extract carrier_values
                        analysis = Analysis.basic_analysis_rxmer(hdr)
                        mags = analysis.get("magnitude") \
                            or analysis.get("carrier_values", {}).get("magnitude", [])
                        freqs = analysis.get("frequency") \
                            or analysis.get("carrier_values", {}).get("frequency", [])
                        if not mags:
                            self.logger.warning(f"[{mac}][ch={channel_id}] empty magnitude, skipping")
                            continue

                        # 3) capture the time & data
                        timestamps.append(hdr.get("pnm_header", {}).get("capture_time", 0))
                        magnitudes.append(mags)
                        # only set freq_bins once per channel
                        if not freq_bins and freqs:
                            freq_bins = freqs

                    except Exception as e:
                        self.logger.error(f"[{mac}][ch={channel_id}] RxMER heatmap parse failed: {e}")
                        continue

                if magnitudes:
                    heatmap_data[channel_id] = {
                        "timestamps": timestamps,
                        "subcarriers": freq_bins if freq_bins else list(range(len(magnitudes[0]))),
                        "values": magnitudes
                    }

        return heatmap_data

