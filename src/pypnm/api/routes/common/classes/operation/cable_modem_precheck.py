# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Module: common_endpoint_classes.schema.precheck

Defines a pre-check service for CableModem connectivity,
verifying reachability via ping, SNMP, and optional DOCSIS version compatibility.
"""

import logging
from typing import Iterable, List, Tuple, Optional

from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.ClabsDocsisVersion import ClabsDocsisVersion
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class CableModemServicePreCheck:
    """
    Performs preliminary connectivity and validation checks against a DOCSIS Cable Modem.

    This service supports:
    - ICMP ping reachability check
    - SNMP reachability check
    - Optional DOCSIS version compatibility validation
    - Optional validation that OFDM (DS) and/or OFDMA (US) channels exist

    Initialization methods:
    - Provide a pre-constructed `CableModem` object
    - Or specify a `mac_address` and `ip_address` pair

    Parameters allow flexible diagnostics for network readiness prior to performing
    PNM measurements or control operations.
    """

    def __init__(
        self,
        cable_modem: Optional[CableModem] = None,
        mac_address: Optional[str] = None,
        ip_address: Optional[str] = None,
        check_docsis_version: Optional[List[ClabsDocsisVersion]] = None,
        validate_ofdm_exist: Optional[bool] = False,
        validate_ofdma_exist: Optional[bool] = False
    ) -> None:
        """
        Initialize the pre-check service.

        Args:
            cable_modem: An existing CableModem instance to use for queries (optional).
            mac_address: MAC address of the target cable modem (optional).
            ip_address: IP address of the target cable modem (optional).
            check_docsis_version: Optional list of acceptable DOCSIS versions to validate.
            validate_ofdm_exist: If True, verifies that one or more downstream OFDM channels exist.
            validate_ofdma_exist: If True, verifies that one or more upstream OFDMA channels exist.

        Raises:
            ValueError: If neither a `CableModem` object nor both `mac_address` and `ip_address` are provided.
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        if cable_modem:
            self.cm = cable_modem
        elif mac_address and ip_address:
            self.cm = CableModem(
                mac_address=MacAddress(mac_address),
                inet=Inet(ip_address)
            )
        else:
            raise ValueError("Must provide either `cable_modem` or both `mac_address` and `ip_address`.")

        if check_docsis_version:
            if not isinstance(check_docsis_version, Iterable) or isinstance(check_docsis_version, (str, bytes)):
                check_docsis_version = [check_docsis_version]
            self.check_docsis_version = list(check_docsis_version)
        else:
            self.check_docsis_version = []
            
        self.validate_ofdma_exist = validate_ofdma_exist
        self.validate_ofdm_exist = validate_ofdm_exist

    async def run_precheck(self) -> Tuple[ServiceStatusCode, str]:
        """
        Run full pre-check routine:
          1. Ping modem
          2. Perform SNMP check
          3. Validate DOCSIS version (optional)

        Returns:
            Tuple[ServiceStatusCode, str]: Status and message.
        """
        self.logger.debug(f"Starting pre-check for CableModem: {self.cm}")

        status = self.ping_reachable()
        if status != ServiceStatusCode.SUCCESS:
            msg = f"Ping check failed: {status}"
            self.logger.error(msg)
            return status, msg

        status = await self.snmp_reachable()
        if status != ServiceStatusCode.SUCCESS:
            msg = f"SNMP check failed: {status}"
            self.logger.error(msg)
            return status, msg

        if self.check_docsis_version:
            status, msg = await self.validate_docsis_version()
            if status != ServiceStatusCode.SUCCESS:
                return status, msg

        if self.validate_ofdm_exist:
            status, msg = await self.validate_ofdm_channel_exist()
            if status != ServiceStatusCode.SUCCESS:
                return status, msg  

        if self.validate_ofdma_exist:
            status, msg = await self.validate_ofdma_channel_exist()
            if status != ServiceStatusCode.SUCCESS:
                return status, msg            
        
        msg = "Pre-check successful: CableModem reachable via ping and SNMP"
        self.logger.info(msg)
        return ServiceStatusCode.SUCCESS, msg

    def ping_reachable(self) -> ServiceStatusCode:
        """
        Perform an ICMP ping test.

        Returns:
            SUCCESS if reachable, else PING_FAILED.
        """
        try:
            if self.cm.is_ping_reachable():
                self.logger.debug("Ping check passed")
                return ServiceStatusCode.SUCCESS
            self.logger.debug("Ping check failed")
            return ServiceStatusCode.PING_FAILED
        except Exception as e:
            self.logger.error(f"Ping check exception: {e}", exc_info=True)
            return ServiceStatusCode.PING_FAILED

    async def snmp_reachable(self) -> ServiceStatusCode:
        """
        Perform SNMP reachability check.

        Returns:
            SUCCESS if SNMP response received, else UNREACHABLE_SNMP.
        """
        try:
            if await self.cm.is_snmp_reachable():
                self.logger.debug("SNMP check passed")
                return ServiceStatusCode.SUCCESS
            self.logger.debug("SNMP check failed")
            return ServiceStatusCode.UNREACHABLE_SNMP
        except Exception as e:
            self.logger.error(f"SNMP check exception: {e}", exc_info=True)
            return ServiceStatusCode.UNREACHABLE_SNMP

    async def validate_docsis_version(self) -> Tuple[ServiceStatusCode, str]:
        """
        Check if the modem's DOCSIS version is in the accepted list.

        Returns:
            SUCCESS if version is allowed, else INVALID_DOCSIS_VERSION.
        """
        try:
            base_cap = await self.cm.getDocsisBaseCapability()
            if base_cap not in self.check_docsis_version:
                msg = f"Invalid DOCSIS Version: {base_cap.name}"
                self.logger.error(msg)
                return ServiceStatusCode.INVALID_DOCSIS_VERSION, msg

            self.logger.debug(f"DOCSIS version check passed: {base_cap.name}")
            return ServiceStatusCode.SUCCESS, "Valid DOCSIS version"

        except Exception as e:
            msg = f"Error checking DOCSIS version: {e}"
            self.logger.error(msg, exc_info=True)
            return ServiceStatusCode.INVALID_DOCSIS_VERSION, msg

    async def validate_ofdm_channel_exist(self) -> Tuple[ServiceStatusCode, str]:
        """
        Checks whether any OFDM downstream channels are present on the cable modem.

        This method queries the cable modem for the DOCSIS 3.1 upstream OFDMA channel
        index stack. If no indices are found, it returns a failure status.

        Returns:
            Tuple[ServiceStatusCode, str]: A tuple containing the status code and an explanatory message.
                - ServiceStatusCode.SUCCESS if channels are found
                - ServiceStatusCode.NO_OFDMA_CHANNELS_EXIST if no channels are detected
        """
        idx_chan_stack = await self.cm.getDocsIf31CmDsOfdmChannelIdIndexStack()

        if not idx_chan_stack:
            msg = "No OFDM channels found on the cable modem."
            return ServiceStatusCode.NO_OFDMA_CHANNELS_EXIST, msg

        return ServiceStatusCode.SUCCESS, "OFDMA upstream channels detected."

    async def validate_ofdma_channel_exist(self) -> Tuple[ServiceStatusCode, str]:
        """
        Checks whether any OFDMA upstream channels are present on the cable modem.

        This method queries the cable modem for the DOCSIS 3.1 upstream OFDMA channel
        index stack. If no indices are found, it returns a failure status.

        Returns:
            Tuple[ServiceStatusCode, str]: A tuple containing the status code and an explanatory message.
                - ServiceStatusCode.SUCCESS if channels are found
                - ServiceStatusCode.NO_OFDMA_CHANNELS_EXIST if no channels are detected
        """
        idx_chan_stack = await self.cm.getDocsIf31CmUsOfdmaChannelIdIndexStack()

        if not idx_chan_stack:
            msg = "No OFDMA channels found on the cable modem."
            return ServiceStatusCode.NO_OFDMA_CHANNELS_EXIST, msg

        return ServiceStatusCode.SUCCESS, "OFDMA upstream channels detected."