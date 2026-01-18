from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import math
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.view.widgets import LabeledEntry
from src.utils.parse import parse_edges_text, build_graph
from src.utils.export_txt import export_steps
from src.algo.dijkstra import dijkstra_with_steps, restore_path, Step


ACTION_RU = {
    "init": "Инициализация",
    "pop": "Извлечение из очереди",
    "skip": "Пропуск (уже обработана)",
    "visit": "Посещение вершины",
    "relax": "Улучшение",
    "no_relax": "Без улучшения",
    "relax_skip": "Пропуск ребра (сосед обработан)",
    "done": "Завершение",
}


def _bool_ru(x: bool) -> str:
    return "да" if x else "нет"


class MainWindow(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        master.title("Алгоритм Дейкстры")
        master.minsize(1200, 700)

        self.master = master
        self.steps: list[Step] = []
        self.g = None
        self.positions = None
        self.last_header = ""

        self._build_ui()
        self._build_plot()

    def _build_ui(self) -> None:
        root = self
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)

        top = ttk.LabelFrame(root, text="Ввод данных", padding=10)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.n_entry = LabeledEntry(top, "Число вершин n:", "6", width=8)
        self.n_entry.grid(row=0, column=0, sticky="w", padx=(0, 12))

        ttk.Label(top, text="Граф:").grid(row=0, column=1, sticky="w")
        self.directed_var = tk.BooleanVar(value=False)
        ttk.Radiobutton(
            top, text="неориентированный",
            variable=self.directed_var, value=False
        ).grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(
            top, text="ориентированный",
            variable=self.directed_var, value=True
        ).grid(row=0, column=3, sticky="w", padx=(8, 0))

        self.s_entry = LabeledEntry(top, "Старт s:", "0", width=6)
        self.t_entry = LabeledEntry(top, "Цель t:", "4", width=6)
        self.s_entry.grid(row=0, column=4, sticky="w", padx=(18, 8))
        self.t_entry.grid(row=0, column=5, sticky="w")

        ttk.Button(top, text="Запустить алгоритм", command=self.on_run).grid(row=0, column=6, padx=(18, 6))
        ttk.Button(top, text="Шаг вперёд", command=self.on_step).grid(row=0, column=7, padx=(6, 6))
        ttk.Button(top, text="Экспорт лога", command=self.on_export).grid(row=0, column=8, padx=(6, 0))

        edges_frame = ttk.LabelFrame(root, text="Список рёбер (u v w), вершины 0..n-1", padding=10)
        edges_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        edges_frame.columnconfigure(0, weight=1)

        self.edges_text = tk.Text(edges_frame, height=8, wrap="none")
        self.edges_text.grid(row=0, column=0, sticky="ew")
        self.edges_text.insert(
            "1.0",
            "0 1 7\n0 2 9\n0 5 14\n1 2 10\n1 3 15\n2 3 11\n2 5 2\n3 4 6\n4 5 9\n"
        )

        log_frame = ttk.LabelFrame(root, text="Ход решения", padding=10)
        log_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        dist_frame = ttk.LabelFrame(root, text="Результаты", padding=10)
        dist_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        dist_frame.rowconfigure(0, weight=1)
        dist_frame.columnconfigure(0, weight=1)

        cols = ("v", "dist", "parent", "visited")
        self.tree = ttk.Treeview(dist_frame, columns=cols, show="headings", height=10)

        # ✅ Заголовки колонок на русском
        self.tree.heading("v", text="Вершина")
        self.tree.heading("dist", text="Расстояние")
        self.tree.heading("parent", text="Предок")
        self.tree.heading("visited", text="Обработана")

        self.tree.column("v", width=80, anchor="center")
        self.tree.column("dist", width=180, anchor="w")
        self.tree.column("parent", width=120, anchor="center")
        self.tree.column("visited", width=120, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")

        sb2 = ttk.Scrollbar(dist_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb2.set)
        sb2.grid(row=0, column=1, sticky="ns")

        self.step_idx = 0

    def _build_plot(self) -> None:
        plot_frame = ttk.LabelFrame(self, text="Граф", padding=10)
        plot_frame.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=5, pady=5)
        self.columnconfigure(2, weight=2)
        self.rowconfigure(2, weight=1)

        self.fig = Figure(figsize=(5.8, 5.8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_off()

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _set_log(self, text: str) -> None:
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, text)

    def _append_log(self, line: str) -> None:
        self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)

    def _fill_table(self, step: Step) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for v in range(len(step.dist)):
            d = step.dist[v]
            d_str = "∞" if math.isinf(d) else f"{d:.10g}"
            p = "—" if step.parent[v] is None else str(step.parent[v])
            vis = _bool_ru(step.visited[v])
            self.tree.insert("", "end", values=(v, d_str, p, vis))

    def _layout_positions(self, n: int) -> np.ndarray:
        angles = np.linspace(0, 2*np.pi, n, endpoint=False)
        x = np.cos(angles)
        y = np.sin(angles)
        return np.column_stack([x, y])

    def _draw_graph(self, highlight_path: list[int] | None, current: int | None, visited: list[bool] | None) -> None:
        self.ax.clear()
        self.ax.set_axis_off()
        if self.g is None or self.positions is None:
            self.canvas.draw()
            return

        g = self.g
        pos = self.positions

        drawn = set()
        for u in range(g.n):
            for v, w in g.adj[u]:
                if not g.directed:
                    key = tuple(sorted((u, v)))
                    if key in drawn:
                        continue
                    drawn.add(key)

                x1, y1 = pos[u]
                x2, y2 = pos[v]
                self.ax.plot([x1, x2], [y1, y2])
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.ax.text(mx, my, f"{w:g}", fontsize=9)

                if g.directed:
                    self.ax.annotate(
                        "", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="->")
                    )

        if highlight_path and len(highlight_path) >= 2:
            for a, b in zip(highlight_path, highlight_path[1:]):
                x1, y1 = pos[a]
                x2, y2 = pos[b]
                self.ax.plot([x1, x2], [y1, y2], linewidth=3)

        for i in range(g.n):
            x, y = pos[i]
            if current is not None and i == current:
                self.ax.scatter([x], [y], s=220)
            elif visited is not None and visited[i]:
                self.ax.scatter([x], [y], s=160)
            else:
                self.ax.scatter([x], [y], s=120)
            self.ax.text(x, y, f"{i}", ha="center", va="center", fontsize=10)

        self.canvas.draw()

    def _build_problem(self):
        try:
            n = int(self.n_entry.get().strip())
            s = int(self.s_entry.get().strip())
            t = int(self.t_entry.get().strip())
            directed = bool(self.directed_var.get())
            edges = parse_edges_text(self.edges_text.get("1.0", tk.END))
            g = build_graph(n, directed, edges)
            if s < 0 or s >= n or t < 0 or t >= n:
                raise ValueError("s и t должны быть в диапазоне 0..n-1")
            return g, s, t
        except Exception as e:
            raise ValueError(str(e))

    def on_run(self) -> None:
        try:
            self.g, s, t = self._build_problem()
            self.positions = self._layout_positions(self.g.n)

            dist, parent, steps = dijkstra_with_steps(self.g, s)
            self.steps = steps
            self.step_idx = 0

            directed_ru = "да" if self.g.directed else "нет"
            self.last_header = f"Алгоритм Дейкстры: n={self.g.n}, ориентированный={directed_ru}, s={s}, t={t}"

            path = restore_path(parent, s, t)
            if path:
                msg = f"Кратчайший путь: {' -> '.join(map(str, path))}\nДлина: {dist[t]:.10g}"
            else:
                msg = "Путь не найден (граф может быть несвязным)."

            self._set_log("")
            self._append_log(self.last_header)
            self._append_log("-" * 60)
            self._append_log(msg)
            self._append_log("-" * 60)

            self._draw_graph(highlight_path=path if path else None, current=None, visited=None)

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_step(self) -> None:
        if not self.steps:
            messagebox.showwarning("Нет данных", "Сначала запусти алгоритм.")
            return
        if self.step_idx >= len(self.steps):
            messagebox.showinfo("Готово", "Шаги закончились.")
            return

        st = self.steps[self.step_idx]
        self.step_idx += 1

        action_ru = ACTION_RU.get(st.action, st.action)
        self._append_log(f"[{st.k:03d}] {action_ru}: {st.details}")
        self._fill_table(st)

        self._draw_graph(highlight_path=None, current=st.current, visited=st.visited)

    def on_export(self) -> None:
        if not self.steps:
            messagebox.showwarning("Нет данных", "Сначала запусти алгоритм.")
            return
        path = filedialog.asksaveasfilename(
            title="Экспорт лога",
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt")]
        )
        if not path:
            return
        try:
            saved = export_steps(path, self.last_header or "Алгоритм Дейкстры", self.steps)
            messagebox.showinfo("Сохранено", f"Файл сохранён:\n{saved}")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))


def run_app() -> None:
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("vista")
    except Exception:
        pass
    MainWindow(root).pack(fill=tk.BOTH, expand=True)
    root.mainloop()
