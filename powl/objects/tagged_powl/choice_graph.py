from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Set, Tuple, List

import networkx as nx

from .activity import Activity
from .graph_base import GraphBacked
from .base import TaggedPOWL
from .partial_order import PartialOrder
from .types import ModelType


# Internal nodes (not TaggedPOWL; users shouldn't ever touch them)
@dataclass(frozen=True, slots=True)
class _ChoiceGraphStart:
    def __repr__(self) -> str:
        return "_ChoiceGraphStart()"


@dataclass(frozen=True, slots=True)
class _ChoiceGraphEnd:
    def __repr__(self) -> str:
        return "_ChoiceGraphEnd()"


class ChoiceGraph(GraphBacked):
    """
    ChoiceGraph:
      - Directed graph among TaggedPOWL nodes
      - Has internal START and END nodes
      - Start marking is encoded as START -> node edges
      - End marking is encoded as node -> END edges

    API:
      - mark_start / unmark_start
      - mark_end / unmark_end
      - start_nodes / end_nodes
      - add/remove nodes/edges
    """

    __slots__ = ("_start", "_end")

    def __init__(
        self,
        nodes: Optional[Iterable[TaggedPOWL]] = None,
        edges: Optional[Iterable[Tuple[TaggedPOWL, TaggedPOWL]]] = None,
        *,
        start_nodes: Optional[Iterable[TaggedPOWL]] = None,
        end_nodes: Optional[Iterable[TaggedPOWL]] = None,
        min_freq: int = 1,
        max_freq: Optional[int] = 1,
    ) -> None:
        super().__init__(ModelType.ChoiceGraph, min_freq=min_freq, max_freq=max_freq)

        self._start = _ChoiceGraphStart()
        self._end = _ChoiceGraphEnd()
        self._g.add_node(self._start)
        self._g.add_node(self._end)

        if nodes is not None:
            self.add_nodes(nodes)
        if edges is not None:
            self.add_edges(edges)
        if start_nodes is not None:
            for n in start_nodes:
                self.mark_start(n)
        if end_nodes is not None:
            for n in end_nodes:
                self.mark_end(n)

    def validate_connectivity(self) -> None:

        # Every node must be on a path START -> ... -> END
        # Equivalent: reachable from START AND can reach END.
        reachable_from_start = nx.descendants(self._g, self._start)
        can_reach_end = nx.ancestors(self._g, self._end)

        for n in self.get_nodes():
            if (n not in reachable_from_start) or (n not in can_reach_end):
                raise ValueError(
                    "ChoiceGraph validity failed: every user node must lie on a path "
                    "from START to END. "
                    f"This node violate the requirement: {n}"
                )

    # --- override node selection to exclude internal ---
    def get_nodes(self) -> Set[TaggedPOWL]:
        return {n for n in self._g.nodes if isinstance(n, TaggedPOWL)}

    def get_edges(self) -> Set[Tuple[TaggedPOWL, TaggedPOWL]]:
        out: Set[Tuple[TaggedPOWL, TaggedPOWL]] = set()
        for u, v in self._g.edges:
            if isinstance(u, TaggedPOWL) and isinstance(v, TaggedPOWL):
                out.add((u, v))
        return out

    def predecessors(self, node: TaggedPOWL) -> Set[TaggedPOWL]:
        return {p for p in self._g.predecessors(node) if isinstance(p, TaggedPOWL)}

    def successors(self, node: TaggedPOWL) -> Set[TaggedPOWL]:
        return {s for s in self._g.successors(node) if isinstance(s, TaggedPOWL)}

    def boundary_edges(self) -> Set[Tuple[object, object]]:
        """Edges involving START or END (useful for debugging/visualization)."""
        out: Set[Tuple[object, object]] = set()
        for u, v in self._g.edges:
            if u in (self._start, self._end) or v in (self._start, self._end):
                out.add((u, v))
        return out

    # --- start/end management ---
    def start_nodes(self) -> Set[TaggedPOWL]:
        return {v for v in self._g.successors(self._start)}

    def end_nodes(self) -> Set[TaggedPOWL]:
        return {u for u in self._g.predecessors(self._end)}

    def is_start(self, node: TaggedPOWL) -> bool:
        return self._g.has_edge(self._start, node)

    def is_end(self, node: TaggedPOWL) -> bool:
        return self._g.has_edge(node, self._end)

    def mark_start(self, node: TaggedPOWL) -> None:
        self.add_node(node)
        self._g.add_edge(self._start, node)

    def unmark_start(self, node: TaggedPOWL) -> None:
        if self._g.has_edge(self._start, node):
            self._g.remove_edge(self._start, node)

    def mark_end(self, node: TaggedPOWL) -> None:
        self.add_node(node)
        self._g.add_edge(node, self._end)

    def unmark_end(self, node: TaggedPOWL) -> None:
        if self._g.has_edge(node, self._end):
            self._g.remove_edge(node, self._end)

    def set_start_nodes(self, nodes: Iterable[TaggedPOWL]) -> None:
        # clear existing
        for n in list(self.start_nodes()):
            self.unmark_start(n)
        for n in nodes:
            self.mark_start(n)

    def set_end_nodes(self, nodes: Iterable[TaggedPOWL]) -> None:
        for n in list(self.end_nodes()):
            self.unmark_end(n)
        for n in nodes:
            self.mark_end(n)

    def pretty(self) -> str:
        return (
            "ChoiceGraph(\n"
            f"  nodes={len(self.get_nodes())}, edges={len(self.get_edges())},\n"
            f"  start_nodes={len(self.start_nodes())}, end_nodes={len(self.end_nodes())},\n"
            f"  min={self.min_freq}, max={self.max_freq}\n"
            ")"
        )

    def clone(self, *, deep: bool = True) -> "ChoiceGraph":
        # Rebuild while preserving start/end marks and user edges
        new = ChoiceGraph(
            nodes=self.get_nodes(),
            edges=self.get_edges(),
            start_nodes=self.start_nodes(),
            end_nodes=self.end_nodes(),
            min_freq=self.min_freq,
            max_freq=self.max_freq,
        )
        return new

    def to_dict(self) -> dict[str, Any]:

        nodes = list(self.get_nodes())
        idx = {n: i for i, n in enumerate(nodes)}
        edges = [(idx[u], idx[v]) for (u, v) in self.get_edges()]
        start = [idx[n] for n in self.start_nodes() if n in idx]
        end = [idx[n] for n in self.end_nodes() if n in idx]

        return {
            "type": self.model_type.value,
            "min_freq": self.min_freq,
            "max_freq": self.max_freq,
            "nodes": [n.to_dict() for n in nodes],
            "edges": edges,
            "start_nodes": start,
            "end_nodes": end,
        }

    def reduce_silent_activities(self) -> TaggedPOWL:
        """
        Reduce silent Activity nodes ONLY when they have exactly one incoming
        arc and one outgoing arc (considering START/END boundary arcs too).

        For such a node τ with pred -> τ -> succ, add pred -> succ and remove τ.
        """
        old_nodes = list(self.get_nodes())
        node_map = {n: n.reduce_silent_activities() for n in old_nodes}

        new = ChoiceGraph(
            nodes=node_map.values(),
            edges=((node_map[u], node_map[v]) for (u, v) in self.get_edges()),
            start_nodes=(node_map[n] for n in self.start_nodes()),
            end_nodes=(node_map[n] for n in self.end_nodes()),
            min_freq=self.min_freq,
            max_freq=self.max_freq,
        )

        node_map[self._start] = new._start
        node_map[self._end] = new._end

        def is_silent_activity(n: object) -> bool:
            return isinstance(n, Activity) and n.is_silent()

        changed = True
        while changed:
            changed = False
            silent_nodes = [n for n in list(new.get_nodes()) if is_silent_activity(n)]
            if not silent_nodes:
                break

            for tau in silent_nodes:

                preds = list(new._g.predecessors(tau))
                succs = list(new._g.successors(tau))

                # if len(preds) == 1 == len(succs):
                if len(preds) <= 1 or len(succs) <= 1:
                    for p in preds:
                        for s in succs:
                            # p = preds[0]
                            # s = succs[0]
                            if p is new._start and s is new._end:
                                new.min_freq = 0
                            elif p is new._end and s is new._start:
                                new.max_freq = None
                            elif p == s:
                                p.max_freq = None
                            else:
                                new._g.add_edge(p, s)

                    new._g.remove_node(tau)
                    changed = True
                else:
                    shared = {n for n in preds if n in succs}
                    if len(shared) == 1:
                        shared_node = shared.pop()
                        if shared_node not in silent_nodes:
                            preds_shared = list(new._g.predecessors(shared_node))
                            succs_shared = list(new._g.successors(shared_node))

                            if {n for n in preds_shared if n in succs_shared} == {tau}:
                                shared_node.min_freq = 0
                                shared_node.max_freq = None
                                for p in set(preds) - {shared_node}:
                                    new._g.add_edge(p, shared_node)
                                for s in set(succs) - {shared_node}:
                                    new._g.add_edge(shared_node, s)
                                new._g.remove_node(tau)
                                changed = True



        if len(new.get_nodes()) == 1:
            assert len(new._g.edges) == 2
            remaining_node = new.get_nodes().pop()
            remaining_node.min_freq = min(remaining_node.min_freq, new.min_freq)
            if remaining_node.max_freq is None or new.max_freq is None:
                remaining_node.max_freq = None
            else:
                remaining_node.max_freq = max(new.max_freq, remaining_node.max_freq)
            return remaining_node

        return new.abstract_head_tail_sequences()

    def abstract_head_tail_sequences(self) -> TaggedPOWL:
        """
        Turn this ChoiceGraph into a PartialOrder consisting of:
          [head_seq_nodes..., middle_choice_graph, tail_seq_nodes...]

        - head_seq_nodes: maximal deterministic chain from START
        - tail_seq_nodes: maximal deterministic chain into END
        - middle_choice_graph: the remaining ChoiceGraph after peeling head/tail

        If the whole model is pure sequential, returns a PartialOrder over all user nodes/edges.
        """

        # ---- collect prefix from START ----
        head: List[TaggedPOWL] = []
        cur: object = self._start

        while self._g.out_degree(cur) == 1:
            nxt = next(iter(self._g.successors(cur)))

            # Pure Concurrency
            if nxt is self._end:
                assert len(head) == len(self.get_nodes())
                po = PartialOrder(
                    nodes=list(self.get_nodes()),
                    edges=list(self.get_edges()),
                    min_freq=self.min_freq,
                    max_freq=self.max_freq,
                )
                return po

            head.append(nxt)
            cur = nxt

        # ---- collect suffix into END ----
        tail: List[TaggedPOWL] = []
        cur = self._end
        while self._g.in_degree(cur) == 1:
            prev = next(iter(self._g.predecessors(cur)))
            if prev is self._start:
                break
            tail.insert(0, prev)
            cur = prev


        shared = [n for n in head if n in tail]
        if len(shared) > 0:
            # This may happen in case of a loop
            assert len(shared) == 1
            shared_node = list(shared)[0]
            assert shared_node == head[-1] == tail[0]
            head = head[:-1]
            tail = tail[1:]

        head_set = set(head)
        tail_set = set(tail)

        assert len(head_set | tail_set) < len(self.get_nodes())

        if len(head) == 0 and len(tail) == 0:
            return self

        middle_nodes = [n for n in self.get_nodes() if n not in head_set and n not in tail_set]

        middle_edges = [
            (u, v)
            for (u, v) in self.get_edges()
            if (u not in head_set and v not in head_set and u not in tail_set and v not in tail_set)
        ]

        middle_empty_path = False

        # start nodes for middle:
        if head:
            last_head = head[-1]
            middle_start_nodes = [
                x for x in self.successors(last_head)
            ]
            if not tail:
                middle_empty_path = self._g.has_edge(last_head, self._end)
        else:
            middle_start_nodes = {n for n in self.start_nodes() if n in middle_nodes}

        # end nodes for middle:
        if tail:
            first_tail = tail[0]
            middle_end_nodes = [
                x for x in self.predecessors(first_tail)
            ]
            if head:
                middle_empty_path = self._g.has_edge(head[-1], first_tail)
            else:
                middle_empty_path = self._g.has_edge(self._start, first_tail)
        else:
            middle_end_nodes = {n for n in self.end_nodes() if n in middle_nodes}


        if len(middle_nodes) == 1:
            middle = middle_nodes[0].clone(deep=True)
            if middle_empty_path:
                middle.min_freq = 0
        else:
            middle_min_freq = 0 if middle_empty_path else 1
            middle = ChoiceGraph(
                nodes=middle_nodes,
                edges=middle_edges,
                start_nodes=middle_start_nodes,
                end_nodes=middle_end_nodes,
                min_freq=middle_min_freq,
                max_freq=1,
            )
            middle = middle.abstract_head_tail_sequences()

        # ---------- wrap into PartialOrder: head -> middle -> tail ----------
        seq_nodes: List[TaggedPOWL] = []
        seq_nodes.extend(head)
        seq_nodes.append(middle)
        seq_nodes.extend(tail)

        seq_edges = [(seq_nodes[i], seq_nodes[i + 1]) for i in range(len(seq_nodes) - 1)]

        po = PartialOrder(
            nodes=seq_nodes,
            edges=seq_edges,
            min_freq=self.min_freq,
            max_freq=self.max_freq,
        )

        return po