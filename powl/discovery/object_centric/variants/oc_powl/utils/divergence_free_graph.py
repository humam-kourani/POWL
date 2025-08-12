# this file is copied from https://github.com/Nik314/DF2-Miner

import pm4py

def get_divergence_free_graph(relations, div, rel):

    alphabet = rel.keys()

    global_dfg = {(a,b):0 for a in alphabet for b in alphabet}
    global_start = {a:0 for a in alphabet}
    global_end = {a:0 for a in alphabet}

    non_starts = []
    non_ends = []


    for ot in relations["ocel:type"].unique():

        sub_log = relations[relations["ocel:type"] == ot]
        local_dfg, local_start, local_end = pm4py.discover_dfg(sub_log,"ocel:activity",
                                                "ocel:timestamp","ocel:oid")

        for key,value in local_dfg.items():
            if value and not (ot in div[key[0]] & div[key[1]]):
                global_dfg[key] += value

        for key,value in local_start.items():
            if value:
                global_start[key] += value

        for key,value in local_end.items():
            if value:
                global_end[key] += value

        non_starts += [a for a in alphabet if not local_start.get(a,0) and ot in rel[a]]
        non_ends += [a for a in alphabet if not local_end.get(a,0) and ot in rel[a]]

    global_dfg = {key:value for key,value in global_dfg.items() if value}
    global_start = {key:value for key,value in global_start.items() if value and key not in non_starts}
    global_end = {key:value for key,value in global_end.items() if value and key not in non_ends}

    for node in alphabet:
        pre = {a for (a, b) in global_dfg if b == node}
        if len(pre) == 0:
            global_start[node] = 1
        post = {b for (a, b) in global_dfg if a == node}
        if len(post) == 0:
            global_end[node] = 1

    return pm4py.objects.dfg.obj.DFG(global_dfg,global_start,global_end)