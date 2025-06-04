# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
import struct
from typing import Any, Dict, List

class CmSpectrumAnalysisSnmp:
    """
    DOCSIS SNMP Spectrum Analysis AmplitudeData parser.

    This class decodes the `docsIf3CmSpectrumAnalysisMeasAmplitudeData` byte stream returned by SNMP
    into a usable structure containing frequency and amplitude pairs, according to the
    DOCSIS AmplitudeData textual convention.
    """

    def __init__(self, byte_stream: bytes):
        """
        Initialize the class by parsing the byte stream into frequency and amplitude data.

        Args:
            byte_stream (bytes): Raw bytes as returned by SNMP for the amplitude data.
        """
        self.logger = logging.getLogger(__name__)
        self.data = self._parse_amplitude_data(byte_stream)

    def _parse_amplitude_data(self, byte_stream: bytes) -> Dict[str, Any]:
        """
        Parses amplitude data based on the SNMP AmplitudeData textual convention.

        Structure of each spectrum group in the byte stream:
            - 4 bytes: Channel Center Frequency (Hz)
            - 4 bytes: Frequency Span (Hz)
            - 4 bytes: Number of Bins
            - 4 bytes: Bin Spacing (Hz)
            - 4 bytes: Resolution Bandwidth (Hz)
            - N x 2 bytes: Amplitudes in 0.01 dB units (signed 16-bit integers)

        Frequency bins are calculated from:
            freq_start = ch_center_freq - (freq_span // 2)
            freqs = [freq_start + i * bin_spacing for i in range(num_bins)]

        Amplitudes are 16-bit signed ints, scaled by 1/100 to dBmV.

        Args:
            byte_stream (bytes): The raw SNMP byte stream.

        Returns:
            Dict[str, Any]: Parsed data with:
                - header: metadata from the first spectrum group
                - total_samples: sum of bins across all groups
                - frequency: list of all frequency values
                - amplitude: list of all amplitude values (in dBmV)
                - amplitude_bytes: all raw amplitude bytes as one hex string
        """
        offset = 0

        all_freqs: List[int] = []
        all_amplitudes: List[float] = []
        all_amplitudes_bytes: List[bytes] = []

        total_bins_count = 0
        parsed_header: Dict[str, Any] = {}

        spectrum_group_idx = 1
        amp_data_header_len = 20  # 5 × 4-byte fields
        amp_data_bytes_len = 2    # each amplitude is a 16-bit (2-byte) signed int

        while offset + amp_data_header_len <= len(byte_stream):
            header = byte_stream[offset : offset + amp_data_header_len]
            try:
                ch_center_freq, freq_span, num_bins, bin_spacing, res_bw = struct.unpack(">5I", header)
            except struct.error as e:
                self.logger.warning(f"Failed to unpack header at offset {offset}: {e}")
                break

            amp_len = num_bins * amp_data_bytes_len
            group_end = offset + amp_data_header_len + amp_len
            if group_end > len(byte_stream):
                self.logger.debug(
                    f"[WARN] Spec-Group {spectrum_group_idx} incomplete "
                    f"(expected {amp_len} bytes), skipping."
                )
                break

            amp_bytes = byte_stream[offset + amp_data_header_len : group_end]
            try:
                amplitudes = struct.unpack(f">{num_bins}h", amp_bytes)
            except struct.error as e:
                self.logger.warning(f"Failed to unpack amplitudes at offset {offset}: {e}")
                break

            amplitudes_dbmv: List[float] = [a / 100.0 for a in amplitudes]
            freq_start: int = ch_center_freq - (freq_span // 2)
            freqs: List[int] = [freq_start + i * bin_spacing for i in range(num_bins)]

            all_freqs.extend(freqs)
            all_amplitudes.extend(amplitudes_dbmv)
            all_amplitudes_bytes.append(amp_bytes)

            total_bins_count += num_bins

            if spectrum_group_idx == 1:
                parsed_header = {
                    "start_frequency": 0,
                    "end_frequency": 0,
                    "frequency_span": 0,
                    "total_bins": num_bins,
                    "bin_spacing": bin_spacing,
                    "resolution_bandwidth": res_bw,
                }

            self.logger.debug(f"[SPEC-GROUP {spectrum_group_idx}] Parsed {num_bins} bins")
            offset = group_end
            spectrum_group_idx += 1

        if total_bins_count == 0:
            self.logger.warning("No spectrum groups parsed; returning empty data.")
        else:
            self.logger.info(
                f"Parsed total of {total_bins_count} bins across {spectrum_group_idx - 1} groups."
            )

        amplitude_bytes_hex = b"".join(all_amplitudes_bytes).hex()

        parsed_header.update({
            "start_frequency": all_freqs[0],
            "end_frequency": all_freqs[-1],
            "frequency_span": (all_freqs[-1] - all_freqs[0]),
        })
        
        return {
            "spectrum_config": parsed_header,
            "total_samples": total_bins_count,
            "frequency": all_freqs,
            "amplitude": all_amplitudes,
            "amplitude_bytes": amplitude_bytes_hex,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Export the parsed frequency and amplitude data.

        Returns:
            Dict[str, Any]: Parsed results with metadata, frequencies, amplitudes, and raw bytes.
        """
        return self.data
