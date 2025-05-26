# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from typing import Callable, Optional

from snmp.snmp_v2c import Snmp_v2c
from snmp.snmp_compiled_oids import COMPILED_OIDS

class DocsIf31CmUsOfdmaChanEntry:

    index: int
    docsIf31CmUsOfdmaChanChannelId: int = 0
    docsIf31CmUsOfdmaChanConfigChangeCt: int = 0
    docsIf31CmUsOfdmaChanSubcarrierZeroFreq: int = 0
    docsIf31CmUsOfdmaChanFirstActiveSubcarrierNum: int = 0
    docsIf31CmUsOfdmaChanLastActiveSubcarrierNum: int = 0
    docsIf31CmUsOfdmaChanNumActiveSubcarriers: int = 0
    docsIf31CmUsOfdmaChanSubcarrierSpacing: int = 0
    docsIf31CmUsOfdmaChanCyclicPrefix: int = 0
    docsIf31CmUsOfdmaChanRollOffPeriod: int = 0
    docsIf31CmUsOfdmaChanNumSymbolsPerFrame: int = 0
    docsIf31CmUsOfdmaChanTxPower: float = 0.0
    docsIf31CmUsOfdmaChanPreEqEnabled: int = 0
    docsIf31CmStatusOfdmaUsT3Timeouts: int = 0
    docsIf31CmStatusOfdmaUsT4Timeouts: int = 0
    docsIf31CmStatusOfdmaUsRangingAborteds: int = 0
    docsIf31CmStatusOfdmaUsT3Exceededs: int = 0
    docsIf31CmStatusOfdmaUsIsMuted: bool = False
    docsIf31CmStatusOfdmaUsRangingStatus: str = "Unknown"

    def __init__(self, index: int, snmp: Snmp_v2c):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.index = index
        self.snmp = snmp

    async def start(self) -> bool:
        """
        Asynchronously populates the channel data from SNMP.

        Returns:
            bool: True if SNMP queries complete successfully (even if some values are None), False otherwise.
        """
        def tenthdBmV_to_float(value: str) -> Optional[float]:
            try:
                return float(value) / 10.0 if value else None
            except Exception:
                return None
            
        def convert_to_int(value: str) -> Optional[int]:
            try:
                return int(value)
            except Exception:
                return None

        fields: dict[str, tuple[str, Callable[[str], Optional[float]]]] = {
            # Existing fields
            "docsIf31CmUsOfdmaChanChannelId": ("docsIf31CmUsOfdmaChanChannelId", int),
            "docsIf31CmUsOfdmaChanConfigChangeCt": ("docsIf31CmUsOfdmaChanConfigChangeCt", int),
            "docsIf31CmUsOfdmaChanSubcarrierZeroFreq": ("docsIf31CmUsOfdmaChanSubcarrierZeroFreq", int),
            "docsIf31CmUsOfdmaChanFirstActiveSubcarrierNum": ("docsIf31CmUsOfdmaChanFirstActiveSubcarrierNum", int),
            "docsIf31CmUsOfdmaChanLastActiveSubcarrierNum": ("docsIf31CmUsOfdmaChanLastActiveSubcarrierNum", int),
            "docsIf31CmUsOfdmaChanNumActiveSubcarriers": ("docsIf31CmUsOfdmaChanNumActiveSubcarriers", int),
            "docsIf31CmUsOfdmaChanSubcarrierSpacing": ("docsIf31CmUsOfdmaChanSubcarrierSpacing", int),
            "docsIf31CmUsOfdmaChanCyclicPrefix": ("docsIf31CmUsOfdmaChanCyclicPrefix", int),
            "docsIf31CmUsOfdmaChanRollOffPeriod": ("docsIf31CmUsOfdmaChanRollOffPeriod", int),
            "docsIf31CmUsOfdmaChanNumSymbolsPerFrame": ("docsIf31CmUsOfdmaChanNumSymbolsPerFrame", int),
            "docsIf31CmUsOfdmaChanTxPower": ("docsIf31CmUsOfdmaChanTxPower", tenthdBmV_to_float),
            "docsIf31CmUsOfdmaChanPreEqEnabled": ("docsIf31CmUsOfdmaChanPreEqEnabled", Snmp_v2c.truth_value),
            "docsIf31CmStatusOfdmaUsT3Timeouts": ("docsIf31CmStatusOfdmaUsT3Timeouts", convert_to_int),
            "docsIf31CmStatusOfdmaUsT4Timeouts": ("docsIf31CmStatusOfdmaUsT4Timeouts", convert_to_int),
            "docsIf31CmStatusOfdmaUsRangingAborteds": ("docsIf31CmStatusOfdmaUsRangingAborteds", convert_to_int),
            "docsIf31CmStatusOfdmaUsT3Exceededs": ("docsIf31CmStatusOfdmaUsT3Exceededs", convert_to_int),
            "docsIf31CmStatusOfdmaUsIsMuted": ("docsIf31CmStatusOfdmaUsIsMuted", Snmp_v2c.truth_value),
            "docsIf31CmStatusOfdmaUsRangingStatus": ("docsIf31CmStatusOfdmaUsRangingStatus", str),
        }
                
        try:
            for attr, (oid_key, transform) in fields.items():
                try:
                    result = await self.snmp.get(f"{COMPILED_OIDS[oid_key]}.{self.index}")
                    value_list = Snmp_v2c.get_result_value(result)

                    if not value_list:
                        self.logger.warning(f"Invalid value returned for {oid_key}.{self.index}: {value_list}")
                        setattr(self, attr, None)
                        continue

                    value = transform(value_list)
                    setattr(self, attr, value)
                except Exception as e:
                    self.logger.warning(f"Failed to fetch or transform {attr} ({oid_key}): {e}")
                    setattr(self, attr, None)

            return True

        except Exception as e:
            self.logger.exception("Unexpected error during SNMP population")
            return False

    def to_dict(self) -> dict:
        """
        Converts the instance into a standardized dictionary format.

        Returns:
            dict: {
                "index": int,
                "channel_id": int,
                "entry": {field: value, ...}
            }
        """
        entry_data = {}
        channel_id = None

        for attr in self.__annotations__:
            if attr == "index":
                continue
            value = getattr(self, attr, None)
            if attr == "docsIf31CmUsOfdmaChanChannelId":
                channel_id = value
            entry_data[attr] = value

        return {
            "index": self.index,
            "channel_id": channel_id if channel_id is not None else 0,
            "entry": entry_data
        }
