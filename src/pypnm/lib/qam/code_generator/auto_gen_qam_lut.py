# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from datetime import datetime
from pathlib import Path
import pprint
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel

from pypnm.lib.collector.complex import ComplexCollector
from pypnm.lib.file_processor import FileProcessor
from pypnm.lib.qam.code_generator.codeword_gen_lut import CodeWordLutGenerator
from pypnm.lib.types import Complex, ComplexArray, PathArray, PathLike
from pypnm.lib.qam.types import QamModulation

QamLutDict = Dict[str, Dict[Any, Any]]
Hard = List[Tuple[float, float]]

class GenerateQamLut:
    """
    High-level entry point to generate a QAM Lookup Table (LUT).

    This class wraps around :class:`QamLut` and handles:
    - Validating that the source QAM table directory exists.
    - Compiling QAM tables into a LUT.
    - Writing the resulting LUT Python file to the destination directory.

    Attributes
    ----------
    path_to_qam_table : Path
        Path to the directory containing raw QAM table `.txt` files.
    path_to_qam_lut : Path
        Path to the directory where the compiled LUT file will be written.
    logger : logging.Logger
        Logger instance for reporting progress and errors.
    """

    def __init__(
        self,
        src_qam_table: Path = Path("src/pypnm/support/qam-table"),
        dst_qam_lut: Path = Path("src/pypnm/lib/qam"),
    ) -> None:
        self.logger = logging.getLogger("GenerateQamLut")
        self.path_to_qam_table = src_qam_table
        self.path_to_qam_lut = dst_qam_lut
        self.build()

    def build(self) -> None:
        """
        Compile the QAM LUT from the specified QAM table files.

        The compiled LUT is written into a generated Python file
        (default: ``qam-lut.py``) inside the configured destination directory.
        """
        if not self.path_to_qam_table.exists():
            self.logger.error("QAM table path does not exist: %s", self.path_to_qam_table)
            return
        QamLut(src_qam_table=self.path_to_qam_table,
               dst_qam_lut=self.path_to_qam_lut).write()
        self.logger.info("QAM LUT generated successfully at %s", self.path_to_qam_lut)


class QamLutDb(BaseModel):
    """
    Pydantic model representation of a single QAM LUT entry.

    Attributes
    ----------
    symbol_count : int
        Number of modulation symbols in this LUT (equals the QAM order).
    hard : ComplexArray
        List of symbol points as (real, imag) coordinates.
    code_words : Dict[int, Complex]
        Dictionary mapping encoded codeword integers to their
        corresponding constellation coordinates.
    """
    symbol_count: int
    hard: ComplexArray
    code_words: Dict[int, Complex]


class QamLut:
    """
    Compiler for QAM Lookup Tables (LUTs).

    The QAM LUT is built from raw text-based constellation tables and
    converted into a Python dictionary structure suitable for runtime lookup.

    Workflow
    --------
    1. Parse all QAM table text files in the source directory.
    2. For each table:
       - Store points in a :class:`ComplexCollector`.
       - Determine QAM order (e.g., QAM_16, QAM_64).
    3. Assemble structured LUTs (symbol count, hard-decision coordinates,
       and placeholder codewords).
    4. Emit a Python file (``qam_lut.py``) with the LUT dictionary.

    Attributes
    ----------
    QAM_LUT_FNAME : str
        Default filename of the generated LUT (``qam-lut.py``).
    logger : logging.Logger
        Logger instance for reporting compilation steps and errors.
    _path_to_qam_table : PathLike
        Source directory containing QAM constellation definition files.
    _qam_cc : Dict[QamModulation, ComplexCollector]
        Mapping of QAM order to its collected constellation points.
    _qam_lut : QamLutDict
        Final LUT data structure keyed by QAM order name.
    _lut_path : Path
        Destination path of the generated LUT Python file.
    """

    QAM_LUT_FNAME = 'qam_lut.py'

    def __init__(self, 
                 src_qam_table: PathLike,
                 dst_qam_lut: PathLike):
        self.logger = logging.getLogger("QamLut")
        self._path_to_qam_table = src_qam_table
        self._qam_cc: Dict[QamModulation, ComplexCollector] = {}
        self._qam_lut: QamLutDict = {}
        self._lut_path: Path = Path(f'{dst_qam_lut}/{self.QAM_LUT_FNAME}')

        self._compile()

    def write(self):
        """
        Write the compiled QAM LUT to a Python file.

        The file contains a top-level dictionary called ``QAM_LUT``,
        which maps QAM order names to their LUT definitions.
        """
        fp = FileProcessor(self._lut_path)
        fp.write_file(self._lut_template())

    def _update_qam_lut(self, order: QamModulation, cc: ComplexCollector) -> None:
        """
        Update internal storage with a new QAM constellation collector.

        Parameters
        ----------
        order : QamModulation
            The modulation type (e.g., QAM_16, QAM_64).
        cc : ComplexCollector
            Collector containing all symbol points for this modulation order.
        """
        self._qam_cc[order] = cc

    def _compile(self):
        """
        Compile all QAM tables into the LUT.

        Steps
        -----
        - Locate valid QAM table files in the source directory.
        - Load each table into a :class:`ComplexCollector`.
        - Store results for subsequent LUT generation.
        """
        for f in self._get_qam_tables():
            self.logger.info(f'Loading {f} to compile QAM LUT')
            cc, qm = self._load_table(f)  # type: ignore
            self._update_qam_lut(qm, cc)

        self._build_qam_lut()

    def _load_table(self, path_to_qam_table: Path) -> Tuple[ComplexCollector, QamModulation]:
        """
        Load a single QAM table file.

        File Format
        -----------
        Each line must contain exactly two floating-point numbers
        representing the (real, imag) coordinates of one constellation symbol.

        Example (16QAM_table.txt)
        -------------------------
            3   3
            3   1
            1   3
            1   1
            ...

        Returns
        -------
        Tuple[ComplexCollector, QamModulation]
            A collector with all parsed symbols and the detected modulation type.
        """
        cc: ComplexCollector = ComplexCollector()

        with open(path_to_qam_table, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 2:
                    self.logger.warning(f"Malformed line in QAM table: {line.strip()}")
                    continue  # skip malformed lines
                r, i = map(float, parts)
                cc.add(r, i)

        qm = eval(f'QamModulation.QAM_{len(cc)}')
        self.logger.info(f'Loaded {qm} with {len(cc)} symbols from {path_to_qam_table}')
        return cc, qm

    def _get_qam_tables(self, skip_files: List[str] = ['ConstellationScalingFactors.txt']) -> PathArray:
        """
        Discover available QAM table files.

        Parameters
        ----------
        skip_files : List[str], optional
            Filenames to exclude from processing.

        Returns
        -------
        PathArray
            List of table file paths ready for compilation.
        """
        return [p for p in self._path_to_qam_table.glob("*.txt") # type: ignore
                if p.is_file() and p.name not in skip_files]  

    def _build_qam_lut(self) -> 'QamLutDict':
        """
        Construct the internal LUT dictionary.

        Output Structure
        ----------------
        {
            "<QAM_ORDER>": {
                "symbol_count": int,
                "hard": [(real, imag), ...],
                "code_words": {int: (real, imag), ...}
            },
            ...
        }

        Returns
        -------
        QamLutDict
            Dictionary representation of the compiled LUT.
        """
        for order, cc in self._qam_cc.items():
            self.logger.info(f'Compiling QAM LUT for {order}')

            cw_lut = CodeWordLutGenerator(cc.to_complex_array()).build().to_dict()

            qld = QamLutDb(symbol_count=len(cc),
                           hard=cc.to_complex_array(),
                           code_words=cw_lut)

            self._qam_lut[order.name] = qld.model_dump()

        return self._qam_lut

    def _lut_template(self) -> str:
        """
        Render the Python source template for the LUT file.

        The file defines a global variable ``QAM_SYMBOL_CODEWORD_LUT`` with
        the compiled dictionary, pretty-printed for readability.

        Returns
        -------
        str
            The full source text of the LUT file.
        """
        formatted = pprint.pformat(self._qam_lut, indent=2, width=100, sort_dicts=True)
        lut =  f'# Do not modify manually. AutoGenerated: {datetime.now()}\n'
        lut += f'QAM_SYMBOL_CODEWORD_LUT = {formatted}\n'
        return lut

