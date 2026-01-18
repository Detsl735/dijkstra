from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import List

from src.algo.dijkstra import Step

def export_steps(filepath: str, header: str, steps: List[Step]) -> str:
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(header)
    lines.append(f"Экспорт: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("-" * 80)
    for st in steps:
        lines.append(f"[{st.k:03d}] {st.action}: {st.details}")
    p.write_text("\n".join(lines), encoding="utf-8")
    return str(p)
