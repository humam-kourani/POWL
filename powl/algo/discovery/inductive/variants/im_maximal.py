from typing import Optional, Tuple, List, Dict, Any

from powl.algo.discovery.inductive.variants.maximal.factory import CutFactoryPOWLMaximal
from powl.algo.discovery.inductive.variants.im_tree import IMBasePOWL, T
from powl.algo.discovery.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from powl.objects.obj import POWL


class POWLInductiveMinerMaximalOrder(IMBasePOWL):

    def instance(self) -> POWLDiscoveryVariant:
        return POWLDiscoveryVariant.MAXIMAL

    def find_cut(self, obj: T, parameters: Optional[Dict[str, Any]] = None) -> Optional[Tuple[POWL, List[T]]]:
        res = CutFactoryPOWLMaximal.find_cut(obj, parameters=parameters)
        return res
