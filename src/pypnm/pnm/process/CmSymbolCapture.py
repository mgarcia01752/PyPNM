
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader
from struct import calcsize, unpack
from typing import Optional, List, Tuple


class CmSymbolCapture(PnmHeader):
    def __init__(self, binary_data: bytes):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Additional attributes specific to CmSymbolCapture
        self.channel_id: Optional[int] = None
        self.mac_address: Optional[str] = None
        self.subcarrier_zero_frequency: Optional[int] = None
        self.sample_rate: Optional[int] = None
        self.fft_size: Optional[int] = None
        self.trigger_group_id: Optional[int] = None
        self.transaction_id: Optional[int] = None
        self.capture_data_length: Optional[int] = None
        self.capture_data: Optional[bytes] = None

    def process_cm_symbol_capture(self) -> None:
        if self.get_pnm_file_type() != PnmFileType.SYMBOL_CAPTURE:
            cann = PnmFileType.SYMBOL_CAPTURE.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
 
        # Extract CmSymbolCapture fields using struct.unpack
        cm_symbol_capture_format = '<B6sII2HI'
        cm_symbol_capture_size = unpack(cm_symbol_capture_format, 
                                        self.pnm_data[:calcsize(cm_symbol_capture_format)])

        # Assign values to attributes
        self.channel_id = cm_symbol_capture_size[0]
        self.mac_address = cm_symbol_capture_size[1].hex(':')
        self.subcarrier_zero_frequency = cm_symbol_capture_size[2]
        self.sample_rate = cm_symbol_capture_size[3]
        self.fft_size = cm_symbol_capture_size[4]
        self.trigger_group_id = cm_symbol_capture_size[5]
        self.transaction_id = cm_symbol_capture_size[6]
        self.capture_data_length = cm_symbol_capture_size[7]
        self.capture_data = self.pnm_data[calcsize(cm_symbol_capture_format):]

    def process_capture_data(self, sm_n_format: Tuple[int, int] = (3, 12)) -> Optional[List[Tuple[float, float]]]:
        """
        Process Capture Data.
        Returns a list of tuples containing the complex data (I, Q) for each sample.
        """
        capture_data = FixedPointDecoder.decode_complex_data(self.capture_data, sm_n_format)
        return capture_data

    def get_cm_symbol_capture(self) -> Optional[dict]:
        return {
            'DS Channel Id': self.channel_id,
            'CM MAC Address': self.mac_address,
            'Subcarrier Zero Frequency': self.subcarrier_zero_frequency,
            'Sample Rate': self.sample_rate,
            'FFT Size': self.fft_size,
            'Trigger Group Id': self.trigger_group_id,
            'Transaction ID': self.transaction_id,
            'Capture Data Length': self.capture_data_length,
            'Capture Data': self.capture_data.hex()
        }
