from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class Graph:
    n: int
    directed: bool
    adj: List[List[Tuple[int, float]]]

    @staticmethod
    def empty(n: int, directed: bool) -> "Graph":
        return Graph(n=n, directed=directed, adj=[[] for _ in range(n)])

    def add_edge(self, u: int, v: int, w: float) -> None:
        self.adj[u].append((v, w))
        if not self.directed and u != v:
            self.adj[v].append((u, w))
