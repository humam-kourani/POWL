from typing import Any, Dict, List, Optional, Tuple, TypeVar

from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureLog

from powl.discovery.total_order_based.inductive.variants.dynamic_clustering.factory import (
    CutFactoryPOWLDynamicClustering,
)
from powl.discovery.total_order_based.inductive.variants.im_tree import IMBasePOWL
from powl.discovery.total_order_based.inductive.variants.powl_discovery_varaints import (
    POWLDiscoveryVariant,
)
from powl.objects.obj import POWL

T = TypeVar("T", bound=IMDataStructureLog)


class POWLInductiveMinerDynamicClustering(IMBasePOWL):
    def instance(self) -> POWLDiscoveryVariant:
        return POWLDiscoveryVariant.DYNAMIC_CLUSTERING

    def find_cut(
        self, obj: T, parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[POWL, List[T]]]:
        res = CutFactoryPOWLDynamicClustering.find_cut(obj, parameters=parameters)
        return res
