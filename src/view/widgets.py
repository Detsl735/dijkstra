from __future__ import annotations
import tkinter as tk
from tkinter import ttk

class LabeledEntry(ttk.Frame):
    def __init__(self, master, label: str, default: str = "", width: int = 10):
        super().__init__(master)
        self.var = tk.StringVar(value=default)
        ttk.Label(self, text=label).pack(side=tk.LEFT, padx=(0, 6))
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        self.var.set(value)
