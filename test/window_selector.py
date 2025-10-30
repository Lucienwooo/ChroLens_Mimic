# ...existing code...
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import win32gui

def _enum_taskbar_titles():
    exclude_keywords = [
        "設定", "windows 輸入體驗", "windows input experience",
        "searchui", "cortana", "開始功能表", "start menu",
        "工作管理員", "task manager", "lockapp", "shell experience host",
        "runtimebroker", "searchapp"
    ]
    items = []
    def enum_handler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title.strip():
                tl = title.strip()
                tl_low = tl.lower()
                if not any(k in tl_low for k in exclude_keywords):
                    items.append((hwnd, tl))
    win32gui.EnumWindows(enum_handler, None)
    return items

class WindowSelectorDialog(tb.Toplevel):
    """
    簡單的視窗列表選擇器。
    on_select(hwnd, title) 會在按下「選擇」時被呼叫。
    """
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.title("選擇目標視窗")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.on_select = on_select
        self.geometry("520x380")

        frm = tb.Frame(self, padding=8)
        frm.pack(fill="both", expand=True)

        lb_frame = tb.Frame(frm)
        lb_frame.pack(fill="both", expand=True, side="left")

        self.listbox = tk.Listbox(lb_frame, width=48, height=18, activestyle="dotbox", exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scroll = tb.Scrollbar(lb_frame, command=self.listbox.yview)
        self.scroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=self.scroll.set)
        self.listbox.bind("<Double-Button-1>", lambda e: self._on_select())

        # 右側按鈕列
        btn_frame = tb.Frame(frm)
        btn_frame.pack(fill="y", side="right", padx=(8,0))

        self.select_btn = tb.Button(btn_frame, text="選擇", bootstyle=SUCCESS, width=12, command=self._on_select)
        self.select_btn.pack(pady=(8,4))

        self.refresh_btn = tb.Button(btn_frame, text="重新整理", bootstyle=SECONDARY, width=12, command=self.refresh)
        self.refresh_btn.pack(pady=4)

        self.clear_btn = tb.Button(btn_frame, text="清除選取", bootstyle=WARNING, width=12, command=self._on_clear)
        self.clear_btn.pack(pady=4)

        self.cancel_btn = tb.Button(btn_frame, text="取消", bootstyle=SECONDARY, width=12, command=self._on_cancel)
        self.cancel_btn.pack(pady=(12,4))

        self._items = []
        self.refresh()

    def refresh(self):
        self.listbox.delete(0, "end")
        self._items = _enum_taskbar_titles()
        for hwnd, title in self._items:
            self.listbox.insert("end", title)
        if self._items:
            self.listbox.selection_set(0)

    def _on_select(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        hwnd, title = self._items[idx]
        try:
            self.on_select(hwnd, title)
        finally:
            self.destroy()

    def _on_clear(self):
        # 傳回 None 表示清除選取
        try:
            self.on_select(None, "")
        finally:
            self.destroy()

    def _on_cancel(self):
        self.destroy()
# ...existing code...