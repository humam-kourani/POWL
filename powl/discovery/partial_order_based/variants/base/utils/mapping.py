from collections import defaultdict

from powl.discovery.partial_order_based.utils.simplified_objects import (
    Graph,
    SelfLoop,
    Skip,
    SkipSelfLoop,
)


def find_self_loops(mapping, new_nodes_counter):
    new_mapping = {}
    reversed_mapping = defaultdict(set)

    for key, value in mapping.items():
        reversed_mapping[value].add(key)

    tagged_node_element_map = defaultdict(list)

    for node in reversed_mapping.keys():
        if (
            isinstance(node, Skip)
            or isinstance(node, SelfLoop)
            or isinstance(node, SkipSelfLoop)
        ):
            pass
        else:
            continue
        tagged_node_element_map[node.element].append(node)

    processed_keys = set()

    for tagged_node_element in tagged_node_element_map.keys():

        element_list = tagged_node_element_map[tagged_node_element]

        if tagged_node_element in reversed_mapping.keys():
            new_node = SelfLoop.create(tagged_node_element)
            values = reversed_mapping[tagged_node_element]
            processed_keys.add(tagged_node_element)
            for tagged_node in element_list:
                values.update(reversed_mapping[tagged_node])
                processed_keys.add(tagged_node)
            for node in values:
                new_mapping[node] = new_node

        elif len(element_list) > 1:
            if any(isinstance(tagged_node, SelfLoop) for tagged_node in element_list):
                new_node = SelfLoop.create(tagged_node_element)
            else:
                new_node = SkipSelfLoop.create(tagged_node_element)

            values = set()
            for tagged_node in element_list:
                values.update(reversed_mapping[tagged_node])
                processed_keys.add(tagged_node)

            for node in values:
                new_mapping[node] = new_node

    for key, value in reversed_mapping.items():
        if key in processed_keys:
            continue
        if new_nodes_counter[key] > 1:
            if isinstance(key, Skip):
                new_node = SkipSelfLoop.create(key.element)
            else:
                new_node = SelfLoop.create(key)
        else:
            new_node = key
        for node in value:
            new_mapping[node] = new_node

    return new_mapping


def apply_node_mapping_on_single_graph(graph: Graph, node_mapping: dict):

    reverse_mapping = defaultdict(set)
    new_nodes = set()
    for n in graph.nodes:
        if n in node_mapping:
            value = node_mapping[n]
            new_nodes.add(value)
            reverse_mapping[value].add(n)
        else:
            raise ValueError

    new_nodes = frozenset(new_nodes)
    new_edges = set()

    for source in new_nodes:
        for target in new_nodes:
            if source != target and all(
                (s, t) in graph.edges
                for s in reverse_mapping[source]
                for t in reverse_mapping[target]
            ):
                new_edges.add((source, target))
    return Graph(
        nodes=new_nodes,
        edges=frozenset(new_edges),
        additional_information=graph.additional_information,
    )
