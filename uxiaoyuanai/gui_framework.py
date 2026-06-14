#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易 Tkinter GUI 框架

这个模块只使用 Python 标准库，提供窗口创建、表单布局、日志面板、进度面板和异步任务调度等基础组件。
"""

import json
import os
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Tuple

JsonDict = Dict[str, Any]
GuiCallback = Callable[..., None]


class GUIApplication:
    """基础应用窗口类"""

    def __init__(self, title: str = "应用", size: str = "900x700", resizable: Tuple[bool, bool] = (True, True)):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(size)
        self.root.resizable(resizable[0], resizable[1])
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def close(self) -> None:
        self.root.quit()

    def run(self) -> None:
        self.root.mainloop()

    def schedule(self, delay_ms: int, callback: GuiCallback, *args: Any, **kwargs: Any) -> None:
        self.root.after(delay_ms, lambda: callback(*args, **kwargs))

    def create_frame(self, **options: Any) -> ttk.Frame:
        frame = ttk.Frame(self.root, **options)
        return frame

    def create_label_frame(self, text: str, **options: Any) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self.root, text=text, **options)
        return frame


class FormBuilder:
    """表单布局辅助类"""

    def __init__(self, parent: tk.Widget, label_width: int = 12, padding: Tuple[int, int] = (5, 5)):
        self.parent = parent
        self.label_width = label_width
        self.padding = padding
        self.row = 0
        self.fields: Dict[str, tk.Widget] = {}

    def add_row(self, label_text: str, widget: tk.Widget, expand: bool = True) -> tk.Widget:
        label = ttk.Label(self.parent, text=label_text, width=self.label_width, anchor="w")
        label.grid(row=self.row, column=0, sticky="w", padx=self.padding[0], pady=self.padding[1])
        widget.grid(row=self.row, column=1, sticky="we" if expand else "w", padx=self.padding[0], pady=self.padding[1])
        self.parent.grid_columnconfigure(1, weight=1)
        self.fields[label_text] = widget
        self.row += 1
        return widget

    def add_entry(self, label_text: str, width: int = 24, show: Optional[str] = None) -> ttk.Entry:
        entry = ttk.Entry(self.parent, width=width, show=show)
        return self.add_row(label_text, entry)

    def add_combobox(self, label_text: str, values: Sequence[str], width: int = 24) -> ttk.Combobox:
        combo = ttk.Combobox(self.parent, values=list(values), width=width)
        return self.add_row(label_text, combo)

    def add_checkbutton(self, label_text: str, variable: tk.Variable) -> ttk.Checkbutton:
        button = ttk.Checkbutton(self.parent, text=label_text, variable=variable)
        return self.add_row("", button, expand=False)

    def get(self, label_text: str) -> Optional[tk.Widget]:
        return self.fields.get(label_text)


class LogPanel:
    """日志面板，支持追加日志和自动滚动"""

    def __init__(self, parent: tk.Widget, height: int = 16):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.text = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, height=height, state=tk.NORMAL)
        self.text.pack(fill=tk.BOTH, expand=True)

    def append(self, message: str, timestamp: bool = True) -> None:
        if timestamp:
            message = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        self.text.configure(state=tk.NORMAL)
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)
        self.text.configure(state=tk.DISABLED)

    def clear(self) -> None:
        self.text.configure(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.configure(state=tk.DISABLED)


class ProgressPanel:
    """进度面板，显示百分比和统计标签"""

    def __init__(self, parent: tk.Widget):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, pady=5)
        self.var = tk.DoubleVar(value=0.0)
        self.bar = ttk.Progressbar(self.frame, variable=self.var, maximum=100)
        self.bar.pack(fill=tk.X, pady=5)

        self.label_frame = ttk.Frame(self.frame)
        self.label_frame.pack(fill=tk.X)
        self.labels: Dict[str, ttk.Label] = {}

    def add_label(self, name: str, text: str) -> ttk.Label:
        label = ttk.Label(self.label_frame, text=text)
        label.pack(side=tk.LEFT, padx=8)
        self.labels[name] = label
        return label

    def update_label(self, name: str, text: str) -> None:
        label = self.labels.get(name)
        if label:
            label.config(text=text)

    def set_percent(self, value: float) -> None:
        self.var.set(max(0.0, min(value, 100.0)))


class AsyncTask:
    """异步任务调度器，支持后台执行并回调主线程"""

    def __init__(self, app: GUIApplication):
        self.app = app

    def start(self, func: Callable[[], Any], on_success: Optional[Callable[[Any], None]] = None, on_error: Optional[Callable[[Exception], None]] = None) -> None:
        def worker() -> None:
            try:
                result = func()
                if on_success:
                    self.app.schedule(0, on_success, result)
            except Exception as exc:
                if on_error:
                    self.app.schedule(0, on_error, exc)
                else:
                    self.app.schedule(0, self._default_error_handler, exc)

        threading.Thread(target=worker, daemon=True).start()

    def _default_error_handler(self, exc: Exception) -> None:
        messagebox.showerror("错误", str(exc))


class JsonConfig:
    """JSON 配置存储器"""

    def __init__(self, path: str):
        self.path = path
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def load(self) -> JsonDict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return {}

    def save(self, data: JsonDict) -> bool:
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False


def show_info(title: str, message: str) -> None:
    messagebox.showinfo(title, message)


def show_warning(title: str, message: str) -> None:
    messagebox.showwarning(title, message)


def show_error(title: str, message: str) -> None:
    messagebox.showerror(title, message)


if __name__ == "__main__":
    app = GUIApplication(title="测试 GUI 框架", size="640x480")
    frame = app.create_frame(padding=10)
    frame.pack(fill=tk.BOTH, expand=True)

    form = FormBuilder(frame)
    form.add_entry("用户名:")
    form.add_entry("密码:", show="*")
    form.add_row("备注:", ttk.Entry(frame, width=32))

    progress = ProgressPanel(frame)
    progress.add_label("status", "状态: 初始化")
    progress.set_percent(20)

    log = LogPanel(frame)
    log.append("框架初始化完成")

    app.run()
