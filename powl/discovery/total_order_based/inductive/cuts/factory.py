from typing import List, Optional, Tuple, Dict, Any, Type

from pm4py.algo.discovery.inductive.cuts.factory import S, T
from powl.discovery.total_order_based.inductive.cuts.concurrency import POWLConcurrencyCutUVCL, POWLConcurrencyCutDFG
from powl.discovery.total_order_based.inductive.cuts.loop import POWLLoopCutUVCL, POWLLoopCutDFG
from powl.discovery.total_order_based.inductive.cuts.sequence import POWLStrictSequenceCutUVCL, POWLStrictSequenceCutDFG
from powl.discovery.total_order_based.inductive.cuts.xor import POWLExclusiveChoiceCutUVCL, POWLExclusiveChoiceCutDFG
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructure, IMDataStructureUVCL, IMDataStructureDFG
from powl.objects.obj import POWL


class CutFactory:

    @classmethod
    def get_cuts(cls, obj: T, parameters: Optional[Dict[str, Any]] = None) -> List[Type[S]]:
        if type(obj) is IMDataStructureUVCL:
            return [POWLExclusiveChoiceCutUVCL, POWLStrictSequenceCutUVCL, POWLConcurrencyCutUVCL, POWLLoopCutUVCL]
        elif type(obj) is IMDataStructureDFG:
            return [POWLExclusiveChoiceCutDFG, POWLStrictSequenceCutDFG, POWLConcurrencyCutDFG, POWLLoopCutDFG]
        else:
            return []

    @classmethod
    def find_cut(cls, obj: IMDataStructure, parameters: Optional[Dict[str, Any]] = None) -> Optional[
        Tuple[POWL, List[T]]]:
        for c in CutFactory.get_cuts(obj):
            r = c.apply(obj, parameters)
            if r is not None:
                return r
        return None
