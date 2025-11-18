from collections import defaultdict

from powl.discovery.partial_order_based.utils.constants import VARIANT_FREQUENCY_KEY
from powl.discovery.partial_order_based.utils.simplified_objects import Graph, Skip


class NodeGrouping:
    @classmethod
    def find_groups(cls, partial_orders):

        partial_orders = list(partial_orders)
        node_to_orders = defaultdict(list)
        n = len(partial_orders)

        all_nodes = list({node for graph in partial_orders for node in graph.nodes})

        for node_id, current_node in enumerate(all_nodes):
            for graph_id, graph in enumerate(partial_orders):
                if current_node in graph.nodes:
                    node_to_orders[node_id].append(graph_id)

        graph_ids_lists_to_nodes = defaultdict(list)

        sorted_keys = sorted(
            node_to_orders.keys(), key=lambda x: len(node_to_orders[x]), reverse=True
        )

        for node_id in sorted_keys:
            graph_id_list = node_to_orders[node_id]

            new_frozenset = frozenset(graph_id_list)

            graph_ids_lists_to_nodes[new_frozenset].append(node_id)

        res_dict = {}
        new_nodes_counter = defaultdict(int)
        if len(graph_ids_lists_to_nodes.keys()) == 1:
            pass
        else:
            for graph_id_list, node_id_list in graph_ids_lists_to_nodes.items():
                all_projections = []
                for graph_id in graph_id_list:
                    graph = partial_orders[graph_id]
                    proj_nodes = [
                        node
                        for i, node in enumerate(all_nodes)
                        if i in node_id_list and node in graph.nodes
                    ]
                    proj_edges = [
                        (s, t)
                        for (s, t) in graph.edges
                        if s in proj_nodes and t in proj_nodes
                    ]
                    projection = Graph(
                        frozenset(proj_nodes),
                        frozenset(proj_edges),
                        {
                            VARIANT_FREQUENCY_KEY: graph.additional_information[
                                VARIANT_FREQUENCY_KEY
                            ]
                        },
                    )
                    all_projections.append(projection)
                from powl.discovery.partial_order_based.variants.base.miner import _mine

                new_graph = _mine(all_projections)

                if len(graph_id_list) < n:
                    xor = Skip.create(new_graph)
                    new_node = xor
                else:
                    new_node = new_graph

                for node_id in node_id_list:
                    node = all_nodes[node_id]
                    res_dict[node] = new_node
                new_nodes_counter[new_node] += 1

        for node in all_nodes:
            if node not in res_dict.keys():
                from powl.discovery.partial_order_based.variants.base.miner import (
                    apply_mining_algorithm_recursively,
                )

                new_node = apply_mining_algorithm_recursively(node)
                res_dict[node] = new_node
                new_nodes_counter[new_node] += 1

        return res_dict, new_nodes_counter
