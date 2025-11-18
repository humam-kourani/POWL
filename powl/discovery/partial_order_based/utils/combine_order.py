from powl.discovery.partial_order_based.utils.simplified_objects import Graph


def combine_orders(orders):
    nodes = sorted({x for g in orders for x in g.nodes})
    idx = {x: i for i, x in enumerate(nodes)}
    n = len(nodes)

    edges_bits = [0] * n
    conflicts_bits = [0] * n
    for g in orders:
        for u in g.nodes:
            ui = idx[u]
            for v in g.nodes:
                vi = idx[v]
                if u == v:
                    conflicts_bits[ui] |= 1 << vi
                if (u, v) in g.edges:
                    edges_bits[ui] |= 1 << vi
                else:
                    conflicts_bits[ui] |= 1 << vi

    for i in range(n):
        edges_bits[i] &= ~conflicts_bits[i]

    # Transitive closure with Floyd–Warshall algorithm
    for k in range(n):
        bk = edges_bits[k]
        for i in range(n):
            if (edges_bits[i] >> k) & 1:
                # add all k→* bits into i→*
                edges_bits[i] |= bk

    # remove any direct conflict edges (they may have been added via closure)
    for i in range(n):
        edges_bits[i] &= ~conflicts_bits[i]

    # build reverse‐lookup bitsets so we can prune “middle” edges fast
    rev_bits = [0] * n
    for i in range(n):
        b = edges_bits[i]
        while b:
            lb = b & -b
            j = lb.bit_length() - 1
            rev_bits[j] |= 1 << i
            b &= ~lb

    # for each conflict (i→k), remove every j→k where i→j
    for i in range(n):
        cb = conflicts_bits[i]
        while cb:
            lb = cb & -cb
            k = lb.bit_length() - 1
            mids = edges_bits[i] & rev_bits[k]
            while mids:
                mlb = mids & -mids
                j = mlb.bit_length() - 1
                edges_bits[j] &= ~(1 << k)
                rev_bits[k] &= ~(1 << j)
                mids &= ~mlb
            cb &= ~lb

    final = {
        (nodes[i], nodes[j])
        for i in range(n)
        for j in range(n)
        if (edges_bits[i] >> j) & 1
    }

    return Graph(frozenset(nodes), frozenset(final))
