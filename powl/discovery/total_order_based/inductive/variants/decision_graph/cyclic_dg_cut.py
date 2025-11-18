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


class CyclicDecisionGraphCut(MaximalDecisionGraphCut[T], ABC):
    @classmethod
    def holds(
        cls, obj: T, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Any]]:

        alphabet = parameters["alphabet"]
        dfg = obj.dfg

        groups = [frozenset([a]) for a in alphabet]

        for a, b in combinations(alphabet, 2):
            if (a, b) in dfg.graph and (b, a) in dfg.graph:
                groups = cut_util.merge_groups_based_on_activities(a, b, groups)

        if len(groups) < 2:
            return None

        return groups


class CyclicDecisionGraphCutUVCL(CyclicDecisionGraphCut[IMDataStructureUVCL], ABC):
    @classmethod
    def project(
        cls,
        obj: IMDataStructureUVCL,
        groups: List[Collection[Any]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[IMDataStructureUVCL]:

        logs = [Counter() for _ in groups]

        for t, freq in obj.data_structure.items():
            for i, group in enumerate(groups):
                seg = []
                for e in t:
                    if e in group:
                        seg.append(e)
                    else:
                        if len(seg) > 0:
                            logs[i][tuple(seg)] += freq
                            seg = []
                if len(seg) > 0:
                    logs[i][tuple(seg)] += freq

        return [IMDataStructureUVCL(l) for l in logs]
