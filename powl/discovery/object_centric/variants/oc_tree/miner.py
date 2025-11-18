from typing import Any, Dict

import pm4py
from pm4py.objects.ocel.obj import OCEL

from powl.discovery.object_centric.variants.oc_powl.utils.divergence_free_graph import (
    get_divergence_free_graph,
)
from powl.discovery.object_centric.variants.oc_powl.utils.filtering import (
    keep_most_frequent_activities,
)
from powl.discovery.object_centric.variants.oc_powl.utils.interaction_properties import (
    get_interaction_patterns,
)
from powl.discovery.object_centric.variants.oc_tree.utils.oc_process_trees import (
    load_from_pt,
)
from powl.discovery.object_centric.variants.oc_tree.utils.tree_to_ocpn_conversion import (
    convert_ocpt_to_ocpn,
)


def apply(
    oc_log: OCEL,
    activity_coverage_threshold: float = 1.0,
) -> Dict[str, Any]:

    relations = oc_log.relations
    relations = keep_most_frequent_activities(
        relations, coverage=activity_coverage_threshold
    )

    div, con, rel, defi = get_interaction_patterns(relations)
    df2_graph, _ = get_divergence_free_graph(relations, div, rel)

    tree = pm4py.discover_process_tree_inductive(df2_graph)
    ocpt = load_from_pt(tree, rel, div, con, defi)
    ocpn = convert_ocpt_to_ocpn(ocpt)

    return ocpn
