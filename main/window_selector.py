import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import win32gui
import sys
import os

def get_icon_path():
    """取得圖示檔案路徑（打包後和開發環境通用）"""
    try:
        if getattr(sys, 'frozen', False):
            # 打包後的環境
            return os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
        else:
            # 開發環境
            # 檢查是否在 main 資料夾中
            if os.path.exists("umi_奶茶色.ico"):
                return "umi_奶茶色.ico"
            # 檢查上層目錄
            elif os.path.exists("../umi_奶茶色.ico"):
                return "../umi_奶茶色.ico"
            else:
                return "umi_奶茶色.ico"
    except:
        return "umi_奶茶色.ico"

def set_window_icon(window):
    """為視窗設定圖示"""
    try:
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            window.iconbitmap(icon_path)
    except Exception as e:
        print(f"設定視窗圖示失敗: {e}")

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
        self.resizable(True, True)  # 允許調整大小
        self.transient(parent)
        self.grab_set()
        self.on_select = on_select
        self.geometry("700x450")  # 增大初始尺寸
        self.minsize(600, 350)  # 設置最小尺寸
        # 設定視窗圖示
        set_window_icon(self)

        frm = tb.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        lb_frame = tb.Frame(frm)
        lb_frame.pack(fill="both", expand=True, side="left")

        self.listbox = tk.Listbox(lb_frame, width=43, height=20, activestyle="dotbox", exportselection=False)  # 從 65 縮減為 43 (約 1/3)
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scroll = tb.Scrollbar(lb_frame, command=self.listbox.yview)
        self.scroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=self.scroll.set)
        self.listbox.bind("<Double-Button-1>", lambda e: self._on_select())

        # 右側按鈕列
        btn_frame = tb.Frame(frm)
        btn_frame.pack(fill="y", side="right", padx=(10,0))

        self.select_btn = tb.Button(btn_frame, text="選擇", bootstyle=SUCCESS, width=14, command=self._on_select)
        self.select_btn.pack(pady=(8,6), fill="x")

        self.refresh_btn = tb.Button(btn_frame, text="重整", bootstyle=SECONDARY, width=14, command=self.refresh)
        self.refresh_btn.pack(pady=6, fill="x")

        self.clear_btn = tb.Button(btn_frame, text="清除", bootstyle=WARNING, width=14, command=self._on_clear)
        self.clear_btn.pack(pady=6, fill="x")

        self.cancel_btn = tb.Button(btn_frame, text="取消", bootstyle=SECONDARY, width=14, command=self._on_cancel)
        self.cancel_btn.pack(pady=(12,6), fill="x")

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