# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging

from pypnm.snmp.snmp_v2c import Snmp_v2c
from pypnm.snmp.compiled_oids import COMPILED_OIDS

class DocsPnmCmUsPreEqEntry:
    
    index:int
    docsPnmCmUsPreEqFileEnable: int = 0
    docsPnmCmUsPreEqAmpRipplePkToPk: int = 0
    docsPnmCmUsPreEqAmpRippleRms: int = 0
    docsPnmCmUsPreEqAmpSlope: int = 0
    docsPnmCmUsPreEqGrpDelayRipplePkToPk: int = 0
    docsPnmCmUsPreEqGrpDelayRippleRms: int = 0
    docsPnmCmUsPreEqPreEqCoAdjStatus: int = 0
    docsPnmCmUsPreEqMeasStatus: int = 0
    docsPnmCmUsPreEqLastUpdateFileName: str = ""
    docsPnmCmUsPreEqFileName: str = ""
    docsPnmCmUsPreEqAmpMean: int = 0
    docsPnmCmUsPreEqGrpDelaySlope: int = 0
    docsPnmCmUsPreEqGrpDelayMean: int = 0

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
        def tenthdBmV_to_float(value: str) -> float | None:
            try:
                return float(value) / 10.0
            except Exception:
                return None
        
        fields = {
            "docsPnmCmUsPreEqFileEnable": ("docsPnmCmUsPreEqFileEnable", int),
            "docsPnmCmUsPreEqAmpRipplePkToPk": ("docsPnmCmUsPreEqAmpRipplePkToPk", int),
            "docsPnmCmUsPreEqAmpRippleRms": ("docsPnmCmUsPreEqAmpRippleRms", int),
            "docsPnmCmUsPreEqAmpSlope": ("docsPnmCmUsPreEqAmpSlope", int),
            "docsPnmCmUsPreEqGrpDelayRipplePkToPk": ("docsPnmCmUsPreEqGrpDelayRipplePkToPk", int),
            "docsPnmCmUsPreEqGrpDelayRippleRms": ("docsPnmCmUsPreEqGrpDelayRippleRms", int),
            "docsPnmCmUsPreEqPreEqCoAdjStatus": ("docsPnmCmUsPreEqPreEqCoAdjStatus", int),
            "docsPnmCmUsPreEqMeasStatus": ("docsPnmCmUsPreEqMeasStatus", int),
            "docsPnmCmUsPreEqLastUpdateFileName": ("docsPnmCmUsPreEqLastUpdateFileName", str),
            "docsPnmCmUsPreEqFileName": ("docsPnmCmUsPreEqFileName", str),
            "docsPnmCmUsPreEqAmpMean": ("docsPnmCmUsPreEqAmpMean", int),
            "docsPnmCmUsPreEqGrpDelaySlope": ("docsPnmCmUsPreEqGrpDelaySlope", int),
            "docsPnmCmUsPreEqGrpDelayMean": ("docsPnmCmUsPreEqGrpDelayMean", int),
        }

        try:
            for attr, (oid_key, transform) in fields.items():
                try:
                    result = await self.snmp.get(f"{COMPILED_OIDS[oid_key]}.{self.index}")
                    value_list = Snmp_v2c.get_result_value(result)

                    if not value_list or not value_list:
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

    def to_dict(self, nested: bool = True) -> dict:
        """
        Converts the instance into a dictionary. If `nested` is True, returns {index: {field: value, ...}}.
        Otherwise, returns a flat dictionary with 'index' as a field.

        Args:
            nested (bool): Whether to return the dictionary in nested form. Defaults to False.

        Returns:
            dict: Dictionary representation of the instance.

        Raises:
            ValueError: If any required attribute is not populated.
        """
        data = {}
        for attr in self.__annotations__:
            value = getattr(self, attr, None)
            if value is None:
                raise ValueError(f"Attribute '{attr}' is not populated. Please call 'start' first.")
            data[attr] = value

        if nested:
            return {data["index"]: {key: value for key, value in data.items() if key != "index"}}

        return data
