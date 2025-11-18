from powl.discovery.partial_order_based.utils.combine_order import combine_orders
from powl.discovery.partial_order_based.utils.simplified_objects import (
    ActivityInstance,
    generate_powl,
    get_leaves,
    Graph,
    LOOP,
    SelfLoop,
    Skip,
    XOR,
)
from powl.discovery.partial_order_based.variants.base.utils.constants import (
    ENABLE_LOOP_DETECTION,
    ENABLE_XOR_DETECTION,
)
from powl.discovery.partial_order_based.variants.base.utils.mapping import (
    apply_node_mapping_on_single_graph,
    find_self_loops,
)
from powl.discovery.partial_order_based.variants.base.utils.node_grouping import (
    NodeGrouping,
)
from powl.discovery.partial_order_based.variants.base.utils.xor_detection import (
    XORMiner,
)


def apply_mining_algorithm_recursively(node):
    if isinstance(node, ActivityInstance):
        if ENABLE_LOOP_DETECTION:
            return ActivityInstance(node.label, 1)
        else:
            return node
    elif isinstance(node, Skip):
        node_element = apply_mining_algorithm_recursively(node.element)
        return Skip.create(node_element)
    elif isinstance(node, Graph):
        return _mine([node])
    elif isinstance(node, LOOP):
        body = apply_mining_algorithm_recursively(node.body)
        redo = apply_mining_algorithm_recursively(node.redo)
        return LOOP(body, redo)
    elif isinstance(node, XOR):
        new_children = {
            apply_mining_algorithm_recursively(child) for child in node.children
        }
        return XOR(frozenset(new_children))
    else:
        raise TypeError("Unsupported node type")


def _mine(orders):

    if len(orders) < 1:
        raise ValueError("Input list of partial orders is empty!")

    all_activity_labels = set()

    for graph in orders:
        for node in graph.nodes:
            all_activity_labels.update(get_leaves(node))

    if ENABLE_LOOP_DETECTION:
        if len(all_activity_labels) == 1:
            activity_label = all_activity_labels.pop()
            activity = ActivityInstance(activity_label, 1)
            if any(len(order.nodes) > 1 for order in orders):
                return SelfLoop.create(activity)
            else:
                return activity

    if ENABLE_XOR_DETECTION:
        xor_clusters = XORMiner.find_disjoint_activities(orders, all_activity_labels)

        label_mapping = {}
        if xor_clusters is not None:

            for cluster in xor_clusters:

                sub_models = []
                for group in cluster:
                    projected_log = XORMiner.project_partial_orders_on_groups(
                        orders, list(group)
                    )
                    sub_models.append(_mine(projected_log))
                model = XOR(children=frozenset(sub_models))
                for group in cluster:
                    for activity_label in group:
                        if activity_label in label_mapping.keys():
                            raise ValueError("Duplicate activity label")
                        label_mapping[activity_label] = model

            orders = XORMiner.apply_mapping(orders, label_mapping)

    mapping_skips, new_nodes_counter = NodeGrouping.find_groups(orders)
    if ENABLE_LOOP_DETECTION:
        node_mapping = find_self_loops(mapping_skips, new_nodes_counter)
    else:
        node_mapping = mapping_skips
    orders = [apply_node_mapping_on_single_graph(g, node_mapping) for g in orders]

    if len(orders) == 1:
        order = orders[0]
    else:
        order = combine_orders(orders)

    if len(order.nodes) == 0:
        return ActivityInstance(None, 1)

    if len(order.nodes) == 1:
        return list(order.nodes)[0]

    return order


def apply(partial_orders):
    order = _mine(partial_orders)
    powl = generate_powl(order)
    return powl
