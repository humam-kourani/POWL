from enum import Enum
from typing import Optional, Dict, Any

import pm4py
from pm4py.objects.ocel.obj import OCEL

import powl
from powl.conversion.to_powl import from_tree
from powl.discovery.object_centric.variants.oc_powl.utils.divergence_free_graph import get_divergence_free_graph
from powl.discovery.object_centric.variants.oc_powl.utils.interaction_properties import get_interaction_patterns
from powl.discovery.total_order_based.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from powl.objects.oc_powl import OCPOWL


class Parameters(Enum):
    POWL_MINER_VARIANT = "powl_miner_variant"


def apply(
    oc_log: OCEL, parameters: Optional[Dict[Any, Any]] = None
) -> OCPOWL:

    if parameters and Parameters.POWL_MINER_VARIANT in parameters:
        powl_miner_variant = parameters[Parameters.POWL_MINER_VARIANT]
    else:
        powl_miner_variant = POWLDiscoveryVariant.MAXIMAL

    div, con, rel, defi = get_interaction_patterns(oc_log.relations)
    df2_graph = get_divergence_free_graph(oc_log.relations,div,rel)

    pm4py.view_dfg(df2_graph.graph, df2_graph.start_activities, df2_graph.end_activities, format='SVG')
    import pickle
    F = open(r"C:\Users\kourani\output.dump", "wb")
    pickle.dump(df2_graph, F)
    F.close()

    tree = pm4py.discover_process_tree_inductive(df2_graph)
    pm4py.view_process_tree(tree, format='SVG')
    # powl_model = from_tree.apply(tree)

    powl_model = powl.discover_from_dfg(df2_graph)

    oc_powl = OCPOWL(powl_model, rel,div, con, defi)

    return oc_powl