from typing import Any, Dict
from pypnm.api.routes.common.classes.analysis.analysis import Analysis, List


class MultiAnalysis:
    
    def __init__(self):
        self._analysis_list:List[Analysis] = []
        pass
    
    def add(self, a:Analysis):
        self._analysis_list.append(a)

    def get_analyses(self) -> List[Analysis]:
        return self._analysis_list

    def length(self) -> int:
        return len(self._analysis_list)
    
    def to_model(self):
        pass

    def to_dict(self) -> Dict[str,Any]:
        return {}