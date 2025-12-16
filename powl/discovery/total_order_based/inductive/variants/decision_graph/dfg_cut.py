from typing import Any, Dict, List, Optional

from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL

from powl.discovery.total_order_based.inductive.variants.decision_graph.cyclic_dg_cut import (
    CyclicDecisionGraphCutUVCL,
)


class DFGCutUVCL(CyclicDecisionGraphCutUVCL):
    @classmethod
    def holds(
        cls,
        obj: IMDataStructureUVCL,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Optional[List[Any]]:
        alphabet = parameters["alphabet"]
        print("alphabet: ", alphabet)
        return [frozenset([a]) for a in alphabet]
