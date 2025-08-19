# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import csv

from pypnm.lib.csv.manager import CSVManager, CSVOrientation, CSVValidationError

class TestCSVManager(unittest.TestCase):
    """Unit tests for CSVManager class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.csv_manager = CSVManager()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
    def tearDown(self):
        """Clean up after each test method"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_default_vertical(self):
        """Test default initialization creates vertical orientation"""
        manager = CSVManager()
        self.assertEqual(manager.orientation, CSVOrientation.VERTICAL)
        self.assertEqual(manager.headers, [])
        self.assertEqual(manager.data, [])
        self.assertFalse(manager._header_set)
    
    def test_initialization_horizontal(self):
        """Test initialization with horizontal orientation"""
        manager = CSVManager(CSVOrientation.HORIZONTAL)
        self.assertEqual(manager.orientation, CSVOrientation.HORIZONTAL)
    
    def test_add_header_single_string(self):
        """Test adding a single header as string"""
        self.csv_manager.set_header("Test Header")
        self.assertEqual(self.csv_manager.headers, ["Test Header"])
        self.assertTrue(self.csv_manager._header_set)
    
    def test_add_header_list(self):
        """Test adding headers as list"""
        headers = ["Header1", "Header2", "Header3"]
        self.csv_manager.set_header(headers)
        self.assertEqual(self.csv_manager.headers, headers)
        self.assertTrue(self.csv_manager._header_set)
    
    def test_add_header_strips_whitespace(self):
        """Test that headers are stripped of whitespace"""
        self.csv_manager.set_header([" Header1 ", "\tHeader2\n", "  Header3  "])
        self.assertEqual(self.csv_manager.headers, ["Header1", "Header2", "Header3"])
    
    def test_add_header_empty_list_raises_error(self):
        """Test that empty headers list raises validation error"""
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.set_header([])
        self.assertIn("Headers cannot be empty", str(context.exception))
    
    def test_add_header_empty_string_raises_error(self):
        """Test that empty string headers raise validation error"""
        with self.assertRaises(CSVValidationError):
            self.csv_manager.set_header(["Header1", "", "Header3"])
    
    def test_add_header_non_string_raises_error(self):
        """Test that non-string headers raise validation error"""
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.set_header(["Header1", 123, "Header3"])                                # type: ignore
        self.assertIn("Header at index 1 must be a string", str(context.exception))
    
    def test_add_header_twice_raises_error(self):
        """Test that setting headers twice raises error"""
        self.csv_manager.set_header(["Header1"])
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.set_header(["Header2"])
        self.assertIn("Headers have already been set", str(context.exception))
    
    def test_insert_row_without_headers_raises_error(self):
        """Test that inserting row without headers raises error"""
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.insert_row(["data1", "data2"])
        self.assertIn("Headers must be set before inserting data", str(context.exception))
    
    def test_insert_row_single_value(self):
        """Test inserting single value for single column CSV"""
        self.csv_manager.set_header("Single Header")
        self.csv_manager.insert_row("single value")
        self.assertEqual(self.csv_manager.data, [["single value"]])
    
    def test_insert_row_list_values(self):
        """Test inserting row with list of values"""
        self.csv_manager.set_header(["Col1", "Col2", "Col3"])
        self.csv_manager.insert_row(["val1", "val2", "val3"])
        self.assertEqual(self.csv_manager.data, [["val1", "val2", "val3"]])
    
    def test_insert_row_wrong_length_raises_error(self):
        """Test that wrong number of elements raises error"""
        self.csv_manager.set_header(["Col1", "Col2", "Col3"])
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.insert_row(["val1", "val2"])  # Missing one value
        self.assertIn("Row data length (2) does not match header count (3)", str(context.exception))
    
    def test_insert_row_handles_none_values(self):
        """Test that None values are converted to empty strings"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["value1", None])
        self.assertEqual(self.csv_manager.data, [["value1", ""]])
    
    def test_insert_row_converts_to_string(self):
        """Test that all values are converted to strings"""
        self.csv_manager.set_header(["Col1", "Col2", "Col3"])
        self.csv_manager.insert_row([123, 45.67, True])
        self.assertEqual(self.csv_manager.data, [["123", "45.67", "True"]])
    
    def test_insert_multiple_rows(self):
        """Test inserting multiple rows at once"""
        self.csv_manager.set_header(["Col1", "Col2"])
        rows = [["val1", "val2"], ["val3", "val4"], ["val5", "val6"]]
        self.csv_manager.insert_multiple_rows(rows)
        self.assertEqual(len(self.csv_manager.data), 3)
        self.assertEqual(self.csv_manager.data[1], ["val3", "val4"])
    
    def test_insert_multiple_rows_with_error(self):
        """Test that error in multiple rows insertion includes row index"""
        self.csv_manager.set_header(["Col1", "Col2"])
        rows = [["val1", "val2"], ["val3"], ["val5", "val6"]]  # Second row has wrong length
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.insert_multiple_rows(rows)
        self.assertIn("Error in row 1", str(context.exception))
    
    def test_get_row_count(self):
        """Test getting row count"""
        self.csv_manager.set_header(["Col1"])
        self.assertEqual(self.csv_manager.get_row_count(), 0)
        self.csv_manager.insert_row(["val1"])
        self.csv_manager.insert_row(["val2"])
        self.assertEqual(self.csv_manager.get_row_count(), 2)
    
    def test_get_column_count(self):
        """Test getting column count"""
        self.csv_manager.set_header(["Col1", "Col2", "Col3"])
        self.assertEqual(self.csv_manager.get_column_count(), 3)
    
    def test_get_headers_returns_copy(self):
        """Test that get_headers returns a copy, not reference"""
        original_headers = ["Col1", "Col2"]
        self.csv_manager.set_header(original_headers)
        returned_headers = self.csv_manager.get_headers()
        returned_headers.append("Col3")  # Modify returned copy
        self.assertEqual(self.csv_manager.headers, original_headers)  # Original unchanged
    
    def test_get_data_returns_copy(self):
        """Test that get_data returns a copy, not reference"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["val1", "val2"])
        returned_data = self.csv_manager.get_data()
        returned_data[0][0] = "modified"  # Modify returned copy
        self.assertEqual(self.csv_manager.data[0][0], "val1")  # Original unchanged
    
    def test_clear(self):
        """Test clearing all data and headers"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["val1", "val2"])
        self.csv_manager.clear()
        self.assertEqual(self.csv_manager.headers, [])
        self.assertEqual(self.csv_manager.data, [])
        self.assertFalse(self.csv_manager._header_set)
    
    def test_create_csv_without_headers_raises_error(self):
        """Test that creating CSV without headers raises error"""
        test_file = self.temp_path / "test.csv"
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.write(test_file)
        self.assertIn("Cannot create CSV: no headers have been set", str(context.exception))
    
    def test_create_vertical_csv_basic(self):
        """Test creating basic vertical CSV"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["val1", "val2"])
        self.csv_manager.insert_row(["val3", "val4"])
        
        test_file = self.temp_path / "test_vertical.csv"
        result_path = self.csv_manager.write(test_file)
        
        self.assertEqual(result_path, test_file)
        self.assertTrue(test_file.exists())
        
        # Read and verify content
        with open(test_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        self.assertEqual(rows[0], ["Col1", "Col2"])  # Headers
        self.assertEqual(rows[1], ["val1", "val2"])  # First data row
        self.assertEqual(rows[2], ["val3", "val4"])  # Second data row
    
    def test_create_vertical_csv_with_index(self):
        """Test creating vertical CSV with row index"""
        self.csv_manager.set_header(["Col1"])
        self.csv_manager.insert_row(["val1"])
        self.csv_manager.insert_row(["val2"])
        
        test_file = self.temp_path / "test_with_index.csv"
        self.csv_manager.write(test_file, include_index=True)
        
        with open(test_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        self.assertEqual(rows[0], ["Index", "Col1"])  # Headers with index
        self.assertEqual(rows[1], ["0", "val1"])      # Row 0
        self.assertEqual(rows[2], ["1", "val2"])      # Row 1
    
    def test_create_horizontal_csv(self):
        """Test creating horizontal CSV"""
        manager = CSVManager(CSVOrientation.HORIZONTAL)
        manager.set_header(["Metric", "Value1", "Value2"])
        manager.insert_row(["Temperature", "25.5", "26.1"])
        manager.insert_row(["Humidity", "60", "65"])
        
        test_file = self.temp_path / "test_horizontal.csv"
        manager.write(test_file)
        
        with open(test_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # In horizontal format, each header becomes a row
        self.assertEqual(rows[0], ["Metric", "Temperature", "Humidity"])
        self.assertEqual(rows[1], ["Value1", "25.5", "60"])
        self.assertEqual(rows[2], ["Value2", "26.1", "65"])
    
    def test_create_csv_custom_delimiter(self):
        """Test creating CSV with custom delimiter"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["val1", "val2"])
        
        test_file = self.temp_path / "test_custom_delimiter.csv"
        self.csv_manager.write(test_file, delimiter=';')
        
        with open(test_file, 'r') as f:
            content = f.read()
        
        self.assertIn("Col1;Col2", content)
        self.assertIn("val1;val2", content)
    
    def test_to_dataframe_empty(self):
        """Test converting empty CSV to DataFrame"""
        self.csv_manager.set_header(["Col1", "Col2"])
        df = self.csv_manager.to_dataframe()
        
        self.assertEqual(list(df.columns), ["Col1", "Col2"])
        self.assertEqual(len(df), 0)
    
    def test_to_dataframe_with_data(self):
        """Test converting CSV with data to DataFrame"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["val1", "val2"])
        self.csv_manager.insert_row(["val3", "val4"])
        
        df = self.csv_manager.to_dataframe()
        
        self.assertEqual(list(df.columns), ["Col1", "Col2"])
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0, 0], "val1")
        self.assertEqual(df.iloc[1, 1], "val4")
    
    def test_to_dataframe_without_headers_raises_error(self):
        """Test that converting to DataFrame without headers raises error"""
        with self.assertRaises(CSVValidationError):
            self.csv_manager.to_dataframe()
    
    def test_from_dataframe(self):
        """Test loading data from DataFrame"""
        df = pd.DataFrame({
            'Col1': ['val1', 'val3'],
            'Col2': ['val2', 'val4']
        })
        
        self.csv_manager.from_dataframe(df)
        
        self.assertEqual(self.csv_manager.headers, ['Col1', 'Col2'])
        self.assertEqual(len(self.csv_manager.data), 2)
        self.assertEqual(self.csv_manager.data[0], ['val1', 'val2'])
        self.assertEqual(self.csv_manager.data[1], ['val3', 'val4'])
    
    def test_preview_no_headers(self):
        """Test preview with no headers set"""
        preview = self.csv_manager.preview()
        self.assertEqual(preview, "No headers set")
    
    def test_preview_with_headers_no_data(self):
        """Test preview with headers but no data"""
        self.csv_manager.set_header(["Col1", "Col2"])
        preview = self.csv_manager.preview()
        
        self.assertIn("Headers (2): Col1, Col2", preview)
        self.assertIn("Data rows: 0", preview)
        self.assertIn("No data rows", preview)
    
    def test_preview_with_data(self):
        """Test preview with data"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["val1", "val2"])
        self.csv_manager.insert_row(["val3", "val4"])
        
        preview = self.csv_manager.preview()
        
        self.assertIn("Headers (2): Col1, Col2", preview)
        self.assertIn("Data rows: 2", preview)
        self.assertIn("val1", preview)
        self.assertIn("val2", preview)
    
    def test_preview_max_rows_limit(self):
        """Test preview respects max_rows limit"""
        self.csv_manager.set_header(["Col1"])
        for i in range(10):
            self.csv_manager.insert_row([f"val{i}"])
        
        preview = self.csv_manager.preview(max_rows=3)
        
        self.assertIn("val0", preview)
        self.assertIn("val2", preview)
        self.assertNotIn("val5", preview)
        self.assertIn("and 7 more rows", preview)
    
    def test_validate_data_integrity_no_headers(self):
        """Test validation without headers raises error"""
        with self.assertRaises(CSVValidationError):
            self.csv_manager.validate_data_integrity()
    
    def test_validate_data_integrity_valid(self):
        """Test validation with valid data"""
        self.csv_manager.set_header(["Col1", "Col2"])
        self.csv_manager.insert_row(["val1", "val2"])
        self.csv_manager.insert_row(["val3", "val4"])
        
        result = self.csv_manager.validate_data_integrity()
        self.assertTrue(result)
    
    def test_validate_data_integrity_invalid(self):
        """Test validation with invalid data (shouldn't happen with normal usage)"""
        self.csv_manager.set_header(["Col1", "Col2"])
        # Manually add invalid row to test validation
        self.csv_manager.data.append(["val1"])  # Missing one element
        
        with self.assertRaises(CSVValidationError) as context:
            self.csv_manager.validate_data_integrity()
        self.assertIn("Row 0 has 1 elements, expected 2", str(context.exception))


class TestCSVValidationError(unittest.TestCase):
    """Test the custom exception class"""
    
    def test_csv_validation_error_creation(self):
        """Test creating CSVValidationError"""
        error = CSVValidationError("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsInstance(error, Exception)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)