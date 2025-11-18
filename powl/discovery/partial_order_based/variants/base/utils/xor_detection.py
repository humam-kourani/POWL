import networkx as nx
from pm4py.algo.discovery.inductive.cuts import utils as cut_util

from powl.discovery.partial_order_based.utils.constants import VARIANT_FREQUENCY_KEY
from powl.discovery.partial_order_based.utils.simplified_objects import (
    get_leaves,
    Graph,
)


class XORMiner:
    @classmethod
    def find_disjoint_activities(cls, partial_orders, all_activity_labels):
        """
        Finds activities that never occur together in the same partial order.

        :param all_activity_labels:
        :param partial_orders: List of partial orders.
        :return: Groups of disjoint activities.
        """

        all_activity_labels = sorted(all_activity_labels)
        adjacency = {
            activity: {other_activity: 0 for other_activity in all_activity_labels}
            for activity in all_activity_labels
        }

        for graph in partial_orders:
            activity_labels_in_trace = get_leaves(graph)
            for i, activity in enumerate(activity_labels_in_trace):
                for j, other_activity in enumerate(activity_labels_in_trace):
                    if i != j:
                        adjacency[activity][other_activity] += 1

        found_xor = False
        clusters = [[a] for a in all_activity_labels]
        for i in range(len(all_activity_labels)):
            activity = all_activity_labels[i]
            for j in range(i + 1, len(all_activity_labels)):
                other_activity = all_activity_labels[j]
                if (
                    adjacency[activity][other_activity] == 0
                    and adjacency[other_activity][activity] == 0
                ):
                    found_xor = True
                    clusters = cut_util.merge_lists_based_on_activities(
                        activity, other_activity, clusters
                    )

        if found_xor:
            res = []
            for cluster in clusters:
                if len(cluster) == 1:
                    pass
                else:
                    from itertools import combinations

                    nx_graph = nx.DiGraph()
                    nx_graph.add_nodes_from(cluster)
                    for a, b in combinations(cluster, 2):
                        if adjacency[a][b] > 0 and adjacency[b][a] > 0:
                            nx_graph.add_edge(a, b)
                    nx_und = nx_graph.to_undirected()
                    conn_comps = [
                        nx_und.subgraph(c).copy()
                        for c in nx.connected_components(nx_und)
                    ]
                    if len(conn_comps) > 1:
                        cuts = list()
                        for comp in conn_comps:
                            cuts.append(set(comp.nodes))
                        res.append(cuts)
                    else:
                        return None
            return res
        else:
            return None

    @classmethod
    def project_partial_orders_on_groups(cls, partial_orders, group):
        res = []
        for graph in partial_orders:
            new_nodes = frozenset(
                [n for n in graph.nodes if get_leaves(n).issubset(group)]
            )
            if len(new_nodes) == 0:
                continue
            new_edges = frozenset(
                [(s, t) for (s, t) in graph.edges if s in new_nodes and t in new_nodes]
            )
            new_graph = Graph(new_nodes, new_edges)
            found = False
            if not found:
                new_graph.additional_information = {
                    VARIANT_FREQUENCY_KEY: graph.additional_information[
                        VARIANT_FREQUENCY_KEY
                    ]
                }
                res.append(new_graph)
        return res

    @classmethod
    def apply_mapping(cls, orders, label_mapping):
        res = []

        for graph in orders:
            new_nodes = set()
            for node in graph.nodes:
                label = get_leaves(node).pop()
                if label in label_mapping.keys():
                    new_nodes.add(label_mapping[node.label])
                else:
                    new_nodes.add(node)

            edges_set = set()
            for (s, t) in graph.edges:
                XORMiner.__add_edge(s, t, label_mapping, edges_set)

            for s in new_nodes:
                for t in new_nodes:
                    if (s, t) in edges_set and (t, s) in edges_set:
                        edges_set.remove((s, t))
                        edges_set.remove((t, s))

            new_graph = Graph(
                frozenset(new_nodes), frozenset(edges_set), graph.additional_information
            )

            found_po = False
            if not found_po:
                res.append(new_graph)
        return res

    @classmethod
    def __add_edge(cls, node, other_node, label_mapping, edges_set):
        label = get_leaves(node).pop()
        if label in label_mapping.keys():
            source = label_mapping[label]
        else:
            source = node
        other_labels = get_leaves(other_node)
        if other_labels.issubset(label_mapping.keys()):
            target = label_mapping[other_labels.pop()]
        else:
            target = other_node
        if source != target:
            edges_set.add((source, target))
