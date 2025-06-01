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
                    • channel_center_frequency (int)
                    • frequency_span (int)
                    • total_bins (int)         # bins in the first group
                    • bin_spacing (int)
                    • resolution_bandwidth (int)
                - total_samples (int): sum of bins across all groups
                - frequency (List[int]): concatenated frequency values
                  for all samples
                - amplitude (List[float]): concatenated amplitude values
                  (in dBmV) for all samples
        """
        offset = 0

        # Initialize accumulators
        all_freqs: List[int] = []
        all_amplitudes: List[float] = []
        total_bins_count = 0
        parsed_header: Dict[str, Any] = {}

        spectrum_group_idx = 1
        amp_data_header_len = 20  # 5 × 4-byte fields
        amp_data_bytes_len = 2    # each amplitude is a 16-bit (2-byte) signed int

        # Iterate over each spectrum‐group in the byte_stream
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
                    f"[WARN] Spec‐Group {spectrum_group_idx} incomplete "
                    f"(expected {amp_len} bytes), skipping."
                )
                break

            # Extract amplitude bytes for this group
            amp_bytes = byte_stream[offset + amp_data_header_len : group_end]
            try:
                amplitudes = struct.unpack(f">{num_bins}h", amp_bytes)
            except struct.error as e:
                self.logger.warning(f"Failed to unpack amplitudes at offset {offset}: {e}")
                break

            # Convert raw ints to dBmV
            amplitudes_dbmv: List[float] = [a / 100.0 for a in amplitudes]

            # Calculate frequency list
            freq_start: int = ch_center_freq - (freq_span // 2)
            freqs: List[int] = [freq_start + i * bin_spacing for i in range(num_bins)]

            # Accumulate across all groups
            all_freqs.extend(freqs)
            all_amplitudes.extend(amplitudes_dbmv)
            total_bins_count += num_bins

            # Save first‐group header metadata
            if spectrum_group_idx == 1:
                parsed_header = {
                    "channel_center_frequency": ch_center_freq,
                    "frequency_span": freq_span,
                    "total_bins": num_bins,
                    "bin_spacing": bin_spacing,
                    "resolution_bandwidth": res_bw,
                }

            self.logger.debug(f"[SPEC‐GROUP {spectrum_group_idx}] Parsed {num_bins} bins")
            offset = group_end
            spectrum_group_idx += 1

        if total_bins_count == 0:
            self.logger.warning("No spectrum groups parsed; returning empty data.")
        else:
            self.logger.info(
                f"Parsed total of {total_bins_count} bins across {spectrum_group_idx - 1} groups."
            )

        return {
            "spectrum_config": parsed_header,
            "total_samples": total_bins_count,
            "frequency": all_freqs,
            "amplitude": all_amplitudes,
        }

    def to_dict(self) -> Dict[str, List[float]]:
        """
        Export the parsed frequency and amplitude data.

        Returns:
            Dict[str, List[float]]: Parsed results with 'frequency' and 'amplitude' keys.
            
        {
            "spectrum_config": {
                "channel_center_frequency": int,
                "frequency_span": int,
                "total_bins": int,
                "bin_spacing": int,
                "resolution_bandwidth": int
            },
            "total_samples": int,
            "frequency": [int],
            "amplitude":[float]
        }            
            
        """
        return self.data
