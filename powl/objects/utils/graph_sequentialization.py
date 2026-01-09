import networkx as nx
from collections import defaultdict


def split_graph_into_stages(G: nx.DiGraph, START, END):
    """
    Splits a directed graph into a sequence of stages [s1, s2, ...] such that
    any valid path from START to END follows this order.

    1. Prunes the graph to valid paths only.
    2. Condenses cycles (Strongly Connected Components) into super-nodes.
    3. Uses Dominator Tree on the condensed DAG to find linear bottlenecks.
    4. Groups remaining nodes into skippable stages between bottlenecks.

    Guarantees: No edge exists from Stage[j] to Stage[i] where j > i.
    """

    # --- 1. Pruning: Keep only nodes on valid paths START -> END ---
    if START not in G or END not in G:
        raise ValueError("START or END not in graph")

    reachable_from_start = nx.descendants(G, START) | {START}
    can_reach_end = nx.ancestors(G, END) | {END}
    valid_nodes = reachable_from_start.intersection(can_reach_end)

    if START not in valid_nodes or END not in valid_nodes:
        raise ValueError("No path exists between START and END")

    subgraph = G.subgraph(valid_nodes).copy()

    # --- 2. Condensation: Convert to DAG of SCCs ---
    G_condensed = nx.condensation(subgraph)

    node_to_scc_mapping = G_condensed.graph['mapping']
    start_scc = node_to_scc_mapping[START]
    end_scc = node_to_scc_mapping[END]


    # --- 3. Dominators on the DAG ---
    # Find immediate dominators in the condensed graph starting from start_scc
    idom = nx.immediate_dominators(G_condensed, start_scc)

    # Trace the backbone (Mandatory SCCs) from END back to START
    backbone_sccs = []
    curr = end_scc
    while curr != start_scc:
        backbone_sccs.append(curr)
        if curr not in idom:
            raise ValueError("Broken path in condensed graph")
        curr = idom[curr]
    backbone_sccs.append(start_scc)
    backbone_sccs.reverse()  # Order: [start_scc, ..., end_scc]
    backbone_to_rank_map = {scc: i for i, scc in enumerate(backbone_sccs)}

    # --- 4. Partitioning Non-Backbone SCCs ---
    # We assign every non-mandatory SCC to the bucket of its closest mandatory dominator.
    # Because it is a DAG, if M_i dominates X, X must appear "after" M_i.
    # Since M_i dominates M_{i+1}, and M_{i+1} does NOT dominate X (otherwise X would be
    # anchored to M_{i+1}), X is strictly between M_i and M_{i+1} (or on a dead branch off M_i).

    scc_to_backbone_idx = {}

    for scc in G_condensed.nodes():
        if scc in backbone_to_rank_map:
            scc_to_backbone_idx[scc] = backbone_to_rank_map[scc]
        else:
            # Walk up dominator tree until we hit a backbone node
            runner = scc
            while runner not in backbone_to_rank_map:
                if runner not in idom:
                    # Should be unreachable code given pruning
                    raise ValueError("Broken path in condensed graph")
                runner = idom[runner]
            scc_to_backbone_idx[scc] = backbone_to_rank_map[runner]

    # --- 5. Reconstruct the Stages (Flatten SCCs back to nodes) ---
    final_stages = []
    is_skippable = []

    # Invert the mapping to get nodes back from SCC IDs
    scc_members = defaultdict(list)
    for node, scc_id in node_to_scc_mapping.items():
        scc_members[scc_id].append(node)

    for i, mand_scc in enumerate(backbone_sccs):
        # A. Add the Mandatory Stage (Bottleneck)
        stage_nodes = set(scc_members[mand_scc])
        final_stages.append(stage_nodes)
        is_skippable.append(False)

        # B. Check for Intermediate Stage (between i and i+1)
        if i < len(backbone_sccs) - 1:
            next_mand_scc = backbone_sccs[i + 1]

            # 1. Collect nodes strictly between mand_scc and next_mand_scc
            intermediate_nodes = set()
            for scc in G_condensed.nodes():
                if scc != mand_scc and scc_to_backbone_idx.get(scc) == i:
                    for node in scc_members[scc]:
                        intermediate_nodes.add(node)

            # 2. If intermediate nodes exist, add the stage
            if intermediate_nodes:
                final_stages.append(intermediate_nodes)

                # 3. CHECK SKIPPABILITY
                if G_condensed.has_edge(mand_scc, next_mand_scc):
                    is_skippable.append(True)
                else:
                    is_skippable.append(False)

    return final_stages, is_skippable
