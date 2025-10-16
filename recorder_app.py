import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import font
import tkinter as tk
import threading, time, json, os, datetime
import keyboard, mouse
import ctypes
import win32api
import win32gui
import win32con
import pywintypes
import random

from utils import (
    move_mouse_abs, mouse_event_win, screen_to_client, client_to_screen,
    SCRIPTS_DIR, LAST_SCRIPT_FILE, LAST_SKIN_FILE, MOUSE_SAMPLE_INTERVAL,
    load_user_config, save_user_config, format_time
)
from lang import LANG_MAP
from tooltip import Tooltip

# 新增：watchdog 可選支援（放在檔案頂端 import 區）
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    _HAVE_WATCHDOG = True
except Exception:
    Observer = None
    FileSystemEventHandler = object
    _HAVE_WATCHDOG = False

class RecorderApp(tb.Window):
    def __init__(self):
        self.user_config = load_user_config()
        skin = self.user_config.get("skin", "darkly")
        lang = self.user_config.get("language", "繁體中文")
        super().__init__(themename=skin)
        self.language_var = tk.StringVar(self, value=lang)
        self._hotkey_handlers = {}
        self.tiny_window = None
        self.target_hwnd = None
        self.target_title = None

        self.hotkey_map = self.user_config.get("hotkey_map", {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "tiny": "alt+`"
        })

        self.style.configure("My.TButton", font=("LINESeedTW_TTF_Rg", 9))  # 替換為新的字體
        self.style.configure("My.TLabel", font=("LINESeedTW_TTF_Rg", 9))  # 替換為新的字體
        self.style.configure("My.TEntry", font=("LINESeedTW_TTF_Rg", 9))  # 替換為新的字體
        self.style.configure("My.TCombobox", font=("LINESeedTW_TTF_Rg", 9))  # 替換為新的字體
        self.style.configure("My.TCheckbutton", font=("LINESeedTW_TTF_Rg", 9))  # 替換為新的字體
        self.style.configure("TinyBold.TButton", font=("LINESeedTW_TTF_Bd", 9, "bold"))  # 替換為新的字體

        self.title("ChroLens_Mimic_2.6")
        try:
            import sys
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                icon_path = "umi_奶茶色.ico"
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定 icon: {e}")

        self.icon_tip_label = tk.Label(self, width=2, height=1, bg=self.cget("background"))
        self.icon_tip_label.place(x=0, y=0)
        Tooltip(self.icon_tip_label, f"{self.title()}_By_Lucien")

        self.geometry("900x550")
        self.resizable(True, True)
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []
        self.speed = 1.0
        self._record_start_time = None
        self._play_start_time = None
        self._total_play_time = 0

        self.script_dir = self.user_config.get("script_dir", SCRIPTS_DIR)
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)

        # 頂部按鈕區域
        frm_top = tb.Frame(self, padding=(8, 10, 8, 5))
        frm_top.pack(fill="x")

        self.btn_start = tb.Button(frm_top, text=f"開始錄製 ({self.hotkey_map['start']})", command=self.start_record, bootstyle=PRIMARY, width=14, style="My.TButton")
        self.btn_start.grid(row=0, column=0, padx=(0, 4))
        self.btn_pause = tb.Button(frm_top, text=f"暫停/繼續 ({self.hotkey_map['pause']})", command=self.toggle_pause, bootstyle=INFO, width=14, style="My.TButton")
        self.btn_pause.grid(row=0, column=1, padx=4)
        self.btn_stop = tb.Button(frm_top, text=f"停止 ({self.hotkey_map['stop']})", command=self.stop_all, bootstyle=WARNING, width=14, style="My.TButton")
        self.btn_stop.grid(row=0, column=2, padx=4)
        self.btn_play = tb.Button(frm_top, text=f"回放 ({self.hotkey_map['play']})", command=self.play_record, bootstyle=SUCCESS, width=10, style="My.TButton")
        self.btn_play.grid(row=0, column=3, padx=4)

        themes = ["darkly", "cyborg", "superhero", "journal","minty", "united", "morph", "lumen"]
        self.theme_var = tk.StringVar(value=self.style.theme_use())
        theme_combo = tb.Combobox(frm_top, textvariable=self.theme_var, values=themes, state="readonly", width=6, style="My.TCombobox")
        theme_combo.grid(row=0, column=8, padx=(4, 8), sticky="e")
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.change_theme())

        self.tiny_mode_btn = tb.Button(frm_top, text="MiniMode", style="My.TButton", command=self.toggle_tiny_mode, width=10)
        self.tiny_mode_btn.grid(row=0, column=7, padx=4)

        # 底部設定區域
        frm_bottom = tb.Frame(self, padding=(8, 0, 8, 5))
        frm_bottom.pack(fill="x")
        self.lbl_speed = tb.Label(frm_bottom, text="回放速度:", style="My.TLabel")
        self.lbl_speed.grid(row=0, column=0, padx=(0, 6))
        self.speed_tooltip = Tooltip(self.lbl_speed, "正常速度1倍=100,範圍1~1000")
        self.update_speed_tooltip()
        self.speed_var = tk.StringVar(value=self.user_config.get("speed", "100"))
        tb.Entry(frm_bottom, textvariable=self.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=6)
        self.btn_hotkey = tb.Button(frm_bottom, text="快捷鍵", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=10, style="My.TButton")
        self.btn_hotkey.grid(row=0, column=4, padx=6)
        self.about_btn = tb.Button(frm_bottom, text="關於", width=6, style="My.TButton", command=self.show_about_dialog, bootstyle=SECONDARY)
        self.about_btn.grid(row=0, column=5, padx=6, sticky="e")
        saved_lang = self.user_config.get("language", "繁體中文")
        # 是示 "Language" 預設（跟你原本 copy 保持一致）
        self.language_var = tk.StringVar(self, value="Language")
        lang_combo = tb.Combobox(frm_bottom, textvariable=self.language_var, values=["繁體中文", "日本語", "English"], state="readonly", width=10, style="My.TCombobox")
        lang_combo.grid(row=0, column=6, padx=(6, 8), sticky="e")
        lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        self.language_combo = lang_combo

        # 重複設定區域
        frm_repeat = tb.Frame(self, padding=(8, 0, 8, 5))
        frm_repeat.pack(fill="x")
        self.repeat_label = tb.Label(frm_repeat, text="重複次數:", style="My.TLabel")
        self.repeat_label.grid(row=0, column=0, padx=(0, 2))
        self.repeat_var = tk.StringVar(value=self.user_config.get("repeat", "1"))
        entry_repeat = tb.Entry(frm_repeat, textvariable=self.repeat_var, width=6, style="My.TEntry")
        entry_repeat.grid(row=0, column=1, padx=2)
        self.repeat_unit_label = tb.Label(frm_repeat, text="次", style="My.TLabel")
        self.repeat_unit_label.grid(row=0, column=2, padx=(0, 2))

        self.repeat_time_var = tk.StringVar(value="00:00:00")
        entry_repeat_time = tb.Entry(frm_repeat, textvariable=self.repeat_time_var, width=10, style="My.TEntry", justify="center")
        entry_repeat_time.grid(row=0, column=3, padx=(10, 2))
        self.repeat_time_label = tb.Label(frm_repeat, text="重複時間", style="My.TLabel")
        self.repeat_time_label.grid(row=0, column=4, padx=(0, 2))

        self.repeat_interval_var = tk.StringVar(value="00:00:00")
        repeat_interval_entry = tb.Entry(frm_repeat, textvariable=self.repeat_interval_var, width=10, style="My.TEntry", justify="center")
        repeat_interval_entry.grid(row=0, column=5, padx=(10, 2))
        self.repeat_interval_label = tb.Label(frm_repeat, text="重複間隔", style="My.TLabel")
        self.repeat_interval_label.grid(row=0, column=6, padx=(0, 2))

        self.random_interval_var = tk.BooleanVar(value=False)
        self.random_interval_check = tb.Checkbutton(frm_repeat, text="隨機", variable=self.random_interval_var, style="My.TCheckbutton")
        self.random_interval_check.grid(row=0, column=7, padx=(8, 2))

        self.save_script_btn_text = tk.StringVar(value=LANG_MAP.get(lang, LANG_MAP["繁體中文"])["儲存"])
        self.save_script_btn = tb.Button(frm_repeat, textvariable=self.save_script_btn_text, width=8, bootstyle=SUCCESS, style="My.TButton", command=self.save_script_settings)
        self.save_script_btn.grid(row=0, column=8, padx=(8, 0))

        def validate_time_input(P):
            import re
            return re.fullmatch(r"[\d:]*", P) is not None
        vcmd = (self.register(validate_time_input), "%P")
        entry_repeat_time.config(validate="key", validatecommand=vcmd)
        repeat_interval_entry.config(validate="key", validatecommand=vcmd)

        def on_repeat_time_change(*args):
            t = self.repeat_time_var.get()
            seconds = self._parse_time_to_seconds(t)
            if seconds > 0:
                self.update_total_time_label(seconds)
            else:
                self.update_total_time_label(0)
        self.repeat_time_var.trace_add("write", on_repeat_time_change)

        entry_repeat.bind("<Button-3>", lambda e: self.repeat_var.set("0"))
        entry_repeat_time.bind("<Button-3>", lambda e: self.repeat_time_var.set("00:00:00"))
        repeat_interval_entry.bind("<Button-3>", lambda e: self.repeat_interval_var.set("00:00:00"))

        # 腳本選單區域
        frm_script = tb.Frame(self, padding=(8, 0, 8, 5))
        frm_script.pack(fill="x")
        self.script_menu_label = tb.Label(frm_script, text="腳本選單:", style="My.TLabel")
        self.script_menu_label.grid(row=0, column=0, sticky="w", padx=(0, 2))
        self.script_var = tk.StringVar(value=self.user_config.get("last_script", ""))
        self.script_combo = tb.Combobox(frm_script, textvariable=self.script_var, width=20, state="readonly", style="My.TCombobox")
        self.script_combo.grid(row=0, column=1, sticky="w", padx=4)
        self.rename_var = tk.StringVar()
        self.rename_entry = tb.Entry(frm_script, textvariable=self.rename_var, width=20, style="My.TEntry")
        self.rename_entry.grid(row=0, column=2, padx=4)
        tb.Button(frm_script, text="Rename", command=self.rename_script, bootstyle=WARNING, width=12, style="My.TButton").grid(row=0, column=3, padx=4)
        tb.Button(frm_script, text="選擇目標視窗", command=self.select_target_window, bootstyle=INFO, width=14, style="My.TButton").grid(row=0, column=4, padx=4)
        self.script_combo.bind("<<ComboboxSelected>>", self.on_script_selected)

        # 日誌標題區域
        frm_log = tb.Frame(self, padding=(10, 0, 10, 10))
        frm_log.pack(fill="both", expand=True)
        log_title_frame = tb.Frame(frm_log)
        log_title_frame.pack(fill="x")

        self.mouse_pos_label = tb.Label(log_title_frame, text="( X:0, Y:0 )", font=("Consolas", 12, "bold"), foreground="#668B9B")
        self.mouse_pos_label.pack(side="left", padx=8)

        self.time_label_time = tb.Label(log_title_frame, text="00:00:00", font=("Consolas", 12), foreground="#888888")
        self.time_label_time.pack(side="right", padx=0)
        self.time_label_prefix = tb.Label(log_title_frame, text="錄製: ", font=("Consolas", 12), foreground="#15D3BD")
        self.time_label_prefix.pack(side="right", padx=0)

        self.countdown_label_time = tb.Label(log_title_frame, text="00:00:00", font=("Consolas", 12), foreground="#888888")
        self.countdown_label_time.pack(side="right", padx=0)
        self.countdown_label_prefix = tb.Label(log_title_frame, text="單次: ", font=("Consolas", 12), foreground="#DB0E59")
        self.countdown_label_prefix.pack(side="right", padx=0)

        self.total_time_label_time = tb.Label(log_title_frame, text="00:00:00", font=("Consolas", 12), foreground="#888888")
        self.total_time_label_time.pack(side="right", padx=0)
        self.total_time_label_prefix = tb.Label(log_title_frame, text="總運作: ", font=("Consolas", 12), foreground="#FF95CA")
        self.total_time_label_prefix.pack(side="right", padx=0)

        # 頁面區域
        frm_page = tb.Frame(self, padding=(10, 0, 10, 10))
        frm_page.pack(fill="both", expand=True)
        frm_page.grid_rowconfigure(0, weight=1)
        frm_page.grid_columnconfigure(1, weight=1)

        self.page_menu = tk.Listbox(frm_page, width=18, font=("LINESeedTW_TTF_Rg", 9), height=5)
        self.page_menu.insert(0, "1.日誌顯示")
        self.page_menu.insert(1, "2.腳本設定")
        self.page_menu.insert(2, "3.整體設定")
        self.page_menu.grid(row=0, column=0, sticky="ns", padx=(0, 8), pady=4)
        self.page_menu.bind("<<ListboxSelect>>", self.on_page_selected)

        # 主要內容區域
        self.page_content_frame = tb.Frame(frm_page, width=700, height=320)
        self.page_content_frame.grid(row=0, column=1, sticky="nsew")
        self.page_content_frame.grid_rowconfigure(0, weight=1)
        self.page_content_frame.grid_columnconfigure(0, weight=1)
        self.page_content_frame.pack_propagate(False)

# 在 __init__ 中的頁面初始化部分：

        # 日誌顯示區域
        self.log_text = tb.Text(self.page_content_frame, height=24, width=110, state="disabled", font=("LINESeedTW_TTF_Rg", 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = tb.Scrollbar(self.page_content_frame, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # 腳本設定區域
        self.script_setting_frame = tb.Frame(self.page_content_frame)
        self.script_setting_frame.grid(row=0, column=0, sticky="nsew")

        # 左側腳本列表框架
        list_frame = tb.Frame(self.script_setting_frame)
        list_frame.pack(side="left", fill="both", expand=True)

        # 腳本列表
        self.script_listbox = tk.Listbox(
            list_frame, 
            width=55,  # 原寬度的一半
            height=24,
            font=("LINESeedTW_TTF_Rg", 9)
        )
        self.script_listbox.pack(side="left", fill="both", expand=True)
        self.script_listbox.bind('<<ListboxSelect>>', self.on_script_listbox_select)

        # 添加捲動條
        list_scroll = tb.Scrollbar(list_frame)
        list_scroll.pack(side="right", fill="y")
        self.script_listbox.config(yscrollcommand=list_scroll.set)
        list_scroll.config(command=self.script_listbox.yview)

        # 右側控制區域
        control_frame = tb.Frame(self.script_setting_frame)
        control_frame.pack(side="right", fill="y", padx=10)

        # 按鍵捕捉框
        self.hotkey_capture_var = tk.StringVar()
        self.hotkey_entry = tb.Entry(
            control_frame,
            textvariable=self.hotkey_capture_var,
            width=20,
            font=("LINESeedTW_TTF_Rg", 9),
            justify="center"
        )
        self.hotkey_entry.pack(pady=(0, 5))
        self.hotkey_entry.bind("<KeyPress>", self.on_hotkey_entry_key)

        # 設定快捷鍵按鈕
        set_hotkey_btn = tb.Button(
            control_frame,
            text="設定快捷鍵",
            command=self.set_script_hotkey,
            width=15,
            style="My.TButton",
            bootstyle=PRIMARY
        )
        set_hotkey_btn.pack(pady=5)

        # 刪除按鈕
        delete_btn = tb.Button(
            control_frame,
            text="刪除",
            command=self.delete_selected_script,
            width=15,
            style="My.TButton",
            bootstyle=DANGER
        )
        delete_btn.pack(pady=5)

        # 初始化腳本列表
        self.refresh_script_listbox()

        # 全域設定區域
        self.global_setting_frame = tb.Frame(self.page_content_frame)
        self.global_setting_frame.grid(row=0, column=0, sticky="nsew")

        # 全域設定右側備用文字框
        self.global_right_text = tb.Text(self.global_setting_frame, height=24, width=110, font=("LINESeedTW_TTF_Rg", 9))
        self.global_right_text.grid(row=0, column=0, sticky="nsew")
        global_right_scroll = tb.Scrollbar(self.global_setting_frame, command=self.global_right_text.yview)
        global_right_scroll.grid(row=0, column=1, sticky="ns")
        self.global_right_text.config(yscrollcommand=global_right_scroll.set)

        self.page_menu.selection_set(0)
        self.show_page(0)

        self.refresh_script_list()
        if self.script_var.get():
            self.on_script_selected()
        self._init_language(saved_lang)
        self.after(1500, self._delayed_init)

    def _delayed_init(self):
        self.after(1600, self._register_hotkeys)
        self.after(1700, self.refresh_script_list)
        self.after(1800, self.load_last_script)
        self.after(1900, self.update_mouse_pos)

    def update_speed_tooltip(self):
        lang = self.language_var.get()
        tips = {
            "繁體中文": "正常速度1倍=100,範圍1~1000",
            "日本語": "標準速度1倍=100、範囲1～1000",
            "English": "Normal speed 1x=100, range 1~1000"
        }
        tip_text = tips.get(lang, tips["繁體中文"])
        if hasattr(self, "speed_tooltip") and self.speed_tooltip:
            self.speed_tooltip.text = tip_text
        try:
            speed_val = int(self.speed_var.get())
            ratio = speed_val / 100.0
            self.lbl_speed.config(text=f"回放速度: {ratio:.2f}:{speed_val}")
        except:
            self.lbl_speed.config(text="回放速度:")

    def _parse_time_to_seconds(self, t):
        if not t or not isinstance(t, str):
            return 0
        parts = t.strip().split(":")
        try:
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(int, parts)
                return m * 60 + s
            elif len(parts) == 1:
                return int(parts[0])
        except Exception:
            return 0
        return 0

    def show_about_dialog(self):
        about_win = tb.Toplevel(self)
        about_win.title("關於 ChroLens_Mimic")
        about_win.geometry("450x300")
        about_win.resizable(False, False)
        about_win.grab_set()
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 175
        y = self.winfo_y() + 80
        about_win.geometry(f"+{x}+{y}")
        try:
            import sys
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                icon_path = "umi_奶茶色.ico"
            about_win.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定 about 視窗 icon: {e}")
        frm = tb.Frame(about_win, padding=20)
        frm.pack(fill="both", expand=True)
        tb.Label(frm, text="ChroLens_Mimic\n可理解為按鍵精靈/操作錄製/掛機工具\n解決重複性高的作業或動作", font=("LINESeedTW_TTF_Rg", 11,)).pack(anchor="w", pady=(0, 6))
        link = tk.Label(frm, text="ChroLens_模擬器討論區", font=("LINESeedTW_TTF_Rg", 10, "underline"), fg="#5865F2", cursor="hand2")
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda e: os.startfile("https://discord.gg/72Kbs4WPPn"))
        github = tk.Label(frm, text="查看更多工具(巴哈)", font=("LINESeedTW_TTF_Rg", 10, "underline"), fg="#24292f", cursor="hand2")
        github.pack(anchor="w", pady=(8, 0))
        github.bind("<Button-1>", lambda e: os.startfile("https://home.gamer.com.tw/profile/index_creation.php?owner=umiwued&folder=523848"))
        tb.Label(frm, text="Creat By Lucienwooo", font=("LINESeedTW_TTF_Rg", 11,)).pack(anchor="w", pady=(0, 6))
        tb.Button(frm, text="關閉", command=about_win.destroy, width=8, bootstyle=SECONDARY).pack(anchor="e", pady=(16, 0))

    def _init_language(self, lang):
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        self.btn_start.config(text=lang_map["開始錄製"] + f" ({self.hotkey_map['start']})")
        self.btn_pause.config(text=lang_map["暫停/繼續"] + f" ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=lang_map["停止"] + f" ({self.hotkey_map['stop']})")
        self.btn_play.config(text=lang_map["回放"] + f" ({self.hotkey_map['play']})")
        self.tiny_mode_btn.config(text=lang_map["MiniMode"])
        self.about_btn.config(text=lang_map["關於"])
        self.lbl_speed.config(text=lang_map["回放速度:"])
        self.btn_hotkey.config(text=lang_map["快捷鍵"])
        self.total_time_label_prefix.config(text=lang_map["總運作"])
        self.countdown_label_prefix.config(text=lang_map["單次"])
        self.time_label_prefix.config(text=lang_map["錄製"])
        self.repeat_label.config(text=lang_map["重複次數:"])
        self.repeat_unit_label.config(text=lang_map["次"])
        self.repeat_time_label.config(text=lang_map["重複時間"])
        self.repeat_interval_label.config(text=lang_map["重複間隔"])
        self.script_menu_label.config(text=lang_map["Script:"])
        self.save_script_btn_text.set(lang_map["儲存"])
        self.update_idletasks()

    def change_language(self, event=None):
        lang = self.language_var.get()
        if lang == "Language":
            return
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        self.btn_start.config(text=lang_map["開始錄製"] + f" ({self.hotkey_map['start']})")
        self.btn_pause.config(text=lang_map["暫停/繼續"] + f" ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=lang_map["停止"] + f" ({self.hotkey_map['stop']})")
        self.btn_play.config(text=lang_map["回放"] + f" ({self.hotkey_map['play']})")
        self.tiny_mode_btn.config(text=lang_map["MiniMode"])
        self.about_btn.config(text=lang_map["關於"])
        self.lbl_speed.config(text=lang_map["回放速度:"])
        self.btn_hotkey.config(text=lang_map["快捷鍵"])
        self.total_time_label_prefix.config(text=lang_map["總運作"])
        self.countdown_label_prefix.config(text=lang_map["單次"])
        self.time_label_prefix.config(text=lang_map["錄製"])
        self.repeat_label.config(text=lang_map["重複次數:"])
        self.repeat_unit_label.config(text=lang_map["次"])
        self.repeat_time_label.config(text=lang_map["重複時間"])
        self.repeat_interval_label.config(text=lang_map["重複間隔"])
        self.script_menu_label.config(text=lang_map["Script:"])
        self.save_script_btn_text.set(lang_map["儲存"])
        self.user_config["language"] = lang
        self.save_config()
        self.update_idletasks()

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_time_label(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        if time_str == "00:00:00":
            self.time_label_time.config(text=time_str, foreground="#888888")
        else:
            self.time_label_time.config(text=time_str, foreground="#15D3BD")

    def update_total_time_label(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        if time_str == "00:00:00":
            self.total_time_label_time.config(text=time_str, foreground="#888888")
        else:
            self.total_time_label_time.config(text=time_str, foreground="#FF95CA")

    def update_countdown_label(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        if time_str == "00:00:00":
            self.countdown_label_time.config(text=time_str, foreground="#888888")
        else:
            self.countdown_label_time.config(text=time_str, foreground="#DB0E59")

    def _update_play_time(self):
        if self.playing:
            idx = getattr(self, "_current_play_index", 0)
            if idx == 0:
                elapsed = 0
            else:
                elapsed = self.events[idx-1]['time'] - self.events[0]['time']
            self.update_time_label(elapsed)
            total = self.events[-1]['time'] - self.events[0]['time'] if self.events else 0
            remain = max(0, total - elapsed)
            self.update_countdown_label(remain)
            if hasattr(self, "_play_start_time"):
                if self._repeat_time_limit:
                    total_remain = max(0, self._repeat_time_limit - (time.time() - self._play_start_time))
                else:
                    total_remain = max(0, self._total_play_time - (time.time() - self._play_start_time))
                self.update_total_time_label(total_remain)
                if hasattr(self, "tiny_window") and self.tiny_window and self.tiny_window.winfo_exists():
                    if hasattr(self, "tiny_countdown_label"):
                        lang = self.language_var.get()
                        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                        h = int(total_remain // 3600)
                        m = int((total_remain % 3600) // 60)
                        s = int(total_remain % 60)
                        time_str = f"{h:02d}:{m:02d}:{s:02d}"
                        self.tiny_countdown_label.config(text=f"{lang_map['剩餘']}: {time_str}")
            self.after(100, self._update_play_time)
        else:
            self.update_time_label(0)
            self.update_countdown_label(0)
            self.update_total_time_label(0)
            if hasattr(self, "tiny_window") and self.tiny_window and self.tiny_window.winfo_exists():
                if hasattr(self, "tiny_countdown_label"):
                    lang = self.language_var.get()
                    lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                    self.tiny_countdown_label.config(text=f"{lang_map['剩餘']}: 00:00:00")

    def start_record(self):
        if self.recording:
            return
        self.events = []
        self.recording = True
        self.paused = False
        self._record_start_time = time.time()
        self.log(f"[{format_time(time.time())}] 開始錄製...")
        self._record_thread_handle = threading.Thread(target=self._record_thread, daemon=True)
        self._record_thread_handle.start()
        self.after(100, self._update_record_time)

    def _update_record_time(self):
        if self.recording:
            now = time.time()
            elapsed = now - self._record_start_time
            self.update_time_label(elapsed)
            self.after(100, self._update_record_time)
        else:
            self.update_time_label(0)

    def toggle_pause(self):
        if self.recording:
            self.paused = not self.paused
            state = "暫停" if self.paused else "繼續"
            mode = "錄製"
            self.log(f"[{format_time(time.time())}] {mode}{state}。")
            if self.paused:
                if hasattr(self, "_keyboard_recording"):
                    k_events = keyboard.stop_recording()
                    if not hasattr(self, "_paused_k_events"):
                        self._paused_k_events = []
                    self._paused_k_events += k_events
                    self._keyboard_recording = False
            else:
                keyboard.start_recording()
                self._keyboard_recording = True
        elif self.playing:
            self.paused = not self.paused
            state = "暫停" if self.paused else "繼續"
            mode = "回放"
            self.log(f"[{format_time(time.time())}] {mode}{state}。")

    def _record_thread(self):
        import keyboard
        from pynput.mouse import Controller, Listener
        try:
            self._mouse_events = []
            self._recording_mouse = True
            self._record_start_time = time.time()
            self._paused_k_events = []

            keyboard.start_recording()
            self._keyboard_recording = True

            mouse_ctrl = Controller()
            last_pos = mouse_ctrl.position

            def on_click(x, y, button, pressed):
                if self._recording_mouse and not self.paused:
                    event = {
                        'type': 'mouse',
                        'event': 'down' if pressed else 'up',
                        'button': str(button).replace('Button.', ''),
                        'x': x,
                        'y': y,
                        'time': time.time()
                    }
                    if self.target_hwnd:
                        rel_x, rel_y = screen_to_client(self.target_hwnd, x, y)
                        event['rel_x'] = rel_x
                        event['rel_y'] = rel_y
                        event['hwnd'] = self.target_hwnd
                    self._mouse_events.append(event)
            def on_scroll(x, y, dx, dy):
                if self._recording_mouse and not self.paused:
                    event = {
                        'type': 'mouse',
                        'event': 'wheel',
                        'delta': dy,
                        'x': x,
                        'y': y,
                        'time': time.time()
                    }
                    if self.target_hwnd:
                        rel_x, rel_y = screen_to_client(self.target_hwnd, x, y)
                        event['rel_x'] = rel_x
                        event['rel_y'] = rel_y
                        event['hwnd'] = self.target_hwnd
                    self._mouse_events.append(event)
            import pynput.mouse
            mouse_listener = pynput.mouse.Listener(on_click=on_click, on_scroll=on_scroll)
            mouse_listener.start()

            now = time.time()
            event = {'type': 'mouse', 'event': 'move', 'x': last_pos[0], 'y': last_pos[1], 'time': now}
            if self.target_hwnd:
                rel_x, rel_y = screen_to_client(self.target_hwnd, last_pos[0], last_pos[1])
                event['rel_x'] = rel_x
                event['rel_y'] = rel_y
                event['hwnd'] = self.target_hwnd
            self._mouse_events.append(event)

            while self.recording:
                now = time.time()
                pos = mouse_ctrl.position
                if pos != last_pos and not self.paused:
                    event = {'type': 'mouse', 'event': 'move', 'x': pos[0], 'y': pos[1], 'time': now}
                    if self.target_hwnd:
                        rel_x, rel_y = screen_to_client(self.target_hwnd, pos[0], pos[1])
                        event['rel_x'] = rel_x
                        event['rel_y'] = rel_y
                        event['hwnd'] = self.target_hwnd
                    self._mouse_events.append(event)
                    last_pos = pos
                time.sleep(MOUSE_SAMPLE_INTERVAL)
            self._recording_mouse = False
            mouse_listener.stop()
            if hasattr(self, "_keyboard_recording") and self._keyboard_recording:
                k_events = keyboard.stop_recording()
            else:
                k_events = []
            all_k_events = []
            if hasattr(self, "_paused_k_events"):
                all_k_events += self._paused_k_events
            all_k_events += k_events

            filtered_k_events = [e for e in all_k_events if not (e.name == 'f10' and e.event_type in ('down', 'up'))]
            self.events = sorted(
                [{'type': 'keyboard', 'event': e.event_type, 'name': e.name, 'time': e.time} for e in filtered_k_events] +
                self._mouse_events,
                key=lambda e: e['time']
            )
            self.log(f"[{format_time(time.time())}] 錄製完成，共 {len(self.events)} 筆事件。")
            self.log(f"事件預覽: {json.dumps(self.events[:10], ensure_ascii=False, indent=2)}")
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] 錄製執行緒發生錯誤: {ex}")

    def stop_record(self):
        if self.recording:
            self.recording = False
            self.log(f"[{format_time(time.time())}] 停止錄製。")
            self._wait_record_thread_finish()

    def stop_all(self):
        stopped = False
        if self.recording:
            self.recording = False
            stopped = True
            self.log(f"[{format_time(time.time())}] 停止錄製。")
            self._wait_record_thread_finish()
        if self.playing:
            self.playing = False
            stopped = True
            self.log(f"[{format_time(time.time())}] 停止回放。")
        if not stopped:
            self.log(f"[{format_time(time.time())}] 無進行中動作可停止。")
        self.update_time_label(0)
        self.update_countdown_label(0)
        self.update_total_time_label(0)
        self._update_play_time()
        self._update_record_time()

    def _wait_record_thread_finish(self):
        if hasattr(self, '_record_thread_handle') and self._record_thread_handle.is_alive():
            self.after(100, self._wait_record_thread_finish)
        else:
            self.auto_save_script()

    def play_record(self):
        import keyboard
        import mouse
        if self.playing:
            return
        if not self.events:
            self.log("沒有可回放的事件，請先錄製或載入腳本。")
            return
        try:
            speed_val = int(self.speed_var.get())
            if speed_val < 1:
                speed_val = 1
            elif speed_val > 1000:
                speed_val = 1000
            self.speed_var.set(str(speed_val))
            self.speed = speed_val / 100.0
        except:
            self.speed = 1.0
            self.speed_var.set("100")

        repeat_time_sec = self._parse_time_to_seconds(self.repeat_time_var.get())
        repeat_interval_sec = self._parse_time_to_seconds(self.repeat_interval_var.get())
        self._repeat_time_limit = repeat_time_sec if repeat_time_sec > 0 else None

        try:
            repeat = int(self.repeat_var.get())
        except:
            repeat = 1
        if repeat <= 0:
            repeat = 0

        if self.events:
            single_time = (self.events[-1]['time'] - self.events[0]['time']) / self.speed
        else:
            single_time = 0

        if self._repeat_time_limit and repeat > 0:
            total_time = self._repeat_time_limit
        else:
            total_time = single_time * repeat + repeat_interval_sec * max(0, repeat - 1)
        self._total_play_time = total_time

        self._play_start_time = time.time()
        self.update_total_time_label(self._total_play_time)
        self.log(f"[{format_time(time.time())}] 開始回放，速度倍率: {self.speed:.2f}: {self.speed_var.get()}")
        self.playing = True
        self.paused = False
        self._repeat_times = repeat
        self._random_interval = self.random_interval_var.get()
        threading.Thread(target=self._play_thread, daemon=True).start()
        self.after(100, self._update_play_time)

    def _play_thread(self):
        self.playing = True
        self.paused = False
        try:
            repeat = int(self.repeat_var.get())
        except:
            repeat = 1
        infinite_repeat = repeat <= 0
        repeat_time_limit = self._repeat_time_limit if hasattr(self, "_repeat_time_limit") else None
        single_time = (self.events[-1]['time'] - self.events[0]['time']) / self.speed if self.events else 0

        repeat_interval_sec = self._parse_time_to_seconds(self.repeat_interval_var.get())
        random_interval = getattr(self, "_random_interval", False)

        count = 0
        play_start_time = time.time()
        while self.playing and (infinite_repeat or count < repeat):
            if repeat_time_limit and (time.time() - play_start_time) >= repeat_time_limit:
                self.log(f"【重複時間到】已達 {repeat_time_limit} 秒，自動停止回放。")
                break
            self._current_play_index = 0
            total_events = len(self.events)
            if total_events == 0 or not self.playing:
                break
            base_time = self.events[0]['time']
            play_start = time.time()
            while self._current_play_index < total_events:
                if not self.playing:
                    break
                while self.paused:
                    if not self.playing:
                        break
                    time.sleep(0.05)
                    play_start += 0.05
                if not self.playing:
                    break
                i = self._current_play_index
                e = self.events[i]
                event_offset = (e['time'] - base_time) / self.speed
                target_time = play_start + event_offset
                while True:
                    now = time.time()
                    if not self.playing:
                        break
                    if now >= target_time:
                        break
                    if self.paused:
                        if not self.playing:
                            break
                        time.sleep(0.05)
                        target_time += 0.05
                        continue
                    time.sleep(min(0.01, target_time - now))
                if not self.playing:
                    break
                if e['type'] == 'mouse':
                    if 'rel_x' in e and 'rel_y' in e and 'hwnd' in e:
                        try:
                            win32gui.ShowWindow(e['hwnd'], win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(e['hwnd'])
                        except Exception:
                            pass
                        abs_x, abs_y = client_to_screen(e['hwnd'], e['rel_x'], e['rel_y'])
                        if e.get('event') == 'move':
                            move_mouse_abs(abs_x, abs_y)
                        elif e.get('event') == 'down':
                            move_mouse_abs(abs_x, abs_y)
                            mouse_event_win('down', button=e.get('button', 'left'))
                            self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                        elif e.get('event') == 'up':
                            move_mouse_abs(abs_x, abs_y)
                            mouse_event_win('up', button=e.get('button', 'left'))
                            self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                        elif e.get('event') == 'wheel':
                            move_mouse_abs(abs_x, abs_y)
                            mouse_event_win('wheel', delta=e.get('delta', 0))
                            self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                    else:
                        if e.get('event') == 'move':
                            move_mouse_abs(e['x'], e['y'])
                        elif e.get('event') == 'down':
                            move_mouse_abs(e['x'], e['y'])
                            mouse_event_win('down', button=e.get('button', 'left'))
                            self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                        elif e.get('event') == 'up':
                            move_mouse_abs(e['x'], e['y'])
                            mouse_event_win('up', button=e.get('button', 'left'))
                            self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                        elif e.get('event') == 'wheel':
                            move_mouse_abs(e['x'], e['y'])
                            mouse_event_win('wheel', delta=e.get('delta', 0))
                            self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                elif e['type'] == 'keyboard':
                    if e['event'] == 'down':
                        keyboard.press(e['name'])
                    elif e['event'] == 'up':
                        keyboard.release(e['name'])
                    self.log(f"[{format_time(e['time'])}] 鍵盤: {e['event']} {e['name']}")
                self._current_play_index += 1
            if not self.playing:
                break
            count += 1
            if count < repeat or infinite_repeat:
                if repeat_interval_sec > 0:
                    if random_interval:
                        interval_sec = random.randint(1, repeat_interval_sec)
                        self.log(f"【隨機間隔】第{count}次執行後，隨機間隔 {interval_sec} 秒。")
                    else:
                        interval_sec = repeat_interval_sec
                        self.log(f"【固定間隔】第{count}次執行後，間隔 {interval_sec} 秒。")
                    interval_start = time.time()
                    while self.playing and time.time() - interval_start < interval_sec:
                        if self.paused:
                            time.sleep(0.05)
                            interval_start += 0.05
                            continue
                        time.sleep(0.05)
        self.playing = False
        self.paused = False
        self.log(f"[{format_time(time.time())}] 回放結束。")

    def get_events_json(self):
        return json.dumps(self.events, ensure_ascii=False, indent=2)

    def set_events_json(self, json_str):
        try:
            self.events = json.loads(json_str)
            self.log(f"[{format_time(time.time())}] 已從 JSON 載入 {len(self.events)} 筆事件。")
        except Exception as e:
            self.log(f"[{format_time(time.time())}] JSON 載入失敗: {e}")

    def save_config(self):
        self.user_config["skin"] = self.theme_var.get()
        self.user_config["last_script"] = self.script_var.get()
        self.user_config["repeat"] = self.repeat_var.get()
        self.user_config["speed"] = self.speed_var.get()
        self.user_config["script_dir"] = self.script_dir
        self.user_config["language"] = self.language_var.get()
        self.user_config["repeat_time"] = self.repeat_time_var.get()
        self.user_config["hotkey_map"] = self.hotkey_map
        save_user_config(self.user_config)
        self.log("【整體設定已更新】")

    def auto_save_script(self):
        try:
            ts = datetime.datetime.now().strftime("%Y_%m%d_%H%M_%S")
            filename = f"{ts}.json"
            path = os.path.join(self.script_dir, filename)
            script_data = {"events": self.events, "speed": self.speed_var.get(), "repeat": self.repeat_var.get(), "repeat_time": self.repeat_time_var.get()}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)
            self.log(f"[{format_time(time.time())}] 自動存檔：{filename}，事件數：{len(self.events)}")
            self.refresh_script_list()
            self.script_var.set(filename)
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(filename)
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] 存檔失敗: {ex}")

    def save_script_settings(self):
        script = self.script_var.get()
        if not script:
            self.log("請先選擇一個腳本再儲存設定。")
            return
        path = os.path.join(self.script_dir, script)
        if not os.path.exists(path):
            self.log("找不到腳本檔案，請先錄製或載入腳本。")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not (isinstance(data, dict) and "events" in data):
                data = {"events": data}
            data["speed"] = self.speed_var.get()
            data["repeat"] = self.repeat_var.get()
            data["repeat_time"] = self.repeat_time_var.get()
            data["repeat_interval"] = self.repeat_interval_var.get()
            data["random_interval"] = self.random_interval_var.get()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log(f"已將設定儲存到腳本：{script}")
            self.log("【腳本設定已更新】")
        except Exception as ex:
            self.log(f"儲存腳本設定失敗: {ex}")

    def on_script_selected(self, event=None):
        script = self.script_var.get()
        if script:
            path = os.path.join(self.script_dir, script)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "events" in data:
                self.events = data["events"]
                self.speed_var.set(data.get("speed", "100"))
                self.repeat_var.set(data.get("repeat", "1"))
                self.repeat_time_var.set(data.get("repeat_time", "00:00:00"))
                self.repeat_interval_var.set(data.get("repeat_interval", "00:00:00"))
                self.random_interval_var.set(data.get("random_interval", False))
            else:
                self.events = data
            self.log(f"[{format_time(time.time())}] 腳本已載入：{script}，共 {len(self.events)} 筆事件。")
            self.log("【腳本設定已載入】")
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(script)
            if self.events:
                total = self.events[-1]['time'] - self.events[0]['time']
                self.update_countdown_label(total)
            else:
                self.update_countdown_label(0)
        self.save_config()

    def load_script(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], initialdir=self.script_dir)
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "events" in data:
                self.events = data["events"]
                self.speed_var.set(data.get("speed", "100"))
                self.repeat_var.set(data.get("repeat", "1"))
                self.repeat_time_var.set(data.get("repeat_time", "00:00:00"))
            else:
                self.events = data
            self.log(f"[{format_time(time.time())}] 腳本已載入：{os.path.basename(path)}，共 {len(self.events)} 筆事件。")
            self.refresh_script_list()
            self.script_var.set(os.path.basename(path))
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(os.path.basename(path))
            self.save_config()

    def load_last_script(self):
        if os.path.exists(LAST_SCRIPT_FILE):
            with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
                last_script = f.read().strip()
            if last_script:
                script_path = os.path.join(self.script_dir, last_script)
                if os.path.exists(script_path):
                    with open(script_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and "events" in data:
                        self.events = data["events"]
                        self.speed_var.set(data.get("speed", "100"))
                        self.repeat_var.set(data.get("repeat", "1"))
                        self.repeat_time_var.set(data.get("repeat_time", "00:00:00"))
                    else:
                        self.events = data
                    self.script_var.set(last_script)
                    self.log(f"[{format_time(time.time())}] 已自動載入上次腳本：{last_script}，共 {len(self.events)} 筆事件。")

    def update_mouse_pos(self):
        try:
            import mouse
            x, y = mouse.get_position()
            self.mouse_pos_label.config(text=f"( X:{x}, Y:{y} )")
        except Exception:
            self.mouse_pos_label.config(text="( X:?, Y:? )")
        self.after(100, self.update_mouse_pos)

    def rename_script(self):
        old_name = self.script_var.get()
        new_name = self.rename_var.get().strip()
        if not old_name or not new_name:
            self.log(f"[{format_time(time.time())}] 請選擇腳本並輸入新名稱。")
            return
        if not new_name.endswith('.json'):
            new_name += '.json'
        old_path = os.path.join(self.script_dir, old_name)
        new_path = os.path.join(self.script_dir, new_name)
        if os.path.exists(new_path):
            self.log(f"[{format_time(time.time())}] 檔案已存在，請換個名稱。")
            return
        try:
            os.rename(old_path, new_path)
            self.log(f"[{format_time(time.time())}] 腳本已更名為：{new_name}")
            self.refresh_script_list()
            self.script_var.set(new_name)
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(new_name)
        except Exception as e:
            self.log(f"[{format_time(time.time())}] 更名失敗: {e}")
        self.rename_var.set("")

    def open_scripts_dir(self):
        path = os.path.abspath(self.script_dir)
        os.startfile(path)

    def open_hotkey_settings(self):
        win = tb.Toplevel(self)
        win.title("Hotkey")
        win.geometry("300x320")
        win.resizable(False, False)
        try:
            import sys
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                icon_path = "umi_奶茶色.ico"
            win.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定快捷鍵視窗 icon: {e}")

        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        labels = {"start": lang_map["開始錄製"], "pause": lang_map["暫停/繼續"], "stop": lang_map["停止"], "play": lang_map["回放"], "tiny": lang_map["MiniMode"]}
        vars = {}
        entries = {}
        row = 0

        def on_entry_key(event, key, var):
            keys = []
            if event.state & 0x0001: keys.append("shift")
            if event.state & 0x0004: keys.append("ctrl")
            if event.state & 0x0008: keys.append("alt")
            key_name = event.keysym.lower()
            if key_name not in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"):
                keys.append(key_name)
            var.set("+".join(keys))
            return "break"

        def on_entry_release(event, key, var):
            key_name = event.keysym.lower()
            if key_name not in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"):
                var.set(key_name)
            return "break"

        def on_entry_focus_in(event, var):
            var.set("輸入按鍵")

        def on_entry_focus_out(event, key, var):
            if var.get() == "輸入按鍵" or not var.get():
                var.set(self.hotkey_map[key])

        for key, label in labels.items():
            tb.Label(win, text=label, font=("LINESeedTW_TTF_Rg", 11)).grid(row=row, column=0, padx=10, pady=8, sticky="w")
            var = tk.StringVar(value=self.hotkey_map[key])
            entry = tb.Entry(win, textvariable=var, width=8, font=("Consolas", 11), state="normal")
            entry.grid(row=row, column=1, padx=10)
            vars[key] = var
            entries[key] = entry
            entry.bind("<KeyRelease>", lambda e, k=key, v=var: on_entry_release(e, k, v))
            entry.bind("<FocusIn>", lambda e, v=var: on_entry_focus_in(e, v))
            entry.bind("<FocusOut>", lambda e, k=key, v=var: on_entry_focus_out(e, k, v))
            row += 1

        def save_and_apply():
            for key in self.hotkey_map:
                val = vars[key].get()
                if val and val != "輸入按鍵":
                    self.hotkey_map[key] = val.lower()
            self._register_hotkeys()
            self._update_hotkey_labels()
            self.save_config()
            self.log("快捷鍵設定已更新。")
            win.destroy()

        tb.Button(win, text="儲存", command=save_and_apply, width=10, bootstyle=SUCCESS).grid(row=row, column=0, columnspan=2, pady=16)

    def _register_hotkeys(self):
        import keyboard
        for handler in list(self._hotkey_handlers.values()):
            try:
                keyboard.remove_hotkey(handler)
            except Exception as ex:
                self.log(f"移除快捷鍵時發生錯誤: {ex}")
        self._hotkey_handlers.clear()
        for key, hotkey in self.hotkey_map.items():
            try:
                target = getattr(self, {"start": "start_record", "pause": "toggle_pause", "stop": "stop_all", "play": "play_record", "tiny": "toggle_tiny_mode"}[key])
                handler = keyboard.add_hotkey(hotkey, target, suppress=False, trigger_on_release=False)
                self._hotkey_handlers[key] = handler
                self.log(f"已註冊快捷鍵: {hotkey} → {key}")
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")

    def _update_hotkey_labels(self):
        self.btn_start.config(text=f"開始錄製 ({self.hotkey_map['start']})")
        self.btn_pause.config(text=f"暫停/繼續 ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=f"停止 ({self.hotkey_map['stop']})")
        self.btn_play.config(text=f"回放 ({self.hotkey_map['play']})")
        # MiniMode 按鈕同步更新（若存在 tiny 按鈕）
        if hasattr(self, "tiny_btns"):
            for btn, icon, key in self.tiny_btns:
                btn.config(text=f"{icon} {self.hotkey_map.get(key, '')}")

    def toggle_tiny_mode(self):
        # 使用 2.5 版本的 MiniMode 行為
        if not hasattr(self, "tiny_mode_on"):
            self.tiny_mode_on = False
        self.tiny_mode_on = not self.tiny_mode_on
        if self.tiny_mode_on:
            if self.tiny_window is None or not self.tiny_window.winfo_exists():
                self.tiny_window = tb.Toplevel(self)
                self.tiny_window.title("ChroLens_Mimic MiniMode")
                # 2.5: 寬 620，高 40 的迷你列
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
                except Exception as e:
                    print(f"無法設定 MiniMode icon: {e}")
                self.tiny_btns = []
                # 倒數 label（多語系）
                lang = self.language_var.get()
                lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                self.tiny_countdown_label = tb.Label(
                    self.tiny_window,
                    text=f"{lang_map['剩餘']}: 00:00:00",
                    font=("LINESeedTW_TTF_Rg", 12),
                    foreground="#FF95CA", width=13
                )
                self.tiny_countdown_label.grid(row=0, column=0, padx=2, pady=5)
                # 拖曳功能
                self.tiny_window.bind("<ButtonPress-1>", self._start_move_tiny)
                self.tiny_window.bind("<B1-Motion>", self._move_tiny)
                # 按鈕定義（圖示 + 對應 hotkey map key）
                btn_defs = [
                    ("⏺", "start"),
                    ("⏸", "pause"),
                    ("⏹", "stop"),
                    ("▶︎", "play"),
                    ("⤴︎", "tiny")
                ]
                for i, (icon, key) in enumerate(btn_defs):
                    text = f"{icon} {self.hotkey_map.get(key, '')}"
                    cmd = getattr(self, {"start": "start_record", "pause": "toggle_pause", "stop": "stop_all", "play": "play_record", "tiny": "toggle_tiny_mode"}[key])
                    btn = tb.Button(
                        self.tiny_window,
                        text=text,
                        width=7, style="My.TButton",
                        command=cmd
                    )
                    btn.grid(row=0, column=i+1, padx=2, pady=5)
                    self.tiny_btns.append((btn, icon, key))
                self.tiny_window.protocol("WM_DELETE_WINDOW", self._close_tiny_mode)
                # 隱藏主視窗，顯示迷你列
                try:
                    self.withdraw()
                except Exception:
                    pass
        else:
            self._close_tiny_mode()

    def _close_tiny_mode(self):
        if self.tiny_window and self.tiny_window.winfo_exists():
            self.tiny_window.destroy()
        self.tiny_mode_on = False
        try:
            self.deiconify()
        except Exception:
            pass

    def _start_move_tiny(self, event):
        self._tiny_drag_x = event.x
        self._tiny_drag_y = event.y

    def _move_tiny(self, event):
        x = self.tiny_window.winfo_x() + event.x - self._tiny_drag_x
        y = self.tiny_window.winfo_y() + event.y - self._tiny_drag_y
        self.tiny_window.geometry(f"+{x}+{y}")

    def use_default_script_dir(self):
        self.script_dir = SCRIPTS_DIR
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        self.refresh_script_list()
        self.save_config()
        os.startfile(self.script_dir)

    def refresh_script_list(self):
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        self.script_combo['values'] = scripts
        if self.script_var.get() not in scripts:
            self.script_var.set('')

    def refresh_script_listbox(self):
        self.script_listbox.delete(0, "end")
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        for f in scripts:
            self.script_listbox.insert("end", f)

    def on_page_selected(self, event=None):
        idx = self.page_menu.curselection()
        if not idx:
            return
        self.show_page(idx[0])

    def show_page(self, idx):
        # 清除所有子元件的配置
        for widget in self.page_content_frame.winfo_children():
            widget.grid_forget()
            
        # 統一使用 grid 佈局，並設定相同的配置參數
        if idx == 0:
            self.log_text.grid(row=0, column=0, sticky="nsew")
            for child in self.page_content_frame.winfo_children():
                if isinstance(child, tb.Scrollbar):
                    child.grid(row=0, column=1, sticky="ns")
        elif idx == 1:
            self.script_setting_frame.grid(row=0, column=0, sticky="nsew")
        elif idx == 2:
            self.global_setting_frame.grid(row=0, column=0, sticky="nsew")

    def on_script_listbox_select(self, event=None):
        idx = self.script_listbox.curselection()
        if idx:
            script = self.script_listbox.get(idx[0])
            self.script_var.set(script)
            self.on_script_selected()
            path = os.path.join(self.script_dir, script)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                hotkey = data.get("script_hotkey", "")
                self.hotkey_capture_var.set(hotkey)
            except Exception:
                self.hotkey_capture_var.set("")

    def on_hotkey_entry_key(self, event):
        """改進的按鍵捕捉處理"""
        keys = []
        
        # 檢測修飾鍵
        if event.state & 0x0001: keys.append("shift")
        if event.state & 0x0004: keys.append("ctrl")
        if event.state & 0x0008: keys.append("alt")
        
        # 獲取按鍵名稱
        key_name = event.keysym.lower()
        
        # 特殊按鍵映射
        special_keys = {
            'space': 'space',
            'return': 'enter',
            'escape': 'esc',
            'tab': 'tab'
        }
        
        # 處理功能鍵 F1-F12
        if key_name.startswith('f') and key_name[1:].isdigit():
            if 1 <= int(key_name[1:]) <= 12:
                keys.append(key_name)
        # 處理特殊按鍵
        elif key_name in special_keys:
            keys.append(special_keys[key_name])
        # 處理一般按鍵
        elif key_name not in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"):
            keys.append(key_name)
        
        # 組合並顯示按鍵
        if keys:
            self.hotkey_capture_var.set("+".join(keys))
        
        # 防止按鍵事件傳遞
        return "break"

    def set_script_hotkey(self):
        script = self.script_var.get()
        hotkey = self.hotkey_capture_var.get()
        if not script or not hotkey:
            self.log("請選擇腳本並輸入快捷鍵。")
            return
        path = os.path.join(self.script_dir, script)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["script_hotkey"] = hotkey
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log(f"已設定腳本 {script} 的快捷鍵：{hotkey}")
        except Exception as ex:
            self.log(f"設定腳本快捷鍵失敗: {ex}")

    def delete_selected_script(self):
        idx = self.script_listbox.curselection()
        if not idx:
            self.log("請先選擇要刪除的腳本。")
            return
        script = self.script_listbox.get(idx[0])
        path = os.path.join(self.script_dir, script)
        try:
            os.remove(path)
            self.log(f"已刪除腳本：{script}")
            self.refresh_script_listbox()
            self.refresh_script_list()
        except Exception as ex:
            self.log(f"刪除腳本失敗: {ex}")

    def select_target_window(self):
        self.log("【選擇目標視窗】功能尚未實作。")

    # 新增：啟動檔案監聽或輪詢（低負載、即時顯示）
    def _start_script_watcher(self):
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        if _HAVE_WATCHDOG and Observer is not None:
            class _Handler(FileSystemEventHandler):
                def __init__(self, app):
                    self.app = app
                def on_any_event(self, event):
                    # 使用 after 保證在主線程更新 UI
                    try:
                        self.app.after(100, self.app.refresh_script_listbox)
                    except Exception:
                        pass
            try:
                handler = _Handler(self)
                self._observer = Observer()
                self._observer.schedule(handler, self.script_dir, recursive=False)
                self._observer.daemon = True
                self._observer.start()
                # 初次載入
                self.refresh_script_listbox()
            except Exception:
                # 若 observer 啟動失敗，退回輪詢
                self._start_script_poller()
        else:
            # fallback: 輪詢（每 2 秒，比較檔案清單差異）
            self._start_script_poller()

    def _start_script_poller(self):
        try:
            self._last_scripts_snapshot = tuple(sorted([f for f in os.listdir(self.script_dir) if f.endswith('.json')]))
        except Exception:
            self._last_scripts_snapshot = ()
        # 立即 refresh，之後靠 _poll_scripts 更新
        self.refresh_script_listbox()
        self.after(2000, self._poll_scripts)

    def _poll_scripts(self):
        try:
            current = tuple(sorted([f for f in os.listdir(self.script_dir) if f.endswith('.json')]))
        except Exception:
            current = ()
        if getattr(self, "_last_scripts_snapshot", None) != current:
            self._last_scripts_snapshot = current
            # 只在變更時更新 listbox（減少不必要 UI 更新）
            try:
                self.refresh_script_listbox()
                self.refresh_script_list()
            except Exception:
                pass
        # 下次輪詢（2 秒）
        try:
            self.after(2000, self._poll_scripts)
        except Exception:
            pass

    # 新增：視窗關閉時清理 observer
    def _on_close(self):
        try:
            if getattr(self, "_observer", None):
                try:
                    self._observer.stop()
                    self._observer.join(timeout=1)
                except Exception:
                    pass
                self._observer = None
        except Exception:
            pass
        try:
            super().destroy()
        except Exception:
            try:
                self.destroy()
            except Exception:
                pass