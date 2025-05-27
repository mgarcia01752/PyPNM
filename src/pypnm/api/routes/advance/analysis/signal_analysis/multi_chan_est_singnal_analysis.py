# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from enum import Enum
import logging
from typing import Any, Dict, List, Optional

from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.ifft import IfftEchoDetector
from pypnm.api.routes.advance.analysis.signal_analysis.detection.echo.phase_slope import PhaseSlopeEchoDetector
from pypnm.api.routes.advance.analysis.signal_analysis.detection.lte.phase_slope_lte_detection import GroupDelayAnomalyDetector
from pypnm.api.routes.advance.analysis.signal_analysis.group_delay_calculator import GroupDelayCalculator
from pypnm.api.routes.advance.common.pnm_collection import PnmCollection
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.pnm.lib.min_avg_max import MinAvgMax
from pypnm.pnm.process.CmDsOfdmChanEstimateCoef import CmDsOfdmChanEstimateCoef

class MultiChanEstimationAnalysisType(Enum):
    """
    Signal analysis routines for Multi-Channel-Estimation data.
    """
    MIN_AVG_MAX                 = 0
    GROUP_DELAY                 = 1
    LTE_DETECTION_PHASE_SLOPE   = 2  
    ECHO_DETECTION_PHASE_SLOPE  = 3
    ECHO_DETECTION_IFFT         = 4


class MultiChanEstimationSignalAnalysis:
    """
    Performs signal-quality analyses on grouped Multi-Channel-Estimation captures.
    """

    def __init__(self,
                 collection: PnmCollection,
                 analysis_type: MultiChanEstimationAnalysisType
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
        if self.analysis_type == MultiChanEstimationAnalysisType.MIN_AVG_MAX:
            return self._analyze_min_avg_max()
        elif self.analysis_type == MultiChanEstimationAnalysisType.GROUP_DELAY:
            return self._analyze_group_delay()
        elif self.analysis_type == MultiChanEstimationAnalysisType.LTE_DETECTION_PHASE_SLOPE:
            return self._analyze_lte_detection()
        elif self.analysis_type == MultiChanEstimationAnalysisType.ECHO_DETECTION_PHASE_SLOPE:
            return self._analyze_echo_detection_phase_slope()
        elif self.analysis_type == MultiChanEstimationAnalysisType.ECHO_DETECTION_IFFT:
            return self._analyze_echo_detection_ifft()        
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
        Aggregate per-capture Channel Estimation magnitude series by channel,
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
        # Prepare storage for magnitudes and frequencies per channel
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
                        # Parse ChannelEstimation sample and extract analysis
                        ocef = CmDsOfdmChanEstimateCoef(data_stream)
                        measurement = ocef.to_dict()
                        result = Analysis.basic_analysis_ds_chan_est(measurement)

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
                            f"[{mac}][ch={channel_id}] ChannelEstimation parse failed: {e}"
                        )
                        continue

                    # Collect magnitudes
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

    def _analyze_group_delay(self) -> Dict[int, Dict[str, List[float]]]:
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
                'dataset_info': self.dataset_info(),
                'freqs': freqs_list,
                'H_raw': H_raw_list,
                'H_avg': H_avg_list,
                'group_delay_full': {
                    'freqs': f_full.tolist(),
                    'tau_g': tau_full.tolist()
                },
                'snapshot_group_delay': tau_snap.tolist(),
                'median_group_delay': {
                    'freqs': f_med.tolist(),
                    'tau_med': tau_med.tolist()
                }
            }
        """
        # Prepare storage for magnitudes and frequencies per channel
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
                        # Parse ChannelEstimation sample and extract analysis
                        ocef = CmDsOfdmChanEstimateCoef(data_stream)
                        measurement = ocef.to_dict()
                        result = Analysis.basic_analysis_ds_chan_est(measurement)

                        # Extract magnitude list
                        complex = result.get("complex")
                        if not isinstance(complex, list):
                            complex = result.get("carrier_values", {}).get("complex", [])

                        # Extract frequency list
                        freqs = result.get("frequency")
                        if not isinstance(freqs, list):
                            freqs = result.get("carrier_values", {}).get("frequency", [])

                        if not complex:
                            self.logger.warning(
                                f"[{mac}][ch={channel_id}] No valid complex, skipping"
                            )
                            continue

                    except Exception as e:
                        self.logger.error(
                            f"[{mac}][ch={channel_id}] ChannelEstimation parse failed: {e}"
                        )
                        continue

                    # Collect magnitudes
                    channel_amplitudes.setdefault(channel_id, []).append(complex)
                    # Store frequency bins once
                    if channel_id not in channel_frequencies and freqs:
                        channel_frequencies[channel_id] = freqs

        # Compute stats per channel and attach frequencies
        stats: Dict[int, Dict[str, List[float]]] = {}
        for channel_id, complex_lists in channel_amplitudes.items():
            frequencies = channel_frequencies.get(channel_id, [])
            try:
                calc = GroupDelayCalculator(complex_lists, frequencies)
                channel_stat = calc.to_dict()
                stats[channel_id] = channel_stat
            except ValueError as ve:
                self.logger.error(
                    f"[ch={channel_id}] Group Delay computation failed: {ve}"
                )

        return stats

    def _analyze_lte_detection(self) -> Any:
        channel_complex: Dict[int, List[List[float]]] = {}
        channel_frequencies: Dict[int, List[float]] = {}
        
        nested = self.collection.get()
        for mac, channel_map in nested.items():
            for channel_id, entries in channel_map.items():
                for entry in entries:
                    data_stream = entry.get("data")
                    if data_stream is None:
                        continue
                    try:
                        # Parse ChannelEstimation sample and extract analysis
                        ocef = CmDsOfdmChanEstimateCoef(data_stream)
                        measurement = ocef.to_dict()
                        result = Analysis.basic_analysis_ds_chan_est(measurement)
                        
                        # Extract complex list
                        complex = result.get("complex")
                        if not isinstance(complex, list):
                            complex = result.get("carrier_values", {}).get("complex", [])

                        # Extract frequency list
                        freqs = result.get("frequency")
                        if not isinstance(freqs, list):
                            freqs = result.get("carrier_values", {}).get("frequency", [])

                        if not complex:
                            self.logger.warning(
                                f"[{mac}][ch={channel_id}] No valid complex, skipping"
                            )
                            continue
                        
                    except Exception as e:
                        self.logger.error(
                            f"[{mac}][ch={channel_id}] ChannelEstimation parse failed: {e}"
                        )
                        continue

                    # Collect magnitudes
                    channel_complex.setdefault(channel_id, []).append(complex)
                    
                    # Store frequency bins once
                    if channel_id not in channel_frequencies and freqs:
                        channel_frequencies[channel_id] = freqs

        # Compute stats per channel and attach frequencies
        stats: Dict[int, Dict[str, List[float]]] = {}
        threshold  = 1e-9               # 1 ns ripple threshold
        bin_widths = [1e6, 5e5, 1e5]    # 1 MHz → 500 kHz → 100 kHz bins
        for channel_id, complex_lists in channel_complex.items():
            try:
                frequencies = channel_frequencies.get(channel_id, [])          
                calc = GroupDelayAnomalyDetector(complex_lists, frequencies)
                channel_stat = calc.run(bin_widths=bin_widths, threshold=threshold)
                stats[channel_id] = channel_stat
            except ValueError as ve:
                self.logger.error(
                    f"[ch={channel_id}] PhaseSlopeEchoDetector computation failed: {ve}"
                )

        return stats 

    def _analyze_echo_detection_phase_slope(self) -> Dict[int, Dict[str, Any]]:
        channel_complex: Dict[int, List[List[float]]] = {}
        channel_frequencies: Dict[int, List[float]] = {}
        
        nested = self.collection.get()
        for mac, channel_map in nested.items():
            for channel_id, entries in channel_map.items():
                for entry in entries:
                    data_stream = entry.get("data")
                    if data_stream is None:
                        continue
                    try:
                        # Parse ChannelEstimation sample and extract analysis
                        ocef = CmDsOfdmChanEstimateCoef(data_stream)
                        measurement = ocef.to_dict()
                        result = Analysis.basic_analysis_ds_chan_est(measurement)
                        
                        # Extract complex list
                        complex = result.get("complex")
                        if not isinstance(complex, list):
                            complex = result.get("carrier_values", {}).get("complex", [])

                        # Extract frequency list
                        freqs = result.get("frequency")
                        if not isinstance(freqs, list):
                            freqs = result.get("carrier_values", {}).get("frequency", [])

                        if not complex:
                            self.logger.warning(
                                f"[{mac}][ch={channel_id}] No valid complex, skipping"
                            )
                            continue
                        
                    except Exception as e:
                        self.logger.error(
                            f"[{mac}][ch={channel_id}] ChannelEstimation parse failed: {e}"
                        )
                        continue

                    # Collect magnitudes
                    channel_complex.setdefault(channel_id, []).append(complex)
                    
                    # Store frequency bins once
                    if channel_id not in channel_frequencies and freqs:
                        channel_frequencies[channel_id] = freqs

        # Compute stats per channel and attach frequencies
        stats: Dict[int, Dict[str, List[float]]] = {}
        for channel_id, complex_lists in channel_complex.items():
            try:
                frequencies = channel_frequencies.get(channel_id, [])          
                calc = PhaseSlopeEchoDetector(complex_lists,frequencies)
                channel_stat = calc.to_dict()
                stats[channel_id] = channel_stat
            except ValueError as ve:
                self.logger.error(
                    f"[ch={channel_id}] PhaseSlopeEchoDetector computation failed: {ve}"
                )

        return stats 

    def _analyze_echo_detection_ifft(self) -> Dict[int, Dict[str, Any]]:
        channel_complex: Dict[int, List[List[float]]] = {}
        channel_frequencies: Dict[int, List[float]] = {}
        occ_chan_bw:Dict[int,int] = {}
        
        nested = self.collection.get()
        for mac, channel_map in nested.items():
            for channel_id, entries in channel_map.items():
                for entry in entries:
                    data_stream = entry.get("data")
                    if data_stream is None:
                        continue
                    try:
                        # Parse ChannelEstimation sample and extract analysis
                        ocef = CmDsOfdmChanEstimateCoef(data_stream)
                        measurement = ocef.to_dict()
                        result = Analysis.basic_analysis_ds_chan_est(measurement)

                        # Get OCB to calcualte sample-rate for IFFT
                        occupied_channel_bandwidth = result.get("carrier_values", {}).get("occupied_channel_bandwidth", 0)
                        if occupied_channel_bandwidth == 0:
                           raise ValueError(f"Occupied Channel Bandwidth can not be ({occupied_channel_bandwidth}Hz)") 
                        
                        # Extract magnitude list
                        complex = result.get("complex")
                        if not isinstance(complex, list):
                            complex = result.get("carrier_values", {}).get("complex", [])

                        # Extract frequency list
                        freqs = result.get("frequency")
                        if not isinstance(freqs, list):
                            freqs = result.get("carrier_values", {}).get("frequency", [])

                        if not complex:
                            self.logger.warning(
                                f"[{mac}][ch={channel_id}] No valid complex, skipping"
                            )
                            continue
                        
                    except Exception as e:
                        self.logger.error(
                            f"[{mac}][ch={channel_id}] ChannelEstimation parse failed: {e}"
                        )
                        continue

                    # Collect magnitudes
                    channel_complex.setdefault(channel_id, []).append(complex)
                    
                    # Store frequency bins once
                    if channel_id not in channel_frequencies and freqs:
                        channel_frequencies[channel_id] = freqs
                        occ_chan_bw[channel_id] = occupied_channel_bandwidth

        # Compute stats per channel and attach frequencies
        stats: Dict[int, Dict[str, List[float]]] = {}
        for channel_id, complex_lists in channel_complex.items():
            try:          
                calc = IfftEchoDetector(complex_lists, 
                                        sample_rate=float(occ_chan_bw.get(channel_id,0)))
                channel_stat = calc.to_dict()
                stats[channel_id] = channel_stat
            except ValueError as ve:
                self.logger.error(
                    f"[ch={channel_id}] IfftEchoDetector computation failed: {ve}"
                )

        return stats        
         