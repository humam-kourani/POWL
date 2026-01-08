from __future__ import annotations

from typing import Any, Iterable, Optional, Tuple

import networkx as nx

from .activity import Activity
from .graph_base import GraphBacked
from .base import TaggedPOWL
from .types import ModelType


class PartialOrder(GraphBacked):

    def __init__(
        self,
        nodes: Optional[Iterable[TaggedPOWL]] = None,
        edges: Optional[Iterable[Tuple[TaggedPOWL, TaggedPOWL]]] = None,
        *,
        min_freq: int = 1,
        max_freq: Optional[int] = 1,
    ) -> None:
        super().__init__(ModelType.PartialOrder, min_freq=min_freq, max_freq=max_freq)

        if nodes is not None:
            self.add_nodes(nodes)
        if edges is not None:
            for u, v in edges:
                self.add_edge(u, v)

    def validate(self) -> None:
        # For a partial order represented as a DAG, acyclicity is the key structural requirement.
        if not nx.is_directed_acyclic_graph(self._g):
            cycle = nx.find_cycle(self._g, orientation="original")
            raise ValueError(f"PartialOrder must be acyclic. Found cycle: {cycle}")

    def validate_and_remove_transitive_edges(self) -> None:
        try:
            self._g = nx.transitive_reduction(self._g)
        except Exception as e:
            cycle = nx.find_cycle(self._g, orientation="original")
            raise ValueError(f"PartialOrder must be acyclic. Found cycle: {cycle}")

    def get_transitive_closure(self, fail_if_cyclic=True) -> nx.DiGraph:
        if fail_if_cyclic:
            return nx.transitive_closure_dag(self._g)
        else:
            return nx.transitive_closure(self._g)

    def pretty(self) -> str:
        return (
            "PartialOrder(\n"
            f"  nodes={len(self.get_nodes())}, edges={len(self.get_edges())},\n"
            f"  min={self.min_freq}, max={self.max_freq}\n"
            ")"
        )

    def to_dict(self) -> dict[str, Any]:
        nodes = list(self.get_nodes())
        idx = {n: i for i, n in enumerate(nodes)}
        edges = [(idx[u], idx[v]) for (u, v) in self.get_edges()]
        return {
            "type": self.model_type.value,
            "min_freq": self.min_freq,
            "max_freq": self.max_freq,
            "nodes": [n.to_dict() for n in nodes],
            "edges": edges,
        }

    def reduce_silent_activities(self) -> "PartialOrder":

        old_nodes = list(self.get_nodes())
        node_map = {n: n.reduce_silent_activities() for n in old_nodes}

        new = PartialOrder(
            nodes=node_map.values(),
            edges=((node_map[u], node_map[v]) for (u, v) in self.get_edges()),
            min_freq=self.min_freq,
            max_freq=self.max_freq,
        )

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

                if len(preds) <= 1 or len(succs) <= 1:
                    for p in preds:
                        for s in succs:
                            new.add_edge(p, s)

                    new._g.remove_node(tau)
                    changed = True

        return new
