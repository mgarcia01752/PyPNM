import unittest
import numpy as np

from pypnm.api.routes.advance.analysis.signal_analysis.group_delay_calculator import GroupDelayCalculator
class TestGroupDelayCalculator(unittest.TestCase):

    def setUp(self):
        self.freqs = np.linspace(1e6, 10e6, 9)  # 9 subcarriers
        self.H_single = np.exp(1j * 2 * np.pi * 1e-6 * self.freqs)
        self.H_snapshots = np.array([
            np.exp(1j * 2 * np.pi * 1e-6 * self.freqs),
            np.exp(1j * 2 * np.pi * 1.5e-6 * self.freqs),
        ])

    def test_init_with_1d_complex(self):
        calc = GroupDelayCalculator(self.H_single, self.freqs)
        self.assertEqual(calc.H_raw.shape, (1, 9))

    def test_init_with_2d_complex(self):
        calc = GroupDelayCalculator(self.H_snapshots, self.freqs)
        self.assertEqual(calc.H_raw.shape, (2, 9))

    def test_init_with_2d_real_imag(self):
        H_real_imag = np.column_stack((self.H_single.real, self.H_single.imag))
        calc = GroupDelayCalculator(H_real_imag, self.freqs)
        self.assertEqual(calc.H_raw.shape, (1, 9))

    def test_init_with_3d_real_imag(self):
        H_3d = np.stack([
            np.column_stack((snap.real, snap.imag)) for snap in self.H_snapshots
        ])
        calc = GroupDelayCalculator(H_3d, self.freqs)
        self.assertEqual(calc.H_raw.shape, (2, 9))

    def test_invalid_freq_shape(self):
        with self.assertRaises(ValueError):
            GroupDelayCalculator(self.H_single, self.freqs.reshape(3, 3))

    def test_invalid_length_mismatch(self):
        bad_freqs = np.linspace(1e6, 9e6, 8)
        with self.assertRaises(ValueError):
            GroupDelayCalculator(self.H_single, bad_freqs)

    def test_compute_group_delay_full(self):
        calc = GroupDelayCalculator(self.H_single, self.freqs)
        f_out, tau_out = calc.compute_group_delay_full()
        self.assertEqual(f_out.shape, (9,))
        self.assertEqual(tau_out.shape, (9,))
        self.assertTrue(np.all(np.isfinite(tau_out)))

    def test_snapshot_group_delay(self):
        calc = GroupDelayCalculator(self.H_snapshots, self.freqs)
        tau = calc.snapshot_group_delay()
        self.assertEqual(tau.shape, (2, 9))

    def test_median_group_delay(self):
        calc = GroupDelayCalculator(self.H_snapshots, self.freqs)
        f_out, tau_med = calc.median_group_delay()
        self.assertEqual(f_out.shape, (9,))
        self.assertEqual(tau_med.shape, (9,))

    def test_to_dict_output_structure(self):
        calc = GroupDelayCalculator(self.H_snapshots, self.freqs)
        data = calc.to_dict()
        self.assertIn("freqs", data)
        self.assertIn("H_raw", data)
        self.assertIn("H_avg", data)
        self.assertIn("group_delay_full", data)
        self.assertIn("snapshot_group_delay", data)
        self.assertIn("median_group_delay", data)
        self.assertIn("dataset_info", data)

        self.assertEqual(len(data["freqs"]), 9)
        self.assertEqual(len(data["H_raw"]), 2)
        self.assertEqual(len(data["H_avg"]), 9)
        self.assertEqual(len(data["group_delay_full"]["tau_g"]), 9)
        self.assertEqual(len(data["median_group_delay"]["tau_med"]), 9)


if __name__ == "__main__":
    unittest.main()
