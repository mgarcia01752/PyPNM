# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import json
import logging
from struct import calcsize, unpack
from typing import Optional, List, Tuple, Dict, Any

from pnm.lib.fixed_point_decoder import FixedPointDecoder
from pnm.process.pnm_file_type import PnmFileType
from pnm.process.pnm_header import PnmHeader


class CmUsPreEq(PnmHeader):
    """
    Parses and decodes CM Upstream Pre-Equalization data from binary input.

    Includes:
        - Header metadata
        - Fixed-point complex coefficient data
    """

    def __init__(self, binary_data: bytes, sm_n_format: Tuple[int, int] = (1, 14)):
        super().__init__(binary_data)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.sm_n_format = sm_n_format

        self.channel_id: Optional[int] = None
        self.mac_address: Optional[str] = None
        self.cmts_mac_address: Optional[str] = None
        self.subcarrier_zero_frequency: Optional[int] = None
        self.first_active_subcarrier_index: Optional[int] = None
        self.subcarrier_spacing: Optional[int] = None
        self.pre_eq_data_length: Optional[int] = None
        self.pre_eq_coefficient_data: Optional[bytes] = None
        self._decoded_coefficients: Optional[List[complex]] = None

        self._parse_header_and_coefficients()

    def convert_complex_list(self, coefficients: List[complex]) -> List[Dict[str, float]]:
        """
        Converts list of Python complex numbers to a JSON-serializable list of dicts.

        Args:
            coefficients (List[complex]): List of complex numbers

        Returns:
            List[Dict[str, float]]: List of {"real": ..., "imag": ...} representations
        """
        return [{"real": c.real, "imag": c.imag} for c in coefficients]

    def _parse_header_and_coefficients(self) -> None:
        """
        Parses the fixed-length header and coefficient block.
        Format:
            - 1 byte: Upstream Channel ID
            - 6 bytes: CM MAC
            - 6 bytes: CMTS MAC
            - 4 bytes: Subcarrier Zero Freq (Hz)
            - 2 bytes: First Active Subcarrier Index
            - 1 byte: Subcarrier Spacing (kHz)
            - 4 bytes: Length of coefficient data (bytes)
        """
        if (self.get_pnm_file_type() != PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS) and (self.get_pnm_file_type() != PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS_LAST_UPDATE):
            cann = PnmFileType.UPSTREAM_PRE_EQUALIZER_COEFFICIENTS.get_pnm_cann()
            raise ValueError(f"PNM File Stream is not  file type: {cann}, Error: {self.get_pnm_file_type().get_pnm_cann()}")
         
        header_format = '>B 6s 6s I H B I'
        header_size = calcsize(header_format)

        if len(self.pnm_data) < header_size:
            raise ValueError("Insufficient data for CmUsPreEq header.")

        (
            self.channel_id,
            cm_mac,
            cmts_mac,
            self.subcarrier_zero_frequency,
            self.first_active_subcarrier_index,
            self.subcarrier_spacing,
            self.pre_eq_data_length
        ) = unpack(header_format, self.pnm_data[:header_size])

        self.mac_address = self._format_mac(cm_mac)
        self.cmts_mac_address = self._format_mac(cmts_mac)
        self.pre_eq_coefficient_data = self.pnm_data[header_size:]

        if len(self.pre_eq_coefficient_data) != self.pre_eq_data_length:
            raise ValueError("Mismatch between reported and actual Pre-EQ data length.")
        
        self._decoded_coefficients = self.process_pre_eq_coefficient_data()

    def _format_mac(self, mac_bytes: bytes) -> str:
        return ':'.join(f'{b:02x}' for b in mac_bytes)

    def process_pre_eq_coefficient_data(self) -> Optional[List[complex]]:
        """
        Decodes fixed-point complex coefficients.

        Returns:
            Optional[List[complex]]: Decoded coefficient list
        """
        if not self.pre_eq_coefficient_data:
            return None

        self._decoded_coefficients = FixedPointDecoder.decode_complex_data(
            self.pre_eq_coefficient_data,
            self.sm_n_format
        )
        return self._decoded_coefficients

    def get_coefficients(self) -> Optional[List[complex]]:
        """
        Returns previously decoded coefficients if available, otherwise decodes on demand.

        Returns:
            Optional[List[complex]]
        """
        if self._decoded_coefficients is not None:
            return self._decoded_coefficients
        return self.process_pre_eq_coefficient_data()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the upstream OFDMA pre-equalization object into a dictionary with snake_case keys.

        Returns:
            Dict[str, Any]: Parsed header and analysis-relevant values.
        """
        result: Dict[str, Any] = self.getPnmHeader(header_only=True)

        coefficients = self.get_coefficients()
        complex_pairs = [[c.real, c.imag] for c in coefficients] if coefficients else []

        result.update({
            "upstream_channel_id": self.channel_id,
            "cm_mac_address": self.mac_address,
            "cmts_mac_address": self.cmts_mac_address,
            "subcarrier_zero_frequency": self.subcarrier_zero_frequency,  # Hz
            "first_active_subcarrier_index": self.first_active_subcarrier_index,
            "subcarrier_spacing": self.subcarrier_spacing * 1_000,        # Convert kHz → Hz
            "value_length": self.pre_eq_data_length,
            "value_unit": "[Real, Imaginary]",
            "values": complex_pairs
        })

        return result


    def to_json(self) -> str:
        """
        Returns:
            str: JSON string of header values
        """
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        return f"<CmUsPreEq(chid={self.channel_id}, cm={self.mac_address}, cmts={self.cmts_mac_address})>"



