import os
import ttkbootstrap as tb
import tkinter as tk

class MiniMode:
    """
    Mini 控制視窗：負責顯示小型按鈕列與倒數文字，
    並提供更新按鈕文字 / 更新倒數 / 關閉介面的 API。
    建構參數:
      parent: 主視窗 (會在 show 時 withdraw()，關閉時 deiconify())
      hotkey_map: dict of hotkey strings
      callbacks: dict mapping keys ('start','pause','stop','play','mini') to callables
      on_close: optional callback invoked when mini 視窗關閉
    """
    def __init__(self, parent, hotkey_map, callbacks, on_close=None, icon_name="umi_奶茶色.ico"):
        self.parent = parent
        self.hotkey_map = hotkey_map or {}
        self.callbacks = callbacks or {}
        self.on_close = on_close
        self.win = None
        self.btns = []
        self.countdown_label = None
        self.icon_name = icon_name

    def _set_icon(self, win):
        try:
            import sys
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, self.icon_name)
            else:
                icon_path = self.icon_name
            win.iconbitmap(icon_path)
        except Exception:
            pass

    def show(self):
        if self.win and self.win.winfo_exists():
            return
        self.win = tb.Toplevel(self.parent)
        self.win.title("MiniMode")
        self.win.geometry("300x100")
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.attributes("-alpha", 0.9)
        self.win.wm_attributes("-topmost", True)
        self._set_icon(self.win)

        # 可拖曳
        self.win.bind("<Button-1>", self._start_move)
        self.win.bind("<B1-Motion>", self._do_move)

        frm = tb.Frame(self.win, padding=8)
        frm.pack(fill="both", expand=True)

        btn_frame = tb.Frame(frm)
        btn_frame.pack(pady=(8, 4))

        icons = {
            "start": "●錄",
            "pause": "▮▮",
            "stop": "■",
            "play": "▶",
            "mini": "↔"
        }

        # 依 hotkey_map 順序建立按鈕（確保穩定的順序）
        keys = ["start", "pause", "stop", "play", "mini"]
        for i, key in enumerate(keys):
            hot = self.hotkey_map.get(key, "")
            icon = icons.get(key, "")
            text = f"{icon} {hot}"
            cmd = self.callbacks.get(key)
            btn = tb.Button(btn_frame, text=text, width=7, style="My.TButton", command=cmd)
            btn.grid(row=0, column=i, padx=2, pady=5)
            self.btns.append((key, btn))

        # 倒數顯示
        self.countdown_label = tb.Label(frm, text="剩餘: 00:00:00", font=("Microsoft JhengHei", 10))
        self.countdown_label.pack(pady=(10,0))

        self.win.protocol("WM_DELETE_WINDOW", self.close)

    def is_open(self):
        return self.win is not None and self.win.winfo_exists()

    def update_buttons(self, hotkey_map):
        """更新按鈕文字（當 shortcut 變更時呼叫）"""
        self.hotkey_map = hotkey_map or self.hotkey_map
        for key, btn in self.btns:
            hot = self.hotkey_map.get(key, "")
            icon = {
                "start": "●錄",
                "pause": "▮▮",
                "stop": "■",
                "play": "▶",
                "mini": "↔"
            }.get(key, "")
            btn.config(text=f"{icon} {hot}")

    def update_countdown(self, text):
        """更新倒數文字（輸入完整文字，例如 '剩餘: 00:00:00'）"""
        if self.countdown_label and self.is_open():
            try:
                self.countdown_label.config(text=text)
            except Exception:
                pass

    def close(self):
        if self.win and self.win.winfo_exists():
            try:
                self.win.destroy()
            except Exception:
                pass
        # 呼叫關閉 callback（讓 parent deiconify 等）
        if callable(self.on_close):
            try:
                self.on_close()
            except Exception:
                pass

    # 簡單的拖曳支援
    def _start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_move(self, event):
        if not self.is_open(): return
        x = self.win.winfo_x() + event.x - getattr(self, "_drag_x", 0)
        y = self.win.winfo_y() + event.y - getattr(self, "_drag_y", 0)
        self.win.geometry(f"+{x}+{y}")