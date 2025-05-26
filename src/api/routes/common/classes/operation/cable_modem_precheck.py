# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

"""
Module: common_endpoint_classes.schema.precheck

Defines a pre-check service for CableModem connectivity, verifying reachability via ping and SNMP.
"""
import logging
from typing import Tuple, Optional

from api.routes.common.service.status_codes import ServiceStatusCode
from docsis.cable_modem import CableModem
from lib.inet import Inet
from lib.mac_address import MacAddress


class CableModemServicePreCheck:
    """
    Performs preliminary connectivity checks against a CableModem.

    Can be initialized with either:
      - a pre-built CableModem instance, or
      - MAC address + IP address (it will construct the CableModem).

    Attributes:
        cm (CableModem): The cable modem under test.
        logger (logging.Logger): Logger for status messages.

    Usage:
        ```python
        # Using existing CableModem
        cm = CableModem(mac_address=MacAddress("00:11:22:33:44:55"), inet=Inet("192.168.1.100"))
        precheck = CableModemServicePreCheck(cm=cm)

        # Or by passing MAC+IP directly
        precheck = CableModemServicePreCheck(
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.100"
        )
        status, message = precheck.run_precheck()
        if status != ServiceStatusCode.SUCCESS:
            print(f"Pre-check failed ({status}): {message}")
        ```
    """

    def __init__(
        self,
        cable_modem: Optional[CableModem] = None,
        mac_address: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Initialize the pre-check service.

        Args:
            cm (CableModem, optional): Pre-built CableModem instance.
            mac_address (str, optional): MAC address if not passing `cm`.
            ip_address (str, optional): IP address if not passing `cm`.

        Raises:
            ValueError: If neither `cm` nor both `mac_address` and `ip_address` are provided.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if cable_modem:
            self.cm = cable_modem
        else:
            if not (mac_address and ip_address):
                raise ValueError(
                    "Must provide either `cm` or both `mac_address` and `ip_address`."
                )
            # Construct CableModem internally
            self.cm = CableModem(
                mac_address=MacAddress(mac_address),
                inet=Inet(ip_address)
            )

    def run_precheck(self) -> Tuple[ServiceStatusCode, str]:
        """
        Execute a sequence of connectivity tests:
          1. ICMP ping reachability
          2. SNMP reachability

        Returns:
            Tuple[ServiceStatusCode, str]:
                - First non-SUCCESS status, or SUCCESS if all tests pass.
                - Descriptive message of result or failure reason.
        """
        self.logger.debug(f"Starting pre-check for CableModem: {self.cm}")

        status = self.ping_reachable()
        if status != ServiceStatusCode.SUCCESS:
            msg = f"Ping check failed: {status}"
            self.logger.error(msg)
            return status, msg

        status = self.snmp_reachable()
        if status != ServiceStatusCode.SUCCESS:
            msg = f"SNMP check failed: {status}"
            self.logger.error(msg)
            return status, msg

        msg = "Pre-check successful: CableModem reachable via ping and SNMP"
        self.logger.info(msg)
        return ServiceStatusCode.SUCCESS, msg

    def ping_reachable(self) -> ServiceStatusCode:
        """
        Perform an ICMP ping check against the cable modem.

        Returns:
            ServiceStatusCode: SUCCESS if reachable, PING_FAILED otherwise.
        """
        try:
            if self.cm.is_ping_reachable():
                self.logger.debug("Ping reachable succeeded")
                return ServiceStatusCode.SUCCESS
            self.logger.debug("Ping reachable failed")
            return ServiceStatusCode.PING_FAILED
        except Exception as e:
            self.logger.error(f"Error during ping check: {e}", exc_info=True)
            return ServiceStatusCode.PING_FAILED

    def snmp_reachable(self) -> ServiceStatusCode:
        """
        Perform an SNMP reachability check against the cable modem.

        Returns:
            ServiceStatusCode: SUCCESS if SNMP queries succeed, UNREACHABLE_SNMP otherwise.
        """
        try:
            if self.cm.is_snmp_reachable():
                self.logger.debug("SNMP reachable succeeded")
                return ServiceStatusCode.SUCCESS
            self.logger.debug("SNMP reachable failed")
            return ServiceStatusCode.UNREACHABLE_SNMP
        except Exception as e:
            self.logger.error(f"Error during SNMP check: {e}", exc_info=True)
            return ServiceStatusCode.UNREACHABLE_SNMP
