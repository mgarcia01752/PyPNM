# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

class FileProcessor:

    def __init__(self, filepath: Union[str, Path]):
        """
        A utility class to handle reading/writing files and hex conversion.

        Args:
            filepath (str): Path to the file to manage.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.filepath = filepath
        self.logger.debug(f"Initialized FileProcessor with path: {self.filepath}")

    def file_exists(self) -> bool:
        """
        Checks if the file exists.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return Path(self.filepath).exists()

    def read_file(self) -> bytes:
        """
        Reads binary data from the file.

        Returns:
            bytes: The file content. Empty if failed.
        """
        try:
            with open(self.filepath, "rb") as file:
                data = file.read()
                self.logger.info(f"Read {len(data)} bytes from {self.filepath}")
                return data
        except FileNotFoundError:
            self.logger.error(f"File not found: {self.filepath}")
        except IOError as e:
            self.logger.error(f"Error reading file {self.filepath}: {e}")
        return b""

    def write_file(self, data: Union[bytes, str, dict], append: bool = False) -> bool:
        """
        Writes data to the file.

        Args:
            data (bytes | str | dict): Data to write.
            append (bool): If True, appends instead of overwriting.

        Returns:
            bool: Success status.
        """
        mode = "ab" if append else "wb"
        try:
            with open(self.filepath, mode) as file:
                if isinstance(data, str):
                    data_bytes = data.encode("utf-8")
                elif isinstance(data, dict):
                    data_bytes = json.dumps(data, indent=2).encode("utf-8")
                elif isinstance(data, bytes):
                    data_bytes = data
                else:
                    raise ValueError("Unsupported type for file write")

                file.write(data_bytes)
                self.logger.info(f"Wrote {len(data_bytes)} bytes to {self.filepath}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to write to {self.filepath}: {e}")
        return False

    def to_hex(self) -> str:
        """
        Converts binary file contents to a hex string.

        Returns:
            str: Hex string, or "" if failed.
        """
        data = self.read_file()
        if data:
            hex_data = data.hex()
            self.logger.debug(f"Hex conversion complete: {len(hex_data)} chars")
            return hex_data
        self.logger.warning("No data available to convert to hex.")
        return ""

    def to_binary(self, hex_data: str) -> bytes:
        """
        Converts a hex string to binary.

        Args:
            hex_data (str): A hex string.

        Returns:
            bytes: Binary data.
        """
        try:
            binary_data = bytes.fromhex(hex_data)
            self.logger.debug(f"Converted hex to binary ({len(binary_data)} bytes)")
            return binary_data
        except ValueError as e:
            self.logger.error(f"Invalid hex data: {e}")
        return b""

    def print_hex(self, limit: int = 64) -> None:
        """
        Prints the first N characters of the hex file content.

        Args:
            limit (int): Max characters to show.
        """
        hex_data = self.to_hex()
        if hex_data:
            snippet = hex_data[:limit]
            self.logger.debug(f"Hex preview: {snippet}")
            print("Hex Preview:", snippet)
        else:
            self.logger.warning("No hex data to display.")

    def write_csv(
        self,
        data: List[Union[Dict[str, Any], List[Any]]],
        headers: Optional[List[str]] = None,
        append: bool = False,
        filepath: Optional[str] = None
    ) -> bool:
        """
        Writes tabular data to a CSV file.

        Supports both list of dicts and list of lists.

        Args:
            data (List[dict] | List[list]): Rows to write.
            headers (List[str], optional): Column headers (required for list of lists).
            append (bool): If True, appends to existing CSV, else overwrites.
            filepath (str, optional): Path to CSV file. Uses self.filepath if None.

        Returns:
            bool: Success status.
        """
        target = filepath or self.filepath
        mode = 'a' if append else 'w'
        try:
            with open(target, mode, newline='', encoding='utf-8') as csvfile:
                if not data:
                    self.logger.warning("No data provided for CSV write.")
                    return False

                first = data[0]
                # Write dict rows
                if isinstance(first, dict):
                    fieldnames = list(first.keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if not append:
                        writer.writeheader()
                    writer.writerows(data)  # type: ignore
                else:
                    writer = csv.writer(csvfile)
                    # Write headers for list rows if provided
                    if headers and not append:
                        writer.writerow(headers)
                    # Write all rows
                    writer.writerows(data)  # type: ignore

                self.logger.info(f"Wrote {len(data)} rows to CSV at {target}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to write CSV to {target}: {e}")
        return False
    
    def close(self) -> None:
        """
        Placeholder for any cleanup actions if needed.
        Currently does nothing but can be overridden in subclasses.
        """
        self.logger.debug("FileProcessor close called, no action taken.")

    def __str__(self) -> str:
        return f"FileProcessor({self.filepath})"

    def __repr__(self) -> str:
        return f"FileProcessor(filepath={self.filepath})"
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        if exc_type:
            self.logger.error(f"Exception in FileProcessor: {exc_value}")
        else:
            self.logger.debug("FileProcessor exited cleanly.")
        return False