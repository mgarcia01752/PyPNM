# SPDX-License-Identifier: MIT
# Run with your test runner or: python -m unittest -q

import unittest

from pypnm.lib.qam.types import QamModulation
from pypnm.pnm.data_type.DsOfdmModulationType import DsOfdmModulationType as DS

class TestQamModulation(unittest.TestCase):

    # ------------------------
    # from_value
    # ------------------------
    def test_from_value_valid_and_invalid(self):
        self.assertEqual(QamModulation.from_value(64), QamModulation.QAM_64)
        self.assertEqual(QamModulation.from_value(256), QamModulation.QAM_256)
        # invalid → UNKNOWN
        self.assertEqual(QamModulation.from_value(123), QamModulation.UNKNOWN)
        self.assertEqual(QamModulation.from_value(-1), QamModulation.UNKNOWN)

    # ------------------------
    # bps & __str__
    # ------------------------
    def test_get_bit_per_symbol(self):
        self.assertEqual(QamModulation.QAM_2.get_bit_per_symbol(), 1)
        self.assertEqual(QamModulation.QAM_4.get_bit_per_symbol(), 2)
        self.assertEqual(QamModulation.QAM_256.get_bit_per_symbol(), 8)
        self.assertEqual(QamModulation.UNKNOWN.get_bit_per_symbol(), 0)

    def test_str_format(self):
        self.assertEqual(str(QamModulation.QAM_64), "qam_64")
        self.assertEqual(str(QamModulation.QAM_1024), "qam_1024")

    # ------------------------
    # from_ds_ofdm_modulation_type: strings
    # ------------------------
    def test_from_ds_mod_type_strings(self):
        cases = [
            ("qpsk", QamModulation.QAM_4),
            ("QPSK", QamModulation.QAM_4),
            ("qam16", QamModulation.QAM_16),
            ("QAM-64", QamModulation.QAM_64),
            ("qam_128", QamModulation.QAM_128),
            (" QAM-256 ", QamModulation.QAM_256),
            ("qam1024", QamModulation.QAM_1024),
            ("qam2048", QamModulation.QAM_2048),
            ("qam4096", QamModulation.QAM_4096),
            ("qam8192", QamModulation.QAM_8192),
            ("qam16384", QamModulation.QAM_16384),
            ("qam65536", QamModulation.QAM_65536),
            ("qam-bad", QamModulation.UNKNOWN),
            ("not_a_modulation", QamModulation.UNKNOWN),
        ]
        for s, expected in cases:
            with self.subTest(s=s):
                self.assertEqual(QamModulation.from_ds_ofdm_modulation_type(s), expected)

    # ------------------------
    # from_ds_ofdm_modulation_type: integer DS codes
    # DS codes expected from earlier layout:
    #   qpsk=3, qam16=4, qam64=5, qam128=6, qam256=7, qam512=8,
    #   qam1024=9, qam2048=10, qam4096=11, qam8192=12
    # ------------------------
    def test_from_ds_mod_type_int_codes(self):
        code_map = {
            3: QamModulation.QAM_4,
            4: QamModulation.QAM_16,
            5: QamModulation.QAM_64,
            6: QamModulation.QAM_128,
            7: QamModulation.QAM_256,
            8: QamModulation.QAM_512,
            9: QamModulation.QAM_1024,
            10: QamModulation.QAM_2048,
            11: QamModulation.QAM_4096,
            12: QamModulation.QAM_8192,
        }
        for code, expected in code_map.items():
            with self.subTest(code=code):
                self.assertEqual(QamModulation.from_ds_ofdm_modulation_type(code), expected)

        # unsupported code → UNKNOWN
        for bad in (-1, 0, 1, 2, 13, 99):
            with self.subTest(code=bad):
                self.assertEqual(QamModulation.from_ds_ofdm_modulation_type(bad), QamModulation.UNKNOWN)

    # ------------------------
    # from_ds_ofdm_modulation_type: enum members (if available)
    # ------------------------
    def test_from_ds_mod_type_enum(self):
        cases = [
            (DS.qpsk, QamModulation.QAM_4),
            (DS.qam16, QamModulation.QAM_16),
            (DS.qam64, QamModulation.QAM_64),
            (DS.qam128, QamModulation.QAM_128),
            (DS.qam256, QamModulation.QAM_256),
            (DS.qam512, QamModulation.QAM_512),
            (DS.qam1024, QamModulation.QAM_1024),
            (DS.qam2048, QamModulation.QAM_2048),
            (DS.qam4096, QamModulation.QAM_4096),
            (DS.qam8192, QamModulation.QAM_8192),
        ]
        for enum_val, expected in cases:
            with self.subTest(enum_val=enum_val):
                self.assertEqual(QamModulation.from_ds_ofdm_modulation_type(enum_val), expected)

        # Unknown-like enums → UNKNOWN (if such members exist)
        if hasattr(DS, "UNKNOWN"):
            self.assertEqual(QamModulation.from_ds_ofdm_modulation_type(DS.UNKNOWN), QamModulation.UNKNOWN)
        if hasattr(DS, "other"):
            self.assertEqual(QamModulation.from_ds_ofdm_modulation_type(DS.other), QamModulation.UNKNOWN)
        if hasattr(DS, "zeroValued"):
            self.assertEqual(QamModulation.from_ds_ofdm_modulation_type(DS.zeroValued), QamModulation.UNKNOWN)

if __name__ == "__main__":
    unittest.main()
