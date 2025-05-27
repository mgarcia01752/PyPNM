# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Maurice Garcia

import logging
from pypnm.snmp.snmp_v2c import Snmp_v2c
from pypnm.snmp.snmp_compiled_oids import COMPILED_OIDS


class DocsIfDownstreamChannel:
    """
    Represents DOCSIS downstream channel configuration and signal metrics retrieved via SNMP.

    Attributes:
        index (int): Channel index used for SNMP OID addressing.
        snmp (Snmp_v2c): SNMP client used to fetch values.
    """

    index: int
    docsIfDownChannelId: int
    docsIfDownChannelFrequency: int
    docsIfDownChannelWidth: int
    docsIfDownChannelModulation: int
    docsIfDownChannelInterleave: int
    docsIfDownChannelPower: float
    docsIfSigQUnerroreds: int
    docsIfSigQCorrecteds: int
    docsIfSigQUncorrectables: int
    docsIfSigQMicroreflections: int
    docsIfSigQExtUnerroreds: int
    docsIfSigQExtCorrecteds: int
    docsIfSigQExtUncorrectables: int
    docsIf3SignalQualityExtRxMER: float

    def __init__(self, index: int, snmp: Snmp_v2c):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.index = index
        self.snmp = snmp

    async def start(self) -> bool:
        """
        Asynchronously populates the channel data from SNMP.

        Returns:
            bool: True if SNMP queries complete successfully, False otherwise.
        """
        def tenthdBmV_to_float(value: str) -> float | None:
            try:
                return float(value) / 10.0
            except Exception:
                return None

        def to_float(value: str) -> float | None:
            try:
                return float(value)
            except Exception:
                return None

        fields = {
            "docsIfDownChannelId": ("docsIfDownChannelId", int),
            "docsIfDownChannelFrequency": ("docsIfDownChannelFrequency", int),
            "docsIfDownChannelWidth": ("docsIfDownChannelWidth", int),
            "docsIfDownChannelModulation": ("docsIfDownChannelModulation", int),
            "docsIfDownChannelInterleave": ("docsIfDownChannelInterleave", int),
            "docsIfDownChannelPower": ("docsIfDownChannelPower", tenthdBmV_to_float),
            "docsIfSigQUnerroreds": ("docsIfSigQUnerroreds", int),
            "docsIfSigQCorrecteds": ("docsIfSigQCorrecteds", int),
            "docsIfSigQUncorrectables": ("docsIfSigQUncorrectables", int),
            "docsIfSigQMicroreflections": ("docsIfSigQMicroreflections", int),
            "docsIfSigQExtUnerroreds": ("docsIfSigQExtUnerroreds", int),
            "docsIfSigQExtCorrecteds": ("docsIfSigQExtCorrecteds", int),
            "docsIfSigQExtUncorrectables": ("docsIfSigQExtUncorrectables", int),
            "docsIf3SignalQualityExtRxMER": ("docsIf3SignalQualityExtRxMER", to_float),
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
            if attr == "docsIfDownChannelId":
                channel_id = value
            entry_data[attr] = value

        return {
            "index": self.index,
            "channel_id": channel_id if channel_id is not None else 0,
            "entry": entry_data
        }
