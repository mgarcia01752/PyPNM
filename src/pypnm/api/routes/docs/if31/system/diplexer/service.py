# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging

from api.routes.docs.if31.system.diplexer.schemas import DiplexerConfigResult
from docsis.cable_modem import CableModem
from docsis.data_type import DocsIf31CmSystemCfgState
from lib.inet import Inet
from lib.mac_address import MacAddress

logger = logging.getLogger(__name__)


class DiplexerConfigService:
    """
    Service for retrieving DOCSIS 3.1 diplexer configuration state from a cable modem.

    The service queries the device over SNMP (via the underlying CableModem API)
    and returns a `DiplexerConfigResult`, converting all band-edge values
    from MHz to Hertz (Hz) using the `MHZ` multiplier.

    Constants:
        MHZ (int): Multiplier to convert MHz to Hz.
    """
    MHZ: int = 1_000_000

    @staticmethod
    async def fetch_diplexer_config(mac_address: str, ip_address: str) -> DiplexerConfigResult:
        """
        Fetch the DOCSIS 3.1 diplexer configuration.

        Args:
            mac_address (str): Normalized MAC address of the cable modem.
            ip_address (str): Normalized IP address of the cable modem.

        Returns:
            DiplexerConfigResult: Contains a `.diplexer` field with:
                - `diplexer_capability` (int)
                - `cfg_band_edge` (int, Hz)
                - `ds_lower_capability` (int)
                - `cfg_ds_lower_band_edge` (int, Hz)
                - `ds_upper_capability` (int)
                - `cfg_ds_upper_band_edge` (int, Hz)

        Raises:
            RuntimeError: If the diplexer configuration could not be retrieved.
        """
        logger.info(f"Fetching diplexer config for {mac_address}@{ip_address}")

        cm = CableModem(
            mac_address=MacAddress(mac_address),
            inet=Inet(ip_address))
        
        state: DocsIf31CmSystemCfgState = await cm.getDocsIf31CmSystemCfgDiplexState()
        if state is None:
            logger.error("Diplexer configuration returned None")
            raise RuntimeError("Failed to retrieve diplexer configuration")

        # Build the Pydantic result model
        return DiplexerConfigResult(
            diplexer={
                "diplexer_capability": state.docsIf31CmSystemCfgStateDiplexerCapability,
                "cfg_band_edge": state.docsIf31CmSystemCfgStateDiplexerCfgBandEdge * DiplexerConfigService.MHZ,
                "ds_lower_capability": state.docsIf31CmSystemCfgStateDiplexerDsLowerCapability,
                "cfg_ds_lower_band_edge": state.docsIf31CmSystemCfgStateDiplexerCfgDsLowerBandEdge * DiplexerConfigService.MHZ,
                "ds_upper_capability": state.docsIf31CmSystemCfgStateDiplexerDsUpperCapability,
                "cfg_ds_upper_band_edge": state.docsIf31CmSystemCfgStateDiplexerCfgDsUpperBandEdge * DiplexerConfigService.MHZ,
            }
        )
