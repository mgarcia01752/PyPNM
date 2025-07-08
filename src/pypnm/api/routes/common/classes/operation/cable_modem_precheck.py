# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Module: common_endpoint_classes.schema.precheck

Defines a pre-check service for CableModem connectivity,
verifying reachability via ping, SNMP, and optional DOCSIS version compatibility.
"""

import logging
from typing import List, Tuple, Optional

from pypnm.api.routes.common.service.status_codes import ServiceStatusCode
from pypnm.docsis.cable_modem import CableModem
from pypnm.docsis.data_type.ClabsDocsisVersion import ClabsDocsisVersion
from pypnm.lib.inet import Inet
from pypnm.lib.mac_address import MacAddress


class CableModemServicePreCheck:
    """
    Performs preliminary connectivity checks against a DOCSIS Cable Modem.

    Supports:
    - Ping (ICMP) reachability
    - SNMP reachability
    - Optional DOCSIS version validation

    Can be initialized using:
    - A `CableModem` object
    - MAC address and IP address pair

    Example:
        ```python
        # Using CableModem instance
        cm = CableModem(mac_address=MacAddress("00:11:22:33:44:55"), inet=Inet("192.168.0.100"))
        precheck = CableModemServicePreCheck(cable_modem=cm)

        # Using MAC and IP directly
        precheck = CableModemServicePreCheck(
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.0.100",
            check_docsis_version=[ClabsDocsisVersion.DOCSIS_31]
        )

        status, msg = await precheck.run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            print(f"Pre-check failed: {msg}")
        ```
    """

    def __init__(
        self,
        cable_modem: Optional[CableModem] = None,
        mac_address: Optional[str] = None,
        ip_address: Optional[str] = None,
        check_docsis_version: Optional[List[ClabsDocsisVersion]] = None
    ) -> None:
        """
        Initialize the pre-check service.

        Args:
            cable_modem: An existing CableModem instance (optional).
            mac_address: The cable modem's MAC address (optional).
            ip_address: The cable modem's IP address (optional).
            check_docsis_version: Optional list of accepted DOCSIS versions.

        Raises:
            ValueError: If insufficient parameters are provided to construct the CableModem.
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

        self.check_docsis_version = check_docsis_version or []

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
