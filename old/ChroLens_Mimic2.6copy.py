#ChroLens Studio - Lucienwooo
#pyinstaller --noconsole --onedir --icon=umi_奶茶色.ico --add-data "umi_奶茶色.ico;." ChroLens_Mimic2.6.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
import threading, time, json, os, datetime
import keyboard, mouse
import ctypes
import win32api
import win32gui
import win32con
import pywintypes
import random  # 新增

def show_error_window(window_name):
    ctypes.windll.user32.MessageBoxW(
        0,
        f'找不到 "{window_name}" 視窗，請重試',
        '錯誤',
        0x10  # MB_ICONERROR
    )

def client_to_screen(hwnd, rel_x, rel_y, window_name=""):
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        abs_x = left + rel_x
        abs_y = top + rel_y
        return abs_x, abs_y
    except pywintypes.error:
        ctypes.windll.user32.MessageBoxW(
            0,
            f'找不到 "{window_name}" 視窗，請重試',
            '錯誤',
            0x10  # MB_ICONERROR
        )
        raise

# ====== UI 介面 row 對應說明 ======
# row 0 (frm_top): 
#   開始錄製（btn_start）、暫停/繼續（btn_pause）、停止（btn_stop）、回放（btn_play）
#   MiniMode（tiny_mode_btn）、skin下拉選單（theme_combo）
#
# row 1 (frm_bottom): 
#   回放速度（lbl_speed, speed_var 輸入框）、script路徑（btn_scripts_dir 按鈕）
#   快捷鍵（btn_hotkey 按鈕）、關於（about_btn）、語言下拉選單（lang_combo）
#
# row 2 (frm_repeat): 
#   重複次數（repeat_var 輸入框）、單位「次」
#   重複時間（repeat_time_var 輸入框）、重複時間標籤（repeat_time_label）
#   重複間隔（repeat_interval_var 輸入框）、重複間隔標籤（repeat_interval_label）
#   儲存按鈕（save_script_btn）
#
# row 3 (frm_script): 
#   腳本選單（script_combo）、腳本重新命名輸入框（rename_entry）、Rename（rename_script 按鈕）
#   選擇目標視窗（select_target_window 按鈕）
#
# row 4 (frm_log): 
#   滑鼠座標（mouse_pos_label）
#   錄製（time_label_prefix, time_label_time）
#   單次剩餘（countdown_label_prefix, countdown_label_time）
#   總運作（total_time_label_prefix, total_time_label_time）
#
# 下方為日誌顯示區（log_text）

# ====== 滑鼠控制函式放在這裡 ======
def move_mouse_abs(x, y):
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

def mouse_event_win(event, x=0, y=0, button='left', delta=0):
    user32 = ctypes.windll.user32
    if not button:
        button = 'left'
    if event == 'down' or event == 'up':
        flags = {'left': (0x0002, 0x0004), 'right': (0x0008, 0x0010), 'middle': (0x0020, 0x0040)}
        flag = flags.get(button, (0x0002, 0x0004))[0 if event == 'down' else 1]
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),
                        ("dy", ctypes.c_long),
                        ("mouseData", ctypes.c_ulong),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),
                        ("mi", MOUSEINPUT)]
        inp = INPUT()
        inp.type = 0
        inp.mi = MOUSEINPUT(0, 0, 0, flag, 0, None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    elif event == 'wheel':
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", ctypes.c_long),
                        ("dy", ctypes.c_long),
                        ("mouseData", ctypes.c_ulong),
                        ("dwFlags", ctypes.c_ulong),
                        ("time", ctypes.c_ulong),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", ctypes.c_ulong),
                        ("mi", MOUSEINPUT)]
        inp = INPUT()
        inp.type = 0
        inp.mi = MOUSEINPUT(0, 0, int(delta * 120), 0x0800, 0, None)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

# ====== RecorderApp 類別與其餘程式碼 ======
SCRIPTS_DIR = "scripts"
LAST_SCRIPT_FILE = "last_script.txt"
LAST_SKIN_FILE = "last_skin.txt"  # 新增這行
MOUSE_SAMPLE_INTERVAL = 0.01  # 10ms

LANG_MAP = {
    "繁體中文": {
        "開始錄製": "開始錄製",
        "暫停/繼續": "暫停/繼續",
        "停止": "停止",
        "回放": "回放",
        "MiniMode": "MiniMode",
        "Script路徑": "Script路徑",
        "快捷鍵": "快捷鍵",
        "關於": "關於",
        "重複次數:": "重複次數:",
        "次": "次",
        "重複時間": "重複時間",
        "Script:": "Script:",
        "重新命名": "重新命名",
        "Script": "Script",
        "合併並儲存": "合併並儲存",
        "所有Script": "所有Script",
        "新Script名稱：": "新Script名稱：",
        "確定": "確定",
        "所有Script": "所有Script",
        "清空": "清空",
        "加入": "加入",
        "移除": "移除",
        "延遲秒數:": "遲延秒數:",
        "Language": "Language",
        "回放速度:": "回放速度:",
        "總運作": "總運作",
        "單次": "單次",
        "錄製": "錄製",
        "刪除": "刪除",
        "儲存": "儲存",
        "重複間隔": "重複間隔",
        "剩餘": "剩餘"
    },
    "日本語": {
        "開始錄製": "録画開始",
        "暫停/繼續": "一時停止 / 再開",
        "停止": "停止",
        "回放": "再生",
        "MiniMode": "ミニモード",
        "Script路徑": "Scriptのパス",
        "快捷鍵": "ホットキー",
        "關於": "アバウト",
        "重複次數:": "繰り返し回数：",
        "次": "回",
        "重複時間": "間隔時間",
        "Script:": "Script：",
        "重新命名": "名前を変更",
        "Script": "Script",
        "合併並儲存": "結合して保存",
        "所有Script": "全Script",
        "新Script名稱：": "新しい名前：",
        "確定": "OK",
        "延遲秒數:": "ディレイ（秒）：",
        "Language": "言語",
        "回放速度:": "再生速度：",
        "總運作": "総再生",
        "單次": "1回のみ",
        "錄製": "録画",
        "刪除": "削除",
        "儲存": "保存",
        "重複間隔": "繰り返し間隔",
        "剩餘": "残り"
    },
    "English": {
        "開始錄製": "Start Recording",
        "暫停/繼續": "Pause/Resume",
        "停止": "Stop",
        "回放": "Play",
        "MiniMode": "Mini Mode",
        "Script路徑": "Script Path",
        "快捷鍵": "Hotkey",
        "關於": "About",
        "重複次數:": "Repeat:",
        "次": "times",
        "重複時間": "Interval",
        "Script:": "Script:",
        "重新命名": "Rename",
        "Script": "Script",
        "所有Script": "All Scripts",
        "新Script名稱：": "New Script Name:",
        "確定": "Confirm",
        "延遲秒數:": "Delay (sec):",
        "Language": "Language",
        "回放速度:": "Playback Speed:",
        "總運作": "Total Runs",
        "單次": "Single Run",
        "錄製": "Record",
        "刪除": "Delete",
        "儲存": "Save",
        "重複間隔": "Repeat Interval",
        "剩餘": "Remain"
    }
}

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, background="#ffffe0",
            relief="solid", borderwidth=1,
            font=("Microsoft JhengHei", 10)
        )
        label.pack(ipadx=6, ipady=2)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def screen_to_client(hwnd, x, y):
    # 螢幕座標轉視窗內座標
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return x - left, y - top

def client_to_screen(hwnd, x, y):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return left + x, top + y

class RecorderApp(tb.Window):
    def __init__(self):
        self.user_config = load_user_config()
        skin = self.user_config.get("skin", "darkly")
        # 讀取最後一次語言設定，預設繁體中文
        lang = self.user_config.get("language", "繁體中文")
        super().__init__(themename=skin)
        self.language_var = tk.StringVar(self, value=lang)
        self._hotkey_handlers = {}
        self.tiny_window = None
        self.target_hwnd = None
        self.target_title = None

        # 讀取 hotkey_map，若無則用預設
        self.hotkey_map = self.user_config.get("hotkey_map", {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "tiny": "alt+`"
        })

        # ====== 統一字體 style ======
        self.style.configure("My.TButton", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TLabel", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TEntry", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TCombobox", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TCheckbutton", font=("Microsoft JhengHei", 9))
        self.style.configure("TinyBold.TButton", font=("Microsoft JhengHei", 9, "bold"))

        self.title("ChroLens_Mimic_2.6")
        try:
            import sys, os
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                icon_path = "umi_奶茶色.ico"
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定 icon: {e}")

        # 在左上角建立一個小label作為icon區域的懸浮觸發點
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

        # 設定腳本資料夾
        self.script_dir = self.user_config.get("script_dir", SCRIPTS_DIR)
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)

        # ====== 上方操作區 ======
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

        # ====== skin下拉選單 ======
        themes = ["darkly", "cyborg", "superhero", "journal","minty", "united", "morph", "lumen"]
        self.theme_var = tk.StringVar(value=self.style.theme_use())
        theme_combo = tb.Combobox(frm_top, textvariable=self.theme_var, values=themes, state="readonly", width=6, style="My.TCombobox")
        theme_combo.grid(row=0, column=8, padx=(4, 8), sticky="e")
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.change_theme())

        # MiniMode 按鈕（skin下拉選單左側）
        self.tiny_mode_btn = tb.Button(
            frm_top, text="MiniMode", style="My.TButton",
            command=self.toggle_tiny_mode, width=10
        )
        self.tiny_mode_btn.grid(row=0, column=7, padx=4)

        # ====== 下方操作區 ======
        frm_bottom = tb.Frame(self, padding=(8, 0, 8, 5))
        frm_bottom.pack(fill="x")
        self.lbl_speed = tb.Label(frm_bottom, text="回放速度:", style="My.TLabel")
        self.lbl_speed.grid(row=0, column=0, padx=(0, 6))
        self.speed_tooltip = Tooltip(self.lbl_speed, "正常速度1倍=100,範圍1~1000")
        self.update_speed_tooltip()
        self.speed_var = tk.StringVar(value=self.user_config.get("speed", "100"))  # 預設100
        tb.Entry(frm_bottom, textvariable=self.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=6)
        self.btn_scripts_dir = tb.Button(frm_bottom, text="script路徑", command=self.use_default_script_dir, bootstyle=SECONDARY, width=10, style="My.TButton")
        self.btn_scripts_dir.grid(row=0, column=3, padx=6)
        self.btn_hotkey = tb.Button(frm_bottom, text="快捷鍵", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=10, style="My.TButton")
        self.btn_hotkey.grid(row=0, column=4, padx=6)
        self.about_btn = tb.Button(
            frm_bottom, text="關於", width=6, style="My.TButton",
            command=self.show_about_dialog, bootstyle=SECONDARY
        )
        self.about_btn.grid(row=0, column=5, padx=6, sticky="e")
        # 語言下拉選單
        saved_lang = self.user_config.get("language", "繁體中文")
        self.language_var = tk.StringVar(self, value="Language")  # 一律顯示 Language
        lang_combo = tb.Combobox(
            frm_bottom,
            textvariable=self.language_var,
            values=["繁體中文", "日本語", "English"],
            state="readonly",
            width=10,
            style="My.TCombobox"
        )
        lang_combo.grid(row=0, column=6, padx=(6, 8), sticky="e")
        lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        self.language_combo = lang_combo

        # ====== 重複次數設定 ======
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

        # 新增「重複間隔」輸入框和標籤
        self.repeat_interval_var = tk.StringVar(value="00:00:00")
        repeat_interval_entry = tb.Entry(frm_repeat, textvariable=self.repeat_interval_var, width=10, style="My.TEntry", justify="center")
        repeat_interval_entry.grid(row=0, column=5, padx=(10, 2))
        self.repeat_interval_label = tb.Label(frm_repeat, text="重複間隔", style="My.TLabel")
        self.repeat_interval_label.grid(row=0, column=6, padx=(0, 2))

        # 新增「隨機」勾選框
        self.random_interval_var = tk.BooleanVar(value=False)
        self.random_interval_check = tb.Checkbutton(
            frm_repeat, text="隨機", variable=self.random_interval_var, style="My.TCheckbutton"
        )
        self.random_interval_check.grid(row=0, column=7, padx=(8, 2))

        # 儲存按鈕往後移動一格
        self.save_script_btn_text = tk.StringVar(value=LANG_MAP.get(lang, LANG_MAP["繁體中文"])["儲存"])
        self.save_script_btn = tb.Button(
            frm_repeat, textvariable=self.save_script_btn_text, width=8, bootstyle=SUCCESS, style="My.TButton",
            command=self.save_script_settings
        )
        self.save_script_btn.grid(row=0, column=8, padx=(8, 0))

        # 只允許輸入數字與冒號
        def validate_time_input(P):
            import re
            return re.fullmatch(r"[\d:]*", P) is not None
        vcmd = (self.register(validate_time_input), "%P")
        entry_repeat_time.config(validate="key", validatecommand=vcmd)
        repeat_interval_entry.config(validate="key", validatecommand=vcmd)  # 新增驗證

        # 當重複時間變動時，更新總運作時間顯示
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

        # ====== 腳本選單區 ======
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

        # 新增「選擇目標視窗」按鈕
        tb.Button(frm_script, text="選擇目標視窗", command=self.select_target_window, bootstyle=INFO, width=14, style="My.TButton").grid(row=0, column=4, padx=4)

        self.script_combo.bind("<<ComboboxSelected>>", self.on_script_selected)


        # ====== 日誌顯示區 ======
        frm_log = tb.Frame(self, padding=(10, 0, 10, 10))
        frm_log.pack(fill="both", expand=True)
        log_title_frame = tb.Frame(frm_log)
        log_title_frame.pack(fill="x")

        self.mouse_pos_label = tb.Label(
            log_title_frame, text="( X:0, Y:0 )",
            font=("Consolas", 12, "bold"),
            foreground="#668B9B"
        )
        self.mouse_pos_label.pack(side="left", padx=8)

        # 錄製時間
        self.time_label_time = tb.Label(log_title_frame, text="00:00:00", font=("Consolas", 12), foreground="#888888")
        self.time_label_time.pack(side="right", padx=0)
        self.time_label_prefix = tb.Label(log_title_frame, text="錄製: ", font=("Consolas", 12), foreground="#15D3BD")
        self.time_label_prefix.pack(side="right", padx=0)

        # 單次剩餘
        self.countdown_label_time = tb.Label(log_title_frame, text="00:00:00", font=("Consolas", 12), foreground="#888888")
        self.countdown_label_time.pack(side="right", padx=0)
        self.countdown_label_prefix = tb.Label(log_title_frame, text="單次: ", font=("Consolas", 12), foreground="#DB0E59")
        self.countdown_label_prefix.pack(side="right", padx=0)

        # 總運作
        self.total_time_label_time = tb.Label(log_title_frame, text="00:00:00", font=("Consolas", 12), foreground="#888888")
        self.total_time_label_time.pack(side="right", padx=0)
        self.total_time_label_prefix = tb.Label(log_title_frame, text="總運作: ", font=("Consolas", 12), foreground="#FF95CA")
        self.total_time_label_prefix.pack(side="right", padx=0)

        # ====== row5 分頁區域 ======
        frm_page = tb.Frame(self, padding=(10, 0, 10, 10))
        frm_page.pack(fill="both", expand=True)
        frm_page.grid_rowconfigure(0, weight=1)
        frm_page.grid_columnconfigure(1, weight=1)

        # 左側選單
        self.page_menu = tk.Listbox(frm_page, width=18, font=("Microsoft JhengHei", 11), height=5)
        self.page_menu.insert(0, "1.日誌顯示")
        self.page_menu.insert(1, "2.腳本設定")
        self.page_menu.insert(2, "3.整體設定")
        self.page_menu.grid(row=0, column=0, sticky="ns", padx=(0, 8), pady=4)
        self.page_menu.bind("<<ListboxSelect>>", self.on_page_selected)

        # 右側內容區（固定高度，內容置中）
        self.page_content_frame = tb.Frame(frm_page, width=700, height=320)
        self.page_content_frame.grid(row=0, column=1, sticky="nsew")
        self.page_content_frame.grid_rowconfigure(0, weight=1)
        self.page_content_frame.grid_columnconfigure(0, weight=1)
        self.page_content_frame.pack_propagate(False)  # 固定大小

        # 日誌顯示區
        self.log_text = tb.Text(self.page_content_frame, height=24, width=110, state="disabled", font=("Microsoft JhengHei", 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = tb.Scrollbar(self.page_content_frame, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # 腳本設定區
        self.script_setting_frame = tb.Frame(self.page_content_frame, width=700, height=320)
        self.script_setting_frame.pack_propagate(False)

        # ==SR1== 腳本設定右側區域 ScriptRight1

        # 參考日誌視窗大小
        log_height = 24
        log_width = 110

        # 腳本列表寬度為日誌視窗一半
        script_listbox_width = log_width // 2  # 55
        script_listbox_height = log_height     # 24

        # 腳本列表視窗，靠左
        self.script_listbox = tk.Listbox(
            self.script_setting_frame,
            width=script_listbox_width,
            height=script_listbox_height,
            font=("Microsoft JhengHei", 10)
        )
        self.script_listbox.place(x=0, y=0)
        self.refresh_script_listbox()
        self.script_listbox.bind("<<ListboxSelect>>", self.on_script_listbox_select)

        # SR1 右側功能區域
        self.script_right_frame = tb.Frame(self.script_setting_frame)
        # 放在腳本列表右側，x 位置為腳本列表寬度
        self.script_right_frame.place(x=script_listbox_width * 7.5, y=0, width=320, height=320)  # 7.5是每單位width約7.5px

        # 快捷鍵捕捉框（寬度與按鈕一致）
        self.hotkey_capture_var = tk.StringVar()
        hotkey_entry = tb.Entry(self.script_right_frame, textvariable=self.hotkey_capture_var, font=("Consolas", 12), width=12)
        hotkey_entry.grid(row=1, column=0, padx=8, pady=(0, 8))
        hotkey_entry.bind("<KeyRelease>", self.on_hotkey_entry_key)

        # 設定快捷鍵按鈕
        set_hotkey_btn = tb.Button(self.script_right_frame, text="設定快捷鍵", width=12, bootstyle=SUCCESS, command=self.set_script_hotkey)
        set_hotkey_btn.grid(row=2, column=0, padx=8, pady=8)

        # script路徑按鈕
        self.btn_scripts_dir_sr1 = tb.Button(self.script_right_frame, text="script路徑", command=self.use_default_script_dir, bootstyle=SECONDARY, width=12, style="My.TButton")
        self.btn_scripts_dir_sr1.grid(row=3, column=0, padx=8, pady=8)

        # 刪除按鈕
        del_btn = tb.Button(self.script_right_frame, text="刪除", width=12, bootstyle=DANGER, command=self.delete_selected_script)
        del_btn.grid(row=4, column=0, padx=8, pady=8)
        # ==SR1== end

        # 左側腳本列表（高度對齊左側選單）
        self.script_listbox = tk.Listbox(self.script_setting_frame, width=32, font=("Microsoft JhengHei", 10), height=5)
        self.script_listbox.place(relx=0.0, rely=0.5, anchor="w", height=220, y=20)
        self.refresh_script_listbox()
        self.script_listbox.bind("<<ListboxSelect>>", self.on_script_listbox_select)

        # ==GR1== 整體設定右側區域 GlobalRight1
        self.global_setting_frame = tb.Frame(self.page_content_frame, width=700, height=320)
        self.global_setting_frame.pack_propagate(False)
        self.global_right_frame = tb.Frame(self.global_setting_frame)
        self.global_right_frame.place(relx=0.5, rely=0.1, anchor="n", width=320, height=260)
        tb.Label(self.global_right_frame, text="GlobalRight1", font=("Microsoft JhengHei", 12, "bold")).pack(pady=10)
        # ==GR1== end

        # 預設選擇第一項
        self.page_menu.selection_set(0)
        self.show_page(0)

        # ====== 其餘初始化 ======
        self.refresh_script_list()
        if self.script_var.get():
            self.on_script_selected()
        # 語言初始化（確保UI語言正確）
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
        # 額外更新顯示倍率
        try:
            speed_val = int(self.speed_var.get())
            ratio = speed_val / 100.0
            self.lbl_speed.config(text=f"回放速度: {ratio:.2f}:{speed_val}")
        except:
            self.lbl_speed.config(text="回放速度:")

    def _parse_time_to_seconds(self, t):
        """將 00:00:00 或 00:00 格式字串轉為秒數"""
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
            import sys, os
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                icon_path = "umi_奶茶色.ico"
            about_win.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定 about 視窗 icon: {e}")
        frm = tb.Frame(about_win, padding=20)
        frm.pack(fill="both", expand=True)
        tb.Label(frm, text="ChroLens_Mimic\n可理解為按鍵精靈/操作錄製/掛機工具\n解決重複性高的作業或動作", font=("Microsoft JhengHei", 11,)).pack(anchor="w", pady=(0, 6))
        link = tk.Label(frm, text="ChroLens_模擬器討論區", font=("Microsoft JhengHei", 10, "underline"), fg="#5865F2", cursor="hand2")
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda e: os.startfile("https://discord.gg/72Kbs4WPPn"))
        github = tk.Label(frm, text="查看更多工具(巴哈)", font=("Microsoft JhengHei", 10, "underline"), fg="#24292f", cursor="hand2")
        github.pack(anchor="w", pady=(8, 0))
        github.bind("<Button-1>", lambda e: os.startfile("https://home.gamer.com.tw/profile/index_creation.php?owner=umiwued&folder=523848"))
        tb.Label(frm, text="Creat By Lucienwooo", font=("Microsoft JhengHei", 11,)).pack(anchor="w", pady=(0, 6))
        tb.Button(frm, text="關閉", command=about_win.destroy, width=8, bootstyle=SECONDARY).pack(anchor="e", pady=(16, 0))

    def _init_language(self, lang):
        # 初始化 UI 語言
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
            # 前導零灰色，非零部分有顏色
            colored = []
            for idx, part in enumerate(time_str.split(":")):
                if part == "00" and idx < 2:
                    colored.append(("#888888", part))
                else:
                    colored.append(("#15D3BD", part))
            # 組合顯示
            self.time_label_time.config(
                text=":".join([p[1] for p in colored]),
                foreground=colored[-1][0]  # 只會有一種顏色，因為 Label 只能一色
            )
            # 但因為 Label 只能一色，建議只讓最後一段有顏色，其餘灰色
            # 若要每段不同色，需用 Text 或 Canvas

    def update_total_time_label(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        if time_str == "00:00:00":
            self.total_time_label_time.config(text=time_str, foreground="#888888")
        else:
            # 只讓最後一段有顏色
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
            # 單次剩餘
            total = self.events[-1]['time'] - self.events[0]['time'] if self.events else 0
            remain = max(0, total - elapsed)
            self.update_countdown_label(remain)
            # 倒數顯示
            if hasattr(self, "_play_start_time"):
                if self._repeat_time_limit:
                    total_remain = max(0, self._repeat_time_limit - (time.time() - self._play_start_time))
                else:
                    total_remain = max(0, self._total_play_time - (time.time() - self._play_start_time))
                self.update_total_time_label(total_remain)
                # 更新 MiniMode 倒數
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
            # MiniMode倒數歸零
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
                # 暫停時停止 keyboard 錄製，暫存事件
                import keyboard
                if hasattr(self, "_keyboard_recording"):
                    k_events = keyboard.stop_recording()
                    if not hasattr(self, "_paused_k_events"):
                        self._paused_k_events = []
                    self._paused_k_events += k_events
                    self._keyboard_recording = False
            else:
                # 繼續時重新開始 keyboard 錄製
                import keyboard
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
                    # 若有指定目標視窗，記錄相對座標
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
            mouse_listener = pynput.mouse.Listener(
                on_click=on_click,
                on_scroll=on_scroll
            )
            mouse_listener.start()

            # 立即記錄當下滑鼠位置（避免剛開始沒動作時漏記）
            now = time.time()
            event = {
                'type': 'mouse',
                'event': 'move',
                'x': last_pos[0],
                'y': last_pos[1],
                'time': now
            }
            if self.target_hwnd:
                rel_x, rel_y = screen_to_client(self.target_hwnd, last_pos[0], last_pos[1], window_name="xxx")
                event['rel_x'] = rel_x
                event['rel_y'] = rel_y
                event['hwnd'] = self.target_hwnd
            self._mouse_events.append(event)

            while self.recording:
                now = time.time()
                pos = mouse_ctrl.position
                if pos != last_pos and not self.paused:
                    event = {
                        'type': 'mouse',
                        'event': 'move',
                        'x': pos[0],
                        'y': pos[1],
                        'time': now
                    }
                    if self.target_hwnd:
                        rel_x, rel_y = screen_to_client(self.target_hwnd, pos[0], pos[1], window_name="xxx")
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

            filtered_k_events = [
                e for e in all_k_events
                if not (e.name == 'f10' and e.event_type in ('down', 'up'))
            ]
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
        # 立即刷新顯示
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
            self.speed_var.set(str(speed_val))  # 修正顯示
            self.speed = speed_val / 100.0
        except:
            self.speed = 1.0
            self.speed_var.set("100")

        repeat_time_sec = self._parse_time_to_seconds(self.repeat_time_var.get())
        repeat_interval_sec = self._parse_time_to_seconds(self.repeat_interval_var.get())
        self._repeat_time_limit = repeat_time_sec if repeat_time_sec > 0 else None

        # 讓 repeat 依照使用者設定
        try:
            repeat = int(self.repeat_var.get())
        except:
            repeat = 1
        if repeat <= 0:
            repeat = 0  # 代表無限重複

        # 計算單次腳本時間
        if self.events:
            single_time = (self.events[-1]['time'] - self.events[0]['time']) / self.speed
        else:
            single_time = 0

        # 計算總運作時間（包含間隔）
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
        # 傳遞隨機勾選狀態
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
            # 強化：若有重複時間限制，超過即停止
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
                # 滑鼠事件
                if e['type'] == 'mouse':
                    # 若有 rel_x, rel_y, hwnd，則映射到目標視窗
                    if 'rel_x' in e and 'rel_y' in e and 'hwnd' in e:
                        try:
                            # bring window to front
                            win32gui.ShowWindow(e['hwnd'], win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(e['hwnd'])
                        except Exception:
                            pass
                        abs_x, abs_y = client_to_screen(e['hwnd'], e['rel_x'], e['rel_y'], window_name="xxx")
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
                        # 沒有指定視窗，照原本方式
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
                # 鍵盤事件照原本方式
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
            # 執行間隔
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
        self.log("【整體設定已更新】")  # 新增：日誌顯示

    def auto_save_script(self):
        try:
            ts = datetime.datetime.now().strftime("%Y_%m%d_%H%M_%S")
            filename = f"{ts}.json"
            path = os.path.join(self.script_dir, filename)
            # 儲存時包含參數
            script_data = {
                "events": self.events,
                "speed": self.speed_var.get(),
                "repeat": self.repeat_var.get(),
                "repeat_time": self.repeat_time_var.get()
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)
            self.log(f"[{format_time(time.time())}] 自動存檔：{filename}，事件數：{len(self.events)}")
            self.refresh_script_list()
            self.script_var.set(filename)
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(filename)
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] 存檔失敗: {ex}")

    # --- 儲存腳本設定 ---
    def save_script_settings(self):
        """將目前 speed/repeat/repeat_time/repeat_interval/random_interval 寫入當前腳本檔案"""
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
            # 若為舊格式，轉為新格式
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
            self.log("【腳本設定已更新】")  # 新增：日誌顯示
        except Exception as ex:
            self.log(f"儲存腳本設定失敗: {ex}")

    # --- 讀取腳本設定 ---
    def on_script_selected(self, event=None):
        script = self.script_var.get()
        if script:
            path = os.path.join(self.script_dir, script)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 支援舊格式
            if isinstance(data, dict) and "events" in data:
                self.events = data["events"]
                # 恢復參數
                self.speed_var.set(data.get("speed", "100"))
                self.repeat_var.set(data.get("repeat", "1"))
                self.repeat_time_var.set(data.get("repeat_time", "00:00:00"))
                self.repeat_interval_var.set(data.get("repeat_interval", "00:00:00"))
                self.random_interval_var.set(data.get("random_interval", False))
            else:
                self.events = data
            self.log(f"[{format_time(time.time())}] 腳本已載入：{script}，共 {len(self.events)} 筆事件。")
            self.log("【腳本設定已載入】")  # 新增：日誌顯示
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(script)
            # 讀取腳本後，顯示單次腳本時間
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
        old_path = os.path.join(self.script_dir, old_name)  # 修正
        new_path = os.path.join(self.script_dir, new_name)  # 修正
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
        self.rename_var.set("")  # 更名後清空輸入框

    def open_scripts_dir(self):
        path = os.path.abspath(self.script_dir)  # 修正
        os.startfile(path)

    def open_hotkey_settings(self):
        win = tb.Toplevel(self)
        win.title("Hotkey")
        win.geometry("300x320")
        win.resizable(False, False)
        # 讓快捷鍵視窗icon跟主程式一致
        try:
            import sys, os
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
            else:
                icon_path = "umi_奶茶色.ico"
            win.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定快捷鍵視窗 icon: {e}")

        # 依目前語言取得標籤
        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        labels = {
            "start": lang_map["開始錄製"],
            "pause": lang_map["暫停/繼續"],
            "stop": lang_map["停止"],
            "play": lang_map["回放"],
            "tiny": lang_map["MiniMode"]
        }
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
            tb.Label(win, text=label, font=("Microsoft JhengHei", 11)).grid(row=row, column=0, padx=10, pady=8, sticky="w")
            var = tk.StringVar(value=self.hotkey_map[key])
            entry = tb.Entry(win, textvariable=var, width=8, font=("Consolas", 11), state="normal")  # 寬度縮短
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
            self.save_config()  # 新增這行，確保儲存
            self.log("快捷鍵設定已更新。")
            win.destroy()

        tb.Button(win, text="儲存", command=save_and_apply, width=10, bootstyle=SUCCESS).grid(row=row, column=0, columnspan=2, pady=16)

    # 不再需要 _make_hotkey_entry_handler

    def _register_hotkeys(self):
        import keyboard
        for handler in self._hotkey_handlers.values():
            try:
                keyboard.remove_hotkey(handler)
            except Exception as ex:
                self.log(f"移除快捷鍵時發生錯誤: {ex}")
        self._hotkey_handlers.clear()
        for key, hotkey in self.hotkey_map.items():
            try:
                handler = keyboard.add_hotkey(
                    hotkey,
                    getattr(self, {
                        "start": "start_record",
                        "pause": "toggle_pause",
                        "stop": "stop_all",
                        "play": "play_record",
                        "tiny": "toggle_tiny_mode"
                    }[key]),
                                       suppress=False,  # 不攔截原本的功能
                    trigger_on_release=False
                )
                self._hotkey_handlers[key] = handler
                self.log(f"已註冊快捷鍵: {hotkey} → {key}")
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")

    def _update_hotkey_labels(self):
        self.btn_start.config(text=f"開始錄製 ({self.hotkey_map['start']})")
        self.btn_pause.config(text=f"暫停/繼續 ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=f"停止 ({self.hotkey_map['stop']})")
        self.btn_play.config(text=f"回放 ({self.hotkey_map['play']})")
        # MiniMode 按鈕同步更新
        if hasattr(self, "tiny_btns"):

            for btn, icon, key in self.tiny_btns:
                btn.config(text=f"{icon} {self.hotkey_map[key]}")

    def toggle_tiny_mode(self):
        # 切換 MiniMode 狀態
        if not hasattr(self, "tiny_mode_on"):
            self.tiny_mode_on = False
        self.tiny_mode_on = not self.tiny_mode_on
        if self.tiny_mode_on:
            if self.tiny_window is None or not self.tiny_window.winfo_exists():
                self.tiny_window = tb.Toplevel(self)
                self.tiny_window.title("MiniMode")
                self.tiny_window.geometry("300x200")
                self.tiny_window.resizable(False, False)
                self.tiny_window.grab_set()
                # 設定視窗透明度
                self.tiny_window.attributes("-alpha", 0.9)
                # 可拖曮
                self.tiny_window.bind("<Button-1>", self._start_move_tiny)
                self.tiny_window.bind("<B1-Motion>", self._move_tiny)
                # 最上層
                self.tiny_window.wm_attributes("-topmost", True)

                # 在這個視窗內放置小型的控制按鈕
                btn_frame = tb.Frame(self.tiny_window, padding=10)
                btn_frame.pack(fill="both", expand=True)

                # 依原有功能自動產生按鈕
                self.tiny_btns = []
                for i, (key, hotkey) in enumerate(self.hotkey_map.items()):
                    icon = {
                        "start": "●錄",
                        "pause": "▮▮",
                        "stop": "■",
                        "play": "▶",
                        "tiny": "↔"
                    }.get(key, "")
                    btn = tb.Button(
                        btn_frame,
                        text=f"{icon} {hotkey}",
                        width=7, style="My.TButton",
                        command=getattr(self, {
                            "start": "start_record",
                            "pause": "toggle_pause",
                            "stop": "stop_all",
                            "play": "play_record",
                            "tiny": "toggle_tiny_mode"
                        }[key])
                    )
                    btn.grid(row=0, column=i+1, padx=2, pady=5)
                    self.tiny_btns.append((btn, icon, key))
                self.tiny_window.protocol("WM_DELETE_WINDOW", self._close_tiny_mode)
                self.withdraw()
        else:
            self._close_tiny_mode()

    def _close_tiny_mode(self):
        if self.tiny_window and self.tiny_window.winfo_exists():
            self.tiny_window.destroy()
        self.tiny_mode_on = False
        self.deiconify()

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

        # 開啟資料夾
        os.startfile(self.script_dir)

    def refresh_script_list(self):
        """刷新腳本下拉選單內容"""
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        self.script_combo['values'] = scripts
        # 若目前選擇的腳本不存在，則清空
        if self.script_var.get() not in scripts:
            self.script_var.set('')

    def refresh_script_listbox(self):
        """刷新腳本設定區左側 Listbox"""
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
        # 清空內容區
        for widget in self.page_content_frame.winfo_children():
            widget.grid_forget()
            widget.place_forget()
        if idx == 0:
            self.log_text.grid(row=0, column=0, sticky="nsew")
            for child in self.page_content_frame.winfo_children():
                if isinstance(child, tb.Scrollbar):
                    child.grid(row=0, column=1, sticky="ns")
        elif idx == 1:
            self.script_setting_frame.place(relx=0.5, rely=0.5, anchor="center")
            # 額外刷新腳本列表
            self.refresh_script_listbox()
        elif idx == 2:
            self.global_setting_frame.place(relx=0.5, rely=0.5, anchor="center")

        def refresh_script_listbox(self):
            self.script_listbox.delete(0, "end")
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        for f in scripts:
            self.script_listbox.insert("end", f)

    def on_script_listbox_select(self, event=None):
        idx = self.script_listbox.curselection()
        if idx:
            script = self.script_listbox.get(idx[0])
            self.script_var.set(script)
            self.on_script_selected()
            # 若腳本有快捷鍵，載入顯示
            path = os.path.join(self.script_dir, script)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                hotkey = data.get("script_hotkey", "")
                self.hotkey_capture_var.set(hotkey)
            except Exception:
                self.hotkey_capture_var.set("")

    def on_hotkey_entry_key(self, event):
        keys = []
        if event.state & 0x0001: keys.append("shift")
        if event.state & 0x0004: keys.append("ctrl")
        if event.state & 0x0008: keys.append("alt")
        key_name = event.keysym.lower()
        if key_name not in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"):
            keys.append(key_name)
        self.hotkey_capture_var.set("+".join(keys))

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
        # 這裡可以加入選擇視窗的功能
        self.log("【選擇目標視窗】功能尚未實作。")

# ====== 設定檔讀寫 ======
CONFIG_FILE = "user_config.json"

def load_user_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 首次開啟才預設繁體中文
    return {
       
        "skin": "darkly",
        "last_script": "",
        "repeat": "1",
        "speed": "100",  # 預設100
        "script_dir": SCRIPTS_DIR,
        "language": "繁體中文"
    }

def save_user_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def format_time(ts):
    """將 timestamp 轉為 HH:MM:SS 字串"""
    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()