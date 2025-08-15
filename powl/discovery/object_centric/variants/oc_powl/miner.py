from typing import Optional, Dict, Any

from pm4py.objects.ocel.obj import OCEL

from powl.discovery.object_centric.variants.oc_powl.utils.divergence_free_graph import get_divergence_free_graph
from powl.discovery.object_centric.variants.oc_powl.utils.filtering import keep_most_frequent_activities
from powl.discovery.object_centric.variants.oc_powl.utils.interaction_properties import get_interaction_patterns
from powl.discovery.object_centric.variants.oc_powl.utils.ocpn_conversion import convert_ocpowl_to_ocpn
from powl.discovery.total_order_based.inductive.variants.powl_discovery_varaints import POWLDiscoveryVariant
from powl.objects.oc_powl import load_oc_powl
from powl.discovery.dfg_based.algorithm import apply as discover_from_dfg



def apply(
    oc_log: OCEL,
    powl_miner_variant = POWLDiscoveryVariant.MAXIMAL,
        activity_coverage_threshold: float = 1.0,
    parameters: Optional[Dict[Any, Any]] = None
) -> Dict[str, Any]:

    relations = oc_log.relations
    relations = keep_most_frequent_activities(relations, coverage=activity_coverage_threshold)

    div, con, rel, defi = get_interaction_patterns(relations)
    df2_graph = get_divergence_free_graph(relations, div, rel)

    # from powl.visualization.dfg.visualizer import apply as view_dfg
    # view_dfg(df2_graph).view()
    # tree = pm4py.discover_process_tree_inductive(df2_graph)
    # pm4py.view_process_tree(tree, format='SVG')
    # powl_model = from_tree.apply(tree)

    powl_model = discover_from_dfg(df2_graph, variant=powl_miner_variant)
    oc_powl = load_oc_powl(powl_model, rel,div, con, defi)
    ocpn = convert_ocpowl_to_ocpn(oc_powl)

    return ocpn