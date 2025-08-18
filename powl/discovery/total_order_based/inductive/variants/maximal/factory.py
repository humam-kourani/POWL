from typing import List, Optional, Dict, Any, Tuple, Type

from powl.discovery.total_order_based.inductive.cuts.concurrency import POWLConcurrencyCutUVCL
from powl.discovery.total_order_based.inductive.cuts.factory import S, T, CutFactory
from powl.discovery.total_order_based.inductive.cuts.loop import POWLLoopCutUVCL
from powl.discovery.total_order_based.inductive.cuts.sequence import POWLStrictSequenceCutUVCL
from powl.discovery.total_order_based.inductive.cuts.xor import POWLExclusiveChoiceCutUVCL
from powl.discovery.total_order_based.inductive.variants.maximal.maximal_partial_order_cut import \
    MaximalPartialOrderCutUVCL
from powl.objects.obj import POWL

from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL
from pm4py.objects.dfg import util as dfu


class CutFactoryPOWLMaximal(CutFactory):

    @classmethod
    def get_cuts(cls, obj: T, parameters: Optional[Dict[str, Any]] = None) -> List[Type[S]]:
        if type(obj) is IMDataStructureUVCL:
            return [POWLExclusiveChoiceCutUVCL, POWLStrictSequenceCutUVCL, POWLConcurrencyCutUVCL, POWLLoopCutUVCL,
                    MaximalPartialOrderCutUVCL]
        return list()

    @classmethod
    def find_cut(cls, obj: IMDataStructureUVCL, parameters: Optional[Dict[str, Any]] = None) -> Optional[
            Tuple[POWL, List[T]]]:

        alphabet = sorted(dfu.get_vertices(obj.dfg), key=lambda g: g.__str__())
        if len(alphabet) < 2:
            return None
        for c in CutFactoryPOWLMaximal.get_cuts(obj):
            r = c.apply(obj, parameters)
            if r is not None:
                return r
        return None
