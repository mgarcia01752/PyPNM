# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import logging
from struct import calcsize, unpack
from typing import Optional, List
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader

class CmDsHist(PnmHeader):
    """
    Represents the Downstream Histogram data collected from a Cable Modem (CM).

    This histogram provides a measurement of nonlinear effects in the downstream channel,
    such as amplifier compression and laser clipping. The CM captures a time-domain
    signal snapshot and sorts the values into bins (buckets) based on signal level,
    allowing visualization of distortions. This helps technicians identify signal issues.

    The histogram includes:
    - MAC address of the CM
    - Symmetry flag (1 byte, additional signal characterization)
    - Dwell Count: Number of samples considered per bin
    - Hit Count: Number of samples that actually fall into each bin
    
    The class extracts and exposes this data from binary format for further analysis.
    """

    def __init__(self, binary_data: bytes):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.mac_address: Optional[str] = None
        self.symmetry: Optional[int] = None
        self.dwell_count_values_length: Optional[int] = None
        self.dwell_count_values: Optional[List[int]] = None
        self.hit_count_values_length: Optional[int] = None
        self.hit_count_values: Optional[List[int]] = None

        self._process_cm_ds_hist()

    def _process_cm_ds_hist(self) -> None:
        
        if self.get_pnm_file_type() != PnmFileType.DOWNSTREAM_HISTOGRAM:
            cann = PnmFileType.DOWNSTREAM_HISTOGRAM.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
                
        mac_sym_format = '>6sB'
        mac_sym_header_size = calcsize(mac_sym_format)

        try:
            unpacked = unpack(mac_sym_format, self.pnm_data[:mac_sym_header_size])
            self.mac_address = ':'.join(f'{b:02X}' for b in unpacked[0])
            self.symmetry = unpacked[1]
        except Exception as e:
            raise ValueError(f"Failed to unpack header: {e}")

        offset = mac_sym_header_size

        # Dwell Count Values
        self.dwell_count_values_length = int.from_bytes(self.pnm_data[offset:offset + 4], byteorder='big')
        offset += 4
        count = self.dwell_count_values_length // 4
        self.dwell_count_values = [int.from_bytes(self.pnm_data[offset + i*4:offset + (i+1)*4], 'big') for i in range(count)]
        offset += self.dwell_count_values_length

        # Hit Count Values
        self.hit_count_values_length = int.from_bytes(self.pnm_data[offset:offset + 4], byteorder='big')
        offset += 4
        count = self.hit_count_values_length // 4
        self.hit_count_values = [int.from_bytes(self.pnm_data[offset + i*4:offset + (i+1)*4], 'big') for i in range(count)]

    def get_cm_ds_hist(self) -> Optional[dict]:
        
        data = self.getPnmHeader(header_only=True)
        data.update({
            'mac_address': self.mac_address,
            'symmetry': self.symmetry,
            'dwell_count_values_length': self.dwell_count_values_length,
            'dwell_count_values': self.dwell_count_values,
            'hit_count_values_length': self.hit_count_values_length,
            'hit_count_values': self.hit_count_values
        })

        return data
    
    def summarize_histogram(self) -> dict:
        
        data = self.getPnmHeader(header_only=True)
        
        data.update( {
            "mac_address": self.mac_address,
            "symmetry": self.symmetry,
            "dwell_count": self.dwell_count_values[0] if self.dwell_count_values else None,
            "hit_counts": self.hit_count_values
        })

        return data
    
    def to_dict(self) -> dict:
        """
        Returns a dictionary containing the summarized histogram data.

        Returns:
            dict: Summary of histogram measurement results.
        """
        return self.summarize_histogram()

    def to_json(self) -> str:
        """
        Returns a JSON-formatted string of the summarized histogram data.

        Returns:
            str: JSON representation of the histogram summary.
        """
        return json.dumps(self.to_dict(), indent=4)
