# TinyMode 獨立模組（可直接 import 使用）
import os
import ttkbootstrap as tb
import tkinter as tk
from lang import LANG_MAP

class TinyMode:
    def __init__(self, parent, hotkey_map, language_var, style):
        self.parent = parent
        self.hotkey_map = hotkey_map
        self.language_var = language_var
        self.style = style
        self.tiny_window = None
        self.tiny_btns = []
        self.tiny_mode_on = False

    def toggle(self):
        if not self.tiny_mode_on:
            self._open()
        else:
            self._close()

    def _open(self):
        self.tiny_mode_on = True
        if self.tiny_window is None or not self.tiny_window.winfo_exists():
            self.tiny_window = tb.Toplevel(self.parent)
            self.tiny_window.title("ChroLens_Mimic MiniMode")
            self.tiny_window.geometry("620x40")
            self.tiny_window.overrideredirect(True)
            self.tiny_window.resizable(False, False)
            self.tiny_window.attributes("-topmost", True)
            try:
                import sys
                if getattr(sys, 'frozen', False):
                    icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
                else:
                    icon_path = "umi_奶茶色.ico"
                self.tiny_window.iconbitmap(icon_path)
            except Exception:
                pass
            lang = self.language_var.get()
            lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
            self.tiny_countdown_label = tb.Label(self.tiny_window, text=f"{lang_map['剩餘']}: 00:00:00", font=("Microsoft JhengHei", 12), foreground="#FF95CA", width=13)
            self.tiny_countdown_label.grid(row=0, column=0, padx=2, pady=5)
            self.tiny_window.bind("<ButtonPress-1>", self._start_move)
            self.tiny_window.bind("<B1-Motion>", self._move)
            btn_defs = [("⏺", "start"), ("⏸", "pause"), ("⏹", "stop"), ("▶︎", "play"), ("⤴︎", "tiny")]
            for i, (icon, key) in enumerate(btn_defs):
                btn = tb.Button(self.tiny_window, text=f"{icon} {self.hotkey_map.get(key, '')}", width=7, style="My.TButton", command=getattr(self.parent, {"start":"start_record","pause":"toggle_pause","stop":"stop_all","play":"play_record","tiny":"toggle_tiny_mode"}[key]))
                btn.grid(row=0, column=i+1, padx=2, pady=5)
                self.tiny_btns.append((btn, icon, key))
            self.tiny_window.protocol("WM_DELETE_WINDOW", self._close)
            try:
                self.parent.withdraw()
            except Exception:
                pass

    def _close(self):
        if self.tiny_window and self.tiny_window.winfo_exists():
            self.tiny_window.destroy()
        self.tiny_mode_on = False
        try:
            self.parent.deiconify()
        except Exception:
            pass

    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _move(self, event):
        x = self.tiny_window.winfo_x() + event.x - self._drag_x
        y = self.tiny_window.winfo_y() + event.y - self._drag_y
        self.tiny_window.geometry(f"+{x}+{y}")