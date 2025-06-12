from typing import List, Optional, Dict, Any, Tuple, Type

from powl.algo.discovery.inductive.cuts.concurrency import POWLConcurrencyCutUVCL
from powl.algo.discovery.inductive.cuts.factory import S, T, CutFactory
from powl.algo.discovery.inductive.cuts.loop import POWLLoopCutUVCL
from powl.algo.discovery.inductive.cuts.sequence import POWLStrictSequenceCutUVCL
from powl.algo.discovery.inductive.cuts.xor import POWLExclusiveChoiceCutUVCL
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL
from powl.algo.discovery.inductive.variants.brute_force.bf_partial_order_cut import BruteForcePartialOrderCutUVCL
from powl.objects.obj import POWL


class CutFactoryPOWLBruteForce(CutFactory):

    @classmethod
    def get_cuts(cls, obj: T, parameters: Optional[Dict[str, Any]] = None) -> List[Type[S]]:
        if type(obj) is IMDataStructureUVCL:
            return [POWLExclusiveChoiceCutUVCL, POWLStrictSequenceCutUVCL, POWLConcurrencyCutUVCL, POWLLoopCutUVCL,
                    BruteForcePartialOrderCutUVCL]
        return list()

    @classmethod
    def find_cut(cls, obj: IMDataStructureUVCL, parameters: Optional[Dict[str, Any]] = None) -> Optional[
            Tuple[POWL, List[T]]]:
        for c in CutFactoryPOWLBruteForce.get_cuts(obj):
            r = c.apply(obj, parameters)
            if r is not None:
                return r
        return None
