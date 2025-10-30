#ChroLens Studio - Lucienwooo
#pyinstaller --noconsole --onedir --icon=umi_奶茶色.ico --add-data "umi_奶茶色.ico;." ChroLens_Mimic2.6.py

# ====== UI 介面 row 對應說明 ======
# row 0 (frm_top):
#   開始錄製（btn_start）、暫停/繼續（btn_pause）、停止（btn_stop）、回放（btn_play）
#   MiniMode（mini_mode_btn）、skin下拉選單（theme_combo）
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
import tkinter.font as tkfont

# 新增：匯入 Recorder / 語言 / script IO 函式（使用健壯的 fallback）
try:
    from recorder import CoreRecorder
except Exception as e:
    print(f"無法匯入 CoreRecorder: {e}")
try:
    from lang import LANG_MAP
except Exception as e:
    print(f"無法匯入 LANG_MAP: {e}")

# 先嘗試以常用命名匯入，若失敗則 import module 並檢查函式名稱，最後提供 fallback 實作
try:
    # 優先嘗試原先預期的命名匯入
    from script_io import sio_auto_save_script, sio_load_script, sio_save_script_settings
except Exception as _e:
    try:
        import script_io as _sio_mod
        sio_auto_save_script = getattr(_sio_mod, "sio_auto_save_script", getattr(_sio_mod, "auto_save_script", None))
        sio_load_script = getattr(_sio_mod, "sio_load_script", getattr(_sio_mod, "load_script", None))
        sio_save_script_settings = getattr(_sio_mod, "sio_save_script_settings", getattr(_sio_mod, "save_script_settings", None))
        if not (sio_auto_save_script and sio_load_script and sio_save_script_settings):
            raise ImportError("script_io 模組缺少預期函式")
    except Exception as e:
        print(f"無法匯入 script_io 函式: {e}")
        # 提供最小 fallback 實作，確保主程式能運作（會回傳/寫入基礎 JSON）
        def sio_auto_save_script(script_dir, events, settings):
            if not os.path.exists(script_dir):
                os.makedirs(script_dir)
            fname = f"autosave_{int(time.time())}.json"
            path = os.path.join(script_dir, fname)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"events": events, "settings": settings}, f, ensure_ascii=False, indent=2)
                return fname
            except Exception as ex:
                print(f"autosave failed: {ex}")
                return ""

        def sio_load_script(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {"events": data.get("events", []), "settings": data.get("settings", {})}
            except Exception as ex:
                print(f"sio_load_script fallback failed: {ex}")
                return {"events": [], "settings": {}}

        def sio_save_script_settings(path, settings):
            try:
                data = {}
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                data["settings"] = settings
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as ex:
                print(f"sio_save_script_settings fallback failed: {ex}")

# 新增：匯入 about 模組
try:
    import about
except Exception as e:
    print(f"無法匯入 about 模組: {e}")

# 新增：將 MiniMode 抽出到 mini.py
try:
    import mini
except Exception as e:
    print(f"無法匯入 mini 模組: {e}")

# 新增：註冊專案內的 LINESeedTW TTF（若存在），並提供通用 font_tuple() 幫助函式
TTF_PATH = os.path.join(os.path.dirname(__file__), "TTF", "LINESeedTW_TTF_Rg.ttf")

def _register_private_ttf(ttf_path):
    try:
        if os.path.exists(ttf_path):
            FR_PRIVATE = 0x10
            ctypes.windll.gdi32.AddFontResourceExW(ttf_path, FR_PRIVATE, 0)
    except Exception as e:
        print(f"註冊字型失敗: {e}")

# 嘗試註冊（不會拋錯，失敗時程式仍可繼續）
_register_private_ttf(TTF_PATH)

def font_tuple(size, weight=None, monospace=False):
    """
    回傳 (family, size) 或 (family, size, weight) 的 tuple，
    優先選擇 LINESeedTW（若可用），否則回退到 Microsoft JhengHei。
    monospace=True 時使用 Consolas。
    """
    fam = "Consolas" if monospace else "LINESeedTW_TTF_Rg"
    try:
        # 若尚未建立 tk root，tkfont.families() 可能會失敗；以 try 防護
        fams = set(f.lower() for f in tkfont.families())
        # 嘗試找出任何以 lineseed 開頭的 family
        for f in tkfont.families():
            if f.lower().startswith("lineseed"):
                fam = f
                break
        else:
            # 若找不到 LINESEED，回退到 Microsoft JhengHei（若存在）
            if not monospace:
                for f in tkfont.families():
                    if f.lower().startswith("microsoft jhenghei") or f.lower().startswith("microsoft jhenghei ui"):
                        fam = f
                        break
    except Exception:
        # 若無法查詢 families，保留預設 fam（依前述值）
        pass
    if weight:
        return (fam, size, weight)
    return (fam, size)

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
            font=font_tuple(10)
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
        # 先初始化 core_recorder，確保它能正確記錄事件
        self.core_recorder = CoreRecorder(logger=self.log)
        self.recording = False
        self.playing = False
        self.paused = False
        self.events = []

        self.user_config = load_user_config()
        skin = self.user_config.get("skin", "darkly")
        # 讀取最後一次語言設定，預設繁體中文
        lang = self.user_config.get("language", "繁體中文")
        super().__init__(themename=skin)
        self.language_var = tk.StringVar(self, value=lang)
        self._hotkey_handlers = {}
        # 用來儲存腳本快捷鍵的 handler id
        self._script_hotkey_handlers = {}
        # MiniMode 管理器（由 mini.py 提供）
        self.mini_controller = None
        self.target_hwnd = None
        self.target_title = None

        # 讀取 hotkey_map，若無則用預設
        self.hotkey_map = self.user_config.get("hotkey_map", {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "mini": "alt+`"
        })

        # ====== 統一字體 style ======
        self.style.configure("My.TButton", font=font_tuple(9))
        self.style.configure("My.TLabel", font=font_tuple(9))
        self.style.configure("My.TEntry", font=font_tuple(9))
        self.style.configure("My.TCombobox", font=font_tuple(9))
        self.style.configure("My.TCheckbutton", font=font_tuple(9))
        self.style.configure("miniBold.TButton", font=font_tuple(9, "bold"))

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
        #themes = ["darkly", "cyborg", "superhero", "journal","minty", "united", "morph", "lumen"]
        #self.theme_var = tk.StringVar(value=self.style.theme_use())
        # 顯示目前 theme，但取消下拉選單的變更功能（保留顯示）
        #theme_combo = tb.Combobox(
        #    frm_top,
        #    textvariable=self.theme_var,
        #    values=themes,
        #    state="disabled",   # 停用選單，僅顯示當前樣式
        #    width=6,
        #    style="My.TCombobox"
        #)
        #theme_combo.grid(row=0, column=8, padx=(4, 8), sticky="e")

        # MiniMode 按鈕（skin下拉選單左側）
        self.mini_mode_btn = tb.Button(
            frm_top, text="MiniMode", style="My.TButton",
            command=self.toggle_mini_mode, width=10
        )
        self.mini_mode_btn.grid(row=0, column=7, padx=4)

        # ====== 下方操作區 ======
        frm_bottom = tb.Frame(self, padding=(8, 0, 8, 5))
        frm_bottom.pack(fill="x")
        self.lbl_speed = tb.Label(frm_bottom, text="回放速度:", style="My.TLabel")
        self.lbl_speed.grid(row=0, column=0, padx=(0, 6))
        self.speed_tooltip = Tooltip(self.lbl_speed, "正常速度1倍=100,範圍1~1000")
        self.update_speed_tooltip()
        self.speed_var = tk.StringVar(value=self.user_config.get("speed", "100"))  # 預設100
        tb.Entry(frm_bottom, textvariable=self.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=6)
        # 合併：在同一列顯示「回放速度」與「重複次數 / 重複時間 / 重複間隔 / 隨機 / 儲存按鈕」
        saved_lang = self.user_config.get("language", "繁體中文")
        self.language_var = tk.StringVar(self, value=saved_lang)

        # ----------------- 以下為合併後的重複參數（原本單獨在 frm_repeat） -----------------
        # 重複次數
        self.repeat_label = tb.Label(frm_bottom, text="重複次數:", style="My.TLabel")
        self.repeat_label.grid(row=0, column=2, padx=(8, 2))
        self.repeat_var = tk.StringVar(value=self.user_config.get("repeat", "1"))
        entry_repeat = tb.Entry(frm_bottom, textvariable=self.repeat_var, width=6, style="My.TEntry")
        entry_repeat.grid(row=0, column=3, padx=2)

        # 重複時間
        self.repeat_time_var = tk.StringVar(value="00:00:00")
        entry_repeat_time = tb.Entry(frm_bottom, textvariable=self.repeat_time_var, width=10, style="My.TEntry", justify="center")
        # 調整欄位位置：如果覺得擁擠，可調整 column index (目前放在 col=5)
        entry_repeat_time.grid(row=0, column=5, padx=(10, 2))
        self.repeat_time_label = tb.Label(frm_bottom, text="重複時間", style="My.TLabel")
        self.repeat_time_label.grid(row=0, column=6, padx=(0, 2))

        # 重複間隔
        self.repeat_interval_var = tk.StringVar(value="00:00:00")
        repeat_interval_entry = tb.Entry(frm_bottom, textvariable=self.repeat_interval_var, width=10, style="My.TEntry", justify="center")
        repeat_interval_entry.grid(row=0, column=7, padx=(10, 2))
        self.repeat_interval_label = tb.Label(frm_bottom, text="重複間隔", style="My.TLabel")
        self.repeat_interval_label.grid(row=0, column=8, padx=(0, 2))

        # 隨機勾選
        self.random_interval_var = tk.BooleanVar(value=False)
        self.random_interval_check = tb.Checkbutton(
            frm_bottom, text="隨機", variable=self.random_interval_var, style="My.TCheckbutton"
        )
        self.random_interval_check.grid(row=0, column=9, padx=(8, 2))

        # 儲存按鈕（放到同一列）
        self.save_script_btn_text = tk.StringVar(value=LANG_MAP.get(saved_lang, LANG_MAP["繁體中文"])["儲存"])
        self.save_script_btn = tb.Button(
            frm_bottom, textvariable=self.save_script_btn_text, width=8, bootstyle=SUCCESS, style="My.TButton",
            command=self.save_script_settings
        )
        self.save_script_btn.grid(row=0, column=10, padx=(8, 0))
        # ----------------- 合併結束 -----------------

        # 只允許輸入數字與冒號（驗證器共用）
        def validate_time_input(P):
            import re
            return re.fullmatch(r"[\d:]*", P) is not None
        vcmd = (self.register(validate_time_input), "%P")
        entry_repeat_time.config(validate="key", validatecommand=vcmd)
        repeat_interval_entry.config(validate="key", validatecommand=vcmd)

        # 右鍵清除快速設定（保持原行為）
        entry_repeat.bind("<Button-3>", lambda e: self.repeat_var.set("0"))
        entry_repeat_time.bind("<Button-3>", lambda e: self.repeat_time_var.set("00:00:00"))
        repeat_interval_entry.bind("<Button-3>", lambda e: self.repeat_interval_var.set("00:00:00"))

        # 當重複時間變動時，更新總運作時間顯示
        def on_repeat_time_change(*args):
            t = self.repeat_time_var.get()
            seconds = self._parse_time_to_seconds(t)
            if seconds > 0:
                self.update_total_time_label(seconds)
            else:
                self.update_total_time_label(0)
        self.repeat_time_var.trace_add("write", on_repeat_time_change)

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
            font=font_tuple(12, "bold", monospace=True),
            foreground="#668B9B"
        )
        self.mouse_pos_label.pack(side="left", padx=8)

        # 錄製時間
        self.time_label_time = tb.Label(log_title_frame, text="00:00:00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.time_label_time.pack(side="right", padx=0)
        self.time_label_prefix = tb.Label(log_title_frame, text="錄製: ", font=font_tuple(12, monospace=True), foreground="#15D3BD")
        self.time_label_prefix.pack(side="right", padx=0)

        # 單次剩餘
        self.countdown_label_time = tb.Label(log_title_frame, text="00:00:00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.countdown_label_time.pack(side="right", padx=0)
        self.countdown_label_prefix = tb.Label(log_title_frame, text="單次: ", font=font_tuple(12, monospace=True), foreground="#DB0E59")
        self.countdown_label_prefix.pack(side="right", padx=0)

        # 總運作
        self.total_time_label_time = tb.Label(log_title_frame, text="00:00:00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.total_time_label_time.pack(side="right", padx=0)
        self.total_time_label_prefix = tb.Label(log_title_frame, text="總運作: ", font=font_tuple(12, monospace=True), foreground="#FF95CA")
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

        # <<< 調整點: page_content_frame 大小與位置 在此處 (可調整 width/height/pack/placement) >>>
        # 右側內容區（固定高度，內容置中）
        self.page_content_frame = tb.Frame(frm_page, width=700, height=320)
        self.page_content_frame.grid(row=0, column=1, sticky="nsew")
        self.page_content_frame.grid_rowconfigure(0, weight=1)
        self.page_content_frame.grid_columnconfigure(0, weight=1)
        self.page_content_frame.pack_propagate(False)  # 固定大小

        # 日誌顯示區
        self.log_text = tb.Text(self.page_content_frame, height=24, width=110, state="disabled", font=font_tuple(9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = tb.Scrollbar(self.page_content_frame, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # 腳本設定區
        self.script_setting_frame = tb.Frame(self.page_content_frame, width=700, height=320)
        self.script_setting_frame.pack_propagate(False)

        # 左側腳本列表
        # <<< 調整點: 腳本列表高度 在此處 (height=18) >>> 
        # 若要改高度請調整下方 height 參數
        self.script_listbox = tk.Listbox(
            self.script_setting_frame,
            width=40,
            height=14,  # <-- 可在此修改 height
            font=font_tuple(10)
        )
        self.script_listbox.grid(row=0, column=0, rowspan=8, sticky="nsw", padx=(8,6), pady=8)
        self.script_listbox.bind("<<ListboxSelect>>", self.on_script_listbox_select)

        # 右側控制區（垂直排列）
        self.script_right_frame = tb.Frame(self.script_setting_frame, padding=6)
        self.script_right_frame.grid(row=0, column=1, sticky="n", padx=(8,0), pady=8)

        # 快捷鍵捕捉（可捕捉任意按鍵或組合鍵）
        self.hotkey_capture_var = tk.StringVar(value="")
        hotkey_label = tb.Label(self.script_right_frame, text="捕捉快捷鍵：", style="My.TLabel")
        hotkey_label.pack(anchor="w", pady=(2,2))
        hotkey_entry = tb.Entry(self.script_right_frame, textvariable=self.hotkey_capture_var, font=font_tuple(12, monospace=True), width=18)
        hotkey_entry.pack(pady=(0,8))
        hotkey_entry.bind("<KeyRelease>", self.on_hotkey_entry_key)
        hotkey_entry.bind("<FocusIn>", lambda e: self.hotkey_capture_var.set("輸入按鍵"))
        hotkey_entry.bind("<FocusOut>", lambda e: None)

        # a) 設定快捷鍵按鈕：將捕捉到的快捷鍵寫入選定腳本並註冊
        set_hotkey_btn = tb.Button(self.script_right_frame, text="設定快捷鍵", width=18, bootstyle=SUCCESS, command=self.set_script_hotkey)
        set_hotkey_btn.pack(pady=6)

        # b) 直接開啟腳本資料夾（輔助功能）
        open_dir_btn = tb.Button(self.script_right_frame, text="開啟腳本資料夾", width=18, bootstyle=SECONDARY, command=self.open_scripts_dir)
        open_dir_btn.pack(pady=6)

        # c) 刪除按鈕：直接刪除檔案並取消註冊其快捷鍵（若有）
        del_btn = tb.Button(self.script_right_frame, text="刪除腳本", width=18, bootstyle=DANGER, command=self.delete_selected_script)
        del_btn.pack(pady=6)

        # 初始化清單
        self.refresh_script_listbox()

        # --- 建立「整體設定」頁面內容區 (global_setting_frame) ---
        # 你可以在這裡調整位置/大小/內部佈局
        self.global_setting_frame = tb.Frame(self.page_content_frame, width=700, height=320)
        self.global_setting_frame.pack_propagate(False)
        # 將原本的「快捷鍵」「關於」「Language」移到這裡
        self.btn_hotkey = tb.Button(self.global_setting_frame, text="快捷鍵", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=12, style="My.TButton")
        self.btn_hotkey.pack(pady=6)
        self.about_btn = tb.Button(self.global_setting_frame, text="關於", width=12, style="My.TButton", command=self.show_about_dialog, bootstyle=SECONDARY)
        self.about_btn.pack(pady=6)
        # 語言下拉（放在整體設定頁）
        lang_combo_global = tb.Combobox(
            self.global_setting_frame,
            textvariable=self.language_var,
            values=["繁體中文", "日本語", "English"],
            state="readonly",
            width=12,
            style="My.TCombobox"
        )
        lang_combo_global.pack(pady=6)
        lang_combo_global.bind("<<ComboboxSelected>>", self.change_language)
        self.language_combo = lang_combo_global

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
        # 註冊腳本快捷鍵（若腳本已包含 script_hotkey）
        self.after(1650, self._register_script_hotkeys)
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
            # 只更新 tooltip 文字，不去改 lbl_speed 的主標籤
            self.speed_tooltip.text = tip_text

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
        # 使用外部抽出的 about 模組顯示視窗
        try:
            about.show_about(self)
        except Exception as e:
            print(f"顯示 about 視窗失敗: {e}")

    def _init_language(self, lang):
        # 初始化 UI 語言
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        self.btn_start.config(text=lang_map["開始錄製"] + f" ({self.hotkey_map['start']})")
        self.btn_pause.config(text=lang_map["暫停/繼續"] + f" ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=lang_map["停止"] + f" ({self.hotkey_map['stop']})")
        self.btn_play.config(text=lang_map["回放"] + f" ({self.hotkey_map['play']})")
        self.mini_mode_btn.config(text=lang_map["MiniMode"])
        self.about_btn.config(text=lang_map["關於"])
        self.lbl_speed.config(text=lang_map["回放速度:"])
        self.btn_hotkey.config(text=lang_map["快捷鍵"])
        self.total_time_label_prefix.config(text=lang_map["總運作"])
        self.countdown_label_prefix.config(text=lang_map["單次"])
        self.time_label_prefix.config(text=lang_map["錄製"])
        self.repeat_label.config(text=lang_map["重複次數:"])
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
        self.mini_mode_btn.config(text=lang_map["MiniMode"])
        self.about_btn.config(text=lang_map["關於"])
        self.lbl_speed.config(text=lang_map["回放速度:"])
        self.btn_hotkey.config(text=lang_map["快捷鍵"])
        self.total_time_label_prefix.config(text=lang_map["總運作"])
        self.countdown_label_prefix.config(text=lang_map["單次"])
        self.time_label_prefix.config(text=lang_map["錄製"])
        self.repeat_label.config(text=lang_map["重複次數:"])
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
                if self.mini_controller and self.mini_controller.is_open():
                    if hasattr(self, "mini_countdown_label") or True:
                        lang = self.language_var.get()
                        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                        h = int(total_remain // 3600)
                        m = int((total_remain % 3600) // 60)
                        s = int(total_remain % 60)
                        time_str = f"{h:02d}:{m:02d}:{s:02d}"
                        try:
                            # 使用 mini controller 的更新 API
                            self.mini_controller.update_countdown(f"{lang_map['剩餘']}: {time_str}")
                        except Exception:
                            pass
            self.after(100, self._update_play_time)
        else:
            self.update_time_label(0)
            self.update_countdown_label(0)
            self.update_total_time_label(0)
            # MiniMode倒數歸零
            if self.mini_controller and self.mini_controller.is_open():
                try:
                    lang = self.language_var.get()
                    lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                    self.mini_controller.update_countdown(f"{lang_map['剩餘']}: 00:00:00")
                except Exception:
                    pass

    def start_record(self):
        """開始錄製"""
        if getattr(self.core_recorder, "recording", False):
            return
        # 每次按開始錄製時，重置「可儲存到腳本」的參數為預設值
        try:
            self.reset_to_defaults()
        except Exception:
            pass
        # 清空目前 events（避免舊資料殘留），並啟動 recorder
        self.events = []
        self.recording = True
        self.paused = False
        self._record_start_time = self.core_recorder.start_record()
        # 盡量抓取 core_recorder 的 thread handle（若尚未建立，稍後等待）
        self._record_thread_handle = getattr(self.core_recorder, "_record_thread", None)
        self.after(100, self._update_record_time)

    def _update_record_time(self):
        if self.recording:
            now = time.time()
            elapsed = now - self._record_start_time
            self.update_time_label(elapsed)
            self.after(100, self._update_record_time)
        else:
            self.update_time_label(0)

    def reset_to_defaults(self):
        """將可被儲存的參數重置為預設（錄製時使用）"""
        # UI 預設
        try:
            self.speed_var.set("100")
        except Exception:
            pass
        try:
            self.repeat_var.set("1")
        except Exception:
            pass
        try:
            self.repeat_time_var.set("00:00:00")
        except Exception:
            pass
        try:
            self.repeat_interval_var.set("00:00:00")
        except Exception:
            pass
        try:
            self.random_interval_var.set(False)
        except Exception:
            pass
        # 內部同步 speed
        try:
            speed_val = int(self.speed_var.get())
            speed_val = min(1000, max(1, speed_val))
            self.speed = speed_val / 100.0
            self.speed_var.set(str(speed_val))
        except Exception:
            self.speed = 1.0
            self.speed_var.set("100")
        # 更新顯示（僅更新 tooltip，不改 lbl_speed）
        try:
            self.update_speed_tooltip()
            self.update_total_time_label(0)
            self.update_countdown_label(0)
            self.update_time_label(0)
        except Exception:
            pass

    def toggle_pause(self):
        """切換暫停/繼續"""
        if self.recording or self.playing:
            is_paused = self.core_recorder.toggle_pause()
            self.paused = is_paused
            state = "暫停" if is_paused else "繼續"
            mode = "錄製" if self.recording else "回放"
            self.log(f"[{format_time(time.time())}] {mode}{state}。")
            if self.paused and self.recording:
                # 暫停時停止 keyboard 錄製，暫存事件
                if hasattr(self.core_recorder, "_keyboard_recording"):
                    k_events = keyboard.stop_recording()
                    if not hasattr(self.core_recorder, "_paused_k_events"):
                        self.core_recorder._paused_k_events = []
                    self.core_recorder._paused_k_events.extend(k_events)
                    self.core_recorder._keyboard_recording = False
            elif self.recording:
                # 繼續時重新開始 keyboard 錄製
                keyboard.start_recording()
                self.core_recorder._keyboard_recording = True

    def stop_record(self):
        """停止錄製"""
        if not self.recording:
            return
        # 告訴 core_recorder 停止錄製，之後等待錄製執行緒真正結束再同步 events 與自動存檔
        self.recording = False
        self.core_recorder.stop_record()
        self.log(f"[{format_time(time.time())}] 停止錄製（等待寫入事件...）。")
        # 等待 core_recorder 的錄製執行緒結束，結束後會同步 events 並 auto_save
        self._wait_record_thread_finish()

    def play_record(self):
        """開始回放"""
        if self.playing:
            return
        if not self.events:
            self.log("沒有可回放的事件，請先錄製或載入腳本。")
            return

        # 設定 core_recorder 的事件（確保回放器有資料）
        self.core_recorder.events = self.events

        try:
            speed_val = int(self.speed_var.get())
            speed_val = min(1000, max(1, speed_val))
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
        repeat = 0 if repeat <= 0 else repeat

        # 計算總運作時間
        single_time = (self.events[-1]['time'] - self.events[0]['time']) / self.speed if self.events else 0
        if self._repeat_time_limit and repeat > 0:
            total_time = self._repeat_time_limit
        else:
            total_time = single_time * repeat + repeat_interval_sec * max(0, repeat - 1)
        self._total_play_time = total_time

        self._play_start_time = time.time()
        self.update_total_time_label(self._total_play_time)
        self.playing = True
        self.paused = False

        def on_event(event):
            """回放事件的回調函數"""
            self._current_play_index = getattr(self.core_recorder, "_current_play_index", 0)
            if not self.playing:
                return

        success = self.core_recorder.play(
            speed=self.speed,
            repeat=repeat,
            on_event=on_event
        )

        if success:
            # 修正日誌顯示，不要把 ratio 字串插入 lbl，保留數值顯示與內部倍率
            self.log(f"[{format_time(time.time())}] 開始回放，速度倍率: {self.speed:.2f} ({self.speed_var.get()})")
            self.after(100, self._update_play_time)
        else:
            self.log("沒有可回放的事件，請先錄製或載入腳本。")

    def stop_all(self):
        """停止所有動作"""
        stopped = False

        if self.recording:
            self.recording = False
            self.core_recorder.stop_record()
            self.events = self.core_recorder.events
            stopped = True
            self.log(f"[{format_time(time.time())}] 停止錄製。")
            self._wait_record_thread_finish()

        if self.playing:
            self.playing = False
            self.core_recorder.stop_play()
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
        """等待錄製執行緒由 core_recorder 結束，結束後同步 events 並 auto_save"""
        # 優先檢查 core_recorder 的 thread
        t = getattr(self.core_recorder, "_record_thread", None)
        if t and getattr(t, "is_alive", lambda: False)():
            # 還沒結束，繼續等待
            self.after(100, self._wait_record_thread_finish)
            return

        # 如果 core_recorder 已完成，從 core_recorder 取回 events 並存檔
        try:
            self.events = getattr(self.core_recorder, "events", []) or []
            self.log(f"[{format_time(time.time())}] 錄製執行緒已完成，取得事件數：{len(self.events)}")
            # 再次確保不會在尚未寫入時呼叫 auto_save
            self.auto_save_script()
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] 同步錄製事件發生錯誤: {ex}")

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
            # 使用 script_io 的 auto_save_script
            settings = {
                "speed": self.speed_var.get(),
                "repeat": self.repeat_var.get(),
                "repeat_time": self.repeat_time_var.get(),
                "repeat_interval": self.repeat_interval_var.get(),
                "random_interval": self.random_interval_var.get()
            }
            filename = sio_auto_save_script(self.script_dir, self.events, settings)
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
            settings = {
                "speed": self.speed_var.get(),
                "repeat": self.repeat_var.get(),
                "repeat_time": self.repeat_time_var.get(),
                "repeat_interval": self.repeat_interval_var.get(),
                "random_interval": self.random_interval_var.get()
            }
            sio_save_script_settings(path, settings)
            self.log(f"已將設定儲存到腳本：{script}")
            self.log("【腳本設定已更新】")  # 新增：日誌顯示
        except Exception as ex:
            self.log(f"儲存腳本設定失敗: {ex}")

    # --- 讀取腳本設定 ---
    def on_script_selected(self, event=None):
        script = self.script_var.get()
        if script:
            path = os.path.join(self.script_dir, script)
            try:
                data = sio_load_script(path)
                self.events = data.get("events", [])
                settings = data.get("settings", {})
                # 恢復參數
                self.speed_var.set(settings.get("speed", "100"))
                self.repeat_var.set(settings.get("repeat", "1"))
                self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
                self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
                self.random_interval_var.set(settings.get("random_interval", False))
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
            except Exception as ex:
                self.log(f"載入腳本失敗: {ex}")
        self.save_config()

    def load_script(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], initialdir=self.script_dir)
        if path:
            try:
                data = sio_load_script(path)
                self.events = data.get("events", [])
                settings = data.get("settings", {})
                self.speed_var.set(settings.get("speed", "100"))
                self.repeat_var.set(settings.get("repeat", "1"))
                self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
                self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
                self.random_interval_var.set(settings.get("random_interval", False))
                self.log(f"[{format_time(time.time())}] 腳本已載入：{os.path.basename(path)}，共 {len(self.events)} 筆事件。")
                self.refresh_script_list()
                self.script_var.set(os.path.basename(path))
                with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                    f.write(os.path.basename(path))
                self.save_config()
            except Exception as ex:
                self.log(f"載入腳本失敗: {ex}")

    def load_last_script(self):
        if os.path.exists(LAST_SCRIPT_FILE):
            with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
                last_script = f.read().strip()
            if last_script:
                script_path = os.path.join(self.script_dir, last_script)
                if os.path.exists(script_path):
                    try:
                        data = sio_load_script(script_path)
                        self.events = data.get("events", [])
                        settings = data.get("settings", {})
                        self.speed_var.set(settings.get("speed", "100"))
                        self.repeat_var.set(settings.get("repeat", "1"))
                        self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
                        self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
                        self.random_interval_var.set(settings.get("random_interval", False))
                        self.script_var.set(last_script)
                        self.log(f"[{format_time(time.time())}] 已自動載入上次腳本：{last_script}，共 {len(self.events)} 筆事件。")
                    except Exception as ex:
                        self.log(f"載入上次腳本失敗: {ex}")

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
            "mini": lang_map["MiniMode"]
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
                        "mini": "toggle_mini_mode"
                    }[key]),
                                       suppress=False,  # 不攔截原本的功能
                    trigger_on_release=False
                )
                self._hotkey_handlers[key] = handler
                self.log(f"已註冊快捷鍵: {hotkey} → {key}")
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")

    def _register_script_hotkeys(self):
        """註冊腳本內定義的快捷鍵"""
        for handler in self._script_hotkey_handlers.values():
            try:
                keyboard.remove_hotkey(handler)
            except Exception as ex:
                self.log(f"移除腳本快捷鍵時發生錯誤: {ex}")
        self._script_hotkey_handlers.clear()

        # 只對目前選中的腳本有效
        script = self.script_var.get()
        if not script:
            return
        path = os.path.join(self.script_dir, script)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            hotkey = data.get("script_hotkey", "")
            if hotkey:
                # 註冊腳本的快捷鍵
                handler = keyboard.add_hotkey(
                    hotkey,
                    self.play_record,  # 直接綁定到回放
                    suppress=False,
                    trigger_on_release=False
                )
                self._script_hotkey_handlers["script_hotkey"] = handler
                self.log(f"已註冊腳本快捷鍵: {hotkey}")
        except Exception as ex:
            self.log(f"註冊腳本快捷鍵失敗: {ex}")

    def _update_hotkey_labels(self):
        self.btn_start.config(text=f"開始錄製 ({self.hotkey_map['start']})")
        self.btn_pause.config(text=f"暫停/繼續 ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=f"停止 ({self.hotkey_map['stop']})")
        self.btn_play.config(text=f"回放 ({self.hotkey_map['play']})")
        # MiniMode 按鈕同步更新
        if hasattr(self, "mini_btns"):
            for btn, icon, key in self.mini_btns:
                btn.config(text=f"{icon} {self.hotkey_map[key]}")
        # 如果使用 mini_controller，直接更新按鈕文字
        if getattr(self, "mini_controller", None):
            try:
                self.mini_controller.update_buttons(self.hotkey_map)
            except Exception:
                pass

    def toggle_mini_mode(self):
        # 切換 MiniMode 狀態，改由 mini.MiniMode 管理視窗
        if not hasattr(self, "mini_mode_on"):
            self.mini_mode_on = False
        self.mini_mode_on = not self.mini_mode_on

        def _on_close():
            # Called by mini when closed
            try:
                self.mini_mode_on = False
                self.deiconify()
            except Exception:
                pass

        if self.mini_mode_on:
            if self.mini_controller is None or not self.mini_controller.is_open():
                # callbacks for buttons
                callbacks = {
                    "start": self.start_record,
                    "pause": self.toggle_pause,
                    "stop": self.stop_all,
                    "play": self.play_record,
                    "mini": self.toggle_mini_mode
                }
                try:
                    self.mini_controller = mini.MiniMode(self, self.hotkey_map, callbacks, on_close=_on_close)
                    self.mini_controller.show()
                except Exception as ex:
                    self.log(f"建立 MiniMode 失敗: {ex}")
                try:
                    self.withdraw()
                except Exception:
                    pass
        else:
            # 關閉 mini
            if self.mini_controller:
                try:
                    self.mini_controller.close()
               

                except Exception:
                    pass
                self.deiconify()

    def _close_mini_mode(self):
        # backwards-compatible close handler (被 mini 呼叫時會觸發)
        if self.mini_controller:
            try:
                self.mini_controller.close()
            except Exception:
                pass
        try:
            self.deiconify()
        except Exception:
            pass
        self.mini_mode_on = False

    # 原本的拖曳函式已經由 mini.MiniMode 管理，不再需要 _start_move_mini/_move_mini

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
        """刷新腳本設定區左側 Listbox（且不影響右側狀態）"""
        try:
            self.script_listbox.delete(0, "end")
            if not os.path.exists(self.script_dir):
                os.makedirs(self.script_dir)
            scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
            for f in sorted(scripts):
                self.script_listbox.insert("end", f)
        except Exception as ex:
            self.log(f"刷新腳本清單失敗: {ex}")

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

    def on_script_listbox_select(self, event=None):
        idx = self.script_listbox.curselection()
        if not idx:
            return
        script = self.script_listbox.get(idx[0])
        self.script_var.set(script)
        # 顯示該腳本內先前設定的 hotkey（若有）
        path = os.path.join(self.script_dir, script)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            hotkey = data.get("script_hotkey", "")
            self.hotkey_capture_var.set(hotkey)
        except Exception:
            self.hotkey_capture_var.set("")
        # 並同步載入腳本內容到 editor/state（不自動執行）
        try:
            data = sio_load_script(path)
            self.events = data.get("events", [])
            settings = data.get("settings", {})
            self.speed_var.set(settings.get("speed", "100"))
            self.repeat_var.set(settings.get("repeat", "1"))
            self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
            self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
            self.random_interval_var.set(settings.get("random_interval", False))
        except Exception:
            pass

    def on_hotkey_entry_key(self, event):
        keys = []
        if event.state & 0x0001: keys.append("shift")
       
        if event.state & 0x0004: keys.append("ctrl")
        if event.state & 0x0008: keys.append("alt")
        key_name = event.keysym.lower()
        if key_name not in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"):
            keys.append(key_name)
        self.hotkey_capture_var.set("+".join(keys))
        return "break"

    def set_script_hotkey(self):
        """為選中的腳本設定快捷鍵並註冊（可用來直接觸發回放）"""
        script = self.script_var.get()
        hotkey = self.hotkey_capture_var.get().strip().lower()
        if not script or not hotkey or hotkey == "輸入按鍵":
            self.log("請先選擇腳本並輸入有效的快捷鍵。")
            return
        path = os.path.join(self.script_dir, script)
        try:
            # 取消原本為該腳本註冊的 hotkey（若有）
            old_hot = None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                old_hot = data.get("script_hotkey", "")
            except Exception:
                data = {}
            data["script_hotkey"] = hotkey
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # 先移除舊註冊（若存在）
            if old_hot:
                # 找到 handler 並移除
                for key, info in list(self._script_hotkey_handlers.items()):
                    if info.get("script") == script:
                        try:
                            keyboard.remove_hotkey(info.get("handler"))
                        except Exception:
                            pass
                        self._script_hotkey_handlers.pop(key, None)
            # 註冊新的 hotkey
            self._register_single_script_hotkey(script, hotkey)
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
        # 先取消註冊此腳本的 hotkey（若有）
        try:
            for key, info in list(self._script_hotkey_handlers.items()):
                if info.get("script") == script:
                    try:
                        keyboard.remove_hotkey(info.get("handler"))
                    except Exception:
                        pass
                    self._script_hotkey_handlers.pop(key, None)
        except Exception:
            pass
        try:
            os.remove(path)
            self.log(f"已刪除腳本：{script}")
            self.refresh_script_listbox()
            self.refresh_script_list()
            # 若被選中也要清除相關 UI
            if self.script_var.get() == script:
                self.script_var.set('')
                self.hotkey_capture_var.set('')
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