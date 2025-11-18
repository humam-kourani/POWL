from collections import Counter


def get_transitive_closure_from_counter(relation: Counter):
    nodes = set()
    adj = {}

    for (a, b), count in relation.items():
        if count > 0:
            nodes.update([a, b])
            adj.setdefault(a, set()).add(b)

    closure = {u: set(adj.get(u, ())) for u in nodes}
    for k in nodes:
        for i in nodes:
            if k in closure[i]:
                closure[i] |= closure[k]

    return closure
