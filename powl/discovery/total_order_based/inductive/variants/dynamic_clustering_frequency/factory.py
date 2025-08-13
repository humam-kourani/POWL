from typing import List, Optional, Dict, Any, Tuple

from powl.discovery.total_order_based.inductive.cuts.concurrency import POWLConcurrencyCutDFG
from powl.discovery.total_order_based.inductive.cuts.factory import T, CutFactory
from powl.discovery.total_order_based.inductive.cuts.loop import POWLLoopCutUVCL, POWLLoopCutDFG
from powl.discovery.total_order_based.inductive.cuts.sequence import POWLStrictSequenceCutDFG
from powl.discovery.total_order_based.inductive.cuts.xor import POWLExclusiveChoiceCutUVCL, POWLExclusiveChoiceCutDFG
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructure, IMDataStructureUVCL, IMDataStructureDFG
from powl.discovery.total_order_based.inductive.variants.dynamic_clustering_frequency.dynamic_clustering_frequency_partial_order_cut import \
    DynamicClusteringFrequencyPartialOrderCutUVCL, DynamicClusteringFrequencyPartialOrderCutDFG
from powl.objects.obj import POWL
from pm4py.objects.dfg import util as dfu


class CutFactoryPOWLDynamicClusteringFrequency(CutFactory):

    @classmethod
    def get_cuts(cls, obj, parameters=None):
        if type(obj) is IMDataStructureUVCL:
            return [POWLExclusiveChoiceCutUVCL, POWLLoopCutUVCL, DynamicClusteringFrequencyPartialOrderCutUVCL]
        elif type(obj) is IMDataStructureDFG:
            return [POWLExclusiveChoiceCutDFG, POWLStrictSequenceCutDFG, POWLConcurrencyCutDFG, POWLLoopCutUVCL, DynamicClusteringFrequencyPartialOrderCutDFG]
        else:
            return []


    @classmethod
    def find_cut(cls, obj: IMDataStructure, parameters: Optional[Dict[str, Any]] = None) -> Optional[
            Tuple[POWL, List[T]]]:
        alphabet = sorted(dfu.get_vertices(obj.dfg), key=lambda g: g.__str__())
        if len(alphabet) < 2:
            return None
        for c in CutFactoryPOWLDynamicClusteringFrequency.get_cuts(obj):
            r = c.apply(obj, parameters)
            if r is not None:
                return r
        return None
