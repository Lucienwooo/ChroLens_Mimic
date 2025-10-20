import tkinter as tk
import ttkbootstrap as tb

class TinyWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.is_visible = False
        
    def toggle(self):
        if not self.is_visible:
            self.show()
        else:
            self.hide()
    
    def show(self):
        if not self.window or not self.window.winfo_exists():
            self.window = tb.Toplevel(self.parent)
            self.window.title("MiniMode")
            self._setup_controls()
            self._setup_position()
        self.window.deiconify()
        self.is_visible = True
        
    def hide(self):
        if self.window:
            self.window.withdraw()
        self.is_visible = False
        
    def close(self):
        if self.window:
            self.window.destroy()
            self.window = None
        self.is_visible = False
        
    def _setup_controls(self):
        frm = tb.Frame(self.window, padding=6)
        frm.pack(fill="both", expand=True)
        
        # 基本控制按鈕
        btn_start = tb.Button(frm, text="開始", width=8, 
                            command=lambda: self.parent.start_record())
        btn_pause = tb.Button(frm, text="暫停", width=8,
                            command=lambda: self.parent.toggle_pause())
        btn_stop = tb.Button(frm, text="停止", width=8,
                            command=lambda: self.parent.stop_all())
        btn_play = tb.Button(frm, text="播放", width=8,
                            command=lambda: self.parent.play_record())
                            
        btn_start.grid(row=0, column=0, padx=4, pady=4)
        btn_pause.grid(row=0, column=1, padx=4, pady=4)
        btn_stop.grid(row=1, column=0, padx=4, pady=4)
        btn_play.grid(row=1, column=1, padx=4, pady=4)
        
    def _setup_position(self):
        # 設定初始位置（在主視窗右下角）
        x = self.parent.winfo_x() + self.parent.winfo_width() - 200
        y = self.parent.winfo_y() + self.parent.winfo_height() - 120
        self.window.geometry(f"180x100+{x}+{y}")