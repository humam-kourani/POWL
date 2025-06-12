from typing import Optional, Tuple, List, Dict, Any, Type

from pm4py.algo.discovery.inductive.fall_through.empty_traces import EmptyTracesUVCL
from powl.algo.discovery.inductive.fall_through.decision_graph.empty_traces_decision_graph import \
    POWLEmptyTracesDecisionGraphUVCL
from powl.algo.discovery.inductive.variants.decision_graph.factory_dg_clst import \
    CutFactoryPOWLDecisionGraphClustering
from powl.algo.discovery.inductive.variants.im_tree import IMBasePOWL, T
from powl.algo.discovery.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from powl.objects.obj import POWL


class POWLInductiveMinerDecisionGraphClustering(IMBasePOWL):

    def instance(self) -> POWLDiscoveryVariant:
        return POWLDiscoveryVariant.DECISION_GRAPH_CLUSTERING

    def empty_traces_cut(self) -> Type[EmptyTracesUVCL]:
        return POWLEmptyTracesDecisionGraphUVCL

    def find_cut(self, obj: T, parameters: Optional[Dict[str, Any]] = None) -> Optional[Tuple[POWL, List[T]]]:
        res = CutFactoryPOWLDecisionGraphClustering.find_cut(obj, parameters=parameters)
        return res
