import unittest

class TestMinAvgMax(unittest.TestCase):

    def test_basic_statistics(self):
        amplitude = [
            [1.0, 2.0, 3.0],
            [2.0, 3.0, 4.0],
            [0.0, 1.0, 5.0]
        ]
        stats = MinAvgMax(amplitude)

        self.assertEqual(stats.min_values, [0.0, 1.0, 3.0])
        self.assertEqual(stats.avg_values, [1.0, 2.0, 4.0])
        self.assertEqual(stats.max_values, [2.0, 3.0, 5.0])
        self.assertEqual(stats.precision, 2)
        self.assertEqual(stats.length(), 3)

    def test_precision_control(self):
        amplitude = [
            [1.12345, 2.54321],
            [1.67891, 2.12345],
        ]
        stats = MinAvgMax(amplitude, precision=3)

        self.assertEqual(stats.min_values, [1.123, 2.123])
        self.assertEqual(stats.avg_values, [1.401, 2.333])
        self.assertEqual(stats.max_values, [1.679, 2.543])

    def test_to_dict_keys(self):
        amplitude = [[1, 2], [3, 4]]
        stats = MinAvgMax(amplitude)
        result = stats.to_dict()

        self.assertIn("min", result)
        self.assertIn("avg", result)
        self.assertIn("max", result)
        self.assertIn("precision", result)
        self.assertIn("signal_statistics", result)

        self.assertIsInstance(result["signal_statistics"], dict)
        self.assertIn("min", result["signal_statistics"])
        self.assertIn("avg", result["signal_statistics"])
        self.assertIn("max", result["signal_statistics"])

    def test_invalid_input_empty(self):
        with self.assertRaises(ValueError):
            MinAvgMax([])

    def test_invalid_input_inconsistent_lengths(self):
        with self.assertRaises(ValueError):
            MinAvgMax([[1, 2], [3]])  # mismatched lengths

    def test_valid_1_column_matrix(self):
        amplitude = [[1], [2], [3]]
        stats = MinAvgMax(amplitude)
        self.assertEqual(stats.min_values, [1.0])
        self.assertEqual(stats.avg_values, [2.0])
        self.assertEqual(stats.max_values, [3.0])
        self.assertEqual(stats.length(), 1)


if __name__ == "__main__":
    unittest.main()
