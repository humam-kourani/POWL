from typing import List, Optional, Tuple, Dict, Any, Type

from pm4py.algo.discovery.inductive.cuts.factory import S, T
from powl.algo.discovery.inductive.cuts.concurrency import POWLConcurrencyCutUVCL
from powl.algo.discovery.inductive.cuts.loop import POWLLoopCutUVCL
from powl.algo.discovery.inductive.cuts.sequence import POWLStrictSequenceCutUVCL
from powl.algo.discovery.inductive.cuts.xor import POWLExclusiveChoiceCutUVCL
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructure, IMDataStructureUVCL
from powl.objects.obj import POWL


class CutFactory:

    @classmethod
    def get_cuts(cls, obj: T, parameters: Optional[Dict[str, Any]] = None) -> List[Type[S]]:
        if type(obj) is IMDataStructureUVCL:
            return [POWLExclusiveChoiceCutUVCL, POWLStrictSequenceCutUVCL, POWLConcurrencyCutUVCL, POWLLoopCutUVCL]
        return list()

    @classmethod
    def find_cut(cls, obj: IMDataStructure, parameters: Optional[Dict[str, Any]] = None) -> Optional[
        Tuple[POWL, List[T]]]:
        for c in CutFactory.get_cuts(obj):
            r = c.apply(obj, parameters)
            if r is not None:
                return r
        return None
