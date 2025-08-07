# this file is copied from https://github.com/Nik314/DF2-Miner

import pm4py

def get_divergence_free_graph(relations, div, rel):

    global_dfg = {(a,b):0 for a in rel.keys() for b in rel.keys()}
    global_start = {a:0 for a in rel.keys()}
    global_end = {a:0 for a in rel.keys()}

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

        non_starts += [a for a in rel.keys() if not local_start.get(a,0) and ot in rel[a]]
        non_ends += [a for a in rel.keys() if not local_end.get(a,0) and ot in rel[a]]

    global_dfg = {key:value for key,value in global_dfg.items() if value}
    global_start = {key:value for key,value in global_start.items() if value and key not in non_starts}
    global_end = {key:value for key,value in global_end.items() if value and key not in non_ends}

    return pm4py.objects.dfg.obj.DFG(global_dfg,global_start,global_end)