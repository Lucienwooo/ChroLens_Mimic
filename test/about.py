import ttkbootstrap as tb
from ttkbootstrap.constants import *  # <-- 確保 SECONDARY 等常數可用
import tkinter as tk
import os

def show_about(parent):
    about_win = tb.Toplevel(parent)
    about_win.title("關於 ChroLens_Mimic")
    about_win.geometry("450x300")
    about_win.resizable(False, False)
    about_win.grab_set()
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - 175
    y = parent.winfo_y() + 80
    about_win.geometry(f"+{x}+{y}")
    try:
        import sys
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
        else:
            icon_path = "umi_奶茶色.ico"
        about_win.iconbitmap(icon_path)
    except Exception:
        pass

    frm = tb.Frame(about_win, padding=20)
    frm.pack(fill="both", expand=True)

    # 文字使用簡單設定（視主程式字型設定而定）
    tb.Label(frm, text="ChroLens_Mimic\n可理解為按鍵精靈/操作錄製/掛機工具\n解決重複性高的作業或動作", font=("Microsoft JhengHei", 11)).pack(anchor="w", pady=(0, 6))
    link = tk.Label(frm, text="ChroLens_模擬器討論區", font=("Microsoft JhengHei", 10, "underline"), fg="#5865F2", cursor="hand2")
    link.pack(anchor="w")
    link.bind("<Button-1>", lambda e: os.startfile("https://discord.gg/72Kbs4WPPn"))
    github = tk.Label(frm, text="查看更多工具(巴哈)", font=("Microsoft JhengHei", 10, "underline"), fg="#24292f", cursor="hand2")
    github.pack(anchor="w", pady=(8, 0))
    github.bind("<Button-1>", lambda e: os.startfile("https://home.gamer.com.tw/profile/index_creation.php?owner=umiwued&folder=523848"))
    tb.Label(frm, text="Creat By Lucienwooo", font=("Microsoft JhengHei", 11)).pack(anchor="w", pady=(6, 0))
    tb.Button(frm, text="關閉", command=about_win.destroy, width=8, bootstyle=SECONDARY).pack(anchor="e", pady=(16, 0))