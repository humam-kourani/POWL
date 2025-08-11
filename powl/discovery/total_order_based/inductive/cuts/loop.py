from abc import ABC
from collections.abc import Collection
from typing import Optional, Any, Dict, Generic, List

from pm4py.algo.discovery.inductive.cuts.loop import LoopCut, LoopCutUVCL, T, LoopCutDFG
from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureUVCL, IMDataStructureDFG
from powl.objects.obj import OperatorPOWL
from pm4py.objects.process_tree.obj import Operator
from pm4py.algo.discovery.inductive.dtypes.im_dfg import InductiveDFG
from pm4py.objects.dfg.obj import DFG


class POWLLoopCut(LoopCut, ABC, Generic[T]):

    @classmethod
    def operator(cls, parameters: Optional[Dict[str, Any]] = None) -> OperatorPOWL:
        return OperatorPOWL(Operator.LOOP, [])


class POWLLoopCutUVCL(LoopCutUVCL, POWLLoopCut[IMDataStructureUVCL]):
    pass

class POWLLoopCutDFG(LoopCutDFG, POWLLoopCut[IMDataStructureDFG]):
    @classmethod
    def project(cls, obj: IMDataStructureUVCL, groups: List[Collection[Any]],
                parameters: Optional[Dict[str, Any]] = None) -> List[IMDataStructureDFG]:
        dfg = obj.dfg
        dfgs = []
        skippable = [False, False]
        for gind, g in enumerate(groups):
            dfn = DFG()
            for (a, b) in dfg.graph:
                if a in g and b in g:
                    dfn.graph[(a, b)] = dfg.graph[(a, b)]
                if b in dfg.start_activities and a in dfg.end_activities:
                    skippable[1] = True
            if gind == 0:
                for a in dfg.start_activities:
                    if a in g:
                        dfn.start_activities[a] = dfg.start_activities[a]
                    else:
                        skippable[0] = True
                for a in dfg.end_activities:
                    if a in g:
                        dfn.end_activities[a] = dfg.end_activities[a]
                    else:
                        skippable[0] = True
            elif gind == 1:
                for a in g:
                    dfn.start_activities[a] = 1
                    dfn.end_activities[a] = 1
            dfgs.append(dfn)
        return [IMDataStructureDFG(InductiveDFG(dfg=dfgs[i], skip=skippable[i])) for i in range(len(dfgs))]
