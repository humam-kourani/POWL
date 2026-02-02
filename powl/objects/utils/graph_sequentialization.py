import networkx as nx


def split_graph_into_stages(G: nx.DiGraph, START, END):
    """
    Splits a directed graph into a sequence of stages [s1, s2, ...] such that
    any valid path from START to END follows this order.

    1. Prunes the graph to valid paths only.
    2. Uses Dominator Tree on the actual nodes to find the backbone.
    3. Initially splits graph into backbone nodes and intermediate nodes.
    4. Post-processes to merge stages that are part of a cycle.

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

    # --- 2. Dominators & Backbone (No SCC abstraction) ---
    # Calculate immediate dominators on the pruned subgraph
    idom = nx.immediate_dominators(subgraph, START)

    # Trace the backbone (Mandatory Nodes) from END back to START
    # The backbone consists of the 'bottleneck' nodes.
    backbone_nodes = []
    curr = END
    while curr != START:
        backbone_nodes.append(curr)
        if curr not in idom:
            raise ValueError("Broken path in graph logic")
        curr = idom[curr]
    backbone_nodes.append(START)
    backbone_nodes.reverse()  # Order: [START, ..., END]

    # Map backbone nodes to their rank (index in the backbone list)
    backbone_rank = {node: i for i, node in enumerate(backbone_nodes)}

    # --- 3. Initial Partitioning (Granular Stages) ---
    # We group every node to its closest backbone dominator.
    # Logic: If 'B' is a backbone node, it owns all nodes 'n' where
    # 'B' is the lowest backbone ancestor of 'n' in the dominator tree.

    # Bucket for intermediate nodes between backbone_nodes[i] and backbone_nodes[i+1]
    intermediate_buckets = {i: set() for i in range(len(backbone_nodes))}

    for node in subgraph.nodes():
        if node in backbone_rank:
            continue

        # Climb up dominator tree to find which backbone node owns this node
        runner = node
        while runner not in backbone_rank:
            if runner not in idom:
                # Should not happen given pruning
                raise ValueError(f"Node {node} is detached from dominator tree")
            runner = idom[runner]

        owner_idx = backbone_rank[runner]
        intermediate_buckets[owner_idx].add(node)

    # Construct the raw list of stages
    # Pattern: [ {Backbone_i}, {Intermediate_Nodes_for_i} ... ]
    raw_stages = []

    # We will track skippability for the raw stages.
    # Only intermediate stages can be skippable (if edge exists Backbone_i -> Backbone_i+1)
    raw_skippable = []

    for i, b_node in enumerate(backbone_nodes):
        # 1. Add Backbone Stage
        raw_stages.append({b_node})
        raw_skippable.append(False)  # Backbone nodes are never skippable

        # 2. Add Intermediate Stage (if it exists and we aren't at the very end)
        if i < len(backbone_nodes) - 1:
            inter_nodes = intermediate_buckets[i]
            if inter_nodes:
                raw_stages.append(inter_nodes)

                # Check skippability: Can we go from b_node directly to next_b_node?
                next_b_node = backbone_nodes[i + 1]
                if subgraph.has_edge(b_node, next_b_node):
                    raw_skippable.append(True)
                else:
                    raw_skippable.append(False)

    # --- 4. Post-Processing: Merge Cycles ---
    # A cycle might be split across multiple raw stages.
    # Example: A -> B -> A. A is backbone. B is intermediate.
    # Stages: [{A}, {B}]. Edge B->A is a back-edge from stage 1 to 0.
    # We must merge any range [i, j] that contains a back-edge.

    # Map every node to its raw stage index
    node_to_stage_idx = {}
    for idx, stage_set in enumerate(raw_stages):
        for node in stage_set:
            node_to_stage_idx[node] = idx

    # Detect back-edges and collect merge intervals
    merge_intervals = []

    for u in subgraph.nodes():
        u_idx = node_to_stage_idx[u]
        for v in subgraph.successors(u):
            v_idx = node_to_stage_idx[v]

            # If edge goes backwards (or self-loop), it's part of a cycle/SCC
            if v_idx <= u_idx:
                # We must merge everything from v_idx to u_idx
                if v_idx != u_idx:  # Ignore self-loops within a single stage
                    merge_intervals.append((v_idx, u_idx))

    # Merge overlapping intervals
    if not merge_intervals:
        merged_ranges = []
    else:
        merge_intervals.sort()  # Sort by start index
        merged_ranges = []
        if merge_intervals:
            curr_start, curr_end = merge_intervals[0]
            for next_start, next_end in merge_intervals[1:]:
                if next_start <= curr_end:
                    # Overlap or adjacent, extend current end
                    curr_end = max(curr_end, next_end)
                else:
                    # Disjoint, push current and start new
                    merged_ranges.append((curr_start, curr_end))
                    curr_start, curr_end = next_start, next_end
            merged_ranges.append((curr_start, curr_end))

    # --- 5. Construct Final Stages ---
    final_stages = []
    final_skippable = []

    current_raw_idx = 0
    merge_ptr = 0

    while current_raw_idx < len(raw_stages):
        # Check if current index is the start of a merge range
        if merge_ptr < len(merged_ranges) and current_raw_idx == merged_ranges[merge_ptr][0]:
            start, end = merged_ranges[merge_ptr]

            # Combine all stages from start to end
            combined_set = set()
            for k in range(start, end + 1):
                combined_set.update(raw_stages[k])

            final_stages.append(combined_set)
            # A merged cycle is not skippable
            final_skippable.append(False)

            current_raw_idx = end + 1
            merge_ptr += 1
        else:
            # No merge needed, keep as is
            final_stages.append(raw_stages[current_raw_idx])
            final_skippable.append(raw_skippable[current_raw_idx])
            current_raw_idx += 1

    return final_stages, final_skippable