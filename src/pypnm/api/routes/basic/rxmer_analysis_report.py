# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Iterable, List, Tuple, cast

from pydantic import BaseModel, ConfigDict, Field

from pypnm.api.routes.basic.abstract.analysis_report import AnalysisReport
from pypnm.api.routes.basic.abstract.base_models.common_analysis import CommonAnalysis
from pypnm.api.routes.common.classes.analysis.analysis import Analysis
from pypnm.lib.csv.manager import CSVManager
from pypnm.lib.matplot.manager import MatplotManager, PlotConfig
from pypnm.lib.numeric_scaler import NumericScaler
from pypnm.lib.signal.linear_regression import LinearRegression1D

class RxMerAnalysisParameters(BaseModel):
    """
    Parameters that augment RxMER analysis output.

    Fields:
      - shannon_limit_db: Optional per-subcarrier Shannon/SNR limit (dB).
      - regression_basis : Whether linear regression uses raw_x (frequency) or index 0..N-1.
    """
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    shannon_limit_db: List[float] = Field(default_factory=list, description="Shannon/SNR limit per subcarrier (dB)")
    regression_line: List[float] = Field(..., description="The regression line over subcarrier")

class RxMerAnalysis(CommonAnalysis):
    """
    Analysis view over RxMER data (extends CommonAnalysis).

    Adds:
      - parameters: RxMerAnalysisParameters (shannon bounds + regression basis)
      - linear_regression (computed): [slope, intercept, r2]
    """
    parameters: RxMerAnalysisParameters = Field(...,description="RxMER analysis parameters and limits.")

class RxMerAnalysisReport(AnalysisReport):
    """
    Concrete report builder for RxMER measurements.

    """

    INVALID_CHANNEL_ID:int = -1

    def __init__(self, analysis: Analysis):
        super().__init__(analysis)
        self.logger = logging.getLogger("RxMerAnalysisReport")

        self._results: Dict[int, RxMerAnalysis] = {}
        self._process()

    def create_csv(self, **kwargs) -> List[CSVManager]:
        """
        Create and write per-channel RxMER CSV files.

        Returns
        -------
        List[CSVManager]
            One CSVManager per channel successfully produced.

        Notes
        -----
        - This function assumes that ``CSVManager`` supports:
            * set_header(List[str])
            * insert_row(List[Any])
            * set_path_fname(PathLike)
        - ``_compile_analysis_data()`` guarantees aligned lengths and finite floats.

        Examples
        --------
        >>> csvs = self.create_csv(include_channel_id=True, include_basis=True)
        >>> for mgr in csvs:
        ...     print(mgr.filepath)  # or equivalent accessor
        """

        csv_mgr_list: List[CSVManager] = []

        compiled = self._compile_analysis_data()
        if not compiled:
            self.logger.info("No analysis data available; no CSVs created.")
            return csv_mgr_list

        for channel_id, segments in compiled.items():
            
            if not segments:
                self.logger.info("No segments for channel %s; skipping.", channel_id)
                continue

            try:
                csv_mgr: CSVManager = self.get_csv_manager()

                csv_mgr.set_header(['channel_id', 'raw_x', 'raw_y', 'shannon_limit_db', 'regression_line'])

                # Write rows: concatenate all segments for this channel 
                total_rows = 0
                for seg_idx, (freq, mer_amplitude, shannon, regress_line) in enumerate(segments):

                    for rx, ry, s, rl in zip(freq, mer_amplitude, shannon, regress_line):
                        row = ([channel_id]) + [rx, ry, s, rl]
                        csv_mgr.insert_row(row)
                        total_rows += 1

                csv_fname = self.create_csv_fname(tags=[str(channel_id)])
                csv_mgr.set_path_fname(csv_fname)

                self.logger.info(
                    "CSV created for channel %s: %s (rows=%d, segments=%d)", channel_id, csv_fname, total_rows, len(segments))
                
                csv_mgr_list.append(csv_mgr)

            except Exception as e:
                self.logger.exception("Failed to create CSV for channel %s: %s", channel_id, e)
                continue

        return csv_mgr_list

    def create_matplot(self, **kwargs) -> List[MatplotManager]:
        """
        Stub for Matplotlib plot creation (left to concrete plotting lib).
        Intended to iterate self.results and generate figures.
        """
        matplot_mgr:List[MatplotManager] = []

        compiled = self._compile_analysis_data()
        if not compiled:
            self.logger.info("No analysis data available; no CSVs created.")
            return matplot_mgr

        for channel_id, segments in compiled.items():
            
            if not segments:
                self.logger.info("No segments for channel %s; skipping.", channel_id)
                continue
            
            for seg_idx, (freq, mer_amplitude, shannon, regression_line) in enumerate(segments):

                freq = cast(List[float], freq)
                mer_amplitude = cast(List[float], mer_amplitude)
                shannon = cast(List[float], shannon)
                regression_line = cast(List[float], regression_line)

                png_fname = self.create_png_fname(tags=[f"{channel_id}"])
                self.logger.info(f"Creating MatPlot ({seg_idx}): {png_fname} for channel: {channel_id}")

                freq , _ = NumericScaler().to_prefix(values=freq, target="k")

                config = PlotConfig(x=freq, y=mer_amplitude, 
                                    xlabel="Frequency (Hz)", ylabel="Magnitude (dB)",
                                    title=f"RxMER OFDM Channel {channel_id}",)
                mat_mgr_tmp = MatplotManager(default_cfg=config)
                mat_mgr_tmp.plot_line(filename=png_fname)

                matplot_mgr.append(mat_mgr_tmp)
        
        return matplot_mgr

    def _process(self) -> None:
        """
        Normalize raw measurement dicts into validated RxMerAnalysis models.

        Expects each item like:
            {
              "channel_id": int,
              "carrier_values": {
                "frequency": List[int|float],
                "magnitude": List[int|float]
              },
              "modulation_statistics": {
                "snr_db_limit": List[float]
              }
            }
        """
        data_list: List[Dict[str, Any]] = self.get_analysis_data() or []

        for idx, data in enumerate(data_list):

            try:
                # Defensive extraction with clear fallbacks
                channel_id: int = int(data.get("channel_id", self.INVALID_CHANNEL_ID))
                cv: Dict[str, Any] = data.get("carrier_values") or {}
                ms: Dict[str, Any] = data.get("modulation_statistics") or {}

                raw_x: List[float] = list(cv.get("frequency") or [])
                raw_y: List[float] = list(cv.get("magnitude") or [])
                shannon_limit_db: List[float] = list(ms.get("snr_db_limit") or [])

                # Parameters: default to regression vs index (0..N-1).
                params = RxMerAnalysisParameters(
                    shannon_limit_db=shannon_limit_db,
                    regression_line=LinearRegression1D(raw_y).regression_line())        # type: ignore

                # Build validated model (CommonAnalysis ensures x/y length & finiteness)
                model = RxMerAnalysis(channel_id=channel_id, 
                                      raw_x=raw_x, raw_y=raw_y,
                                      parameters=params,)
                
                self.add_common_analysis_model(channel_id, model)

            except Exception as exc:
                self.logger.exception(f"Failed to process RxMER item {idx}: reason: {exc}")
                continue

    def _compile_analysis_data(self) -> Dict[int, List[Tuple[List[float], List[float], List[float], List[float]]]]:
        """
        Compile, validate, and normalize RxMER analysis data for downstream use.

        Returns:
            Dict[int, List[Tuple[List[float], List[float], List[float], List[float]]]]:
                Mapping of channel_id -> list of (freq, mer_db, shannon_db, regression_basis)
                where every list is the same length per tuple and all values are finite floats.

        Behavior:
            - Requires presence of model.parameters and core arrays: raw_x, raw_y, parameters.shannon_limit_db.
            - Lengths: len(raw_x) == len(raw_y) == len(shannon_limit_db) must hold.
            - parameters.regression_basis:
                * None or empty    → filled with zeros (len == len(raw_x))
                * length == 1      → broadcast scalar to len(raw_x)
                * length == len(x) → accepted as-is
                * otherwise        → entry skipped (warning logged)
            - Any non-finite (NaN/Inf) value in a series causes the entry to be skipped.
            - One bad model does not abort the batch.

        Logging:
            - error: missing parameters/core data, invalid channel_id, non-finite values
            - warning: length mismatches (core or basis)
            - info: regression_basis auto-filled or broadcast
        """

        def _to_float_list(seq: Iterable[Any], name: str) -> List[float]:
            out: List[float] = []
            try:
                for v in seq:
                    fv = float(v)
                    if not math.isfinite(fv):
                        self.logger.error("Non-finite value in %s: %r", name, v)
                        raise ValueError(f"non-finite {name}")
                    out.append(fv)
            except Exception as e:
                raise ValueError(f"Failed to coerce {name} to floats: {e}") from e
            return out

        data: Dict[int, List[Tuple[List[float], List[float], List[float], List[float]]]] = {}

        for common_analysis_model in self.get_common_analysis_model():
            try:
                model = cast(RxMerAnalysis, common_analysis_model)

                # Presence checks
                params = getattr(model, "parameters", None)
                if params is None:
                    self.logger.error("Missing parameters for channel %s", getattr(model, "channel_id", "<?>"))
                    continue

                freq_raw     = getattr(model, "raw_x", None)
                mer_raw      = getattr(model, "raw_y", None)
                shan_raw     = getattr(params, "shannon_limit_db", None)
                regress_line_raw    = getattr(params, "regression_line", None)

                missing = [n for n, v in [
                    ("raw_x", freq_raw),
                    ("raw_y", mer_raw),
                    ("parameters.shannon_limit_db", shan_raw),
                ] if v is None]
                if missing:
                    self.logger.error("Required data missing for channel %s: %s",
                                    getattr(model, "channel_id", "<?>"), ", ".join(missing))
                    continue

                # Coerce and validate core vectors
                x    = _to_float_list(freq_raw,  "raw_x")
                y    = _to_float_list(mer_raw,   "raw_y")
                shan = _to_float_list(shan_raw,  "parameters.shannon_limit_db")

                if not (len(x) == len(y) == len(shan)):
                    self.logger.warning("Length mismatch for channel %s: raw_x=%d raw_y=%d shannon=%d",
                                        getattr(model, "channel_id", "<?>"), len(x), len(y), len(shan))
                    continue

                # Normalize regression_basis
                if regress_line_raw is None:
                    basis = [0.0] * len(x)
                    self.logger.info("regression_basis missing for channel %s; filling zeros (n=%d)",
                                    getattr(model, "channel_id", "<?>"), len(x))
                else:
                    try:
                        basis_list = _to_float_list(regress_line_raw, "parameters.regression_line")
                    except ValueError:
                        # Treat uncoercible basis as missing → zeros
                        basis_list = []
                    if len(basis_list) == 0:
                        basis = [0.0] * len(x)
                        self.logger.info("regression_basis empty for channel %s; filling zeros (n=%d)",
                                        getattr(model, "channel_id", "<?>"), len(x))
                    elif len(basis_list) == 1:
                        basis = [basis_list[0]] * len(x)
                        self.logger.info("Broadcasting regression_basis scalar for channel %s to length %d",
                                        getattr(model, "channel_id", "<?>"), len(x))
                    elif len(basis_list) == len(x):
                        basis = basis_list
                    else:
                        self.logger.warning("Length mismatch for regression_basis on channel %s: basis=%d raw_x=%d",
                                            getattr(model, "channel_id", "<?>"), len(basis_list), len(x))
                        continue

                # Normalize channel id
                try:
                    chan_id = int(getattr(model, "channel_id"))
                except Exception:
                    self.logger.error("Invalid channel_id: %r", getattr(model, "channel_id", None))
                    continue

                data.setdefault(chan_id, []).append((x, y, shan, basis))

            except ValueError as e:
                self.logger.error("Skipping channel %s due to data error: %s",
                                getattr(common_analysis_model, "channel_id", "<?>"), e)
                continue
            except Exception as e:
                self.logger.exception("Unexpected error compiling data for channel %s: %s",
                                    getattr(common_analysis_model, "channel_id", "<?>"), e)
                continue

        return data
