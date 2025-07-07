import logging

from pypnm.snmp.snmp_v2c import Snmp_v2c


class DocsFddCmFddSystemCfgState:
    '''
    docsFddCmFddSystemCfgState": "1.3.6.1.4.1.4491.2.1.39.0.1",
    '''
    
    docsFddCmFddSystemCfgStateDiplexerDsLowerBandEdgeCfg:int = 0
    docsFddCmFddSystemCfgStateDiplexerDsUpperBandEdgeCfg:int = 0 
    docsFddCmFddSystemCfgStateDiplexerUsUpperBandEdgeCfg:int = 0
    
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
        fields = {
            "docsFddCmFddSystemCfgStateDiplexerDsLowerBandEdgeCfg": ("docsFddCmFddSystemCfgStateDiplexerDsLowerBandEdgeCfg", int),
            "docsFddCmFddSystemCfgStateDiplexerDsUpperBandEdgeCfg": ("docsFddCmFddSystemCfgStateDiplexerDsUpperBandEdgeCfg", int),
            "docsFddCmFddSystemCfgStateDiplexerUsUpperBandEdgeCfg": ("docsFddCmFddSystemCfgStateDiplexerUsUpperBandEdgeCfg", int),
        }
        
        