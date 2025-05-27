#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
import unittest
from pypnm.pnm.lib.fixed_point_decoder import FixedPointDecoder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class TestFixedPointDecoder(unittest.TestCase):
    def test_signed_fixed_point_decoding(self):
        # Test cases: (hex_value, (integer_bits, fractional_bits), expected_result)
        # All are signed fixed-point values (sX.Y format)
        test_cases = [
            (0x1400, (3, 12), 1.25),  
            (0x2400, (1, 14), 0.5625),  
            (0x2400, (2, 13), 1.125),  
            (0x2400, (3, 12), 2.25),
            (0xFFFF, (3, 12), -0.000244140625), 
            (0x8fff, (3, 12), -7.000244140625),
            (0x8fff, (5, 10), -28.0009765625), 
        ]

        for hex_val, fmt, expected in test_cases:
            with self.subTest(hex_value=hex(hex_val), format=fmt):
                # Call the decoder with signed=True for signed fixed-point interpretation
                result = FixedPointDecoder.decode_fixed_point(hex_val, fmt, signed=True)
                self.assertAlmostEqual(result, expected, places=6)

if __name__ == '__main__':
    unittest.main()
