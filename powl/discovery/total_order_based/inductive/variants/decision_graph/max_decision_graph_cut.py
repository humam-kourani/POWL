from abc import ABC
from collections import Counter
from itertools import combinations, product
from typing import Any, Collection, Dict, Generic, List, Optional, Tuple

from pm4py.algo.discovery.inductive.cuts import utils as cut_util

from pm4py.algo.discovery.inductive.cuts.abc import Cut, T
from pm4py.algo.discovery.inductive.dtypes.im_dfg import InductiveDFG
from pm4py.algo.discovery.inductive.dtypes.im_ds import (
    IMDataStructureDFG,
    IMDataStructureUVCL,
)
from pm4py.objects.dfg import util as dfu
from pm4py.objects.dfg.obj import DFG
from pm4py.objects.process_tree.obj import Operator

from powl.objects.BinaryRelation import BinaryRelation
from powl.objects.obj import DecisionGraph, POWL


class MaximalDecisionGraphCut(Cut[T], ABC, Generic[T]):
    @classmethod
    def operator(cls, parameters: Optional[Dict[str, Any]] = None) -> Operator:
        return None

    @classmethod
    def holds(
        cls, obj: T, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Any]]:

        alphabet = parameters["alphabet"]
        transitive_successors = parameters["transitive_successors"]

        groups = [frozenset([a]) for a in alphabet]

        for a, b in combinations(alphabet, 2):
            if b in transitive_successors[a] and a in transitive_successors[b]:
                groups = cut_util.merge_groups_based_on_activities(a, b, groups)

        if len(groups) < 2:
            return None

        # merged = True
        # while merged:
        #     merged = False
        #     new_groups = [g for g in groups]
        #     presets = {g: set() for g in groups}
        #     postsets = {g: set() for g in groups}
        #     for i, g1 in enumerate(groups):
        #         for j, g2 in enumerate(groups):
        #             if i != j:
        #                 pairs = product(g1, g2)
        #                 if any((a, b) in dfg.graph for (a, b) in pairs):
        #                     presets[g2] = presets[g2].union(g1)
        #                     postsets[g1] = postsets[g1].union(g2)
        #     for i, g1 in enumerate(groups):
        #         for j, g2 in enumerate(groups):
        #             if i != j:
        #                 if presets[g1] == presets[g2] and postsets[g1] == postsets[g2]:
        #                     new_groups = cut_util.merge_groups_based_on_activities(list(g1)[0], list(g2)[0], new_groups)
        #                     merged = True
        #     if len(new_groups) < 2:
        #         return groups
        #     else:
        #         groups = new_groups
        #
        # if len(groups) < 2:
        #     return None

        return groups

    @classmethod
    def apply(
        cls, obj: T, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[DecisionGraph, List[POWL]]]:

        dfg = obj.dfg
        alphabet = sorted(dfu.get_vertices(dfg), key=lambda g: g.__str__())

        start_activities = set(obj.dfg.start_activities.keys())
        end_activities = set(obj.dfg.end_activities.keys())

        transitive_predecessors, transitive_successors = dfu.get_transitive_relations(
            dfg
        )

        def keep(a):
            ok_start = (a in start_activities) or (
                len(set(transitive_predecessors[a]) & start_activities) > 0
            )
            ok_end = (a in end_activities) or (
                len(set(transitive_successors[a]) & end_activities) > 0
            )
            return ok_start and ok_end

        alphabet = [a for a in alphabet if keep(a)]

        parameters["alphabet"] = alphabet
        parameters["transitive_successors"] = transitive_successors

        groups = cls.holds(obj, parameters)
        if groups is None:
            return groups
        children = cls.project(obj, groups, parameters)

        order = BinaryRelation(nodes=children)
        for i, g1 in enumerate(groups):
            for j, g2 in enumerate(groups):
                if i != j:
                    pairs = product(g1, g2)
                    if any((a, b) in dfg.graph for (a, b) in pairs):
                        order.add_edge(children[i], children[j])

        start_nodes = []
        end_nodes = []
        for i in range(len(groups)):
            node = groups[i]
            if any(a in start_activities for a in node):
                start_nodes.append(children[i])
            if any(a in end_activities for a in node):
                end_nodes.append(children[i])

        dg = DecisionGraph(order, start_nodes, end_nodes)
        return dg, dg.children


class MaximalDecisionGraphCutUVCL(MaximalDecisionGraphCut[IMDataStructureUVCL], ABC):
    @classmethod
    def project(
        cls,
        obj: IMDataStructureUVCL,
        groups: List[Collection[Any]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[IMDataStructureUVCL]:

        logs = [Counter() for _ in groups]

        for t in obj.data_structure:
            for i, group in enumerate(groups):
                proj = tuple(e for e in t if e in group)
                if proj:
                    logs[i].update({proj: obj.data_structure[t]})

        return [IMDataStructureUVCL(l) for l in logs]


class MaximalDecisionGraphCutDFG(MaximalDecisionGraphCut[IMDataStructureDFG], ABC):
    @classmethod
    def project(
        cls,
        obj: IMDataStructureDFG,
        groups: List[Collection[Any]],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[IMDataStructureDFG]:

        base_dfg = obj.dfg
        dfg_map = {group: DFG() for group in groups}

        activity_to_group_map = {}
        for group in groups:
            for activity in group:
                activity_to_group_map[activity] = group

        for (a, b) in base_dfg.graph:
            group_a = activity_to_group_map[a]
            group_b = activity_to_group_map[b]
            freq = base_dfg.graph[(a, b)]
            if group_a == group_b:
                dfg_map[group_a].graph[(a, b)] = freq
            else:
                dfg_map[group_a].end_activities[a] += freq
                dfg_map[group_b].start_activities[b] += freq
        for a in base_dfg.start_activities:
            group_a = activity_to_group_map[a]
            dfg_map[group_a].start_activities[a] += base_dfg.start_activities[a]
        for a in base_dfg.end_activities:
            group_a = activity_to_group_map[a]
            dfg_map[group_a].end_activities[a] += base_dfg.end_activities[a]

        return list(
            map(
                lambda g: IMDataStructureDFG(InductiveDFG(dfg=dfg_map[g], skip=False)),
                groups,
            )
        )
