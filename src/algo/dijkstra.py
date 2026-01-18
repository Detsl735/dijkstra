from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import math
import heapq

from .graph import Graph

@dataclass
class Step:
    k: int
    action: str
    details: str
    visited: List[bool]
    dist: List[float]
    parent: List[Optional[int]]
    current: Optional[int]

def dijkstra_with_steps(g: Graph, s: int) -> tuple[List[float], List[Optional[int]], List[Step]]:
    n = g.n
    dist = [math.inf] * n
    parent: List[Optional[int]] = [None] * n
    visited = [False] * n

    dist[s] = 0.0
    pq: List[Tuple[float, int]] = [(0.0, s)]

    steps: List[Step] = []
    k = 0

    def snap(action: str, details: str, current: Optional[int]) -> None:
        nonlocal k
        k += 1
        steps.append(
            Step(
                k=k,
                action=action,
                details=details,
                visited=visited.copy(),
                dist=dist.copy(),
                parent=parent.copy(),
                current=current
            )
        )

    snap("init", f"Стартовая вершина s={s}", current=s)

    while pq:
        d, u = heapq.heappop(pq)
        snap("pop", f"Извлечено из очереди: (расст={d:g}, v={u})", current=u)

        if visited[u]:
            snap("skip", f"Вершина {u} уже обработана, пропуск.", current=u)
            continue

        visited[u] = True
        snap("visit", f"Помечаем вершину {u} как обработанную.", current=u)

        for v, w in g.adj[u]:
            if w < 0:
                raise ValueError("Дейкстра не работает с отрицательными весами (w < 0).")
            if visited[v]:
                snap("relax_skip", f"Сосед {v} уже обработан, ребро {u}->{v} пропуск.", current=u)
                continue

            nd = dist[u] + w
            if nd < dist[v]:
                old = dist[v]
                dist[v] = nd
                parent[v] = u
                heapq.heappush(pq, (nd, v))
                snap(
                    "relax",
                    f"Улучшение {u}->{v} (w={w:g}): расст[{v}] {old:g} -> {nd:g}, предок[{v}]={u}. Добавляем в очередь.",
                    current=u
                )
            else:
                snap(
                    "no_relax",
                    f"Нет улучшения для {u}->{v} (w={w:g}): расст[{v}]={dist[v]:g}, новое={nd:g}.",
                    current=u
                )

    snap("done", "Очередь пуста. Алгоритм завершён.", current=None)
    return dist, parent, steps

def restore_path(parent: List[Optional[int]], s: int, t: int) -> List[int]:
    if s == t:
        return [s]
    path: List[int] = []
    cur: Optional[int] = t
    while cur is not None:
        path.append(cur)
        if cur == s:
            break
        cur = parent[cur]
    path.reverse()
    if not path or path[0] != s:
        return []
    return path
