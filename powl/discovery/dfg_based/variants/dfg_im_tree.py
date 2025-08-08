from itertools import combinations
from typing import Optional, Tuple, List, TypeVar, Generic, Dict, Any, Type

from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureDFG
from pm4py.algo.discovery.inductive.variants.abc import InductiveMinerFramework
from powl.discovery.total_order_based.inductive.base_case.factory import BaseCaseFactory
from powl.discovery.total_order_based.inductive.cuts.factory import CutFactory
from powl.discovery.total_order_based.inductive.fall_through.empty_traces import POWLEmptyTracesDFG
from powl.discovery.total_order_based.inductive.fall_through.factory import FallThroughFactory
from powl.discovery.total_order_based.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from powl.objects.BinaryRelation import BinaryRelation
from powl.objects.obj import POWL, StrictPartialOrder, DecisionGraph

T = TypeVar('T', bound=IMDataStructureDFG)


class DFGIMBasePOWL(Generic[T], InductiveMinerFramework[T]):

    def instance(self) -> POWLDiscoveryVariant:
        return POWLDiscoveryVariant.TREE

    def empty_traces_cut(self) -> Type[POWLEmptyTracesDFG]:
        return POWLEmptyTracesDFG

    def apply(self, dfg: IMDataStructureDFG, parameters: Optional[Dict[str, Any]] = None) -> POWL:

        empty_traces = self.empty_traces_cut().apply(dfg, parameters)
        if empty_traces is not None:
            return self._recurse(empty_traces[0], empty_traces[1], parameters)

        powl = self.apply_base_cases(dfg, parameters)
        if powl is not None:
            return powl

        cut = self.find_cut(dfg, parameters)
        if cut is not None:
            powl = self._recurse(cut[0], cut[1], parameters=parameters)

        if powl is not None:
            return powl

        ft = self.fall_through(dfg, parameters)
        return self._recurse(ft[0], ft[1], parameters=parameters)

    def apply_base_cases(self, obj: T, parameters: Optional[Dict[str, Any]] = None) -> Optional[POWL]:
        return BaseCaseFactory.apply_base_cases(obj, parameters=parameters)

    def find_cut(self, obj: T, parameters: Optional[Dict[str, Any]] = None) -> Optional[Tuple[POWL, List[T]]]:
        return CutFactory.find_cut(obj, parameters=parameters)

    def fall_through(self, obj: T, parameters: Optional[Dict[str, Any]] = None) -> Tuple[POWL, List[T]]:
        return FallThroughFactory.fall_through(obj, self._pool, self._manager, parameters=parameters)

    def _recurse(self, powl: POWL, objs: List[T], parameters: Optional[Dict[str, Any]] = None):
        children = [self.apply(obj, parameters=parameters) for obj in objs]
        if isinstance(powl, StrictPartialOrder):
            powl_new = StrictPartialOrder(children)
            for i, j in combinations(range(len(powl.children)), 2):
                if powl.order.is_edge_id(i, j):
                    powl_new.order.add_edge(children[i], children[j])
                elif powl.order.is_edge_id(j, i):
                    powl_new.order.add_edge(children[j], children[i])
            return powl_new
        elif isinstance(powl, DecisionGraph):
            new_order = BinaryRelation(children)
            for i, j in combinations(range(len(powl.children)), 2):
                if powl.order.is_edge(objs[i], objs[j]):
                    new_order.add_edge(children[i], children[j])
                elif powl.order.is_edge(objs[j], objs[i]):
                    new_order.add_edge(children[j], children[i])
            start_nodes = [children[i] for i in range(len(powl.children)) if objs[i] in powl.start_nodes]
            end_nodes = [children[i] for i in range(len(powl.children)) if objs[i] in powl.end_nodes]
            empty_path = powl.order.is_edge(powl.start, powl.end)
            return DecisionGraph(new_order, start_nodes, end_nodes, empty_path=empty_path)
        else:
            powl.children.extend(children)
            return powl

