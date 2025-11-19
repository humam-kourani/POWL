from typing import Optional, List, Dict, Any

from pm4py.algo.discovery.inductive.dtypes.im_ds import (
    IMDataStructureUVCL,
)
from powl.discovery.total_order_based.inductive.variants.decision_graph.cyclic_dg_cut import CyclicDecisionGraphCutUVCL
from abc import ABC
from collections import Counter
from itertools import combinations
from typing import Any, Collection, Dict, List, Optional

from pm4py.algo.discovery.inductive.cuts import utils as cut_util

from pm4py.algo.discovery.inductive.cuts.abc import T
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL

from powl.discovery.total_order_based.inductive.variants.decision_graph.max_decision_graph_cut import (
    MaximalDecisionGraphCut,
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