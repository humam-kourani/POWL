# this file was initially copied from https://github.com/Nik314/DF2-Miner

from collections import Counter

import pm4py
from pm4py.objects.dfg.obj import DFG

from powl.objects.utils.relation import get_transitive_closure_from_counter


# def _partitions_from_edges(nodes, edges):
#     edges = [tuple(edge) for edge in edges]
#     parts = [{a} for a in nodes]
#
#     def find_group(a):
#         for g in parts:
#             if a in g:
#                 return g
#         return None
#
#     for u, v in edges:
#         gu = find_group(u)
#         gv = find_group(v)
#         assert gu is not None and gv is not None
#         if gu is gv:
#             continue
#         gu |= gv
#         parts.remove(gv)
#
#     covered = set().union(*parts) if parts else set()
#     nodes_set = set(nodes)
#     assert covered == nodes_set, "Invalid partition: missing/extra nodes!"
#     assert all(len(g) > 0 for g in parts), "Invalid partition: empty group encountered!"
#     assert sum(len(g) for g in parts) == len(covered), "Invalid partition: overlapping groups!"
#
#     return parts


def get_divergence_free_graph(relations, div, rel):

    alphabet = rel.keys()

    global_dfg = {(a, b): 0 for a in alphabet for b in alphabet}
    global_start = {a: 0 for a in alphabet}
    global_end = {a: 0 for a in alphabet}

    non_starts = []
    non_ends = []

    divergence_matrices = {}

    for ot in relations["ocel:type"].unique():

        sub_log = relations[relations["ocel:type"] == ot]
        local_dfg, local_start, local_end = pm4py.discover_dfg(
            sub_log, "ocel:activity", "ocel:timestamp", "ocel:oid"
        )

        filtered_edges = set()

        for key, value in local_dfg.items():
            if not value:
                continue
            source = key[0]
            target = key[1]
            if (ot in div[source]) and (ot in div[target]):
                if source != target:
                    filtered_edges.add(frozenset((source, target)))
            else:
                global_dfg[(source, target)] += value

        for key, value in local_start.items():
            if value:
                global_start[key] += value

        for key, value in local_end.items():
            if value:
                global_end[key] += value

        non_starts += [
            a for a in alphabet if not local_start.get(a, 0) and ot in rel[a]
        ]
        non_ends += [a for a in alphabet if not local_end.get(a, 0) and ot in rel[a]]

        divergence_matrices[ot] = filtered_edges

    global_dfg = {key: value for key, value in global_dfg.items() if value}
    global_start = {
        key: value
        for key, value in global_start.items()
        if value and key not in non_starts
    }
    global_end = {
        key: value for key, value in global_end.items() if value and key not in non_ends
    }

    closure = get_transitive_closure_from_counter(Counter(global_dfg))

    for node in alphabet:
        if node not in closure.keys():
            closure[node] = set()

    new_starts = set()
    new_ends = set()

    for node in alphabet:
        if node not in global_start.keys():
            reachable_from_start = any(
                node in closure[start] for start in global_start.keys()
            )
            if not reachable_from_start:
                new_starts.add(node)
        if node not in global_end.keys():
            reachable_from_end = any(end in closure[node] for end in global_end.keys())
            if not reachable_from_end:
                new_ends.add(node)

    for node in new_starts:
        global_start[node] = 1

    for node in new_ends:
        global_end[node] = 1

    return DFG(global_dfg, global_start, global_end), divergence_matrices
