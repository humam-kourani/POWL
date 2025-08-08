from pm4py.algo.discovery.inductive.dtypes.im_ds import IMDataStructureDFG

from powl.discovery.dfg_based.variants.dfg_im_tree import DFGIMBasePOWL
from powl.objects.obj import POWL
from powl.discovery.total_order_based.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from pm4py.objects.dfg.obj import DFG
from pm4py.algo.discovery.inductive.dtypes.im_dfg import InductiveDFG

from typing import Optional, Dict, Any, Type



def get_variant(variant: POWLDiscoveryVariant) -> Type[DFGIMBasePOWL]:
    if variant == POWLDiscoveryVariant.TREE:
        return DFGIMBasePOWL
    # elif variant == POWLDiscoveryVariant.DECISION_GRAPH_MAX:
    #     return DFGPOWLInductiveMinerDecisionGraphMaximal
    else:
        raise Exception('Invalid Variant!')


def apply(dfg: DFG, parameters: Optional[Dict[Any, Any]] = None,
          variant=POWLDiscoveryVariant.TREE) -> POWL:
    if parameters is None:
        parameters = {}

    im_dfg = InductiveDFG(dfg=dfg, skip=False)

    algorithm = get_variant(variant)
    im = algorithm(parameters)
    res = im.apply(IMDataStructureDFG(im_dfg), parameters)
    res = res.simplify()

    return res
