# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import List
from pathlib import Path

from pysmi.reader.localfile import FileReader
from pysmi.writer.pyfile import PyFileWriter
from pysmi.parser.smi import SmiV2Parser
from pysmi.codegen.pysnmp import PySnmpCodeGen
from pysmi.compiler import MibCompiler
from pysmi import debug


class CompileMibs:
    """
    Compiles all SNMP MIB text files (.txt) in a source directory into
    Python modules for use with PySNMP.

    Attributes:
        source_dir (Path): Directory containing raw .txt MIB files.
        output_dir (Path): Directory to store compiled .py MIB files.
    """

    def __init__(self, source_dir: str, output_dir: str, verbose: bool = True, rebuild: bool = False) -> None:
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)

        # Set up logging
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
            #debug.set_logger(debug.Debug('all'))

        # Automatically compile MIBs during initialization
        self.compile_if_needed(rebuild)

    def _get_mib_names(self) -> List[str]:
        """
        Discover all MIB text files and extract MIB names (filenames without extension).

        Returns:
            List[str]: MIB names found in the source directory.
        """
        return [f.stem for f in self.source_dir.glob("*.txt")]

    def _compiled_mibs_exist(self) -> bool:
        """
        Check if the output directory already contains compiled .py MIB files.

        Returns:
            bool: True if any compiled MIBs exist, False otherwise.
        """
        return any(f.suffix == ".py" for f in self.output_dir.glob("*.py"))

    def compile_if_needed(self, rebuild: bool = False) -> None:
        """
        Compile MIBs only if no compiled MIBs exist in the output directory.

        Args:
            rebuild (bool): Whether to force recompile even if .py MIBs already exist.
        """
        if self._compiled_mibs_exist() and not rebuild:
            logging.info("✅ Compiled MIBs already exist. Skipping compilation.")
            return

        mib_names = self._get_mib_names()
        if not mib_names:
            logging.warning("No MIB files found to compile.")
            return

        compiler = MibCompiler(
            SmiV2Parser(),
            PySnmpCodeGen(),
            PyFileWriter(str(self.output_dir))
        )
        
        compiler.addSources(FileReader(str(self.source_dir)))
        compile_dict = compiler.compile(*mib_names, rebuild=rebuild)
        print(f'COMPILED-MIBS: {compile_dict}')
        print("✅ MIB compilation complete.")

    def get_compile_dir(self) -> Path:
        """
        Returns the path to the directory where compiled MIB Python files are stored.

        Returns:
            Path: The directory containing compiled MIB Python files.
        """
        return self.output_dir
