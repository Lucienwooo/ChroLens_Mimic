import tkinter as tk
import ttkbootstrap as tb
import os

class miniWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.is_visible = False
        self.mini_btns = []
        self.mini_countdown_label = None
        # 新增按鈕狀態追蹤
        self.active_btn = None
        
    def toggle(self):
        if not self.is_visible:
            self.show()
        else:
            self.hide()
    
    def show(self):
        # 隱藏主視窗並顯示 minimode 視窗（600x50）
        try:
            # 確保父視窗已更新位置/大小資訊
            self.parent.update_idletasks()
            self.parent.withdraw()
        except Exception:
            pass

        if not self.window or not self.window.winfo_exists():
            self.window = tb.Toplevel(self.parent)
            self.window.title("Minimode")
            self.window.resizable(False, False)
            # 添加這行來處理視窗關閉事件
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
            # 將 mini 視窗設定為最上層，並調整大小為 600x50
            try:
                self.window.attributes("-topmost", True)
            except Exception:
                pass
            self._setup_controls()
            self._setup_position()
        else:
            # 即使已存在，也重新定位與調整大小
            self._setup_position()
        # 強制設定大小（保險）
        try:
            self.window.geometry(f"600x50+{self._calc_x()}+{self._calc_y()}")
        except Exception:
            pass
        self.window.deiconify()
        self.is_visible = True
        
    def hide(self):
        # 隱藏 mini 視窗並復原主視窗
        if self.window:
            try:
                self.window.withdraw()
            except Exception:
                pass
        try:
            self.parent.deiconify()
        except Exception:
            pass
        self.is_visible = False
        
    def close(self):
        # 銷毀 mini 視窗並復原主視窗
        if self.window:
            try:
                self.window.destroy()
                self.window = None
            except Exception:
                pass
        try:
            self.parent.deiconify()
        except Exception:
            pass
        self.is_visible = False
        
    def _setup_controls(self):
        frm = tb.Frame(self.window, padding=6)
        frm.pack(fill="both", expand=True)
        
        # 倒數 label（可被外部更新）
        lang = getattr(self.parent, "language_var", None)
        lang_val = lang.get() if lang else "繁體中文"
        lang_map = getattr(__import__("lang", fromlist=["LANG_MAP"]), "LANG_MAP") if os.path.exists("lang.py") else {"繁體中文": {"剩餘":"剩餘"}}
        lm = lang_map.get(lang_val, lang_map.get("繁體中文", {"剩餘":"剩餘"}))
        self.mini_countdown_label = tb.Label(
            frm,
            text=f"{lm.get('剩餘','剩餘')}: 00:00:00",
            font=("LINESeedTW_TTF_Rg", 12),
            foreground="#FF95CA", width=20
        )
        self.mini_countdown_label.grid(row=0, column=0, padx=6, pady=10, sticky="w")
        
        # 按鈕定義（改用 Label 偽裝）
        btn_defs = [
            ("⏺", "start"),
            ("⏸", "pause"),
            ("⏹", "stop"),
            ("▶︎", "play"),
            ("⤴︎", "mini")
        ]
        self.mini_btns = []
        btn_font = ("LINESeedTW_TTF_Rg", 9)
        # 取得容器預設背景以供還原
        try:
            default_bg = frm.cget("background")
        except Exception:
            default_bg = "#00a5ce"
        default_fg = "#000"
        danger_bg = "#d9534f"
        danger_fg = "#fff"
        # 將顏色存到實例供其他方法使用
        self._label_normal_bg = default_bg
        self._label_normal_fg = default_fg
        self._label_danger_bg = danger_bg
        self._label_danger_fg = danger_fg

        # 對應父物件的方法名稱（若父物件沒實作，會被捕捉）
        cmd_map = {
            "start": "start_record",
            "pause": "toggle_pause",
            "stop": "stop_all",
            "play": "play_record",
            "mini": "toggle_mini_mode"
        }

        def make_wrapped_cmd(btn_key, method_name, widget):
            def wrapped_cmd(event=None):
                # 嘗試呼叫父物件方法
                try:
                    fn = getattr(self.parent, method_name)
                except Exception:
                    fn = None
                result = None
                if fn:
                    try:
                        result = fn()
                    except Exception:
                        result = None
                # 更新狀態顯示
                if btn_key == "start":
                    self._set_button_active("start")
                elif btn_key == "pause":
                    if getattr(self.parent, "paused", False):
                        self._set_button_active("pause")
                    else:
                        self._set_button_active("start")
                elif btn_key == "stop":
                    self._set_button_active("stop")
                    # stop 後短暫延遲清除狀態
                    try:
                        if self.window:
                            self.window.after(500, lambda: self._clear_button_states())
                    except Exception:
                        pass
                elif btn_key == "play":
                    self._set_button_active("play")
                return result
            return wrapped_cmd

        for i, (icon, key) in enumerate(btn_defs):
            hotkey_text = ""
            try:
                hotkey_text = self.parent.hotkey_map.get(key, "")
            except Exception:
                hotkey_text = ""
            text = f"{icon} {hotkey_text}"

            lbl = tb.Label(
                frm,
                text=text,
                width=8,                  # 固定寬度
                font=btn_font,
                background=self._label_normal_bg,
                foreground=self._label_normal_fg,
                anchor="center",
                cursor="hand2",
                padding=(6, 2)
            )
            lbl.grid(row=0, column=i+1, padx=4, pady=6)
            # 強制一次寬度（保險）
            try:
                lbl.configure(width=8)
            except Exception:
                pass

            # 綁定點擊事件
            method_name = cmd_map.get(key, "")
            wrapped = make_wrapped_cmd(key, method_name, lbl)
            lbl.bind("<Button-1>", wrapped)
            # 也支援鍵盤/無障礙觸發（Enter）
            lbl.bind("<Return>", wrapped)
            self.mini_btns.append((lbl, icon, key))

    def _set_button_active(self, active_key):
        """設定指定按鈕為危險色，其他恢復預設（label 版本）"""
        for lbl, _, key in self.mini_btns:
            try:
                if key == active_key:
                    lbl.configure(background=self._label_danger_bg, foreground=self._label_danger_fg)
                else:
                    lbl.configure(background=self._label_normal_bg, foreground=self._label_normal_fg)
                # 再次強制 width（保險）
                lbl.configure(width=8)
            except Exception:
                pass
        self.active_btn = active_key
        
    def _clear_button_states(self):
        """清除所有按鈕的狀態（label 版本）"""
        for lbl, _, _ in self.mini_btns:
            try:
                lbl.configure(background=self._label_normal_bg, foreground=self._label_normal_fg)
                lbl.configure(width=8)
            except Exception:
                pass
        self.active_btn = None

    def _setup_position(self):
        # 設定初始位置（在主視窗下方靠中或靠右，保證不超出畫面）
        try:
            x = self._calc_x()
            y = self._calc_y()
            self.window.geometry(f"600x50+{x}+{y}")
        except Exception:
            pass

    def _calc_x(self):
        # 讓 mini 視窗置於父視窗水平中間偏右位置（或畫面可見範圍內）
        try:
            px = int(self.parent.winfo_x())
            pw = int(self.parent.winfo_width())
            screen_w = self.parent.winfo_screenwidth()
            x = px + max(0, (pw - 600) // 2)
            # 防止超出螢幕右邊界
            if x + 600 > screen_w:
                x = max(0, screen_w - 600 - 10)
            return x
        except Exception:
            return 50

    def _calc_y(self):
        try:
            py = int(self.parent.winfo_y())
            ph = int(self.parent.winfo_height())
            screen_h = self.parent.winfo_screenheight()
            # 放在父視窗下方一點，或靠底部
            y = py + max(0, ph - 90)
            if y + 50 > screen_h:
                y = max(0, screen_h - 50 - 10)
            return y
        except Exception:
            return 50

    def set_hotkeys(self, hotkey_map):
        """更新 mini 按鈕顯示的快捷鍵文字（安全呼叫）。"""
        try:
            for lbl, icon, key in self.mini_btns:
                try:
                    hk = hotkey_map.get(key, "")
                    text = f"{icon} {hk}" if hk else icon
                    lbl.config(text=text)
                except Exception:
                    pass
        except Exception:
            pass

    def update_countdown(self, time_str):
        """外部用來更新倒數顯示，time_str 格式 'HH:MM:SS'。"""
        try:
            if self.mini_countdown_label:
                # 保留原 prefix（從語言檔取得），只替換時間部分
                prefix = self.mini_countdown_label.cget("text").split(":")[0]
                self.mini_countdown_label.config(text=f"{prefix}: {time_str}")
        except Exception:
            pass

    def _setup_position(self):
        # 設定初始位置（在主視窗下方靠中或靠右，保證不超出畫面）
        try:
            x = self._calc_x()
            y = self._calc_y()
            self.window.geometry(f"600x50+{x}+{y}")
        except Exception:
            pass

    def _calc_x(self):
        # 讓 mini 視窗置於父視窗水平中間偏右位置（或畫面可見範圍內）
        try:
            px = int(self.parent.winfo_x())
            pw = int(self.parent.winfo_width())
            screen_w = self.parent.winfo_screenwidth()
            x = px + max(0, (pw - 600) // 2)
            # 防止超出螢幕右邊界
            if x + 600 > screen_w:
                x = max(0, screen_w - 600 - 10)
            return x
        except Exception:
            return 50

    def _calc_y(self):
        try:
            py = int(self.parent.winfo_y())
            ph = int(self.parent.winfo_height())
            screen_h = self.parent.winfo_screenheight()
            # 放在父視窗下方一點，或靠底部
            y = py + max(0, ph - 90)
            if y + 50 > screen_h:
                y = max(0, screen_h - 50 - 10)
            return y
        except Exception:
            return 50

    def on_closing(self):
        """處理視窗關閉事件"""
        self.close()