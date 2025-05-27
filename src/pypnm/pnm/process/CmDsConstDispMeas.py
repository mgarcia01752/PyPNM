# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from struct import unpack, calcsize
from typing import List, Optional, Tuple, Dict
import json

from pypnm.pnm.data_type.DsOfdmModulationType import DsOfdmModulationType
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


class CmDsConstDispMeas(PnmHeader):
    """
    Parses and processes Downstream Constellation Display Measurement (CmDsConstDispMeas) data.
    Inherits from PnmHeader to handle binary SNMP-based CM measurement data.
    """    
    def __init__(self, binary_data: bytes):
        """
        Initializes the CmDsConstDispMeas instance and parses the binary payload.

        Args:
            binary_data (bytes): Raw binary data from SNMP or TFTP source.
        """
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.channel_id: Optional[int] = None
        self.mac_address: Optional[str] = None
        self.subcarrier_zero_frequency: Optional[int] = None
        self.actual_modulation_order: Optional[int] = None
        self.num_sample_symbols: Optional[int] = None
        self.subcarrier_spacing: Optional[int] = None
        self.display_data_length: Optional[int] = None
        self.constellation_display_data: Optional[bytes] = None
        self.parsed_constellation_data: Optional[List[Tuple[float, float]]] = None

        self._process_const_disp_meas()

    def _process_const_disp_meas(self) -> None:
        """
        Parses the binary payload for constellation display measurement.

        Expected binary format:
            - 1 byte: channel ID
            - 6 bytes: CM MAC address
            - 4 bytes: subcarrier zero frequency (Hz)
            - 2 bytes: actual modulation order
            - 2 bytes: number of sample symbols
            - 1 byte: subcarrier spacing (kHz)
            - 4 bytes: display data length (bytes)
            - N bytes: constellation display data (complex samples)
        """
        
        if self.get_pnm_file_type() != PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY:
            cann = PnmFileType.DOWNSTREAM_CONSTELLATION_DISPLAY.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not RxMER file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
        
        const_disp_meas_format = '>B6sIHHBI'
        const_disp_meas_size = calcsize(const_disp_meas_format)
        unpacked_data = unpack(const_disp_meas_format, self.pnm_data[:const_disp_meas_size])

        self.channel_id = unpacked_data[0]
        self.mac_address = unpacked_data[1].hex(':')
        self.subcarrier_zero_frequency = unpacked_data[2]
        self.actual_modulation_order = unpacked_data[3]
        self.num_sample_symbols = unpacked_data[4]
        self.subcarrier_spacing = unpacked_data[5]
        self.display_data_length = unpacked_data[6]
        self.constellation_display_data = self.pnm_data[const_disp_meas_size:]

        self.parsed_constellation_data = self._process_constellation_display_data()

    def _process_constellation_display_data(self) -> List[List[float]]:
        """
        Decodes the constellation display binary data into a list of [i, q] float pairs.

        This reduced format is optimized for REST payload transmission.

        Returns:
            List of [i, q] float pairs.
        """
        offset = 0
        raw = self.constellation_display_data
        decode_list = []

        while offset + 4 <= len(raw):
            # Assuming this returns a list of complex numbers
            decoded = FixedPointDecoder.decode_complex_data(raw[offset:offset + 4], (2, 13))
            
            for pt in decoded:
                decode_list.append([float(pt.real), float(pt.imag)])
            
            offset += 4

        return decode_list

    def get_const_disp_meas(self) -> Dict[str, Optional[object]]:
        """
        Returns a dictionary of parsed measurement data with lowercase snake_case keys.

        Returns:
            dict: Parsed data including metadata and I/Q constellation points.
        """
        data = self.getPnmHeader(header_only=True)
        
        data.update ({
            'channel_id': self.channel_id,
            'mac_address': self.mac_address,
            'subcarrier_zero_frequency': self.subcarrier_zero_frequency,
            'actual_modulation_order': DsOfdmModulationType.get_name(self.actual_modulation_order),
            'num_sample_symbols': self.num_sample_symbols,
            'subcarrier_spacing': self.subcarrier_spacing *1000,
            'sample_length': self.display_data_length,
            "value_units":"[Real(I), Imaginary(Q)]",
            "values": self.parsed_constellation_data,
        })
        
        return data

    def to_dict(self) -> Dict[str, Optional[object]]:
        """
        Returns:
            dict: Alias for `get_const_disp_meas()`.
        """
        return self.get_const_disp_meas()
    
    def to_json(self) -> str:
        """
        Serializes the parsed measurement data to a JSON string.

        Returns:
            str: JSON-formatted string representation of the data.
        """
        return json.dumps(self.to_dict(), indent=2)