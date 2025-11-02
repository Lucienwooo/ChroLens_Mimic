#ChroLens Studio - Lucienwooo
#python "C:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main\ChroLens_Mimic.py"
#pyinstaller --noconsole --onedir --icon=..\umi_奶茶色.ico --add-data "..\umi_奶茶色.ico;." --add-data "TTF;TTF" --add-data "recorder.py;." --add-data "lang.py;." --add-data "script_io.py;." --add-data "about.py;." --add-data "mini.py;." --add-data "window_selector.py;." --add-data "script_parser.py;." --add-data "config_manager.py;." --add-data "hotkey_manager.py;." --add-data "script_editor_methods.py;." --add-data "script_manager.py;." --add-data "ui_components.py;." --add-data "visual_script_editor.py;." ChroLens_Mimic.py

VERSION = "2.6.2"

import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import threading, time, json, os, datetime
import keyboard, mouse
import ctypes
import win32api
import win32gui
import win32con
import pywintypes
import random  # 新增
import tkinter.font as tkfont
import sys

# 檢查是否以管理員身份執行
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# 新增：匯入 Recorder / 語言 / script IO 函式（使用健壯的 fallback）
try:
    from recorder import CoreRecorder
except Exception as e:
    print(f"無法匯入 CoreRecorder: {e}")

try:
    from visual_script_editor import VisualScriptEditor
except Exception as e:
    print(f"無法匯入 VisualScriptEditor: {e}")
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

# 新增：匯入 window_selector 模組
try:
    from window_selector import WindowSelectorDialog
except Exception as e:
    print(f"無法匯入 window_selector 模組: {e}")
    WindowSelectorDialog = None

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

def get_icon_path():
    """取得圖示檔案路徑（打包後和開發環境通用）"""
    try:
        import sys
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

def get_dpi_scale():
    """獲取 Windows 系統的 DPI 縮放比例"""
    try:
        # 設定 DPI Awareness
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
    except:
        pass
    
    try:
        # 獲取系統 DPI
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        scale = dpi / 96.0  # 96 DPI 是 100% 縮放
        return scale
    except:
        return 1.0

def get_screen_resolution():
    """獲取螢幕解析度"""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)   # SM_CXSCREEN
        height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
        return (width, height)
    except:
        return (1920, 1080)  # 預設值

def get_window_info(hwnd):
    """獲取視窗的完整資訊（包含 DPI、解析度等）"""
    try:
        # 獲取視窗矩形
        rect = win32gui.GetWindowRect(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        pos = (rect[0], rect[1])
        
        # 獲取系統資訊
        dpi_scale = get_dpi_scale()
        screen_res = get_screen_resolution()
        
        return {
            "size": (width, height),
            "position": pos,
            "dpi_scale": dpi_scale,
            "screen_resolution": screen_res,
            "client_size": (width, height)  # 實際可用區域
        }
    except Exception as e:
        return None

def screen_to_client(hwnd, x, y):
    # 螢幕座標轉視窗內座標
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return x - left, y - top

def client_to_screen(hwnd, x, y):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return left + x, top + y

class RecorderApp(tb.Window):
    def __init__(self):
        # 檢查管理員權限
        if not is_admin():
            # 顯示警告但仍繼續執行
            print("⚠️ 警告：程式未以管理員身份執行，錄製功能可能無法正常工作！")
        
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
        
        # 如果不是管理員，顯示警告對話框
        if not is_admin():
            self.after(1000, self._show_admin_warning)
        
        self.language_var = tk.StringVar(self, value=lang)
        self._hotkey_handlers = {}
        # 用來儲存腳本快捷鍵的 handler id
        self._script_hotkey_handlers = {}
        # MiniMode 管理器（由 mini.py 提供）
        self.mini_window = None
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

        self.title("ChroLens_Mimic_2.6.2")
        # 設定視窗圖示
        set_window_icon(self)

        # 在左上角建立一個小label作為icon區域的懸浮觸發點
        self.icon_tip_label = tk.Label(self, width=2, height=1, bg=self.cget("background"))
        self.icon_tip_label.place(x=0, y=0)
        Tooltip(self.icon_tip_label, f"{self.title()}_By_Lucien")

        # 設定最小視窗尺寸並允許彈性調整
        self.minsize(1000, 550)  # 增加最小寬度以容納新功能
        self.geometry("1050x550")  # 增加初始寬度
        self.resizable(True, True)  # 允許調整大小
        
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

        # ====== MiniMode 按鈕 ======
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
        self.speed_var = tk.StringVar(value=self.user_config.get("speed", "100"))
        tb.Entry(frm_bottom, textvariable=self.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=6)
        saved_lang = self.user_config.get("language", "繁體中文")
        self.language_var = tk.StringVar(self, value=saved_lang)

        # ====== 重複參數設定 ======
        self.repeat_label = tb.Label(frm_bottom, text="重複次數:", style="My.TLabel")
        self.repeat_label.grid(row=0, column=2, padx=(8, 2))
        self.repeat_var = tk.StringVar(value=self.user_config.get("repeat", "1"))
        entry_repeat = tb.Entry(frm_bottom, textvariable=self.repeat_var, width=6, style="My.TEntry")
        entry_repeat.grid(row=0, column=3, padx=2)

        self.repeat_time_var = tk.StringVar(value="00:00:00")
        entry_repeat_time = tb.Entry(frm_bottom, textvariable=self.repeat_time_var, width=10, style="My.TEntry", justify="center")
        entry_repeat_time.grid(row=0, column=5, padx=(10, 2))
        self.repeat_time_label = tb.Label(frm_bottom, text="重複時間", style="My.TLabel")
        self.repeat_time_label.grid(row=0, column=6, padx=(0, 2))
        self.repeat_time_tooltip = Tooltip(self.repeat_time_label, "設定總運作時間，格式HH:MM:SS\n例如: 01:30:00 表示持續1.5小時\n留空或00:00:00則依重複次數執行")

        self.repeat_interval_var = tk.StringVar(value="00:00:00")
        repeat_interval_entry = tb.Entry(frm_bottom, textvariable=self.repeat_interval_var, width=10, style="My.TEntry", justify="center")
        repeat_interval_entry.grid(row=0, column=7, padx=(10, 2))
        self.repeat_interval_label = tb.Label(frm_bottom, text="重複間隔", style="My.TLabel")
        self.repeat_interval_label.grid(row=0, column=8, padx=(0, 2))
        self.repeat_interval_tooltip = Tooltip(self.repeat_interval_label, "每次重複之間的等待時間\n格式HH:MM:SS，例如: 00:00:30\n表示每次執行完等待30秒再開始下一次")

        self.random_interval_var = tk.BooleanVar(value=False)
        self.random_interval_check = tb.Checkbutton(
            frm_bottom, text="隨機", variable=self.random_interval_var, style="My.TCheckbutton"
        )
        self.random_interval_check.grid(row=0, column=9, padx=(8, 2))
        self.random_interval_tooltip = Tooltip(self.random_interval_check, "勾選後，重複間隔將在0到設定值之間隨機\n可避免被偵測為機器人行為")

        # ====== 自動切換 MiniMode 勾選框 ======
        self.auto_mini_var = tk.BooleanVar(value=self.user_config.get("auto_mini_mode", False))
        lang_map = LANG_MAP.get(saved_lang, LANG_MAP["繁體中文"])
        self.main_auto_mini_check = tb.Checkbutton(
            frm_top, text=lang_map["自動切換"], variable=self.auto_mini_var, style="My.TCheckbutton"
        )
        self.main_auto_mini_check.grid(row=0, column=8, padx=4)
        Tooltip(self.main_auto_mini_check, lang_map["勾選時，程式錄製/回放將自動轉換"])
        
        # ====== 儲存按鈕 ======
        self.save_script_btn_text = tk.StringVar(value=LANG_MAP.get(saved_lang, LANG_MAP["繁體中文"])["儲存"])
        self.save_script_btn = tb.Button(
            frm_bottom, textvariable=self.save_script_btn_text, width=8, bootstyle=SUCCESS, style="My.TButton",
            command=self.save_script_settings
        )
        self.save_script_btn.grid(row=0, column=10, padx=(8, 0))

        # ====== 時間輸入驗證 ======
        def validate_time_input(P):
            import re
            return re.fullmatch(r"[\d:]*", P) is not None
        vcmd = (self.register(validate_time_input), "%P")
        entry_repeat_time.config(validate="key", validatecommand=vcmd)
        repeat_interval_entry.config(validate="key", validatecommand=vcmd)

        entry_repeat.bind("<Button-3>", lambda e: self.repeat_var.set("0"))
        entry_repeat_time.bind("<Button-3>", lambda e: self.repeat_time_var.set("00:00:00"))
        repeat_interval_entry.bind("<Button-3>", lambda e: self.repeat_interval_var.set("00:00:00"))

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
        self.rename_btn = tb.Button(frm_script, text=lang_map["重新命名"], command=self.rename_script, bootstyle=WARNING, width=12, style="My.TButton")
        self.rename_btn.grid(row=0, column=3, padx=4)

        self.select_target_btn = tb.Button(frm_script, text=lang_map["選擇視窗"], command=self.select_target_window, bootstyle=INFO, width=14, style="My.TButton")
        self.select_target_btn.grid(row=0, column=4, padx=4)

        # ====== 滑鼠模式勾選框（預設打勾）======
        self.mouse_mode_var = tk.BooleanVar(value=self.user_config.get("mouse_mode", True))  # 改為 True
        self.mouse_mode_check = tb.Checkbutton(
            frm_script, text=lang_map["滑鼠模式"], variable=self.mouse_mode_var, style="My.TCheckbutton"
        )
        self.mouse_mode_check.grid(row=0, column=5, padx=4)
        Tooltip(self.mouse_mode_check, lang_map["勾選時以控制真實滑鼠的模式回放"])

        self.script_combo.bind("<<ComboboxSelected>>", self.on_script_selected)
        # 綁定點擊事件，在展開下拉選單前自動刷新列表
        self.script_combo.bind("<Button-1>", self._on_script_combo_click)


        # ====== 日誌顯示區 ======
        frm_log = tb.Frame(self, padding=(10, 0, 10, 10))
        frm_log.pack(fill="both", expand=True)
        log_title_frame = tb.Frame(frm_log)
        log_title_frame.pack(fill="x")

        self.mouse_pos_label = tb.Label(
            log_title_frame, text="(X=0,Y=0)",
            font=("Consolas", 10),  # 字體縮小一個單位
            foreground="#668B9B"
        )
        self.mouse_pos_label.pack(side="left", padx=4)  # 減少間距更緊湊

        # 顯示目前選定的目標視窗（緊接在滑鼠座標右邊，但不要卡到總運作）
        self.target_label = tb.Label(
            log_title_frame, text="",
            font=font_tuple(9),
            foreground="#FF9500",
            anchor="w",
            width=25,  # 限制最大寬度
            cursor="hand2"  # 滑鼠懸停時顯示手型游標
        )
        self.target_label.pack(side="left", padx=(0, 4))
        # 綁定右鍵點擊事件來取消視窗選擇
        self.target_label.bind("<Button-3>", self._clear_target_window)

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
        frm_page.grid_columnconfigure(0, weight=0)  # 左側選單固定寬度
        frm_page.grid_columnconfigure(1, weight=1)  # 右側內容區彈性擴展

        # 左側選單
        lang_map = LANG_MAP.get(saved_lang, LANG_MAP["繁體中文"])
        self.page_menu = tk.Listbox(frm_page, width=18, font=("Microsoft JhengHei", 11), height=5)
        self.page_menu.insert(0, lang_map["1.日誌顯示"])
        self.page_menu.insert(1, lang_map["2.腳本設定"])
        self.page_menu.insert(2, lang_map["3.整體設定"])
        self.page_menu.grid(row=0, column=0, sticky="ns", padx=(0, 8), pady=4)
        self.page_menu.bind("<<ListboxSelect>>", self.on_page_selected)

        # 右側內容區（隨視窗大小調整）
        self.page_content_frame = tb.Frame(frm_page)
        self.page_content_frame.grid(row=0, column=1, sticky="nsew")
        self.page_content_frame.grid_rowconfigure(0, weight=1)
        self.page_content_frame.grid_columnconfigure(0, weight=1)

        # 日誌顯示區（彈性調整）
        self.log_text = tb.Text(self.page_content_frame, state="disabled", font=font_tuple(9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = tb.Scrollbar(self.page_content_frame, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # 腳本設定區（彈性調整）
        self.script_setting_frame = tb.Frame(self.page_content_frame)
        self.script_setting_frame.grid_rowconfigure(0, weight=1)
        self.script_setting_frame.grid_columnconfigure(0, weight=1)  # 列表區自適應
        self.script_setting_frame.grid_columnconfigure(1, weight=0)  # 右側控制固定

        # 左側腳本列表區（使用 Text 顯示檔名和快捷鍵）
        list_frame = tb.Frame(self.script_setting_frame)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(8,0), pady=8)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # 使用 Treeview 來顯示兩欄（腳本名稱 | 快捷鍵）
        from tkinter import ttk
        self.script_treeview = ttk.Treeview(
            list_frame,
            columns=("name", "hotkey"),
            show="headings",
            height=15
        )
        self.script_treeview.heading("name", text="腳本名稱")
        self.script_treeview.heading("hotkey", text="快捷鍵")
        self.script_treeview.column("name", width=300, anchor="w")
        self.script_treeview.column("hotkey", width=100, anchor="center")
        self.script_treeview.grid(row=0, column=0, sticky="nsew")
        
        # 加入捲軸
        list_scroll = tb.Scrollbar(list_frame, command=self.script_treeview.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.script_treeview.config(yscrollcommand=list_scroll.set)
        
        # 綁定選擇事件
        self.script_treeview.bind("<<TreeviewSelect>>", self.on_script_treeview_select)
        
        # 儲存當前選中的腳本
        self.selected_script_line = None

        # 右側控制區（垂直排列，填滿剩餘空間）
        self.script_right_frame = tb.Frame(self.script_setting_frame, padding=6)
        self.script_right_frame.grid(row=0, column=1, sticky="nsew", padx=(6,8), pady=8)

        # 快捷鍵捕捉（可捕捉任意按鍵或組合鍵）
        self.hotkey_capture_var = tk.StringVar(value="")
        self.hotkey_capture_label = tb.Label(self.script_right_frame, text="捕捉快捷鍵：", style="My.TLabel")
        self.hotkey_capture_label.pack(anchor="w", pady=(2,2))
        hotkey_entry = tb.Entry(self.script_right_frame, textvariable=self.hotkey_capture_var, font=font_tuple(10, monospace=True), width=16)
        hotkey_entry.pack(anchor="w", pady=(0,8))
        # 改用 KeyPress 事件以正確捕捉組合鍵
        hotkey_entry.bind("<KeyPress>", self.on_hotkey_entry_key)
        hotkey_entry.bind("<FocusIn>", lambda e: self.hotkey_capture_var.set("輸入按鍵"))
        hotkey_entry.bind("<FocusOut>", lambda e: None)

        # a) 設定快捷鍵按鈕：將捕捉到的快捷鍵寫入選定腳本並註冊
        self.set_hotkey_btn = tb.Button(self.script_right_frame, text="設定快捷鍵", width=16, bootstyle=SUCCESS, command=self.set_script_hotkey)
        self.set_hotkey_btn.pack(anchor="w", pady=4)

        # b) 直接開啟腳本資料夾（輔助功能）
        self.open_dir_btn = tb.Button(self.script_right_frame, text="開啟資料夾", width=16, bootstyle=SECONDARY, command=self.open_scripts_dir)
        self.open_dir_btn.pack(anchor="w", pady=4)

        # c) 刪除按鈕：直接刪除檔案並取消註冊其快捷鍵（若有）
        self.del_script_btn = tb.Button(self.script_right_frame, text="刪除腳本", width=16, bootstyle=DANGER, command=self.delete_selected_script)
        self.del_script_btn.pack(anchor="w", pady=4)
        
        # d) 視覺化編輯器按鈕：開啟拖放式編輯器（主要編輯器）
        self.visual_editor_btn = tb.Button(self.script_right_frame, text="腳本編輯器", width=16, bootstyle=SUCCESS, command=self.open_visual_editor)
        self.visual_editor_btn.pack(anchor="w", pady=4)

        # 初始化清單
        self.refresh_script_listbox()

        # ====== 整體設定頁面 ======
        self.global_setting_frame = tb.Frame(self.page_content_frame)
        
        self.btn_hotkey = tb.Button(self.global_setting_frame, text="快捷鍵", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=15, style="My.TButton")
        self.btn_hotkey.pack(anchor="w", pady=4, padx=8)
        
        self.about_btn = tb.Button(self.global_setting_frame, text="關於", width=15, style="My.TButton", command=self.show_about_dialog, bootstyle=SECONDARY)
        self.about_btn.pack(anchor="w", pady=4, padx=8)
        
        self.update_btn = tb.Button(self.global_setting_frame, text="檢查更新", width=15, style="My.TButton", command=self.check_for_updates, bootstyle=INFO)
        self.update_btn.pack(anchor="w", pady=4, padx=8)
        
        self.actual_language = saved_lang
        self.language_display_var = tk.StringVar(self, value="Language")
        
        lang_combo_global = tb.Combobox(
            self.global_setting_frame,
            textvariable=self.language_display_var,
            values=["繁體中文", "日本語", "English"],
            state="readonly",
            width=12,
            style="My.TCombobox"
        )
        lang_combo_global.pack(anchor="w", pady=4, padx=8)
        lang_combo_global.bind("<<ComboboxSelected>>", self.change_language)
        self.language_combo = lang_combo_global

        # ====== 初始化設定 ======
        self.page_menu.selection_set(0)
        self.show_page(0)

        self.refresh_script_list()
        if self.script_var.get():
            self.on_script_selected()
        self._init_language(saved_lang)
        self.after(1500, self._delayed_init)

    def _show_admin_warning(self):
        """顯示管理員權限警告"""
        try:
            import tkinter.messagebox as messagebox
            result = messagebox.askquestion(
                "管理員權限警告",
                "⚠️ 檢測到程式未以管理員身份執行！\n\n"
                "錄製功能需要管理員權限才能正常工作。\n"
                "鍵盤和滑鼠監聽可能會失敗。\n\n"
                "是否要以管理員身份重新啟動程式？\n"
                "（選擇「否」將繼續執行，但錄製功能可能無法使用）",
                icon='warning'
            )
            
            if result == 'yes':
                # 重新以管理員身份啟動
                self._restart_as_admin()
        except Exception as e:
            self.log(f"顯示管理員警告時發生錯誤: {e}")
    
    def _restart_as_admin(self):
        """以管理員身份重新啟動程式"""
        try:
            import sys
            if getattr(sys, 'frozen', False):
                # 打包後的 exe
                script = sys.executable
            else:
                # 開發環境
                script = os.path.abspath(sys.argv[0])
            
            params = ' '.join([script] + sys.argv[1:])
            
            # 使用 ShellExecute 以管理員身份執行
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",  # 以管理員身份執行
                sys.executable if getattr(sys, 'frozen', False) else sys.executable,
                f'"{script}"' if not getattr(sys, 'frozen', False) else None,
                None, 
                1
            )
            
            # 關閉當前程式
            self.quit()
            sys.exit(0)
        except Exception as e:
            self.log(f"重新啟動為管理員時發生錯誤: {e}")

    def _delayed_init(self):
        self.after(1600, self._register_hotkeys)
        self.after(1650, self._register_script_hotkeys)
        self.after(1700, self.refresh_script_list)
        self.after(1800, self.load_last_script)
        self.after(1900, self.update_mouse_pos)
        self.after(2000, self._init_background_mode)

    def _init_background_mode(self):
        """初始化後台模式設定（固定使用智能模式）"""
        mode = "smart"
        if hasattr(self.core_recorder, 'set_background_mode'):
            self.core_recorder.set_background_mode(mode)
        self.log(f"後台模式：智能模式（自動適應）")

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
    
    def _actions_to_events(self, actions):
        """將視覺化編輯器的動作列表轉換為事件列表"""
        events = []
        current_time = 0.0
        
        try:
            for action in actions:
                command = action.get("command", "")
                params_str = action.get("params", "")
                delay = float(action.get("delay", 0)) / 1000.0  # 毫秒轉秒
                
                # 先加上延遲
                current_time += delay
                
                # 根據指令類型創建事件
                if command == "move_to" or command == "move_to_path":
                    # 解析座標
                    try:
                        if command == "move_to_path":
                            # move_to_path: params 是 JSON 字串格式的軌跡列表
                            # 嘗試使用 json.loads 解析
                            try:
                                trajectory = json.loads(params_str)
                            except:
                                # 如果 json.loads 失敗,嘗試 ast.literal_eval
                                import ast
                                trajectory = ast.literal_eval(params_str)
                            
                            if trajectory and isinstance(trajectory, list) and len(trajectory) > 0:
                                # 取最後一個點作為終點
                                last_point = trajectory[-1]
                                x = int(last_point.get("x", 0))
                                y = int(last_point.get("y", 0))
                                
                                events.append({
                                    "type": "mouse",
                                    "event": "move",
                                    "x": x,
                                    "y": y,
                                    "time": current_time,
                                    "trajectory": trajectory
                                })
                            else:
                                self.log(f"move_to_path 軌跡數據格式錯誤或為空")
                        else:
                            # move_to: params 是 "x, y" 或 "x, y, trajectory"
                            parts = [p.strip() for p in params_str.split(",", 2)]  # 最多分割為3部分
                            x = int(parts[0]) if len(parts) > 0 else 0
                            y = int(parts[1]) if len(parts) > 1 else 0
                            
                            # 檢查是否有軌跡數據
                            if len(parts) > 2 and parts[2]:
                                # 有軌跡數據,嘗試解析
                                try:
                                    trajectory = json.loads(parts[2])
                                except:
                                    import ast
                                    trajectory = ast.literal_eval(parts[2])
                                
                                events.append({
                                    "type": "mouse",
                                    "event": "move",
                                    "x": x,
                                    "y": y,
                                    "time": current_time,
                                    "trajectory": trajectory
                                })
                            else:
                                # 普通移動
                                events.append({
                                    "type": "mouse",
                                    "event": "move",
                                    "x": x,
                                    "y": y,
                                    "time": current_time
                                })
                    except Exception as e:
                        self.log(f"解析 {command} 參數失敗: {e}")
                        import traceback
                        self.log(f"錯誤詳情: {traceback.format_exc()}")
                
                elif command == "click":
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": "left",
                        "time": current_time
                    })
                    current_time += 0.05
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": "left",
                        "time": current_time
                    })
                
                elif command == "double_click":
                    for _ in range(2):
                        events.append({
                            "type": "mouse",
                            "event": "down",
                            "button": "left",
                            "time": current_time
                        })
                        current_time += 0.05
                        events.append({
                            "type": "mouse",
                            "event": "up",
                            "button": "left",
                            "time": current_time
                        })
                        current_time += 0.05
                
                elif command == "right_click":
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": "right",
                        "time": current_time
                    })
                    current_time += 0.05
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": "right",
                        "time": current_time
                    })
                
                elif command == "press_down":
                    button = params_str.strip() if params_str else "left"
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": button,
                        "time": current_time
                    })
                
                elif command == "release":
                    button = params_str.strip() if params_str else "left"
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": button,
                        "time": current_time
                    })
                
                elif command == "scroll":
                    try:
                        delta = int(params_str) if params_str else 1
                        events.append({
                            "type": "mouse",
                            "event": "wheel",
                            "delta": delta,
                            "time": current_time
                        })
                    except:
                        pass
                
                elif command == "type_text":
                    text = params_str.strip()
                    for char in text:
                        events.append({
                            "type": "keyboard",
                            "event": "down",
                            "key": char,
                            "time": current_time
                        })
                        current_time += 0.05
                        events.append({
                            "type": "keyboard",
                            "event": "up",
                            "key": char,
                            "time": current_time
                        })
                        current_time += 0.05
                
                elif command == "press_key":
                    key = params_str.strip()
                    if key:
                        events.append({
                            "type": "keyboard",
                            "event": "down",
                            "key": key,
                            "time": current_time
                        })
                        current_time += 0.05
                        events.append({
                            "type": "keyboard",
                            "event": "up",
                            "key": key,
                            "time": current_time
                        })
                
                elif command == "hotkey":
                    keys = [k.strip() for k in params_str.split("+")]
                    # 按下所有按鍵
                    for key in keys:
                        events.append({
                            "type": "keyboard",
                            "event": "down",
                            "key": key,
                            "time": current_time
                        })
                        current_time += 0.02
                    # 釋放所有按鍵（反向）
                    for key in reversed(keys):
                        events.append({
                            "type": "keyboard",
                            "event": "up",
                            "key": key,
                            "time": current_time
                        })
                        current_time += 0.02
                
                elif command == "delay":
                    try:
                        extra_delay = float(params_str) / 1000.0 if params_str else 0
                        current_time += extra_delay
                    except:
                        pass
        
        except Exception as e:
            self.log(f"轉換動作為事件時發生錯誤: {e}")
            import traceback
            self.log(traceback.format_exc())
        
        return events

    def show_about_dialog(self):
        try:
            about.show_about(self)
        except Exception as e:
            print(f"顯示 about 視窗失敗: {e}")
    
    def check_for_updates(self):
        """檢查 GitHub 上的新版本"""
        # 創建進度視窗
        progress_window = tk.Toplevel(self)
        progress_window.title("檢查更新")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        progress_window.transient(self)
        progress_window.grab_set()
        set_window_icon(progress_window)
        
        # 居中顯示
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
        y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
        progress_window.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = tb.Frame(progress_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # 狀態標籤
        status_label = tb.Label(main_frame, text="正在連線到 GitHub...", font=("Microsoft JhengHei", 11))
        status_label.pack(pady=(0, 15))
        
        # 進度條
        progress_bar = tb.Progressbar(main_frame, length=350, mode='determinate')
        progress_bar.pack(pady=10)
        progress_bar['value'] = 0
        
        # 詳細資訊標籤
        detail_label = tb.Label(main_frame, text="初始化...", font=("Microsoft JhengHei", 9), foreground="#888")
        detail_label.pack(pady=(5, 0))
        
        def check_update_thread():
            try:
                import urllib.request
                import json
                
                # 更新進度：10%
                self.after(0, lambda: progress_bar.configure(value=10))
                self.after(0, lambda: detail_label.config(text="正在取得最新版本資訊..."))
                
                # GitHub API URL
                api_url = "https://api.github.com/repos/Lucienwooo/ChroLens_Mimic/releases/latest"
                
                # 發送請求
                req = urllib.request.Request(api_url)
                req.add_header('User-Agent', 'ChroLens-Mimic-UpdateChecker')
                
                # 更新進度：30%
                self.after(0, lambda: progress_bar.configure(value=30))
                self.after(0, lambda: detail_label.config(text="正在連線到伺服器..."))
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    # 更新進度：60%
                    self.after(0, lambda: progress_bar.configure(value=60))
                    self.after(0, lambda: detail_label.config(text="正在解析版本資訊..."))
                    
                    data = json.loads(response.read().decode())
                    latest_version = data.get('tag_name', '').lstrip('v')
                    release_notes = data.get('body', '無發行說明')
                    download_url = data.get('html_url', '')
                    
                    # 取得下載連結（尋找 .zip 檔案）
                    assets = data.get('assets', [])
                    asset_url = None
                    asset_name = None
                    for asset in assets:
                        name = asset.get('name', '')
                        if name.endswith('.zip'):
                            asset_url = asset.get('browser_download_url', '')
                            asset_name = name
                            break
                    
                    # 更新進度：90%
                    self.after(0, lambda: progress_bar.configure(value=90))
                    self.after(0, lambda: detail_label.config(text="正在比較版本..."))
                    
                    # 比較版本
                    current = VERSION.split('.')
                    latest = latest_version.split('.')
                    
                    is_newer = False
                    for i in range(min(len(current), len(latest))):
                        if int(latest[i]) > int(current[i]):
                            is_newer = True
                            break
                        elif int(latest[i]) < int(current[i]):
                            break
                    
                    # 更新進度：100%
                    self.after(0, lambda: progress_bar.configure(value=100))
                    self.after(0, lambda: detail_label.config(text="檢查完成！"))
                    
                    # 延遲 500ms 後關閉進度視窗並顯示結果
                    self.after(500, lambda: progress_window.destroy())
                    self.after(600, lambda: self._show_update_result(
                        is_newer, VERSION, latest_version, release_notes, 
                        download_url, asset_url, asset_name
                    ))
                    
            except Exception as e:
                self.after(0, lambda: progress_window.destroy())
                self.after(50, lambda: messagebox.showerror("錯誤", f"檢查更新失敗：{str(e)}\n\n請確認網路連線正常"))
        
        # 在背景執行緒中檢查
        threading.Thread(target=check_update_thread, daemon=True).start()
    
    def _show_update_result(self, is_newer, current_ver, latest_ver, notes, page_url, asset_url, asset_name):
        """顯示更新檢查結果"""
        if is_newer:
            message = f"發現新版本！\n\n"
            message += f"目前版本：{current_ver}\n"
            message += f"最新版本：{latest_ver}\n\n"
            message += f"更新內容：\n{notes[:200]}{'...' if len(notes) > 200 else ''}\n\n"
            
            if asset_url:
                message += f"是否立即下載並安裝更新？\n"
                message += f"檔案：{asset_name}"
            else:
                message += f"是否前往下載頁面手動更新？"
            
            result = messagebox.askyesno("發現新版本", message)
            if result:
                if asset_url:
                    # 自動更新
                    self._start_auto_update(asset_url, asset_name, latest_ver)
                else:
                    # 手動更新（開啟網頁）
                    import webbrowser
                    webbrowser.open(page_url)
        else:
            messagebox.showinfo("已是最新版本", f"您使用的是最新版本 {current_ver}")
    
    def _start_auto_update(self, download_url, filename, new_version):
        """開始自動更新流程（高級版本）"""
        # 創建更新進度視窗
        update_window = tk.Toplevel(self)
        update_window.title("自動更新")
        update_window.geometry("500x300")
        update_window.resizable(False, False)
        update_window.transient(self)
        update_window.grab_set()
        set_window_icon(update_window)
        
        # 居中顯示
        update_window.update_idletasks()
        x = (update_window.winfo_screenwidth() // 2) - (update_window.winfo_width() // 2)
        y = (update_window.winfo_screenheight() // 2) - (update_window.winfo_height() // 2)
        update_window.geometry(f"+{x}+{y}")
        
        # 主框架
        main_frame = tb.Frame(update_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # 標題
        title_label = tb.Label(main_frame, text=f"正在更新到版本 {new_version}", 
                              font=("Microsoft JhengHei", 12, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 進度標籤
        status_label = tb.Label(main_frame, text="準備下載更新...", font=("Microsoft JhengHei", 11))
        status_label.pack(pady=(0, 10))
        
        # 進度條
        progress_bar = tb.Progressbar(main_frame, length=450, mode='determinate')
        progress_bar.pack(pady=10)
        
        # 詳細資訊
        detail_label = tb.Label(main_frame, text="", font=("Microsoft JhengHei", 9), foreground="#888")
        detail_label.pack(pady=5)
        
        # 百分比顯示
        percent_label = tb.Label(main_frame, text="0%", font=("Consolas", 14, "bold"), foreground="#00A0E9")
        percent_label.pack(pady=5)
        
        # 取消按鈕
        cancel_flag = {'cancelled': False}
        
        def cancel_update():
            cancel_flag['cancelled'] = True
            update_window.destroy()
            messagebox.showinfo("已取消", "更新已取消")
        
        cancel_btn = tb.Button(main_frame, text="取消", command=cancel_update, bootstyle="danger")
        cancel_btn.pack(pady=10)
        
        def download_and_update():
            try:
                import urllib.request
                import os
                import tempfile
                import shutil
                import zipfile
                import sys
                
                if cancel_flag['cancelled']:
                    return
                
                # 1. 下載檔案
                self.after(0, lambda: status_label.config(text="正在下載更新檔案..."))
                self.after(0, lambda: detail_label.config(text=f"來源：{filename}"))
                
                # 建立臨時目錄
                temp_dir = tempfile.mkdtemp(prefix="ChroLens_Update_")
                download_path = os.path.join(temp_dir, filename)
                
                def download_progress(block_num, block_size, total_size):
                    if cancel_flag['cancelled']:
                        raise Exception("使用者取消更新")
                    downloaded = block_num * block_size
                    if total_size > 0:
                        percent = min(100, int(downloaded * 50 / total_size))  # 下載佔 50%
                        self.after(0, lambda: progress_bar.config(value=percent))
                        self.after(0, lambda: percent_label.config(text=f"{percent}%"))
                        size_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        self.after(0, lambda: detail_label.config(
                            text=f"已下載：{size_mb:.1f} MB / {total_mb:.1f} MB"
                        ))
                
                urllib.request.urlretrieve(download_url, download_path, download_progress)
                
                if cancel_flag['cancelled']:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return
                
                # 2. 解壓檔案
                if filename.endswith('.zip'):
                    self.after(0, lambda: status_label.config(text="正在解壓縮檔案..."))
                    self.after(0, lambda: progress_bar.config(value=55))
                    self.after(0, lambda: percent_label.config(text="55%"))
                    self.after(0, lambda: detail_label.config(text="正在解壓縮更新檔案..."))
                    
                    extract_dir = os.path.join(temp_dir, "extracted")
                    os.makedirs(extract_dir, exist_ok=True)
                    
                    with zipfile.ZipFile(download_path, 'r') as zip_ref:
                        members = zip_ref.namelist()
                        total_files = len(members)
                        for idx, member in enumerate(members):
                            if cancel_flag['cancelled']:
                                shutil.rmtree(temp_dir, ignore_errors=True)
                                return
                            zip_ref.extract(member, extract_dir)
                            percent = 55 + int(idx * 15 / total_files)  # 解壓縮佔 15% (55-70%)
                            self.after(0, lambda p=percent: progress_bar.config(value=p))
                            self.after(0, lambda p=percent: percent_label.config(text=f"{p}%"))
                    
                    self.after(0, lambda: progress_bar.config(value=70))
                    self.after(0, lambda: percent_label.config(text="70%"))
                    
                    # 尋找更新檔案（ChroLens_Mimic 資料夾）
                    update_source_dir = None
                    for root, dirs, files in os.walk(extract_dir):
                        if 'ChroLens_Mimic' in dirs:
                            update_source_dir = os.path.join(root, 'ChroLens_Mimic')
                            break
                        # 如果直接就是 ChroLens_Mimic 內容
                        if any(f.endswith('.exe') and 'ChroLens' in f for f in files):
                            update_source_dir = root
                            break
                    
                    if not update_source_dir:
                        raise Exception("無法在壓縮檔中找到更新檔案")
                else:
                    update_source_dir = os.path.dirname(download_path)
                
                if cancel_flag['cancelled']:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return
                
                # 3. 備份當前程式
                self.after(0, lambda: status_label.config(text="正在備份當前版本..."))
                self.after(0, lambda: progress_bar.config(value=75))
                self.after(0, lambda: percent_label.config(text="75%"))
                self.after(0, lambda: detail_label.config(text="建立備份..."))
                
                if getattr(sys, 'frozen', False):
                    # 打包後的執行檔
                    current_exe_dir = os.path.dirname(sys.executable)
                    backup_dir = os.path.join(current_exe_dir, f"backup_{VERSION}")
                    
                    if os.path.exists(backup_dir):
                        shutil.rmtree(backup_dir, ignore_errors=True)
                    
                    # 備份整個目錄（除了 scripts 等使用者資料）
                    os.makedirs(backup_dir, exist_ok=True)
                    for item in os.listdir(current_exe_dir):
                        if item not in ['scripts', 'backup_', 'user_config.json', 'last_script.txt']:
                            src = os.path.join(current_exe_dir, item)
                            dst = os.path.join(backup_dir, item)
                            try:
                                if os.path.isdir(src):
                                    shutil.copytree(src, dst, ignore_dangling_symlinks=True)
                                else:
                                    shutil.copy2(src, dst)
                            except Exception as e:
                                print(f"備份 {item} 時發生錯誤: {e}")
                
                self.after(0, lambda: progress_bar.config(value=85))
                self.after(0, lambda: percent_label.config(text="85%"))
                
                # 4. 複製新版本檔案
                self.after(0, lambda: status_label.config(text="正在安裝新版本..."))
                self.after(0, lambda: detail_label.config(text="複製更新檔案..."))
                
                if getattr(sys, 'frozen', False):
                    # 複製所有檔案到當前目錄
                    files_to_copy = [f for f in os.listdir(update_source_dir)]
                    total_copy = len(files_to_copy)
                    
                    for idx, item in enumerate(files_to_copy):
                        if cancel_flag['cancelled']:
                            # 如果取消，還原備份
                            self.after(0, lambda: status_label.config(text="正在還原備份..."))
                            if os.path.exists(backup_dir):
                                for backup_item in os.listdir(backup_dir):
                                    src = os.path.join(backup_dir, backup_item)
                                    dst = os.path.join(current_exe_dir, backup_item)
                                    if os.path.isdir(src):
                                        if os.path.exists(dst):
                                            shutil.rmtree(dst, ignore_errors=True)
                                        shutil.copytree(src, dst)
                                    else:
                                        shutil.copy2(src, dst)
                            shutil.rmtree(temp_dir, ignore_errors=True)
                            return
                        
                        src = os.path.join(update_source_dir, item)
                        dst = os.path.join(current_exe_dir, item)
                        
                        # 跳過使用者資料
                        if item in ['scripts', 'user_config.json', 'last_script.txt']:
                            continue
                        
                        try:
                            if os.path.isdir(src):
                                if os.path.exists(dst):
                                    shutil.rmtree(dst, ignore_errors=True)
                                shutil.copytree(src, dst)
                            else:
                                # 特殊處理：如果是 exe 檔案，重新命名當前檔案
                                if item.endswith('.exe'):
                                    if os.path.exists(dst):
                                        os.rename(dst, dst + '.old')
                                shutil.copy2(src, dst)
                        except Exception as e:
                            print(f"複製 {item} 時發生錯誤: {e}")
                        
                        percent = 85 + int(idx * 10 / total_copy)  # 複製佔 10% (85-95%)
                        self.after(0, lambda p=percent: progress_bar.config(value=p))
                        self.after(0, lambda p=percent: percent_label.config(text=f"{p}%"))
                
                # 5. 清理臨時檔案
                self.after(0, lambda: status_label.config(text="正在清理暫存檔案..."))
                self.after(0, lambda: progress_bar.config(value=95))
                self.after(0, lambda: percent_label.config(text="95%"))
                self.after(0, lambda: detail_label.config(text="清理中..."))
                
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                # 6. 完成
                self.after(0, lambda: progress_bar.config(value=100))
                self.after(0, lambda: percent_label.config(text="100%"))
                self.after(0, lambda: status_label.config(text="更新完成！"))
                self.after(0, lambda: detail_label.config(text="準備重新啟動..."))
                self.after(0, lambda: cancel_btn.config(state='disabled'))
                
                # 延遲後詢問是否重啟
                self.after(1000, lambda: self._ask_restart(update_window, current_exe_dir if getattr(sys, 'frozen', False) else None))
                
            except Exception as e:
                if not cancel_flag['cancelled']:
                    self.after(0, lambda: update_window.destroy())
                    self.after(0, lambda: messagebox.showerror("更新失敗", f"自動更新失敗：{str(e)}\n\n請嘗試手動更新"))
                # 清理臨時檔案
                try:
                    if 'temp_dir' in locals():
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
        
        # 在背景執行緒中下載
        threading.Thread(target=download_and_update, daemon=True).start()
    
    def _ask_restart(self, update_window, exe_dir):
        """詢問是否重新啟動程式"""
        update_window.destroy()
        
        result = messagebox.askyesno(
            "更新完成",
            "程式已成功更新！\n\n"
            "是否立即重新啟動程式以套用更新？\n"
            "（選擇「否」將在下次啟動時套用）"
        )
        
        if result:
            import sys
            import subprocess
            
            if getattr(sys, 'frozen', False) and exe_dir:
                # 打包後的環境：啟動新的 exe
                exe_path = os.path.join(exe_dir, 'ChroLens_Mimic.exe')
                if os.path.exists(exe_path):
                    subprocess.Popen([exe_path], cwd=exe_dir)
                else:
                    messagebox.showerror("錯誤", "找不到更新後的執行檔")
                    return
            else:
                # 開發環境：重新執行 Python 腳本
                python = sys.executable
                script = os.path.abspath(__file__)
                subprocess.Popen([python, script])
            
            # 關閉當前程式
            self.quit()
            sys.exit(0)

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
        # 腳本管理按鈕
        if hasattr(self, 'rename_btn'):
            self.rename_btn.config(text=lang_map["重新命名"])
        if hasattr(self, 'select_target_btn'):
            self.select_target_btn.config(text=lang_map["選擇視窗"])
        if hasattr(self, 'mouse_mode_check'):
            self.mouse_mode_check.config(text=lang_map["滑鼠模式"])
        if hasattr(self, 'hotkey_capture_label'):
            self.hotkey_capture_label.config(text=lang_map["捕捉快捷鍵："])
        if hasattr(self, 'set_hotkey_btn'):
            self.set_hotkey_btn.config(text=lang_map["設定快捷鍵"])
        if hasattr(self, 'open_dir_btn'):
            self.open_dir_btn.config(text=lang_map["開啟資料夾"])
        if hasattr(self, 'del_script_btn'):
            self.del_script_btn.config(text=lang_map["刪除腳本"])
        if hasattr(self, 'edit_script_btn'):
            self.edit_script_btn.config(text=lang_map["腳本編輯器"])
        # Treeview 標題
        if hasattr(self, 'script_treeview'):
            self.script_treeview.heading("name", text=lang_map["腳本名稱"])
            self.script_treeview.heading("hotkey", text=lang_map["快捷鍵"])
        # 勾選框
        if hasattr(self, 'random_interval_check'):
            self.random_interval_check.config(text=lang_map["隨機"])
        if hasattr(self, 'main_auto_mini_check'):
            self.main_auto_mini_check.config(text=lang_map["自動切換"])
            # 更新 tooltip
            if hasattr(self, 'main_auto_mini_check'):
                # 移除舊的 tooltip 並建立新的
                try:
                    Tooltip(self.main_auto_mini_check, lang_map["勾選時，程式錄製/回放將自動轉換"])
                except:
                    pass
            self.random_interval_check.config(text=lang_map["隨機"])
        
        # 更新左側選單
        if hasattr(self, 'page_menu'):
            self.page_menu.delete(0, tk.END)
            self.page_menu.insert(0, lang_map["1.日誌顯示"])
            self.page_menu.insert(1, lang_map["2.腳本設定"])
            self.page_menu.insert(2, lang_map["3.整體設定"])
        
        self.update_idletasks()

    def change_language(self, event=None):
        lang = self.language_display_var.get()
        if lang == "Language" or not lang:
            return
        
        # 更新實際語言和顯示
        self.actual_language = lang
        self.language_var.set(lang)
        
        # 更新完後重置顯示為 "Language"
        self.after(100, lambda: self.language_display_var.set("Language"))
        
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
        # 腳本設定區按鈕
        if hasattr(self, 'rename_btn'):
            self.rename_btn.config(text=lang_map["重新命名"])
        if hasattr(self, 'select_target_btn'):
            self.select_target_btn.config(text=lang_map["選擇視窗"])
        if hasattr(self, 'mouse_mode_check'):
            self.mouse_mode_check.config(text=lang_map["滑鼠模式"])
        if hasattr(self, 'hotkey_capture_label'):
            self.hotkey_capture_label.config(text=lang_map["捕捉快捷鍵："])
        if hasattr(self, 'set_hotkey_btn'):
            self.set_hotkey_btn.config(text=lang_map["設定快捷鍵"])
        if hasattr(self, 'open_dir_btn'):
            self.open_dir_btn.config(text=lang_map["開啟資料夾"])
        if hasattr(self, 'del_script_btn'):
            self.del_script_btn.config(text=lang_map["刪除腳本"])
        if hasattr(self, 'edit_script_btn'):
            self.edit_script_btn.config(text=lang_map["腳本編輯器"])
        # Treeview 標題
        if hasattr(self, 'script_treeview'):
            self.script_treeview.heading("name", text=lang_map["腳本名稱"])
            self.script_treeview.heading("hotkey", text=lang_map["快捷鍵"])
        # 勾選框
        if hasattr(self, 'random_interval_check'):
            self.random_interval_check.config(text=lang_map["隨機"])
        if hasattr(self, 'main_auto_mini_check'):
            self.main_auto_mini_check.config(text=lang_map["自動切換"])
        # 更新左側選單
        if hasattr(self, 'page_menu'):
            self.page_menu.delete(0, tk.END)
            self.page_menu.insert(0, lang_map["1.日誌顯示"])
            self.page_menu.insert(1, lang_map["2.腳本設定"])
            self.page_menu.insert(2, lang_map["3.整體設定"])
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
            colored = []
            for idx, part in enumerate(time_str.split(":")):
                if part == "00" and idx < 2:
                    colored.append(("#888888", part))
                else:
                    colored.append(("#15D3BD", part))
            self.time_label_time.config(
                text=":".join([p[1] for p in colored]),
                foreground=colored[-1][0]
            )

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
        """更新回放時間顯示（強化版 - 確保時間計算準確）"""
        if self.playing:
            # 檢查 core_recorder 是否仍在播放
            if not getattr(self.core_recorder, 'playing', False):
                # 回放已結束，同步狀態
                self.playing = False
                self.log(f"[{format_time(time.time())}] 回放完成")
                
                # 釋放所有可能卡住的修飾鍵
                self._release_all_modifiers()
                
                self.update_time_label(0)
                self.update_countdown_label(0)
                self.update_total_time_label(0)
                # MiniMode倒數歸零
                if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
                    if hasattr(self, "mini_countdown_label"):
                        try:
                            lang = self.language_var.get()
                            lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                            self.mini_countdown_label.config(text=f"{lang_map['剩餘']}: 00:00:00")
                        except Exception:
                            pass
                return
            
            # 獲取當前事件索引（從 core_recorder）
            try:
                idx = getattr(self.core_recorder, "_current_play_index", 0)
            except:
                idx = 0
            
            # 計算已播放時間
            if idx == 0 or not self.events:
                elapsed = 0
            else:
                # 防止 index 超出範圍
                if idx > len(self.events):
                    idx = len(self.events)
                if idx > 0 and len(self.events) > 0:
                    elapsed = self.events[min(idx-1, len(self.events)-1)]['time'] - self.events[0]['time']
                else:
                    elapsed = 0
                    
            self.update_time_label(elapsed)
            
            # 計算單次剩餘時間
            if self.events and len(self.events) > 0:
                total = self.events[-1]['time'] - self.events[0]['time']
                remain = max(0, total - elapsed)
            else:
                remain = 0
            self.update_countdown_label(remain)
            
            # 計算總運作剩餘時間
            if hasattr(self, "_play_start_time") and self._play_start_time:
                elapsed_real = time.time() - self._play_start_time
                
                if self._repeat_time_limit:
                    # 使用時間限制模式
                    total_remain = max(0, self._repeat_time_limit - elapsed_real)
                else:
                    # 使用總播放時間模式
                    total_remain = max(0, self._total_play_time - elapsed_real)
                    
                self.update_total_time_label(total_remain)
                
                # 更新 MiniMode 倒數
                if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
                    if hasattr(self, "mini_countdown_label"):
                        try:
                            lang = self.language_var.get()
                            lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                            h = int(total_remain // 3600)
                            m = int((total_remain % 3600) // 60)
                            s = int(total_remain % 60)
                            time_str = f"{h:02d}:{m:02d}:{s:02d}"
                            self.mini_countdown_label.config(text=f"{lang_map['剩餘']}: {time_str}")
                        except Exception:
                            pass
            
            # 持續更新（100ms 刷新率）
            self.after(100, self._update_play_time)
        else:
            # 回放停止時重置所有時間顯示
            self.update_time_label(0)
            self.update_countdown_label(0)
            self.update_total_time_label(0)
            # MiniMode倒數歸零
            if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
                if hasattr(self, "mini_countdown_label"):
                    try:
                        lang = self.language_var.get()
                        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                        self.mini_countdown_label.config(text=f"{lang_map['剩餘']}: 00:00:00")
                    except Exception:
                        pass

    def start_record(self):
        """開始錄製"""
        if getattr(self.core_recorder, "recording", False):
            return
        
        # 自動切換到 MiniMode（如果勾選）
        if self.auto_mini_var.get() and not self.mini_mode_on:
            self.toggle_mini_mode()
        
        # 每次按開始錄製時，重置「可儲存到腳本」的參數為預設值
        try:
            self.reset_to_defaults()
        except Exception:
            pass
        # 確保 core_recorder 知道目標視窗設定
        if hasattr(self.core_recorder, 'set_target_window'):
            self.core_recorder.set_target_window(self.target_hwnd)
        
        # 記錄目標視窗的完整資訊（包含 DPI、解析度等）
        self.recorded_window_info = None
        if self.target_hwnd:
            try:
                window_info = get_window_info(self.target_hwnd)
                if window_info:
                    self.recorded_window_info = window_info
                    self.log(f"記錄視窗資訊:")
                    self.log(f"  大小: {window_info['size'][0]} x {window_info['size'][1]}")
                    self.log(f"  位置: ({window_info['position'][0]}, {window_info['position'][1]})")
                    self.log(f"  DPI 縮放: {window_info['dpi_scale']:.2f}x ({int(window_info['dpi_scale'] * 100)}%)")
                    self.log(f"  螢幕解析度: {window_info['screen_resolution'][0]} x {window_info['screen_resolution'][1]}")
            except Exception as e:
                self.log(f"無法記錄視窗資訊: {e}")
        
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
        
        # 自動切換到 MiniMode（如果勾選）
        if self.auto_mini_var.get() and not self.mini_mode_on:
            self.toggle_mini_mode()
        
        # 初始化座標偏移量（用於相對座標回放）
        self.playback_offset_x = 0
        self.playback_offset_y = 0
        
        # 檢查視窗狀態（大小、位置、DPI、解析度）
        if self.target_hwnd:
            try:
                from tkinter import messagebox
                
                # 獲取當前視窗資訊
                current_info = get_window_info(self.target_hwnd)
                if not current_info:
                    self.log("無法獲取視窗資訊")
                    return
                
                # 獲取錄製時的視窗資訊
                recorded_info = getattr(self, 'recorded_window_info', None)
                
                if recorded_info:
                    # 檢查各項差異
                    size_mismatch = (current_info['size'] != recorded_info['size'])
                    pos_mismatch = (current_info['position'] != recorded_info['position'])
                    dpi_mismatch = abs(current_info['dpi_scale'] - recorded_info['dpi_scale']) > 0.01
                    resolution_mismatch = (current_info['screen_resolution'] != recorded_info['screen_resolution'])
                    
                    if size_mismatch or pos_mismatch or dpi_mismatch or resolution_mismatch:
                        # 創建詳細的對話框
                        dialog = tk.Toplevel(self)
                        dialog.title("視窗狀態檢測")
                        dialog.geometry("600x500")
                        dialog.resizable(True, True)
                        dialog.grab_set()
                        dialog.transient(self)
                        set_window_icon(dialog)
                        
                        # 居中顯示
                        dialog.update_idletasks()
                        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
                        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
                        dialog.geometry(f"+{x}+{y}")
                        
                        # 主框架
                        main_frame = tb.Frame(dialog)
                        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                        
                        # 標題
                        title_label = tb.Label(main_frame, 
                            text="⚠️ 偵測到視窗狀態不同！", 
                            font=("Microsoft JhengHei", 12, "bold"))
                        title_label.pack(pady=(0, 15))
                        
                        # 訊息內容
                        msg_frame = tb.Frame(main_frame)
                        msg_frame.pack(fill="both", expand=True)
                        
                        msg = "📊 錄製時 vs 目前狀態比較：\n\n"
                        
                        if size_mismatch:
                            msg += f"🖼️ 視窗大小：\n"
                            msg += f"   錄製時: {recorded_info['size'][0]} x {recorded_info['size'][1]}\n"
                            msg += f"   目前: {current_info['size'][0]} x {current_info['size'][1]}\n\n"
                        
                        if pos_mismatch:
                            msg += f"📍 視窗位置：\n"
                            msg += f"   錄製時: ({recorded_info['position'][0]}, {recorded_info['position'][1]})\n"
                            msg += f"   目前: ({current_info['position'][0]}, {current_info['position'][1]})\n\n"
                        
                        if dpi_mismatch:
                            msg += f"🔍 DPI 縮放：\n"
                            msg += f"   錄製時: {recorded_info['dpi_scale']:.2f}x ({int(recorded_info['dpi_scale'] * 100)}%)\n"
                            msg += f"   目前: {current_info['dpi_scale']:.2f}x ({int(current_info['dpi_scale'] * 100)}%)\n\n"
                        
                        if resolution_mismatch:
                            msg += f"🖥️ 螢幕解析度：\n"
                            msg += f"   錄製時: {recorded_info['screen_resolution'][0]} x {recorded_info['screen_resolution'][1]}\n"
                            msg += f"   目前: {current_info['screen_resolution'][0]} x {current_info['screen_resolution'][1]}\n\n"
                        
                        msg_label = tb.Label(msg_frame, text=msg, font=("Microsoft JhengHei", 10), justify="left")
                        msg_label.pack(anchor="w", padx=10, pady=10)
                        
                        # 分隔線
                        separator = tb.Separator(main_frame, orient="horizontal")
                        separator.pack(fill="x", pady=10)
                        
                        # 使用者選擇
                        user_choice = {"action": None}
                        
                        def on_force_adjust():
                            user_choice["action"] = "adjust"
                            dialog.destroy()
                        
                        def on_auto_scale():
                            user_choice["action"] = "auto_scale"
                            dialog.destroy()
                        
                        def on_cancel():
                            user_choice["action"] = "cancel"
                            dialog.destroy()
                        
                        btn_frame = tb.Frame(main_frame)
                        btn_frame.pack(fill="x", pady=10)
                        
                        tb.Button(btn_frame, text="🔧 強制歸位（調整視窗）", bootstyle=PRIMARY, 
                                 command=on_force_adjust, width=25).pack(pady=5, fill="x")
                        
                        tb.Button(btn_frame, text="✨ 智能適配（推薦）", bootstyle=SUCCESS, 
                                 command=on_auto_scale, width=25).pack(pady=5, fill="x")
                        
                        tb.Button(btn_frame, text="❌ 取消回放", bootstyle=DANGER, 
                                 command=on_cancel, width=25).pack(pady=5, fill="x")
                        
                        # 添加說明
                        info_label = tb.Label(main_frame, 
                            text="💡 提示：「智能適配」會自動調整座標以適應當前環境\n"
                                 "適用於不同解析度、DPI 縮放和視窗大小", 
                            font=("Microsoft JhengHei", 9), 
                            foreground="#666",
                            wraplength=550)
                        info_label.pack(pady=(10, 0))
                        
                        dialog.wait_window()
                        
                        # 處理使用者選擇
                        if user_choice["action"] == "cancel":
                            self.log("已取消回放")
                            return
                        elif user_choice["action"] == "adjust":
                            # 強制歸位
                            try:
                                target_width, target_height = recorded_info['size']
                                target_x, target_y = recorded_info['position']
                                
                                win32gui.SetWindowPos(
                                    self.target_hwnd,
                                    0,  # HWND_TOP
                                    target_x, target_y,
                                    target_width, target_height,
                                    0x0240  # SWP_SHOWWINDOW | SWP_ASYNCWINDOWPOS
                                )
                                
                                self.log(f"已調整視窗至錄製時狀態")
                                self.log("將在 2 秒後開始回放...")
                                
                                # 延遲 2 秒後繼續
                                self.after(2000, self._continue_play_record)
                                return
                            except Exception as e:
                                self.log(f"無法調整視窗: {e}")
                        elif user_choice["action"] == "auto_scale":
                            # 智能適配模式
                            self.log(f"使用智能適配模式進行回放")
                            self.log(f"將自動調整座標以適應當前環境")
                            # 設定縮放比例（用於後續座標轉換）
                            self._scale_ratio = {
                                'x': current_info['size'][0] / recorded_info['size'][0] if recorded_info['size'][0] > 0 else 1.0,
                                'y': current_info['size'][1] / recorded_info['size'][1] if recorded_info['size'][1] > 0 else 1.0,
                                'dpi': current_info['dpi_scale'] / recorded_info['dpi_scale'] if recorded_info['dpi_scale'] > 0 else 1.0
                            }
                            self.log(f"縮放比例 - X: {self._scale_ratio['x']:.3f}, Y: {self._scale_ratio['y']:.3f}, DPI: {self._scale_ratio['dpi']:.3f}")
            except Exception as e:
                self.log(f"檢查視窗狀態時發生錯誤: {e}")
                import traceback
                self.log(f"錯誤詳情: {traceback.format_exc()}")
        
        # 直接開始回放
        self._continue_play_record()
    
    def _continue_play_record(self):
        """實際執行回放的內部方法（支援智能縮放）"""
        # 獲取當前視窗位置（如果有目標視窗）
        current_window_x = 0
        current_window_y = 0
        if self.target_hwnd:
            try:
                import win32gui
                rect = win32gui.GetWindowRect(self.target_hwnd)
                current_window_x, current_window_y = rect[0], rect[1]
            except Exception as e:
                self.log(f"無法獲取視窗位置: {e}")
        
        # 檢查是否有縮放比例設定（智能適配模式）
        has_scale_ratio = hasattr(self, '_scale_ratio') and self._scale_ratio
        
        # 轉換事件座標
        adjusted_events = []
        scaled_count = 0  # 記錄縮放事件數量
        
        for event in self.events:
            event_copy = event.copy()
            
            # 處理滑鼠事件的座標
            if event.get('type') == 'mouse' and 'x' in event and 'y' in event:
                # 檢查是否為視窗相對座標
                if event.get('relative_to_window', False):
                    # 取得相對座標
                    rel_x = event['x']
                    rel_y = event['y']
                    
                    # 如果有智能縮放，應用縮放比例
                    if has_scale_ratio:
                        # 應用視窗大小縮放
                        rel_x = int(rel_x * self._scale_ratio['x'])
                        rel_y = int(rel_y * self._scale_ratio['y'])
                        scaled_count += 1
                    
                    # 轉換為當前螢幕絕對座標
                    event_copy['x'] = rel_x + current_window_x
                    event_copy['y'] = rel_y + current_window_y
                else:
                    # 螢幕絕對座標，不做轉換
                    pass
            
            adjusted_events.append(event_copy)
        
        # 顯示縮放資訊（僅顯示一次）
        if has_scale_ratio and scaled_count > 0:
            self.log(f"[智能適配] 已縮放 {scaled_count} 個座標事件")
            # 清除縮放比例（避免影響下次回放）
            del self._scale_ratio
        
        # 設定 core_recorder 的事件
        self.core_recorder.events = adjusted_events
        
        # 設定滑鼠模式
        if hasattr(self.core_recorder, 'set_mouse_mode'):
            mouse_mode = self.mouse_mode_var.get()
            self.core_recorder.set_mouse_mode(mouse_mode)
            if mouse_mode:
                self.log("回放模式：滑鼠模式（將控制真實滑鼠游標）")
            else:
                self.log("回放模式：後台模式（智能自動適應）")
        
        if self.target_hwnd and any(e.get('relative_to_window', False) for e in self.events):
            relative_count = sum(1 for e in self.events if e.get('relative_to_window', False))
            self.log(f"[座標轉換] {relative_count} 個視窗相對座標 → 當前螢幕座標")

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

        # 初始化事件索引（用於 UI 更新）
        self._current_play_index = 0

        def on_event(event):
            """回放事件的回調函數（確保索引同步更新）"""
            # 從 core_recorder 獲取最新索引
            try:
                idx = getattr(self.core_recorder, "_current_play_index", 0)
                self._current_play_index = idx
            except:
                pass

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
            # 確保 core_recorder 的 recording 標記也設為 False
            if hasattr(self.core_recorder, 'recording'):
                self.core_recorder.recording = False
            self.core_recorder.stop_record()
            self.events = self.core_recorder.events
            stopped = True
            self.log(f"[{format_time(time.time())}] 停止錄製，共 {len(self.events)} 筆事件。")
            self._wait_record_thread_finish()

        if self.playing:
            self.playing = False
            self.core_recorder.stop_play()
            stopped = True
            self.log(f"[{format_time(time.time())}] 停止回放。")
            
            # 釋放所有可能卡住的修飾鍵
            self._release_all_modifiers()

        if not stopped:
            self.log(f"[{format_time(time.time())}] 無進行中動作可停止。")

        self.update_time_label(0)
        self.update_countdown_label(0)
        self.update_total_time_label(0)
        self._update_play_time()
        self._update_record_time()
    
    def _release_all_modifiers(self):
        """釋放所有修飾鍵以防止卡住"""
        try:
            import keyboard
            # 釋放常見的修飾鍵
            modifiers = ['ctrl', 'shift', 'alt', 'win']
            for mod in modifiers:
                try:
                    keyboard.release(mod)
                except:
                    pass
            self.log("[系統] 已釋放所有修飾鍵")
        except Exception as e:
            self.log(f"[警告] 釋放修飾鍵時發生錯誤: {e}")

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
            
            # 若使用者選定了目標視窗，處理視窗相對座標
            if getattr(self, "target_hwnd", None):
                try:
                    rect = win32gui.GetWindowRect(self.target_hwnd)
                    l, t, r, b = rect
                    window_x, window_y = l, t
                    
                    # 轉換為視窗內相對座標並過濾視窗外的事件
                    converted_events = []
                    for e in self.events:
                        if not isinstance(e, dict):
                            continue
                        
                        # 檢查是否有座標
                        x = y = None
                        if 'x' in e and 'y' in e:
                            x, y = e.get('x'), e.get('y')
                        elif 'pos' in e and isinstance(e.get('pos'), (list, tuple)) and len(e.get('pos')) >= 2:
                            x, y = e.get('pos')[0], e.get('pos')[1]
                        
                        # 若找不到座標則視為非滑鼠事件，直接保留
                        if x is None or y is None:
                            converted_events.append(e)
                            continue
                        
                        # 檢查是否在視窗內
                        if (l <= int(x) <= r) and (t <= int(y) <= b):
                            # 轉換為視窗內相對座標
                            event_copy = e.copy()
                            event_copy['x'] = int(x) - window_x
                            event_copy['y'] = int(y) - window_y
                            # 標記這是視窗內相對座標
                            event_copy['relative_to_window'] = True
                            converted_events.append(event_copy)
                    
                    self.log(f"[{format_time(time.time())}] 錄製完成，原始事件數：{len(self.events)}，轉換為視窗相對座標：{len(converted_events)}")
                    self.events = converted_events
                except Exception as ex:
                    self.log(f"[{format_time(time.time())}] 轉換視窗相對座標時發生錯誤: {ex}")
            else:
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
        # theme_var 已被移除，使用當前 theme
        current_theme = self.style.theme_use()
        self.user_config["skin"] = current_theme
        # 確保儲存時加上副檔名
        script_name = self.script_var.get()
        if script_name and not script_name.endswith('.json'):
            script_name = script_name + '.json'
        self.user_config["last_script"] = script_name
        self.user_config["repeat"] = self.repeat_var.get()
        self.user_config["speed"] = self.speed_var.get()
        self.user_config["script_dir"] = self.script_dir
        self.user_config["language"] = self.language_var.get()
        self.user_config["repeat_time"] = self.repeat_time_var.get()
        self.user_config["hotkey_map"] = self.hotkey_map
        self.user_config["auto_mini_mode"] = self.auto_mini_var.get()  # 儲存自動切換設定
        self.user_config["mouse_mode"] = self.mouse_mode_var.get()  # 儲存滑鼠模式設定
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
            # 儲存完整的視窗資訊（包含 DPI、解析度等）
            if hasattr(self, 'recorded_window_info') and self.recorded_window_info:
                settings["window_info"] = self.recorded_window_info
                self.log(f"[儲存] 視窗資訊已包含在腳本中")
            
            filename = sio_auto_save_script(self.script_dir, self.events, settings)
            # 去除 .json 副檔名以顯示在 UI
            display_name = os.path.splitext(filename)[0] if filename.endswith('.json') else filename
            self.log(f"[{format_time(time.time())}] 自動存檔：{filename}，事件數：{len(self.events)}")
            self.refresh_script_list()
            self.refresh_script_listbox()  # 同時更新腳本列表
            self.script_var.set(display_name)  # 使用去除副檔名的名稱
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(filename)  # 仍然儲存完整檔名以供讀取
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
            self.log("【腳本設定已更新】提示：快捷鍵將使用這些參數回放")
        except Exception as ex:
            self.log(f"儲存腳本設定失敗: {ex}")

    # --- 讀取腳本設定 ---
    def on_script_selected(self, event=None):
        script = self.script_var.get()
        if script:
            # 如果沒有副檔名，加上 .json
            if not script.endswith('.json'):
                script_file = script + '.json'
            else:
                script_file = script
            
            path = os.path.join(self.script_dir, script_file)
            try:
                data = sio_load_script(path)
                self.events = data.get("events", [])
                settings = data.get("settings", {})
                
                # 檢查是否為視覺化編輯器創建的腳本（有 script_actions 但 events 為空）
                if not self.events and "script_actions" in settings and settings["script_actions"]:
                    self.log("偵測到視覺化編輯器腳本，正在轉換為事件格式...")
                    self.events = self._actions_to_events(settings["script_actions"])
                    self.log(f"轉換完成：{len(self.events)} 筆事件")
                
                # 恢復參數
                self.speed_var.set(settings.get("speed", "100"))
                self.repeat_var.set(settings.get("repeat", "1"))
                self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
                self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
                self.random_interval_var.set(settings.get("random_interval", False))
                
                # 讀取視窗資訊（新格式優先）
                if "window_info" in settings:
                    self.recorded_window_info = settings["window_info"]
                    self.log(f"[載入] 視窗資訊:")
                    self.log(f"  大小: {self.recorded_window_info['size'][0]} x {self.recorded_window_info['size'][1]}")
                    self.log(f"  DPI: {self.recorded_window_info['dpi_scale']:.2f}x ({int(self.recorded_window_info['dpi_scale'] * 100)}%)")
                    self.log(f"  解析度: {self.recorded_window_info['screen_resolution'][0]} x {self.recorded_window_info['screen_resolution'][1]}")
                elif "window_size" in settings:
                    # 兼容舊格式
                    self.recorded_window_info = {
                        "size": tuple(settings["window_size"]),
                        "position": (0, 0),
                        "dpi_scale": 1.0,
                        "screen_resolution": (1920, 1080),
                        "client_size": tuple(settings["window_size"])
                    }
                    self.log(f"[載入] 舊格式視窗資訊（已轉換）")
                else:
                    self.recorded_window_info = None
                
                # 顯示檔名時去除副檔名
                display_name = os.path.splitext(script_file)[0]
                self.log(f"[{format_time(time.time())}] 腳本已載入：{display_name}，共 {len(self.events)} 筆事件。")
                self.log("【腳本設定已載入】")  # 新增：日誌顯示
                
                # 儲存完整檔名到 last_script.txt
                with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                    f.write(script_file)
                
                # 讀取腳本後，計算並顯示總運作時間
                if self.events:
                    # 單次時間
                    single_time = self.events[-1]['time'] - self.events[0]['time']
                    self.update_countdown_label(single_time)
                    
                    # 計算總運作時間
                    try:
                        speed_val = int(self.speed_var.get())
                        speed = speed_val / 100.0
                    except:
                        speed = 1.0
                    
                    try:
                        repeat = int(self.repeat_var.get())
                    except:
                        repeat = 1
                    
                    repeat_time_sec = self._parse_time_to_seconds(self.repeat_time_var.get())
                    repeat_interval_sec = self._parse_time_to_seconds(self.repeat_interval_var.get())
                    
                    # 計算總時間
                    single_adjusted = single_time / speed
                    if repeat_time_sec > 0:
                        total_time = repeat_time_sec
                    else:
                        total_time = single_adjusted * repeat + repeat_interval_sec * max(0, repeat - 1)
                    
                    self.update_total_time_label(total_time)
                else:
                    self.update_countdown_label(0)
                    self.update_total_time_label(0)
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
                # 確保有副檔名
                if not last_script.endswith('.json'):
                    last_script = last_script + '.json'
                
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
                        
                        # 讀取視窗資訊（新格式優先）
                        if "window_info" in settings:
                            self.recorded_window_info = settings["window_info"]
                        elif "window_size" in settings:
                            # 兼容舊格式
                            self.recorded_window_info = {
                                "size": tuple(settings["window_size"]),
                                "position": (0, 0),
                                "dpi_scale": 1.0,
                                "screen_resolution": (1920, 1080),
                                "client_size": tuple(settings["window_size"])
                            }
                        else:
                            self.recorded_window_info = None
                        
                        # 顯示時去除副檔名
                        display_name = os.path.splitext(last_script)[0]
                        self.script_var.set(display_name)
                        self.log(f"[{format_time(time.time())}] 自動載入腳本：{display_name}，共 {len(self.events)} 筆事件。")
                    except Exception as ex:
                        self.log(f"載入上次腳本失敗: {ex}")
                        self.random_interval_var.set(settings.get("random_interval", False))
                        self.script_var.set(last_script)
                        self.log(f"[{format_time(time.time())}] 已自動載入上次腳本：{last_script}，共 {len(self.events)} 筆事件。")
                    except Exception as ex:
                        self.log(f"載入上次腳本失敗: {ex}")

    def update_mouse_pos(self):
        try:
            import mouse
            x, y = mouse.get_position()
            self.mouse_pos_label.config(text=f"(X={x},Y={y})")
        except Exception:
            self.mouse_pos_label.config(text="(X=?,Y=?)")
        self.after(100, self.update_mouse_pos)

    def rename_script(self):
        old_name = self.script_var.get()
        new_name = self.rename_var.get().strip()
        if not old_name or not new_name:
            self.log(f"[{format_time(time.time())}] 請選擇腳本並輸入新名稱。")
            return
        
        # 確保 old_name 有副檔名
        if not old_name.endswith('.json'):
            old_name += '.json'
        
        # 確保 new_name 有副檔名
        if not new_name.endswith('.json'):
            new_name += '.json'
        
        old_path = os.path.join(self.script_dir, old_name)
        new_path = os.path.join(self.script_dir, new_name)
        
        if not os.path.exists(old_path):
            self.log(f"[{format_time(time.time())}] 找不到原始腳本檔案。")
            return
        
        if os.path.exists(new_path):
            self.log(f"[{format_time(time.time())}] 檔案已存在，請換個名稱。")
            return
        
        try:
            os.rename(old_path, new_path)
            # 更新 last_script.txt
            new_display_name = os.path.splitext(new_name)[0]
            self.log(f"[{format_time(time.time())}] 腳本已更名為：{new_display_name}")
            self.refresh_script_list()
            self.refresh_script_listbox()
            # 更新選擇（顯示時不含副檔名）
            self.script_var.set(new_display_name)
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
        win.geometry("350x380")  # 增大尺寸
        win.resizable(True, True)  # 允許調整大小
        win.minsize(300, 320)  # 設置最小尺寸
        # 設定視窗圖示
        set_window_icon(win)

        # 建立主框架
        main_frame = tb.Frame(win)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

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
            """強化版快捷鍵捕捉"""
            keys = []
            
            # 檢測修飾鍵
            if event.state & 0x0001 or event.keysym in ('Shift_L', 'Shift_R'):  # Shift
                keys.append("shift")
            if event.state & 0x0004 or event.keysym in ('Control_L', 'Control_R'):  # Ctrl
                keys.append("ctrl")
            if event.state & 0x0008 or event.state & 0x20000 or event.keysym in ('Alt_L', 'Alt_R'):  # Alt
                keys.append("alt")
            if event.state & 0x0040:  # Win key
                keys.append("win")
            
            # 取得主按鍵
            key_name = event.keysym.lower()
            
            # 特殊按鍵映射
            special_keys = {
                'return': 'enter',
                'prior': 'page_up',
                'next': 'page_down',
                'backspace': 'backspace',
                'delete': 'delete',
                'insert': 'insert',
                'home': 'home',
                'end': 'end',
                'tab': 'tab',
                'escape': 'esc',
                'space': 'space',
                'caps_lock': 'caps_lock',
                'num_lock': 'num_lock',
                'scroll_lock': 'scroll_lock',
                'print': 'print_screen',
                'pause': 'pause',
            }
            
            # 功能鍵 F1-F24
            if key_name.startswith('f') and key_name[1:].isdigit():
                key_name = key_name  # F1-F24 保持原樣
            # 方向鍵
            elif key_name in ('up', 'down', 'left', 'right'):
                key_name = key_name
            # 特殊按鍵
            elif key_name in special_keys:
                key_name = special_keys[key_name]
            # 修飾鍵本身不加入（已經在 keys 列表中）
            elif key_name in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r", "win_l", "win_r"):
                # 如果只按修飾鍵，顯示修飾鍵本身
                if not keys:
                    keys.append(key_name.replace('_l', '').replace('_r', ''))
                key_name = None
            # 數字鍵盤
            elif key_name.startswith('kp_'):
                key_name = key_name.replace('kp_', 'num_')
            
            # 組合按鍵字串
            if key_name and key_name not in [k for k in keys]:
                keys.append(key_name)
            
            # 去除重複並排序（ctrl, alt, shift, win, 主鍵）
            modifier_order = {'ctrl': 0, 'alt': 1, 'shift': 2, 'win': 3}
            modifiers = [k for k in keys if k in modifier_order]
            main_key = [k for k in keys if k not in modifier_order]
            
            modifiers.sort(key=lambda x: modifier_order[x])
            result = modifiers + main_key
            
            if result:
                var.set("+".join(result))
            
            return "break"

        def on_entry_focus_in(event, var):
            var.set("輸入按鍵")

        def on_entry_focus_out(event, key, var):
            if var.get() == "輸入按鍵" or not var.get():
                var.set(self.hotkey_map[key])

        for key, label in labels.items():
            entry_frame = tb.Frame(main_frame)
            entry_frame.pack(fill="x", pady=5)
            
            tb.Label(entry_frame, text=label, font=("Microsoft JhengHei", 11), width=12, anchor="w").pack(side="left", padx=5)
            var = tk.StringVar(value=self.hotkey_map[key])
            entry = tb.Entry(entry_frame, textvariable=var, font=("Consolas", 10), state="normal")
            entry.pack(side="left", fill="x", expand=True, padx=5)
            vars[key] = var
            entries[key] = entry
            # 強化版：只用 KeyPress 事件
            entry.bind("<KeyPress>", lambda e, k=key, v=var: on_entry_key(e, k, v))
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
            self.save_config()  # 新增這行,確保儲存
            self.log("快捷鍵設定已更新。")
            win.destroy()

        # 按鈕框架
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill="x", pady=15)
        tb.Button(btn_frame, text="儲存", command=save_and_apply, width=15, bootstyle=SUCCESS).pack(pady=5)

    # 不再需要 _make_hotkey_entry_handler

    def _register_hotkeys(self):
        import keyboard
        # 先移除所有已註冊的快捷鍵
        for handler in self._hotkey_handlers.values():
            try:
                keyboard.remove_hotkey(handler)
            except Exception as ex:
                pass  # 忽略移除錯誤
        self._hotkey_handlers.clear()
        
        # 重新註冊快捷鍵
        for key, hotkey in self.hotkey_map.items():
            try:
                # 對於 stop 使用 suppress=True 確保能攔截
                use_suppress = (key == "stop")
                handler = keyboard.add_hotkey(
                    hotkey,
                    getattr(self, {
                        "start": "start_record",
                        "pause": "toggle_pause",
                        "stop": "stop_all",
                        "play": "play_record",
                        "mini": "toggle_mini_mode"
                    }[key]),
                    suppress=use_suppress,  # stop 使用 suppress=True
                    trigger_on_release=False
                )
                self._hotkey_handlers[key] = handler
                self.log(f"已註冊快捷鍵: {hotkey} → {key}")
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")

    def _register_script_hotkeys(self):
        """註冊所有腳本的快捷鍵（而非僅當前選中的）"""
        # 先清除所有已註冊的腳本快捷鍵
        for info in self._script_hotkey_handlers.values():
            try:
                keyboard.remove_hotkey(info.get("handler"))
            except Exception as ex:
                pass
        self._script_hotkey_handlers.clear()

        # 掃描所有腳本並註冊快捷鍵
        if not os.path.exists(self.script_dir):
            return
        
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        for script in scripts:
            path = os.path.join(self.script_dir, script)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 嘗試從 settings 讀取，如果沒有則從根讀取（兼容舊格式）
                hotkey = ""
                if "settings" in data and "script_hotkey" in data["settings"]:
                    hotkey = data["settings"]["script_hotkey"]
                elif "script_hotkey" in data:
                    hotkey = data["script_hotkey"]
                
                if hotkey:
                    # 為每個腳本註冊快捷鍵，使用 functools.partial 確保正確捕獲參數
                    from functools import partial
                    handler = keyboard.add_hotkey(
                        hotkey,
                        partial(self._play_script_by_hotkey, script),
                        suppress=False,
                        trigger_on_release=False
                    )
                    self._script_hotkey_handlers[script] = {
                        "handler": handler,
                        "script": script,
                        "hotkey": hotkey
                    }
                    self.log(f"已註冊腳本快捷鍵: {hotkey} → {script}")
            except Exception as ex:
                self.log(f"註冊腳本快捷鍵失敗 ({script}): {ex}")

    def _play_script_by_hotkey(self, script):
        """透過快捷鍵觸發腳本回放（使用腳本儲存的參數）"""
        if self.playing or self.recording:
            self.log(f"目前正在錄製或回放中，無法執行腳本：{script}")
            return
        
        path = os.path.join(self.script_dir, script)
        if not os.path.exists(path):
            self.log(f"找不到腳本檔案：{script}")
            return
        
        try:
            # 載入腳本及其設定
            data = sio_load_script(path)
            self.events = data.get("events", [])
            settings = data.get("settings", {})
            
            # 套用腳本的參數設定
            self.speed_var.set(settings.get("speed", "100"))
            self.repeat_var.set(settings.get("repeat", "1"))
            self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
            self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
            self.random_interval_var.set(settings.get("random_interval", False))
            
            # 更新腳本選單顯示
            self.script_var.set(script)
            
            self.log(f"透過快捷鍵載入腳本：{script}")
            
            # 開始回放
            self.play_record()
            
        except Exception as ex:
            self.log(f"載入並執行腳本失敗：{ex}")

    def _update_hotkey_labels(self):
        self.btn_start.config(text=f"開始錄製 ({self.hotkey_map['start']})")
        self.btn_pause.config(text=f"暫停/繼續 ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=f"停止 ({self.hotkey_map['stop']})")
        self.btn_play.config(text=f"回放 ({self.hotkey_map['play']})")
        # MiniMode 按鈕同步更新
        if hasattr(self, "mini_btns") and self.mini_btns:
            for btn, icon, key in self.mini_btns:
                btn.config(text=f"{icon} {self.hotkey_map[key]}")

    def toggle_mini_mode(self):
        # 切換 MiniMode 狀態（參考 ChroLens_Mimic2.5.py 的 TinyMode）
        if not hasattr(self, "mini_mode_on"):
            self.mini_mode_on = False
        if not hasattr(self, "mini_window"):
            self.mini_window = None
        
        self.mini_mode_on = not self.mini_mode_on
        
        if self.mini_mode_on:
            if self.mini_window is None or not self.mini_window.winfo_exists():
                self.mini_window = tb.Toplevel(self)
                self.mini_window.title("ChroLens_Mimic MiniMode")
                self.mini_window.geometry("810x40")
                self.mini_window.overrideredirect(True)
                self.mini_window.resizable(False, False)
                self.mini_window.attributes("-topmost", True)
                # 設定視窗圖示
                set_window_icon(self.mini_window)
                
                self.mini_btns = []
                
                # 新增倒數Label（多語系）
                lang = self.language_var.get()
                lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                self.mini_countdown_label = tb.Label(
                    self.mini_window,
                    text=f"{lang_map['剩餘']}: 00:00:00",
                    font=("Microsoft JhengHei", 12),
                    foreground="#FF95CA", width=13
                )
                self.mini_countdown_label.grid(row=0, column=0, padx=2, pady=5)
                
                # 拖曳功能
                self.mini_window.bind("<ButtonPress-1>", self._start_move_mini)
                self.mini_window.bind("<B1-Motion>", self._move_mini)
                
                btn_defs = [
                    ("⏺", "start"),
                    ("⏸", "pause"),
                    ("⏹", "stop"),
                    ("▶︎", "play"),
                    ("⤴︎", "mini")
                ]
                
                for i, (icon, key) in enumerate(btn_defs):
                    command_map = {
                        "start": "start_record",
                        "pause": "toggle_pause",
                        "stop": "stop_all",
                        "play": "play_record",
                        "mini": "toggle_mini_mode"
                    }
                    btn = tb.Button(
                        self.mini_window,
                        text=f"{icon} {self.hotkey_map[key]}",
                        width=7, style="My.TButton",
                        command=getattr(self, command_map[key])
                    )
                    btn.grid(row=0, column=i+1, padx=2, pady=5)
                    self.mini_btns.append((btn, icon, key))
                
                # 添加自動切換勾選框
                self.mini_auto_check = tb.Checkbutton(
                    self.mini_window,
                    text=lang_map["自動切換"],
                    variable=self.auto_mini_var,
                    style="My.TCheckbutton"
                )
                self.mini_auto_check.grid(row=0, column=len(btn_defs)+1, padx=5, pady=5)
                
                # 添加 Tooltip
                Tooltip(self.mini_auto_check, lang_map["勾選時，程式錄製/回放將自動轉換"])
                
                self.mini_window.protocol("WM_DELETE_WINDOW", self._close_mini_mode)
                self.withdraw()
        else:
            self._close_mini_mode()
    
    def _close_mini_mode(self):
        """關閉 MiniMode"""
        if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
            self.mini_window.destroy()
        self.mini_window = None
        self.deiconify()
        self.mini_mode_on = False
    
    def _start_move_mini(self, event):
        """開始拖曳 MiniMode 視窗"""
        self._mini_x = event.x
        self._mini_y = event.y
    
    def _move_mini(self, event):
        """拖曳 MiniMode 視窗"""
        if hasattr(self, 'mini_window') and self.mini_window:
            x = self.mini_window.winfo_x() + event.x - self._mini_x
            y = self.mini_window.winfo_y() + event.y - self._mini_y
            self.mini_window.geometry(f"+{x}+{y}")

    def use_default_script_dir(self):
        self.script_dir = SCRIPTS_DIR
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        self.refresh_script_list()
        self.save_config()

        # 開啟資料夾
        os.startfile(self.script_dir)
    
    def _on_script_combo_click(self, event=None):
        """當點擊腳本下拉選單時，即時刷新列表"""
        self.refresh_script_list()

    def refresh_script_list(self):
        """刷新腳本下拉選單內容（去除副檔名顯示）"""
        if not os.path.exists(self.script_dir):
            os.makedirs(self.script_dir)
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        # 顯示時去除副檔名，但實際儲存時仍使用完整檔名
        display_scripts = [os.path.splitext(f)[0] for f in scripts]
        self.script_combo['values'] = display_scripts
        
        # 若目前選擇的腳本不存在，則清空
        current = self.script_var.get()
        if current.endswith('.json'):
            current_display = os.path.splitext(current)[0]
        else:
            current_display = current
        
        if current_display not in display_scripts:
            self.script_var.set('')
        else:
            self.script_var.set(current_display)

    def refresh_script_listbox(self):
        """刷新腳本設定區左側列表（顯示檔名和快捷鍵）"""
        try:
            # 清空 Treeview
            for item in self.script_treeview.get_children():
                self.script_treeview.delete(item)
            
            if not os.path.exists(self.script_dir):
                os.makedirs(self.script_dir)
            
            scripts = sorted([f for f in os.listdir(self.script_dir) if f.endswith('.json')])
            
            # 建立顯示列表
            for script_file in scripts:
                # 去除副檔名
                script_name = os.path.splitext(script_file)[0]
                
                # 讀取快捷鍵
                hotkey = ""
                try:
                    path = os.path.join(self.script_dir, script_file)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "settings" in data and "script_hotkey" in data["settings"]:
                            hotkey = data["settings"]["script_hotkey"]
                except Exception:
                    pass
                
                # 插入到 Treeview（兩欄）
                self.script_treeview.insert("", "end", values=(script_name, hotkey if hotkey else ""))
                
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
            self.script_setting_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            # 額外刷新腳本列表
            self.refresh_script_listbox()
        elif idx == 2:
            self.global_setting_frame.place(x=0, y=0, anchor="nw")  # 靠左上角

    def on_script_treeview_select(self, event=None):
        """處理腳本 Treeview 選擇事件"""
        try:
            selection = self.script_treeview.selection()
            if not selection:
                return
            
            # 取得選中項目的值
            item = selection[0]
            values = self.script_treeview.item(item, "values")
            if not values:
                return
            
            script_name = values[0]  # 腳本名稱（不含副檔名）
            
            # 加回 .json 副檔名
            script_file = script_name + ".json"
            
            # 更新下拉選單
            self.script_var.set(script_name)  # 下拉選單只顯示名稱
            
            # 載入腳本資訊
            path = os.path.join(self.script_dir, script_file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 顯示快捷鍵
                if "settings" in data:
                    hotkey = data["settings"].get("script_hotkey", "")
                    self.hotkey_capture_var.set(hotkey)
                    
                    # 載入其他設定
                    self.speed_var.set(data["settings"].get("speed", "100"))
                    self.repeat_var.set(data["settings"].get("repeat", "1"))
                    self.repeat_time_var.set(data["settings"].get("repeat_time", "00:00:00"))
                    self.repeat_interval_var.set(data["settings"].get("repeat_interval", "00:00:00"))
                    self.random_interval_var.set(data["settings"].get("random_interval", False))
                
                # 載入事件
                self.events = data.get("events", [])
                
            except Exception as ex:
                self.log(f"載入腳本資訊失敗: {ex}")
                self.hotkey_capture_var.set("")
        except Exception as ex:
            self.log(f"處理點擊事件失敗: {ex}")

    def on_script_listbox_select(self, event=None):
        """保留舊的選擇處理（兼容性）"""
        # 此方法已被 on_script_listbox_click 取代
        pass

    def on_hotkey_entry_key(self, event):
        """強化版快捷鍵捕捉（用於腳本快捷鍵）"""
        keys = []
        
        # 檢測修飾鍵
        if event.state & 0x0001 or event.keysym in ('Shift_L', 'Shift_R'):  # Shift
            keys.append("shift")
        if event.state & 0x0004 or event.keysym in ('Control_L', 'Control_R'):  # Ctrl
            keys.append("ctrl")
        if event.state & 0x0008 or event.state & 0x20000 or event.keysym in ('Alt_L', 'Alt_R'):  # Alt
            keys.append("alt")
        if event.state & 0x0040:  # Win key
            keys.append("win")
        
        # 取得主按鍵
        key_name = event.keysym.lower()
        
        # 特殊按鍵映射
        special_keys = {
            'return': 'enter',
            'prior': 'page_up',
            'next': 'page_down',
            'backspace': 'backspace',
            'delete': 'delete',
            'insert': 'insert',
            'home': 'home',
            'end': 'end',
            'tab': 'tab',
            'escape': 'esc',
            'space': 'space',
            'caps_lock': 'caps_lock',
            'num_lock': 'num_lock',
            'scroll_lock': 'scroll_lock',
            'print': 'print_screen',
            'pause': 'pause',
        }
        
        # 功能鍵 F1-F24
        if key_name.startswith('f') and key_name[1:].isdigit():
            key_name = key_name  # F1-F24 保持原樣
        # 方向鍵
        elif key_name in ('up', 'down', 'left', 'right'):
            key_name = key_name
        # 特殊按鍵
        elif key_name in special_keys:
            key_name = special_keys[key_name]
        # 修飾鍵本身不加入（已經在 keys 列表中）
        elif key_name in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r", "win_l", "win_r"):
            # 如果只按修飾鍵，顯示修飾鍵本身
            if not keys:
                keys.append(key_name.replace('_l', '').replace('_r', ''))
            key_name = None
        # 數字鍵盤
        elif key_name.startswith('kp_'):
            key_name = key_name.replace('kp_', 'num_')
        
        # 組合按鍵字串
        if key_name and key_name not in [k for k in keys]:
            keys.append(key_name)
        
        # 去除重複並排序（ctrl, alt, shift, win, 主鍵）
        modifier_order = {'ctrl': 0, 'alt': 1, 'shift': 2, 'win': 3}
        modifiers = [k for k in keys if k in modifier_order]
        main_key = [k for k in keys if k not in modifier_order]
        
        modifiers.sort(key=lambda x: modifier_order[x])
        result = modifiers + main_key
        
        if result:
            self.hotkey_capture_var.set("+".join(result))
        
        return "break"

    def set_script_hotkey(self):
        """為選中的腳本設定快捷鍵並註冊"""
        script_name = self.script_var.get()
        hotkey = self.hotkey_capture_var.get().strip().lower()
        
        if not script_name or not hotkey or hotkey == "輸入按鍵":
            self.log("請先選擇腳本並輸入有效的快捷鍵。")
            return
        
        # 確保有 .json 副檔名
        if not script_name.endswith('.json'):
            script_name = script_name + '.json'
        
        path = os.path.join(self.script_dir, script_name)
        
        if not os.path.exists(path):
            self.log(f"找不到腳本檔案：{script_name}")
            return
        
        try:
            # 讀取現有資料
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 確保有 settings 區塊
            if "settings" not in data:
                data["settings"] = {}
            
            # 儲存快捷鍵到腳本的 settings
            data["settings"]["script_hotkey"] = hotkey
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 重新註冊所有腳本的快捷鍵
            self._register_script_hotkeys()
            
            # 更新列表顯示
            self.refresh_script_listbox()
            
            self.log(f"已設定腳本 {script_name} 的快捷鍵：{hotkey}")
            self.log("提示：按下快捷鍵將使用腳本內儲存的參數直接回放")
        except Exception as ex:
            self.log(f"設定腳本快捷鍵失敗: {ex}")
            import traceback
            self.log(f"錯誤詳情: {traceback.format_exc()}")

    def delete_selected_script(self):
        """刪除選中的腳本"""
        if not self.script_var.get():
            self.log("請先選擇要刪除的腳本。")
            return
        
        script_name = self.script_var.get()
        # 確保有 .json 副檔名
        if not script_name.endswith('.json'):
            script_name = script_name + '.json'
        
        path = os.path.join(self.script_dir, script_name)
        
        if not os.path.exists(path):
            self.log(f"找不到腳本檔案：{script_name}")
            return
        
        # 確認刪除
        import tkinter.messagebox as messagebox
        result = messagebox.askyesno(
            "確認刪除",
            f"確定要刪除腳本「{script_name}」嗎？\n此操作無法復原！",
            icon='warning'
        )
        
        if not result:
            return
        
        try:
            os.remove(path)
            self.log(f"已刪除腳本：{script_name}")
            
            # 取消註冊此腳本的快捷鍵（如果有的話）
            if script_name in self._script_hotkey_handlers:
                handler_id = self._script_hotkey_handlers[script_name]
                try:
                    keyboard.remove_hotkey(handler_id)
                except:
                    pass
                del self._script_hotkey_handlers[script_name]
            
            # 重新整理列表
            self.refresh_script_listbox()
            self.refresh_script_list()
            
            # 清除相關 UI
            self.script_var.set('')
            self.hotkey_capture_var.set('')
            self.selected_script_line = None
        except Exception as ex:
            self.log(f"刪除腳本失敗: {ex}")
            import traceback
            self.log(f"錯誤詳情: {traceback.format_exc()}")


    def open_visual_editor(self):
        """開啟視覺化拖放式編輯器"""
        # 檢查是否已經有視覺化編輯器視窗開啟
        if hasattr(self, 'visual_editor_window') and self.visual_editor_window and self.visual_editor_window.winfo_exists():
            # 如果已存在，將焦點切到該視窗
            self.visual_editor_window.focus_force()
            self.visual_editor_window.lift()
        else:
            try:
                # 建立新視窗並儲存引用
                self.visual_editor_window = VisualScriptEditor(self)
                self.log("[資訊] 已開啟視覺化腳本編輯器")
            except Exception as e:
                self.log(f"[錯誤] 無法開啟視覺化編輯器：{e}")
                import traceback
                self.log(f"錯誤詳情: {traceback.format_exc()}")
        pass

    def select_target_window(self):
        """開啟視窗選擇器，選定後只錄製該視窗內的滑鼠動作"""
        if WindowSelectorDialog is None:
            self.log("視窗選擇器模組不可用，無法選擇視窗。")
            return

        def on_selected(hwnd, title):
            # 清除先前 highlight
            try:
                self.clear_window_highlight()
            except Exception:
                pass
            if not hwnd:
                # 清除選定
                self._clear_target_window()
                return
            # 驗證 hwnd 是否有效
            try:
                if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
                    self.log("選取的視窗不可見或不存在。")
                    return
            except Exception:
                pass
            self.target_hwnd = hwnd
            self.target_title = title
            # 更新 UI 顯示（只顯示文字，不顯示圖示）
            short = title if len(title) <= 30 else title[:27] + "..."
            self.target_label.config(text=f"[目標] {short}")
            self.log(f"已選定目標視窗：{title} (hwnd={hwnd})")
            self.log("💡 提示：右鍵點擊視窗名稱可取消選擇")
            # 為使用者在畫面上畫出框框提示
            try:
                self.show_window_highlight(hwnd)
            except Exception:
                pass
            # 告訴 core_recorder（若支援）只捕捉該 hwnd
            if hasattr(self.core_recorder, 'set_target_window'):
                self.core_recorder.set_target_window(hwnd)
            try:
                setattr(self.core_recorder, "target_hwnd", hwnd)
            except Exception:
                pass

        WindowSelectorDialog(self, on_selected)
    
    def _clear_target_window(self, event=None):
        """清除目標視窗設定（可由右鍵點擊觸發）"""
        self.target_hwnd = None
        self.target_title = None
        self.target_label.config(text="")
        # 告訴 core_recorder 取消視窗限定
        if hasattr(self.core_recorder, 'set_target_window'):
            self.core_recorder.set_target_window(None)
        self.log("已清除目標視窗設定")

    # 新增：在畫面上以 topmost 無邊框視窗顯示選定視窗的邊框提示
    def show_window_highlight(self, hwnd):
        try:
            rect = win32gui.GetWindowRect(hwnd)
        except Exception:
            return
        l, t, r, b = rect
        w = max(2, r - l)
        h = max(2, b - t)
        # 清除已存在
        self.clear_window_highlight()
        try:
            win = tk.Toplevel(self)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            # 半透明背景，內側以 frame 畫出 border
            win.attributes("-alpha", 0.5)
            win.geometry(f"{w}x{h}+{l}+{t}")
            # 設定視窗圖示
            set_window_icon(win)
            
            # 設定視窗為 click-through（滑鼠事件穿透）
            hwnd_win = win.winfo_id()
            try:
                # WS_EX_TRANSPARENT = 0x00000020, WS_EX_LAYERED = 0x00080000
                GWL_EXSTYLE = -20
                WS_EX_LAYERED = 0x00080000
                WS_EX_TRANSPARENT = 0x00000020
                style = ctypes.windll.user32.GetWindowLongW(hwnd_win, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd_win, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
            except Exception:
                pass
            
            # 顯示邊框
            frm = tk.Frame(win, bg="#00ff00", bd=4, relief="solid")
            frm.pack(fill="both", expand=True, padx=2, pady=2)
            
            # 中央顯示提示文字
            label = tk.Label(frm, text="✓ 已設定目標視窗", 
                           font=("Microsoft JhengHei", 16, "bold"),
                           fg="#00ff00", bg="#000000")
            label.place(relx=0.5, rely=0.5, anchor="center")
            
            self._highlight_win = win
            
            # 2秒後自動清除高亮框
            self.after(2000, self.clear_window_highlight)
        except Exception as ex:
            self._highlight_win = None
            self.log(f"顯示高亮框時發生錯誤: {ex}")

    def clear_window_highlight(self):
        """清除視窗高亮框"""
        w = getattr(self, "_highlight_win", None)
        if w:
            try:
                if w.winfo_exists():
                    w.destroy()
            except Exception:
                pass
            finally:
                self._highlight_win = None

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