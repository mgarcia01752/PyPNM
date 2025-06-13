# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import logging
from struct import unpack, calcsize
from typing import Optional, List, Dict
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader

class CmSpectrumAnalysis(PnmHeader):
    """
    Parses DOCSIS PNM Spectrum Analysis binary data.

    Extracts channel info, metadata, and amplitude bin values expressed
    in hundredths of a dB (referenced to 0 dBmV). Supports segmented amplitude
    data with possible incomplete final segment.
    """

    AMPLITUDE_BIN_SIZE = 2

    def __init__(self, binary_data: bytes):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.channel_id: Optional[int] = None
        self.mac_address: Optional[str] = None
        self.first_segment_center_frequency: Optional[float] = None
        self.last_segment_center_frequency: Optional[float] = None
        self.segment_frequency_span: Optional[float] = None
        self.num_bins_per_segment: Optional[int] = None
        self.equivalent_noise_bandwidth: Optional[int] = None
        self.window_function: Optional[int] = None
        self.spectrum_analysis_data_length: Optional[int] = None
        self.spectrum_analysis_data: Optional[bytes] = None
        self.bin_frequency_spacing: Optional[float] = None
        self.amplitude_bin_segments_float: List[List[float]] = []
        self.num_of_bin_segments = 0

        self._process_spectrum_analysis_data()

    def _process_spectrum_analysis_data(self) -> None:
        """
        Unpacks the spectrum analysis header and extracts metadata and
        the raw amplitude data stream.
        """
        if self.get_pnm_file_type() != PnmFileType.SPECTRUM_ANALYSIS:
            cann = PnmFileType.SPECTRUM_ANALYSIS.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
        
        spectrum_analysis_format = '>B6sIIIHHHI'
        spectrum_analysis_size = calcsize(spectrum_analysis_format)
        unpacked_data = unpack(spectrum_analysis_format, self.pnm_data[:spectrum_analysis_size])

        self.channel_id = unpacked_data[0]
        self.mac_address = unpacked_data[1].hex(':')
        self.first_segment_center_frequency = unpacked_data[2]
        self.last_segment_center_frequency = unpacked_data[3]
        self.segment_frequency_span = unpacked_data[4]
        self.num_bins_per_segment = unpacked_data[5]
        self.equivalent_noise_bandwidth = unpacked_data[6]
        self.window_function = unpacked_data[7]
        self.spectrum_analysis_data_length = unpacked_data[8]
        self.spectrum_analysis_data = self.pnm_data[spectrum_analysis_size:]

        if self.num_bins_per_segment:
            self.bin_frequency_spacing = self.segment_frequency_span / self.num_bins_per_segment

        self._process_spectrum_analysis_amplitude_data()

    def _process_spectrum_analysis_amplitude_data(self) -> None:
        """
        Parses the raw amplitude data into segments.
        Each segment contains `num_bins_per_segment` values (except possibly the last one).

        Values are 16-bit signed integers in hundredths of a dB.
        """
        if not self.spectrum_analysis_data or self.num_bins_per_segment is None:
            self.logger.warning("Amplitude data or bin count not available.")
            return

        try:
            segment_size_bytes = self.num_bins_per_segment * self.AMPLITUDE_BIN_SIZE
            total_data_len = len(self.spectrum_analysis_data)
            self.logger.debug(f'Total Data Length: {total_data_len} bytes')

            for offset in range(0, total_data_len, segment_size_bytes):
                segment_bytes = self.spectrum_analysis_data[offset:offset + segment_size_bytes]
                actual_bins = len(segment_bytes) // self.AMPLITUDE_BIN_SIZE

                if actual_bins == 0:
                    self.logger.warning(f"Empty segment encountered at offset {offset}, skipping.")
                    continue

                if actual_bins < self.num_bins_per_segment:
                    self.logger.warning(f"Incomplete segment encountered at offset {offset} with only {actual_bins} bins.")

                format_string = f'>{actual_bins}h'
                self.logger.debug(f'Unpack format: {format_string} for {actual_bins} bins')

                raw_bins = unpack(format_string, segment_bytes)
                amplitude_values = [val / 100.0 for val in raw_bins]
                self.amplitude_bin_segments_float.append(amplitude_values)
                self.num_of_bin_segments += 1

        except Exception as e:
            self.logger.error(f"Failed to unpack spectrum amplitude data: {e}")
            self.amplitude_bin_segments_float = []

    def get_spectrum_analysis(self) -> Optional[Dict[str, Optional[float]]]:
        """
        Returns the parsed spectrum metadata as a dictionary.
        """
        return {
            'Channel ID': self.channel_id,
            'MAC Address': self.mac_address,
            'First Segment Center Frequency': self.first_segment_center_frequency,
            'Last Segment Center Frequency': self.last_segment_center_frequency,
            'Segment Frequency Span': self.segment_frequency_span,
            'Number of Bins Per Segment': self.num_bins_per_segment,
            'Equivalent Noise Bandwidth': self.equivalent_noise_bandwidth,
            'Window Function': self.window_function,
            'Bin Frequency Spacing': self.bin_frequency_spacing,
            'Spectrum Analysis Data Length': self.spectrum_analysis_data_length,
            'Spectrum Analysis Data': self.spectrum_analysis_data.hex() if self.spectrum_analysis_data else None,
            'Number of Bin Segments': self.num_bins_per_segment,
            'Amplitude Bin Segments Float': self.amplitude_bin_segments_float}

    def to_dict(self) -> Optional[Dict[str, Optional[float]]]:
        """
        Returns the spectrum analysis data as a dictionary.

        This method calls `get_spectrum_analysis()` and returns its result.
        The returned dictionary typically contains frequency and amplitude data,
        or `None` if the analysis has not been performed or data is unavailable.

        Returns:
            Optional[Dict[str, Optional[float]]]: A dictionary of spectrum analysis data,
            or `None` if no data is available.
        """
        return self.get_spectrum_analysis()

    def to_json(self) -> str:
        """
        Returns the spectrum metadata as a JSON-formatted string
        with snake_case keys.
        """
        data = self.get_spectrum_analysis()

        normalized_data = {
            key.lower().replace(' ', '_'): value
            for key, value in data.items()
        }

        return json.dumps(normalized_data, indent=4)
