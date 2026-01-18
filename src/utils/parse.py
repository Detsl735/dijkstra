from __future__ import annotations
from typing import List, Tuple
from src.algo.graph import Graph

def parse_edges_text(text: str) -> list[tuple[int, int, float]]:
    edges: list[tuple[int, int, float]] = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = line.replace(",", " ")
        parts = [p for p in line.split() if p]
        if len(parts) != 3:
            raise ValueError(f"Строка {line_no}: ожидается 'u v w', получено: {raw!r}")
        u = int(parts[0])
        v = int(parts[1])
        w = float(parts[2].replace(",", "."))
        edges.append((u, v, w))
    return edges

def build_graph(n: int, directed: bool, edges: list[tuple[int, int, float]]) -> Graph:
    if n <= 0:
        raise ValueError("n должно быть > 0")
    g = Graph.empty(n, directed)
    for (u, v, w) in edges:
        if u < 0 or v < 0 or u >= n or v >= n:
            raise ValueError(f"Вершины должны быть в диапазоне [0..{n-1}], получено ребро: {u} {v} {w}")
        g.add_edge(u, v, w)
    return g
