
from __future__ import annotations

# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import unittest
import struct
from pypnm.pnm.process.pnm_file_type import PnmFileType
from pypnm.pnm.process.pnm_header import PnmHeader


class TestPnmHeader(unittest.TestCase):

    def test_default_header_parsing(self):
        # Header: !3sBBBI → b'PNN', 1, 2, 3, 12345678
        header_bytes = struct.pack("!3sBBBI", b"PNN", 1, 2, 3, 12345678)
        data_bytes = b'\xDE\xAD\xBE\xEF'
        packet = header_bytes + data_bytes

        hdr = PnmHeader(packet)

        self.assertEqual(hdr.file_type, b"PNN")
        self.assertEqual(hdr.file_type_num, 1)
        self.assertEqual(hdr.major_version, 2)
        self.assertEqual(hdr.minor_version, 3)
        self.assertEqual(hdr.capture_time, 12345678)
        self.assertEqual(hdr.pnm_data, data_bytes)

        header_dict = hdr.getPnmHeader()
        self.assertEqual(header_dict["pnm_header"]["file_type"], "PNN")
        self.assertEqual(header_dict["pnm_header"]["file_type_version"], 1)
        self.assertEqual(header_dict["pnm_header"]["major_version"], 2)
        self.assertEqual(header_dict["pnm_header"]["minor_version"], 3)
        self.assertEqual(header_dict["pnm_header"]["capture_time"], 12345678)
        self.assertEqual(header_dict["data"], data_bytes.hex())

    def test_special_case_header_parsing(self):
        # Special case: byte_array[3] == 8 triggers <3sBBB
        header_bytes = struct.pack("<3sBBB", b"PNN", 10, 2, 8)
        data_bytes = b'\x00\x11\x22'
        packet = header_bytes + data_bytes

        hdr = PnmHeader(packet)

        self.assertEqual(hdr.file_type, b"PNN")
        self.assertEqual(hdr.file_type_num, 10)
        self.assertEqual(hdr.major_version, 2)
        self.assertEqual(hdr.minor_version, 8)
        self.assertEqual(hdr.capture_time, 0)  # not set in special case
        self.assertEqual(hdr.pnm_data, data_bytes)

    def test_get_pnm_file_type_match(self):
        # Assume PnmFileType.PNN10 exists and maps to 'PNN10'
        header_bytes = struct.pack("<3sBBB", b"PNN", 10, 2, 8)
        packet = header_bytes + b'\x00'

        hdr = PnmHeader(packet)
        pnm_type = hdr.get_pnm_file_type()

        self.assertEqual(pnm_type, PnmFileType.OFDM_MODULATION_PROFILE)

    def test_get_pnm_file_type_unrecognized(self):
        header_bytes = struct.pack("<3sBBB", b"ZZZ", 99, 1, 8)
        packet = header_bytes + b'\x00'

        hdr = PnmHeader(packet)
        pnm_type = hdr.get_pnm_file_type()

        self.assertIsNone(pnm_type)

    def test_get_header_without_data(self):
        header_bytes = struct.pack("!3sBBBI", b"PNN", 4, 1, 2, 1111)
        packet = header_bytes + b"ignored-data"

        hdr = PnmHeader(packet)
        result = hdr.getPnmHeader(header_only=True)

        self.assertIn("pnm_header", result)
        self.assertNotIn("data", result)


if __name__ == "__main__":
    unittest.main()
