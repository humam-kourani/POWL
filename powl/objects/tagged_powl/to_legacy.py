from __future__ import annotations

from powl.objects.BinaryRelation import BinaryRelation
from powl.objects.obj import POWL, SilentTransition, Transition, StrictPartialOrder, DecisionGraph, OperatorPOWL, Operator
from powl.objects.tagged_powl.activity import Activity
from powl.objects.tagged_powl.base import TaggedPOWL
from powl.objects.tagged_powl.choice_graph import ChoiceGraph
from powl.objects.tagged_powl.partial_order import PartialOrder


def _strip_freq(n: TaggedPOWL) -> TaggedPOWL:
    """
    Clone without frequency effects (used before wrapping with XOR/LOOP).
    """
    c = n.clone()
    c.set_freqs(min_freq=1, max_freq=1)
    return c

def convert_tagged_powl_to_legacy_model(model: TaggedPOWL) -> POWL:

    def rec(n: TaggedPOWL):

        if n.is_repeatable():
            if n.is_skippable():
                body = rec(_strip_freq(n))
                loop = OperatorPOWL(operator=Operator.LOOP, children=[SilentTransition(), body])
                return loop
            else:
                body = rec(_strip_freq(n))
                loop = OperatorPOWL(operator=Operator.LOOP, children=[body, SilentTransition()])
                return loop
        elif n.is_skippable():
            body = rec(_strip_freq(n))
            xor = OperatorPOWL(
                operator=Operator.XOR,
                children=[body, SilentTransition()],
            )
            return xor

        if isinstance(n, Activity):
            old = SilentTransition() if n.is_silent() else Transition(n.label)
            return old

        if isinstance(n, PartialOrder):
            new_nodes = list(n.get_nodes())
            old_nodes = [rec(x) for x in new_nodes]
            m = {new_nodes[i]: old_nodes[i] for i in range(len(new_nodes))}

            po = StrictPartialOrder(old_nodes)
            for u, v in n.get_edges():
                po.add_edge(m[u], m[v])
            return po

        if isinstance(n, ChoiceGraph):
            new_nodes = list(n.get_nodes())
            old_nodes = [rec(x) for x in new_nodes]
            m = {new_nodes[i]: old_nodes[i] for i in range(len(new_nodes))}

            rel = BinaryRelation(old_nodes)
            for u, v in n.get_edges():
                rel.add_edge(m[u], m[v])

            start_old = [m[x] for x in n.start_nodes()]
            end_old = [m[x] for x in n.end_nodes()]

            cg = DecisionGraph(rel, start_nodes=start_old, end_nodes=end_old, empty_path=False)
            return cg

        raise TypeError(f"Unsupported model type: {type(n).__name__}")

    return rec(model)
