from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Set, Tuple

import networkx as nx

from .activity import Activity
from .graph_base import GraphBacked
from .base import TaggedPOWL
from .partial_order import PartialOrder
from .types import ModelType
from ..utils.graph_sequentialization import split_graph_into_stages


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

    # --- start/end management ---
    def start_nodes(self) -> Set[TaggedPOWL]:
        return {v for v in self._g.successors(self._start) if isinstance(v, TaggedPOWL)}

    def end_nodes(self) -> Set[TaggedPOWL]:
        return {u for u in self._g.predecessors(self._end) if isinstance(u, TaggedPOWL)}

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
        Reduces silent activities by merging redundant edges, handling global self-loops,
        and abstracting isolated subgraphs that are dominated by a silent loop transition.
        """

        # 1. Trivial leaf self-loops
        for (u, v) in self.get_edges():
            if u == v:
                self.remove_edge(u, v)
                u.max_freq = None

        # 2. Recursively reduce children first
        node_map = {n: n.reduce_silent_activities() for n in self.get_nodes()}
        self._map_graph(node_map)

        def is_silent(n: Any) -> bool:
            return isinstance(n, Activity) and n.is_silent()

        changed = True
        while changed:

            changed = False
            silent_nodes = [n for n in self.get_nodes() if is_silent(n)]

            for tau in silent_nodes:

                if tau not in self._g.nodes:
                    continue

                preds = set(self._g.predecessors(tau))
                succs = set(self._g.successors(tau))

                # --- A: Simple Reduction (1-in or 1-out) --:
                if len(preds) <= 1 or len(succs) <= 1:
                    self._bypass_silent_node(tau, preds, succs)
                    changed = True

                # --- B: Loops ---
                else:
                    start_nodes = set(self._g.successors(self._start))
                    end_nodes = set(self._g.predecessors(self._end))

                    # B1: Global Skippable Self-Loop (Start -> tau -> End)
                    if start_nodes == {tau} == end_nodes:
                        self._g.remove_node(tau)
                        self.min_freq = 0
                        self.max_freq = None
                        for p in preds - {self._start}:
                            self.mark_end(p)
                        for s in succs - {self._end}:
                            self.mark_start(s)
                        changed = True

                    # B2: Global Non-Skippable Self-Loop
                    elif preds == end_nodes and succs == start_nodes:
                        self._g.remove_node(tau)
                        self.max_freq = None
                        changed = True

                    # B3: Isolated Loop Subgraph
                    else:
                        loop_body = self._find_loop_body(tau)
                        if loop_body:
                            self._abstract_loop_subgraph(tau, loop_body, preds, succs)
                            changed = True

        # 3. Final flattening
        if len(self.get_nodes()) == 1:
            return self._flatten_single_node()

        return self._abstract_sequences()


    def _abstract_self_loop(self) -> None:

        silent_nodes = [n for n in self.get_nodes() if isinstance(n, Activity) and n.is_silent()]
        start_nodes = set(self._g.successors(self._start))
        end_nodes = set(self._g.predecessors(self._end))

        for tau in silent_nodes:

            preds = set(self._g.predecessors(tau))
            succs = set(self._g.successors(tau))

            if preds == end_nodes and succs == start_nodes:
                self._g.remove_node(tau)
                self.max_freq = None
                return

        edges = self._g.edges()

        back_edges = []
        for u in end_nodes:
            for v in start_nodes:
                if (u, v) in edges:
                    back_edges.append((u, v))
                else:
                    return

        if back_edges:
            self.max_freq = None
            self._g.remove_edges_from(back_edges)
        else:
            raise ValueError("This code should be unreachable!")

    def _abstract_sequences(self) -> TaggedPOWL:
        """
        General sequential chunking for ChoiceGraph using dominators/post-dominators.

        Produces a sequential PartialOrder:
            chunk1 -> chunk2 -> chunk3 -> ...

        Each chunk may itself be complex (ChoiceGraph / PartialOrder / etc.).
        This is a generalization of head/tail peeling.

        Efficiency notes:
        - Uses dominator spines and a monotone assignment to avoid O(V * spine) scanning.
        - Avoids cloning nodes; builds induced subgraphs using original TaggedPOWL objects.
        - Merges away trivial boundary regions caused by artificial START/END nodes.
        """

        self._abstract_self_loop()

        G = self._g
        START = self._start
        END = self._end
        stages, is_skippable = split_graph_into_stages(G, START, END)
        if len(stages) < 2:
            raise Exception("Something went wrong!")
        if {START} != stages[0] or {END} != stages[-1]:
            raise Exception("Something went wrong!")
        stages = stages[1:-1]
        is_skippable = is_skippable[1:-1]

        if len(stages) < 2:
            return self

        def build_chunk(chunk_nodes: set[TaggedPOWL], skippable_chunk: bool) -> TaggedPOWL:

            if len(chunk_nodes) == 1:
                chunk_node = chunk_nodes.pop()
                if skippable_chunk:
                    chunk_node.min_freq = 0
                return chunk_node

            chunk_edges = [(u, v) for (u, v) in self.get_edges() if u in chunk_nodes and v in chunk_nodes]

            chunk_start: set[TaggedPOWL] = set()
            chunk_end: set[TaggedPOWL] = set()

            for n in chunk_nodes:
                preds = list(G.predecessors(n))
                succs = list(G.successors(n))

                if any(p not in chunk_nodes for p in preds):
                    chunk_start.add(n)
                if any(s not in chunk_nodes for s in succs):
                    chunk_end.add(n)

            sub = ChoiceGraph(
                nodes=chunk_nodes,
                edges=chunk_edges,
                start_nodes=chunk_start,
                end_nodes=chunk_end,
                min_freq= 0 if skippable_chunk else 1,
                max_freq=1,
            )

            return sub._abstract_sequences()

        chunks: list[TaggedPOWL] = [build_chunk(stages[i], is_skippable[i]) for i in range(len(stages))]

        po_edges = [(chunks[i], chunks[i + 1]) for i in range(len(chunks) - 1)]
        return PartialOrder(
            nodes=chunks,
            edges=po_edges,
            min_freq=self.min_freq,
            max_freq=self.max_freq,
        )

    def _flatten_single_node(self):
        assert len(self._g.edges) == 2  # assuming leaf-level self-loops were abstracted before
        remaining_node = self.get_nodes().pop()
        remaining_node.min_freq = min(remaining_node.min_freq, self.min_freq)
        if remaining_node.max_freq is None or self.max_freq is None:
            remaining_node.max_freq = None
        else:
            remaining_node.max_freq = max(self.max_freq, remaining_node.max_freq)
        return remaining_node

    def _bypass_silent_node(self, tau: TaggedPOWL, preds: Set[TaggedPOWL], succs: Set[TaggedPOWL]) -> None:
        """Removes tau and connects preds directly to succs."""
        for p in preds:
            for s in succs:
                if p is self._start and s is self._end:
                    self.min_freq = 0
                elif p is self._end or s is self._start:
                    raise ValueError("This code should be unreachable!")
                elif p == s:
                    p.max_freq = None  # Collapse local loop
                else:
                    self._g.add_edge(p, s)

        self._g.remove_node(tau)

    def _find_loop_body(self, tau: TaggedPOWL) -> Optional[Set[TaggedPOWL]]:
        """
        Finds a loop body where 'tau' is the unique entry and exit.
        Optimization: Uses intersection of descendants/ancestors instead of full SCCs.
        """
        # 1. Identify the SCC containing tau via set intersection
        body = nx.descendants(self._g, tau) & nx.ancestors(self._g, tau)

        if not body:
            return None

        # 2. Verify Isolation (Tau must be the ONLY gateway)
        for n in body:
            if any(p not in body and p is not tau for p in self._g.predecessors(n)):
                return None

            if any(s not in body and s is not tau for s in self._g.successors(n)):
                return None

        return body

    def _abstract_loop_subgraph(self, tau: TaggedPOWL, body: Set[TaggedPOWL],
                                preds: Set[TaggedPOWL], succs: Set[TaggedPOWL]) -> None:
        """Extracts 'body' into a new nested ChoiceGraph (0..*) and replaces it."""

        if len(body) == 1:
            new_node = body.pop()
            new_node.min_freq = 0
            new_node.max_freq = None
        else:
            sub_start = body.intersection(succs)
            sub_end = body.intersection(preds)
            sub_edges = [(u, v) for u, v in self.get_edges() if u in body and v in body]
            new_node = ChoiceGraph(
                nodes=body,
                edges=sub_edges,
                start_nodes=sub_start,
                end_nodes=sub_end,
                min_freq=0,
                max_freq=None
            )

        # Recurse immediately
        new_node = new_node.reduce_silent_activities()

        # Wire into parent
        for p in preds - body:
            self._g.add_edge(p, new_node)
        for s in succs - body:
            self._g.add_edge(new_node, s)
        self._g.remove_nodes_from(body)
        self._g.remove_node(tau)

    def _map_graph(self, node_map: dict) -> None:
        """Refreshes the internal graph structure based on a node mapping."""
        new_nodes = list(node_map.values())
        new_edges = [(node_map[u], node_map[v]) for u, v in self.get_edges()]
        old_start = self.start_nodes()
        old_end = self.end_nodes()

        self._g = nx.DiGraph()
        self._g.add_node(self._start)
        self._g.add_node(self._end)
        self.add_nodes(new_nodes)
        self.add_edges(new_edges)

        for n in old_start:
            self.mark_start(node_map[n])
        for n in old_end:
            self.mark_end(node_map[n])





