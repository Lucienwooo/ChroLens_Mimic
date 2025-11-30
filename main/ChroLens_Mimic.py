#ChroLens Studio - Lucienwooo
#python "C:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main\ChroLens_Mimic.py"
#
# ═══════════════════════════════════════════════════════════════════════════
# 【自動發布流程說明 - 給 AI Agent 使用】
# ═══════════════════════════════════════════════════════════════════════════
#
# 🚀 快速發布指令：
#   python auto_release.py
#
# 📋 完整發布流程：
#   1. 清理多餘檔案
#      - 刪除 build/、dist/、__pycache__/ 目錄
#      - 刪除所有 *.spec 檔案
#      - 刪除測試檔案（test_*.py, quick_*.py, *_test.py）
#      - 保留：test_editor_manual.py（手動測試工具）
#
#   2. 讀取版本資訊
#      - 從本檔案讀取 VERSION 變數
#      - 從 更新說明_v{版本}.md 讀取 Release Notes
#
#   3. PyInstaller 打包
#      參數：
#        --name=ChroLens_Mimic
#        --onedir
#        --windowed
#        --icon=pic/umi_奶茶色.ico
#        --add-data=TTF;TTF
#        --add-data=指令說明.html;.
#        --hidden-import=pynput,PIL,cv2,numpy
#
#   4. 創建 ZIP 壓縮檔
#      - 檔名格式：ChroLens_Mimic_{版本號}.zip
#      - 包含整個 dist/ChroLens_Mimic/ 目錄
#
#   5. 清理建置檔案
#      - 刪除 build/ 目錄
#      - 刪除所有 *.spec 檔案
#      - 保留 dist/ 目錄和 ZIP 檔案
#
#   6. 發布到 GitHub Release
#      使用 GitHub CLI (gh)：
#        gh release create v{版本號} \
#          ChroLens_Mimic_{版本號}.zip \
#          --title "ChroLens_Mimic v{版本號}" \
#          --notes "{更新說明}" \
#          --repo Lucienwooo/ChroLens_Mimic
#
# 📝 Release Notes 格式（簡短版）：
#   只列出當前版本的新增/修改內容，3-6 項重點即可
#   範例：
#     - 🔧 修復標籤顯示問題
#     - 💾 優化腳本編輯器儲存機制
#     - 🖼️ 強化圖片辨識功能
#     - 🎨 新增語法高亮功能
#
# ⚙️ 前置需求：
#   - PyInstaller: pip install pyinstaller
#   - GitHub CLI: 下載安裝並執行 gh auth login
#     下載位置: https://cli.github.com/
#
# 🔍 檢查 GitHub CLI 是否就緒：
#   gh auth status
#
# 💡 如果 GitHub CLI 無法使用，腳本會提示手動上傳 ZIP
#
# ═══════════════════════════════════════════════════════════════════════════
#
# === 專案文件清理規則（給 AI Agent） ===
# 重要：本專案應該保持精簡，避免累積測試檔案
# 
# 【應保留的檔案】
# - README.md (專案根目錄，主要說明文件)
# - 使用說明_sop.md, 更新系統說明.md, RELEASE_NOTES_*.md (功能文檔)
# - installer/BUILD_GUIDE.md (打包指南)
# 
# 【應刪除的檔案】（每次修復後清理）
# - main/tests/*.py (所有測試腳本：test_*.py, *_test.py, quick_check.py 等)
# - main/tests/*.md (測試報告：REPAIR_REPORT.md, TEST_REPORT.md 等)
# - main/*_test.py, main/test_*.py (主目錄下的測試檔案)
# - main/run_*.py (臨時執行腳本)
# - main/tests
#
# 【清理命令】
# Remove-Item main\tests\*.py -Force
# Remove-Item main\tests\*.md -Force
# Remove-Item main\*_test.py -Force
# Remove-Item main\test_*.py -Force
# Remove-Item main\run_*.py -Force
#
# === 打包說明 ===
# 1. 執行 python auto_release.py 進行自動發布
# 2. 或執行 python build_simple.py 僅打包（不發布）
# 3. 打包後檔名統一為 "ChroLens_Mimic.exe"
# 4. 版本號顯示於視窗標題和 version{版本號}.txt
#
# === 版本更新紀錄 ===
# [2.6.6] - 修復標籤顯示、優化編輯器、強化圖片辨識、新增語法高亮
# [2.6.5] - 整合2.5穩定機制：簡化快捷鍵系統、優化錄製流程、即時日誌輸出、移除不必要模組
# [2.6.4] - 快捷鍵系統優化、打包系統完善、更新UI改進、備份機制優化

VERSION = "2.6.6"

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

# ✅ v2.6.5: 不再使用 HotkeyListener，改用純 keyboard.add_hotkey（2.5 風格）

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
    # 使用腳本編輯器
    from text_script_editor import TextCommandEditor as VisualScriptEditor
    print("✅ 已載入腳本編輯器 (可直接編輯文字指令)")
except Exception as e:
    try:
        # 備用：舊版圖形化編輯器
        from visual_script_editor import VisualScriptEditor
        print("⚠️ 使用舊版圖形化編輯器")
    except Exception as e2:
        print(f"❌ 無法匯入編輯器: {e}, {e2}")
        VisualScriptEditor = None
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
            # 檢查上層 pic 目錄
            elif os.path.exists("../pic/umi_奶茶色.ico"):
                return "../pic/umi_奶茶色.ico"
            # 檢查上層目錄（向下兼容）
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
            try:
                print("⚠️ 警告：程式未以管理員身份執行，錄製功能可能無法正常工作！")
            except:
                print("[WARNING] Program not running as administrator, recording may not work properly!")
        
        # 初始化基本變數
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
        # ✅ v2.6.5: 直接使用 keyboard 模組，不再使用 HotkeyListener
        # MiniMode 管理器（由 mini.py 提供）
        self.mini_window = None
        self.mini_mode_on = False  # ✅ 修復: 初始化 mini_mode_on
        self.target_hwnd = None
        self.target_title = None
        
        # 首次運行標誌（用於控制是否顯示快捷鍵提示）
        self._is_first_run = self.user_config.get("first_run", True)
        if self._is_first_run:
            # 標記為已運行過
            self.user_config["first_run"] = False
            save_user_config(self.user_config)

        # 讀取 hotkey_map，若無則用預設
        default_hotkeys = {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "mini": "alt+`",
            "force_quit": "ctrl+alt+z"  # 強制停止的預設快捷鍵
        }
        self.hotkey_map = self.user_config.get("hotkey_map", default_hotkeys)
        
        # 確保 force_quit 存在（向下相容舊配置）
        if "force_quit" not in self.hotkey_map:
            self.hotkey_map["force_quit"] = "ctrl+alt+z"

        # ====== 統一字體 style ======
        self.style.configure("My.TButton", font=font_tuple(9))
        self.style.configure("My.TLabel", font=font_tuple(9))
        self.style.configure("My.TEntry", font=font_tuple(9))
        self.style.configure("My.TCombobox", font=font_tuple(9))
        self.style.configure("My.TCheckbutton", font=font_tuple(9))
        self.style.configure("miniBold.TButton", font=font_tuple(9, "bold"))

        self.title(f"ChroLens_Mimic_{VERSION}")
        # 設定視窗圖示
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                # 使用 wm_iconbitmap 方法 (更相容 ttkbootstrap)
                self.wm_iconbitmap(icon_path)
        except Exception as e:
            print(f"設定視窗圖示失敗: {e}")
        # 關閉視窗時使用強制關閉清理函式
        try:
            self.protocol("WM_DELETE_WINDOW", self.force_quit)
        except Exception:
            pass

        # 在左上角建立一個小label作為icon區域的懸浮觸發點
        self.icon_tip_label = tk.Label(self, width=2, height=1, bg=self.cget("background"))
        self.icon_tip_label.place(x=0, y=0)
        window_title = self.title()
        Tooltip(self.icon_tip_label, f"{window_title}_By_Lucien")

        # ✅ 設定響應式佈局 (Responsive Layout / Adaptive Window)
        # 設定最小視窗尺寸並允許彈性調整
        self.minsize(1100, 600)  # 增加最小寬度以容納新功能
        self.geometry("1150x620")  # 增加初始寬度和高度
        self.resizable(True, True)  # 允許調整大小
        
        # ✅ 啟用內容自動適應
        self.update_idletasks()  # 更新所有待處理的 GUI 事件
        
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
        
        # ====== 新增管理器 ======
        # 多螢幕管理器
        self.multi_monitor = None
        # 排程管理器
        self.schedule_manager = None
        # 效能優化器
        self.performance_optimizer = None

        # ✅ v2.6.5: 移除不必要的管理器，簡化架構
        # 直接使用內建的 _register_hotkeys 和 script_io

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
        # 添加重複次數的懸浮提示
        self.repeat_tooltip = Tooltip(self.repeat_label, "設定重複執行次數\n輸入 0 表示無限重複\n右鍵點擊輸入框可快速設為0")

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
        # 綁定左鍵點擊事件來刷新相同視窗
        self.target_label.bind("<Button-1>", self._refresh_target_window)
        # 綁定右鍵點擊事件來取消視窗選擇
        self.target_label.bind("<Button-3>", self._clear_target_window)

        # 錄製時間（使用 Frame 包裹多個 Label 實現部分變色）
        time_frame = tb.Frame(log_title_frame)
        time_frame.pack(side="right", padx=0)
        self.time_label_prefix = tb.Label(time_frame, text="錄製: ", font=font_tuple(12, monospace=True), foreground="#15D3BD")
        self.time_label_prefix.pack(side="left", padx=0)
        # 分段顯示：時:分:秒 (可獨立設置顏色)
        self.time_label_h = tb.Label(time_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.time_label_h.pack(side="left", padx=0)
        tb.Label(time_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.time_label_m = tb.Label(time_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.time_label_m.pack(side="left", padx=0)
        tb.Label(time_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.time_label_s = tb.Label(time_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.time_label_s.pack(side="left", padx=0)

        # 單次剩餘（使用 Frame 包裹多個 Label 實現部分變色）
        countdown_frame = tb.Frame(log_title_frame)
        countdown_frame.pack(side="right", padx=0)
        self.countdown_label_prefix = tb.Label(countdown_frame, text="單次: ", font=font_tuple(12, monospace=True), foreground="#DB0E59")
        self.countdown_label_prefix.pack(side="left", padx=0)
        self.countdown_label_h = tb.Label(countdown_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.countdown_label_h.pack(side="left", padx=0)
        tb.Label(countdown_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.countdown_label_m = tb.Label(countdown_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.countdown_label_m.pack(side="left", padx=0)
        tb.Label(countdown_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.countdown_label_s = tb.Label(countdown_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.countdown_label_s.pack(side="left", padx=0)

        # 總運作（使用 Frame 包裹多個 Label 實現部分變色）
        total_frame = tb.Frame(log_title_frame)
        total_frame.pack(side="right", padx=0)
        self.total_time_label_prefix = tb.Label(total_frame, text="總運作: ", font=font_tuple(12, monospace=True), foreground="#FF95CA")
        self.total_time_label_prefix.pack(side="left", padx=0)
        self.total_time_label_h = tb.Label(total_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.total_time_label_h.pack(side="left", padx=0)
        tb.Label(total_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.total_time_label_m = tb.Label(total_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.total_time_label_m.pack(side="left", padx=0)
        tb.Label(total_frame, text=":", font=font_tuple(12, monospace=True), foreground="#888888").pack(side="left", padx=0)
        self.total_time_label_s = tb.Label(total_frame, text="00", font=font_tuple(12, monospace=True), foreground="#888888")
        self.total_time_label_s.pack(side="left", padx=0)

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
        
        # 使用 Treeview 來顯示三欄（腳本名稱 | 快捷鍵 | 定時）
        from tkinter import ttk
        self.script_treeview = ttk.Treeview(
            list_frame,
            columns=("name", "hotkey", "schedule"),
            show="headings",
            height=15,
            selectmode="extended"  # 支援多選（Ctrl+點擊 或 Shift+點擊）
        )
        self.script_treeview.heading("name", text="腳本名稱")
        self.script_treeview.heading("hotkey", text="快捷鍵")
        self.script_treeview.heading("schedule", text="定時")
        self.script_treeview.column("name", width=250, anchor="w")
        self.script_treeview.column("hotkey", width=80, anchor="center")
        self.script_treeview.column("schedule", width=120, anchor="center")
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
        
        # e) 排程按鈕：設定腳本定時執行
        self.schedule_btn = tb.Button(self.script_right_frame, text="排程", width=16, bootstyle=INFO, command=self.open_schedule_settings)
        self.schedule_btn.pack(anchor="w", pady=4)
        
        # f) 合併腳本按鈕：將多個腳本合併為一個
        self.merge_btn = tb.Button(self.script_right_frame, text=lang_map["合併腳本"], width=16, bootstyle=SUCCESS, command=self.merge_scripts)
        self.merge_btn.pack(anchor="w", pady=4)

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
        # self._init_language(saved_lang)  # 此方法不存在，已移除
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
        # 初始化 core_recorder（需要在 self.log 可用之後）
        self.core_recorder = CoreRecorder(logger=self.log)
        
        # ✅ v2.6.5: 強化焦點獲取和快捷鍵註冊時序
        self.after(50, self._force_focus)   # 主動獲得焦點
        self.after(200, self._force_focus)  # 再次確認焦點
        self.after(300, self._register_hotkeys)  # 註冊快捷鍵
        self.after(400, self._register_script_hotkeys)
        self.after(500, self.refresh_script_list)
        self.after(600, self.load_last_script)
        self.after(700, self.update_mouse_pos)
        self.after(800, self._init_background_mode)

    def _force_focus(self):
        """主動獲得焦點，確保鍵盤鉤子正常工作"""
        try:
            # ✅ 強化焦點獲取機制（不使用topmost避免蓋過其他視窗）
            self.lift()  # 提升視窗
            self.focus_force()  # 強制獲得焦點
            self.update()  # 強制更新
            
            # ✅ 额外觸發一次鍵盤事件來激活鉤子
            self.event_generate('<KeyPress>', keysym='Shift_L')
            self.event_generate('<KeyRelease>', keysym='Shift_L')
        except Exception as e:
            pass  # 靜默處理錯誤

    def _init_background_mode(self):
        """初始化後台模式設定（固定使用智能模式）"""
        mode = "smart"
        if hasattr(self.core_recorder, 'set_background_mode'):
            self.core_recorder.set_background_mode(mode)
        # 靜默設定，不顯示日誌

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
        """檢查更新（使用新的更新系統）"""
        try:
            from update_manager import UpdateManager
            from update_dialog import UpdateDialog, NoUpdateDialog
        except Exception as e:
            self.log(f"無法載入更新模組: {e}")
            messagebox.showerror("錯誤", "更新系統模組載入失敗")
            return
        
        def check_in_thread():
            try:
                # 建立更新管理器
                updater = UpdateManager(VERSION, logger=self.log)
                
                # 檢查更新
                update_info = updater.check_for_updates()
                
                def show_result():
                    if update_info:
                        # 有更新：顯示更新對話框
                        UpdateDialog(self, updater, update_info)
                    else:
                        # 無更新：顯示已是最新版本
                        NoUpdateDialog(self, VERSION)
                
                self.after(0, show_result)
                
            except Exception as e:
                error_msg = str(e)
                self.after(0, lambda msg=error_msg: messagebox.showerror("錯誤", f"檢查更新失敗：\n{msg}"))
        
        # 在背景執行緒中執行
        threading.Thread(target=check_in_thread, daemon=True).start()

    # ✅ v2.6.5: 已移除 open_image_manager 和 open_combat_control（不必要的功能）


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
        if hasattr(self, 'merge_btn'):
            self.merge_btn.config(text=lang_map["合併腳本"])
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
            self.script_treeview.heading("schedule", text=lang_map.get("定時", "定時"))
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
        """更新錄製時間顯示（動態顏色：非零數字顯示 #FF95CA）"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        
        # 設定顏色：非零數字顯示 #FF95CA，零顯示灰色 #888888
        h_color = "#FF95CA" if h > 0 else "#888888"
        m_color = "#FF95CA" if m > 0 or h > 0 else "#888888"  # 如果小時>0，分鐘也要亮
        s_color = "#FF95CA" if s > 0 or m > 0 or h > 0 else "#888888"  # 如果分鐘>0，秒也要亮
        
        self.time_label_h.config(text=f"{h:02d}", foreground=h_color)
        self.time_label_m.config(text=f"{m:02d}", foreground=m_color)
        self.time_label_s.config(text=f"{s:02d}", foreground=s_color)

    def update_total_time_label(self, seconds):
        """更新總運作時間顯示（動態顏色：非零數字顯示 #FF95CA）"""
        # 處理無限重複的情況
        if seconds == float('inf') or (isinstance(seconds, float) and (seconds != seconds or seconds > 1e10)):
            # NaN 或無限大，顯示 ∞
            self.total_time_label_h.config(text="∞", foreground="#FF95CA")
            self.total_time_label_m.config(text="", foreground="#888888")
            self.total_time_label_s.config(text="", foreground="#888888")
            return
        
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        
        # 設定顏色：非零數字顯示 #FF95CA，零顯示灰色 #888888
        h_color = "#FF95CA" if h > 0 else "#888888"
        m_color = "#FF95CA" if m > 0 or h > 0 else "#888888"
        s_color = "#FF95CA" if s > 0 or m > 0 or h > 0 else "#888888"
        
        self.total_time_label_h.config(text=f"{h:02d}", foreground=h_color)
        self.total_time_label_m.config(text=f"{m:02d}", foreground=m_color)
        self.total_time_label_s.config(text=f"{s:02d}", foreground=s_color)

    def update_countdown_label(self, seconds):
        """更新單次剩餘時間顯示（動態顏色：非零數字顯示 #FF95CA）"""
        # 處理無限重複的情況
        if seconds == float('inf') or (isinstance(seconds, float) and (seconds != seconds or seconds > 1e10)):
            # NaN 或無限大，顯示 ∞
            self.countdown_label_h.config(text="∞", foreground="#FF95CA")
            self.countdown_label_m.config(text="", foreground="#888888")
            self.countdown_label_s.config(text="", foreground="#888888")
            return
        
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        
        # 設定顏色：非零數字顯示 #FF95CA，零顯示灰色 #888888
        h_color = "#FF95CA" if h > 0 else "#888888"
        m_color = "#FF95CA" if m > 0 or h > 0 else "#888888"
        s_color = "#FF95CA" if s > 0 or m > 0 or h > 0 else "#888888"
        
        self.countdown_label_h.config(text=f"{h:02d}", foreground=h_color)
        self.countdown_label_m.config(text=f"{m:02d}", foreground=m_color)
        self.countdown_label_s.config(text=f"{s:02d}", foreground=s_color)

    def _update_play_time(self):
        """更新回放時間顯示（強化版 - 使用實際時間確保準確倒數）"""
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
            
            # ✅ 修復：使用實際經過的時間而非事件索引
            # 計算腳本的總長度（邏輯時間）
            if self.events and len(self.events) > 0:
                script_duration = self.events[-1]['time'] - self.events[0]['time']
            else:
                script_duration = 0
            
            # 獲取當前循環計數
            current_repeat = getattr(self.core_recorder, '_current_repeat_count', 0)
            
            # 檢測循環變化（開始新的循環）
            if not hasattr(self, '_last_repeat_count'):
                self._last_repeat_count = 0
            
            if current_repeat != self._last_repeat_count:
                # 循環變化，重置循環起始時間
                self._current_cycle_start_time = time.time()
                self._last_repeat_count = current_repeat
            
            # 獲取單次回放的起始時間
            if not hasattr(self, '_current_cycle_start_time') or self._current_cycle_start_time is None:
                # 初始化當前循環起始時間
                self._current_cycle_start_time = time.time()
            
            # 計算當前循環內的實際經過時間
            elapsed_real = time.time() - self._current_cycle_start_time
            
            # 應用速度係數來計算邏輯時間
            speed = getattr(self, 'speed', 1.0)
            elapsed = elapsed_real * speed
            
            # 限制 elapsed 不超過腳本總長度（單次）
            if script_duration > 0 and elapsed > script_duration:
                elapsed = script_duration
                    
            self.update_time_label(elapsed)
            
            # 計算單次剩餘時間（邏輯時間）
            remain = max(0, script_duration - elapsed)
            self.update_countdown_label(remain)
            
            # 計算總運作剩餘時間
            if hasattr(self, "_play_start_time") and self._play_start_time:
                elapsed_real = time.time() - self._play_start_time
                
                # 處理無限重複的情況
                if self._total_play_time == float('inf'):
                    total_remain = float('inf')
                elif self._repeat_time_limit:
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
                            
                            # 處理無限重複
                            if total_remain == float('inf'):
                                time_str = "∞"
                            else:
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
        """開始錄製 (v2.6.5 - 簡化版，參考2.5穩定機制)"""
        if self.recording:
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
        if hasattr(self, 'core_recorder') and hasattr(self.core_recorder, 'set_target_window'):
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
        
        # ✅ 清空 events 並設定狀態
        self.events = []
        self.recording = True
        self.paused = False
        self.log(f"[{format_time(time.time())}] 開始錄製...")
        
        # ✅ 2.5 風格：不需要重置 keyboard 狀態（因為 add_hotkey 不受 record 影響）
        # 啟動 core_recorder (如果存在)
        if hasattr(self, 'core_recorder'):
            # 跳過 _reset_keyboard_state，直接開始錄製
            self.core_recorder.recording = True
            self.core_recorder.paused = False
            self.core_recorder.events = []
            self._record_start_time = time.time()
            self.core_recorder._record_start_time = self._record_start_time
            self.core_recorder._record_thread = threading.Thread(target=self.core_recorder._record_loop, daemon=True)
            self.core_recorder._record_thread.start()
            self._record_thread_handle = self.core_recorder._record_thread
        else:
            # 向後相容: 使用舊的 threading 方式
            self._record_start_time = time.time()
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
        """切換暫停/繼續（v2.6.5 - 參考2.5簡化邏輯）"""
        if self.recording or self.playing:
            # ✅ 優先使用 core_recorder 的暫停功能
            if hasattr(self, 'core_recorder'):
                is_paused = self.core_recorder.toggle_pause()
                self.paused = is_paused
            else:
                # 向後相容：直接切換狀態
                self.paused = not self.paused
            
            state = "暫停" if self.paused else "繼續"
            mode = "錄製" if self.recording else "回放"
            self.log(f"[{format_time(time.time())}] {mode}{state}。")
            
            # ✅ 2.5 風格：暫停時停止 keyboard 錄製，暫存事件
            if self.paused and self.recording:
                try:
                    import keyboard
                    if hasattr(self.core_recorder, "_keyboard_recording") and self.core_recorder._keyboard_recording:
                        k_events = keyboard.stop_recording()
                        if not hasattr(self.core_recorder, "_paused_k_events"):
                            self.core_recorder._paused_k_events = []
                        self.core_recorder._paused_k_events.extend(k_events)
                        self.core_recorder._keyboard_recording = False
                except Exception as e:
                    self.log(f"[警告] 暫停時停止keyboard錄製失敗: {e}")
            elif self.recording:
                # 繼續時重新開始 keyboard 錄製
                try:
                    import keyboard
                    keyboard.start_recording()
                    if hasattr(self.core_recorder, "_keyboard_recording"):
                        self.core_recorder._keyboard_recording = True
                except Exception as e:
                    self.log(f"[警告] 繼續錄製時啟動keyboard失敗: {e}")

    def stop_record(self):
        """停止錄製（簡化版 - v2.1 風格）"""
        if not self.recording:
            return
        
        # 告訴 core_recorder 停止錄製
        self.recording = False
        self.core_recorder.stop_record()
        self.log(f"[{format_time(time.time())}] 停止錄製（等待寫入事件...）。")
        
        # 等待 core_recorder 的錄製執行緒結束
        self._wait_record_thread_finish()
        
        # ✅ v2.1 風格：不重新註冊快捷鍵，保持始終有效

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
                        dialog.geometry("650x550")
                        dialog.resizable(True, True)
                        dialog.minsize(550, 450)  # 設定最小尺寸
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
    
    def play_script(self):
        """✅ 新增：供編輯器調用的播放方法別名"""
        self.play_record()
    
    def _continue_play_record(self):
        """實際執行回放的內部方法（支援智能縮放）"""
        # ✅ 設定圖片辨識目錄
        images_dir = os.path.join(self.script_dir, "images")
        if os.path.exists(images_dir):
            self.core_recorder.set_images_directory(images_dir)
            self.log(f"[圖片辨識] 已設定圖片目錄: {images_dir}")
        
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
        
        # 重複次數 = 0 表示無限重複，傳入 -1 給 core_recorder
        if repeat == 0:
            repeat = -1  # 無限重複
            self.log(f"[{format_time(time.time())}] 設定為無限重複模式")
        elif repeat < 0:
            repeat = 1  # 負數視為1次

        # 計算總運作時間
        single_time = (self.events[-1]['time'] - self.events[0]['time']) / self.speed if self.events else 0
        if repeat == -1:
            # 無限重複模式
            total_time = float('inf') if not self._repeat_time_limit else self._repeat_time_limit
        elif self._repeat_time_limit and repeat > 0:
            total_time = self._repeat_time_limit
        else:
            total_time = single_time * repeat + repeat_interval_sec * max(0, repeat - 1)
        self._total_play_time = total_time

        self._play_start_time = time.time()
        self._current_cycle_start_time = time.time()  # ✅ 初始化當前循環起始時間
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
            repeat_time_limit=self._repeat_time_limit,
            repeat_interval=repeat_interval_sec,
            on_event=on_event
        )

        if success:
            # 修正日誌顯示，不要把 ratio 字串插入 lbl，保留數值顯示與內部倍率
            self.log(f"[{format_time(time.time())}] 開始回放，速度倍率: {self.speed:.2f} ({self.speed_var.get()})")
            self.after(100, self._update_play_time)
        else:
            self.log("沒有可回放的事件，請先錄製或載入腳本。")

    def stop_all(self):
        """停止所有動作（全新實作 - 更穩健的處理）"""
        stopped = False
        
        # ✅ 立即設定狀態
        if self.recording:
            self.recording = False
            stopped = True
            self.log(f"[{format_time(time.time())}] 停止錄製。")
            
            # 停止 core_recorder
            if hasattr(self, 'core_recorder'):
                try:
                    if hasattr(self.core_recorder, 'recording'):
                        self.core_recorder.recording = False
                    if hasattr(self.core_recorder, 'stop_record'):
                        self.core_recorder.stop_record()
                    if hasattr(self.core_recorder, 'events'):
                        self.events = self.core_recorder.events
                except Exception as e:
                    self.log(f"[警告] 停止 core_recorder 時發生錯誤: {e}")
                    # ✅ 強制重置狀態
                    self.core_recorder.recording = False
            
            # 等待錄製執行緒結束
            try:
                self._wait_record_thread_finish()
            except Exception as e:
                self.log(f"[警告] 等待錄製結束時發生錯誤: {e}")
            
            # ✅ v2.1 風格：不重新註冊快捷鍵
        
        if self.playing:
            self.playing = False
            stopped = True
            self.log(f"[{format_time(time.time())}] 停止回放。")
            
            # 停止 core_recorder 播放
            if hasattr(self, 'core_recorder') and hasattr(self.core_recorder, 'stop_play'):
                try:
                    self.core_recorder.stop_play()
                except Exception as e:
                    self.log(f"[警告] 停止回放時發生錯誤: {e}")
            
            # 釋放所有可能卡住的修飾鍵
            try:
                self._release_all_modifiers()
            except Exception as e:
                self.log(f"[警告] 釋放修飾鍵時發生錯誤: {e}")
        
        if not stopped:
            self.log(f"[{format_time(time.time())}] 無進行中動作可停止。")
        
        # ✅ 立即刷新顯示
        self.update_time_label(0)
        self.update_countdown_label(0)
        self.update_total_time_label(0)
        
        # 強制更新時間顯示
        try:
            self._update_play_time()
            self._update_record_time()
        except Exception:
            pass
    


    def force_quit(self):
        """
        強制停止所有動作並關閉程式（v2.6.5+ 精確清理版）
        
        ✅ 重構改進：
        - 只移除本程式註冊的快捷鍵
        - 不使用 keyboard.unhook_all()
        - 保護其他程式的全域熱鍵
        
        【執行順序】
        1. 立即停止所有錄製和回放
        2. 釋放所有按鍵和 hooks
        3. 清理本程式註冊的快捷鍵（不影響其他程式）
        4. 強制終止程式
        """
        try:
            self.log("[系統] 🔴 強制停止：立即終止所有動作...")
        except:
            pass

        # ✅ 步驟1：立即停止所有動作
        try:
            self.recording = False
            self.playing = False
            self.paused = False
            
            # 停止 core_recorder
            if hasattr(self, 'core_recorder'):
                try:
                    self.core_recorder.recording = False
                    self.core_recorder.playing = False
                    self.core_recorder.stop_record()
                    self.core_recorder.stop_play()
                except:
                    pass
        except Exception as e:
            try:
                self.log(f"[警告] 停止動作錯誤: {e}")
            except:
                pass

        # ✅ 步驟2：釋放所有按鍵（避免卡鍵）
        try:
            self._release_all_modifiers()
        except:
            pass

        # ✅ 步驟3：精確清理本程式的快捷鍵（不影響其他程式）
        try:
            import keyboard
            
            # 移除系統快捷鍵
            for handler in self._hotkey_handlers.values():
                try:
                    keyboard.remove_hotkey(handler)
                except:
                    pass
            self._hotkey_handlers.clear()
            
            # 移除腳本快捷鍵
            for handler in self._script_hotkey_handlers.values():
                try:
                    keyboard.remove_hotkey(handler)
                except:
                    pass
            self._script_hotkey_handlers.clear()
            
            # ❌ 禁止：keyboard.unhook_all() 
            # 原因：會移除所有程式的熱鍵，包括使用者的其他工具
            
        except Exception:
            pass

        # 嘗試關閉視窗與退出
        try:
            self.log("[系統] 即將結束程式")
        except:
            pass
        try:
            # 直接使用 os._exit 以確保立即終止
            import os, sys
            try:
                self.quit()
            except:
                try:
                    self.destroy()
                except:
                    pass
            try:
                os._exit(0)
            except SystemExit:
                sys.exit(0)
        except Exception:
            try:
                import sys
                sys.exit(0)
            except:
                pass
    
    def _release_all_modifiers(self):
        """釋放所有修飾鍵以防止卡住（v2.6.5 修復版 - 不移除快捷鍵）"""
        try:
            import keyboard
            # 釋放常見的修飾鍵與常用按鍵，盡量避免卡鍵
            keys_to_release = ['ctrl', 'shift', 'alt', 'win']
            # 加入功能鍵與字母數字
            keys_to_release += [f'f{i}' for i in range(1, 13)]
            keys_to_release += [chr(c) for c in range(ord('a'), ord('z')+1)]
            keys_to_release += [str(d) for d in range(0, 10)]

            for k in keys_to_release:
                try:
                    keyboard.release(k)
                except:
                    pass

            # ✅ v2.6.5 修復：不再呼叫 unhook_all/unhook_all_hotkeys
            # 這些會移除系統快捷鍵 (F9/F10 等)，導致 3-5 次後失效
            # 只需釋放按鍵本身即可，快捷鍵保持註冊狀態

            self.log("[系統] 已釋放常見按鍵")
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
            data = json.loads(json_str)
            
            # 處理兩種格式：
            # 1. 完整格式: {"events": [...], "settings": {...}}
            # 2. 簡化格式: [...] (直接是事件列表)
            if isinstance(data, dict) and "events" in data:
                self.events = data["events"]
            elif isinstance(data, list):
                self.events = data
            else:
                raise ValueError("不支援的 JSON 格式")
            
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
        
        # 必須先選擇腳本才能儲存設定
        if not script:
            self.log("請先選擇一個腳本再儲存設定。")
            return
        
        # 確保腳本名稱包含 .json 副檔名
        if not script.endswith('.json'):
            script_file = script + '.json'
        else:
            script_file = script
        
        # 建立完整路徑
        path = os.path.join(self.script_dir, script_file)
        
        # 檢查檔案是否存在
        if not os.path.exists(path):
            self.log("找不到腳本檔案，請確認腳本是否存在。")
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

    def merge_scripts(self):
        """開啟腳本合併對話框，允許將多個腳本按順序合併為一個新腳本"""
        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        
        # 創建合併對話框
        merge_win = tb.Toplevel(self)
        merge_win.title(lang_map.get("合併腳本", "合併腳本"))
        merge_win.geometry("850x550")
        merge_win.resizable(True, True)
        merge_win.minsize(750, 500)
        
        # 個別腳本延遲字典（腳本名稱 -> 延遲秒數）
        script_delays = {}
        
        # 說明標籤
        info_frame = tb.Frame(merge_win, padding=10)
        info_frame.pack(fill="x")
        info_label = tb.Label(
            info_frame, 
            text="📋 選擇要合併的腳本，按順序執行（點兩下腳本設定延遲）",
            font=("微軟正黑體", 10),
            wraplength=800
        )
        info_label.pack()
        
        # 主要內容區
        main_content = tb.Frame(merge_win)
        main_content.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 可用腳本列表（左側）
        left_frame = tb.LabelFrame(main_content, text=lang_map.get("所有Script", "所有腳本"), padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        available_list = tk.Listbox(left_frame, height=12, selectmode=tk.EXTENDED, font=("微軟正黑體", 10))
        available_list.pack(fill="both", expand=True)
        
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        for script in scripts:
            display_name = os.path.splitext(script)[0]
            available_list.insert(tk.END, display_name)
        
        # 中間控制按鈕
        middle_frame = tb.Frame(main_content, padding=5)
        middle_frame.pack(side="left", fill="y")
        
        def add_to_merge():
            selected_indices = available_list.curselection()
            for idx in selected_indices:
                script_name = available_list.get(idx)
                if script_name not in merge_list.get(0, tk.END):
                    merge_list.insert(tk.END, script_name)
                    script_delays[script_name] = 0  # 預設延遲 0 秒
        
        def remove_from_merge():
            selected_indices = list(merge_list.curselection())
            for idx in reversed(selected_indices):
                script_name = merge_list.get(idx)
                merge_list.delete(idx)
                if script_name in script_delays:
                    del script_delays[script_name]
        
        def move_up():
            selected_indices = merge_list.curselection()
            if not selected_indices or selected_indices[0] == 0:
                return
            for idx in selected_indices:
                if idx > 0:
                    item = merge_list.get(idx)
                    merge_list.delete(idx)
                    merge_list.insert(idx - 1, item)
                    merge_list.selection_set(idx - 1)
        
        def move_down():
            selected_indices = merge_list.curselection()
            if not selected_indices or selected_indices[-1] == merge_list.size() - 1:
                return
            for idx in reversed(selected_indices):
                if idx < merge_list.size() - 1:
                    item = merge_list.get(idx)
                    merge_list.delete(idx)
                    merge_list.insert(idx + 1, item)
                    merge_list.selection_set(idx + 1)
        
        def on_double_click(event):
            """點兩下腳本設定延遲時間"""
            index = merge_list.nearest(event.y)
            if index < 0:
                return
            script_name = merge_list.get(index)
            
            # 創建輸入對話框
            delay_win = tb.Toplevel(merge_win)
            delay_win.title("設定延遲")
            delay_win.geometry("300x150")
            delay_win.resizable(False, False)
            delay_win.transient(merge_win)
            delay_win.grab_set()
            
            # 置中顯示
            delay_win.update_idletasks()
            x = merge_win.winfo_x() + (merge_win.winfo_width() - 300) // 2
            y = merge_win.winfo_y() + (merge_win.winfo_height() - 150) // 2
            delay_win.geometry(f"+{x}+{y}")
            
            frame = tb.Frame(delay_win, padding=20)
            frame.pack(fill="both", expand=True)
            
            tb.Label(frame, text=f"腳本：{script_name}", font=("微軟正黑體", 10, "bold")).pack(pady=(0, 10))
            tb.Label(frame, text="延遲執行秒數：", font=("微軟正黑體", 10)).pack()
            
            current_delay = script_delays.get(script_name, 0)
            delay_var = tk.StringVar(value=str(current_delay))
            delay_entry = tb.Entry(frame, textvariable=delay_var, width=15, font=("微軟正黑體", 11), justify="center")
            delay_entry.pack(pady=5)
            delay_entry.focus()
            delay_entry.select_range(0, tk.END)
            
            # 只允許數字，最多 4 位
            def validate_delay(P):
                if P == "":
                    return True
                try:
                    if len(P) > 4:
                        return False
                    val = int(P)
                    return 0 <= val <= 9999
                except:
                    return False
            
            vcmd = (delay_win.register(validate_delay), '%P')
            delay_entry.config(validate="key", validatecommand=vcmd)
            
            def save_delay():
                try:
                    delay_value = int(delay_var.get()) if delay_var.get() else 0
                    script_delays[script_name] = delay_value
                    # 更新顯示
                    update_merge_list_display()
                    delay_win.destroy()
                except:
                    messagebox.showerror("錯誤", "請輸入有效的數字")
            
            btn_frame = tb.Frame(frame)
            btn_frame.pack(pady=10)
            tb.Button(btn_frame, text="確定", command=save_delay, width=8, bootstyle=SUCCESS).pack(side="left", padx=5)
            tb.Button(btn_frame, text="取消", command=delay_win.destroy, width=8, bootstyle=SECONDARY).pack(side="left", padx=5)
            
            # Enter 鍵確認
            delay_entry.bind("<Return>", lambda e: save_delay())
        
        def update_merge_list_display():
            """更新合併列表顯示（顯示延遲時間）"""
            current_items = list(merge_list.get(0, tk.END))
            merge_list.delete(0, tk.END)
            for script_name in current_items:
                delay = script_delays.get(script_name, 0)
                if delay > 0:
                    display_text = f"{script_name}  [延遲 {delay}秒]"
                else:
                    display_text = script_name
                merge_list.insert(tk.END, display_text)
        
        add_btn = tb.Button(middle_frame, text="➡ " + lang_map.get("加入", "加入"), command=add_to_merge, width=10, bootstyle=SUCCESS)
        add_btn.pack(pady=5)
        
        remove_btn = tb.Button(middle_frame, text="⬅ " + lang_map.get("移除", "移除"), command=remove_from_merge, width=10, bootstyle=DANGER)
        remove_btn.pack(pady=5)
        
        tb.Label(middle_frame, text="").pack(pady=10)
        
        up_btn = tb.Button(middle_frame, text="⬆ 上移", command=move_up, width=10, bootstyle=INFO)
        up_btn.pack(pady=5)
        
        down_btn = tb.Button(middle_frame, text="⬇ 下移", command=move_down, width=10, bootstyle=INFO)
        down_btn.pack(pady=5)
        
        # 合併列表（右側）
        right_frame = tb.LabelFrame(main_content, text="待合併腳本（執行順序）", padding=10)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        merge_list = tk.Listbox(right_frame, height=12, selectmode=tk.EXTENDED, font=("微軟正黑體", 10))
        merge_list.pack(fill="both", expand=True)
        merge_list.bind("<Double-Button-1>", on_double_click)
        
        # 底部操作區
        bottom_frame = tb.Frame(merge_win, padding=15)
        bottom_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        tb.Label(bottom_frame, text="合併名稱：", 
                font=("微軟正黑體", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        
        new_name_var = tk.StringVar(value="merged_script")
        new_name_entry = tb.Entry(bottom_frame, textvariable=new_name_var, width=40, font=("微軟正黑體", 10))
        new_name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 20))
        
        button_frame = tb.Frame(bottom_frame)
        button_frame.grid(row=0, column=2, sticky="e", padx=(20, 0))
        
        bottom_frame.columnconfigure(1, weight=1)
        
        def do_merge():
            """執行腳本合併"""
            script_names_display = list(merge_list.get(0, tk.END))
            # 提取真實腳本名稱（移除顯示的延遲標記）
            script_names = []
            for display_name in script_names_display:
                # 移除 [延遲 X秒] 標記
                if "  [" in display_name:
                    real_name = display_name.split("  [")[0]
                else:
                    real_name = display_name
                script_names.append(real_name)
            
            if len(script_names) < 2:
                messagebox.showwarning("提示", "請至少選擇2個腳本進行合併")
                return
            
            new_name = new_name_var.get().strip()
            if not new_name:
                messagebox.showwarning("提示", "請輸入合併名稱")
                return
            
            if not new_name.endswith('.json'):
                new_name += '.json'
            
            new_path = os.path.join(self.script_dir, new_name)
            if os.path.exists(new_path):
                if not messagebox.askyesno("確認", f"腳本 {new_name} 已存在，是否覆蓋？"):
                    return
            
            try:
                merged_events = []
                time_offset = 0.0
                first_script_settings = None
                
                for i, script_name in enumerate(script_names):
                    script_path = os.path.join(self.script_dir, script_name + '.json')
                    if not os.path.exists(script_path):
                        self.log(f"[警告] 找不到腳本：{script_name}")
                        continue
                    
                    data = sio_load_script(script_path)
                    events = data.get("events", [])
                    
                    if i == 0:
                        first_script_settings = data.get("settings", {}).copy()
                        self.log(f"✓ 使用腳本A的參數設定：{script_name}")
                    
                    if not events:
                        continue
                    
                    script_base_time = events[0]['time'] if events else 0
                    
                    for event in events:
                        new_event = event.copy()
                        new_event['time'] = (event['time'] - script_base_time) + time_offset
                        merged_events.append(new_event)
                    
                    # 更新時間偏移（加上本腳本持續時間 + 個別延遲）
                    if merged_events:
                        script_duration = events[-1]['time'] - script_base_time
                        individual_delay = script_delays.get(script_name, 0)
                        time_offset = merged_events[-1]['time'] + individual_delay
                        if individual_delay > 0:
                            self.log(f"✓ 腳本 {script_name} 設定延遲 {individual_delay} 秒")
                
                # 儲存合併後的腳本
                merged_data = {
                    "events": merged_events,
                    "settings": first_script_settings or {}
                }
                
                with open(new_path, "w", encoding="utf-8") as f:
                    json.dump(merged_data, f, ensure_ascii=False, indent=2)
                
                self.log(f"✅ 合併完成：{new_name}，共 {len(merged_events)} 筆事件")
                messagebox.showinfo("成功", f"已合併 {len(script_names)} 個腳本為\n{new_name}")
                
                self.refresh_script_list()
                self.script_var.set(os.path.splitext(new_name)[0])
                merge_win.destroy()
                
            except Exception as e:
                self.log(f"合併失敗: {e}")
                messagebox.showerror("錯誤", f"合併失敗：\n{e}")
                import traceback
                traceback.print_exc()
                
                # 刷新腳本列表
                self.refresh_script_list()
                self.refresh_script_listbox()
                
                # 關閉對話框
                merge_win.destroy()
                
                # 詢問是否載入新腳本
                if messagebox.askyesno("提示", "是否載入新合併的腳本？"):
                    # 載入新腳本
                    self.events = merged_events
                    self.script_settings = first_script_settings
                    self.script_var.set(os.path.splitext(new_name)[0])
                    with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                        f.write(new_name)
                
            except Exception as e:
                messagebox.showerror("錯誤", f"合併失敗：{e}")
                import traceback
                self.log(f"合併錯誤詳情: {traceback.format_exc()}")
        
        merge_execute_btn = tb.Button(
            button_frame, 
            text=lang_map.get("合併並儲存", "合併並儲存"), 
            command=do_merge, 
            bootstyle=SUCCESS,
            width=15
        )
        merge_execute_btn.pack(side="left", padx=(0, 5))
        
        cancel_btn = tb.Button(
            button_frame, 
            text=lang_map.get("取消", "取消"), 
            command=merge_win.destroy, 
            bootstyle=SECONDARY,
            width=10
        )
        cancel_btn.pack(side="left")

    def open_scripts_dir(self):
        path = os.path.abspath(self.script_dir)  # 修正
        os.startfile(path)

    def open_hotkey_settings(self):
        win = tb.Toplevel(self)
        win.title("Hotkey")
        win.geometry("400x450")  # 增大尺寸以容納強制停止欄位
        win.resizable(True, True)  # 允許調整大小
        win.minsize(350, 400)  # 設置最小尺寸
        # 設定視窗圖示
        set_window_icon(win)
        
        # 居中顯示
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")

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
            "mini": lang_map["MiniMode"],
            "force_quit": lang_map["強制停止"]
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
                var.set(self.hotkey_map.get(key, ""))

        for key, label in labels.items():
            entry_frame = tb.Frame(main_frame)
            entry_frame.pack(fill="x", pady=5)
            
            tb.Label(entry_frame, text=label, font=("Microsoft JhengHei", 11), width=12, anchor="w").pack(side="left", padx=5)
            # 確保 hotkey_map 有此鍵，避免 KeyError
            hotkey_value = self.hotkey_map.get(key, "")
            var = tk.StringVar(value=hotkey_value)
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
            # 由 HotkeyManager 統一註冊（若存在），否則使用舊的 _register_hotkeys
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                try:
                    self.hotkey_manager.register_all()
                except Exception:
                    self._register_hotkeys()
            else:
                self._register_hotkeys()
            self._update_hotkey_labels()
            self.save_config()  # 新增這行,確保儲存
            self.log("快捷鍵設定已更新。")
            win.destroy()

        # 按鈕框架
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill="x", pady=15)
        tb.Button(btn_frame, text="儲存", command=save_and_apply, width=15, bootstyle=SUCCESS).pack(pady=5)

    # ✅ v2.6.5+: 儲存快捷鍵 handle，避免使用 keyboard.unhook_all()

    def _register_hotkeys(self):
        """
        註冊系統快捷鍵（v2.6.5+ - 精確 Hook 管理）
        
        ✅ 重構改進：
        - 儲存每個快捷鍵的 handle
        - 清理時只移除本程式註冊的快捷鍵
        - 不影響其他程式的全域熱鍵
        
        ❌ 禁止：keyboard.unhook_all() - 會移除所有熱鍵（包括其他程式）
        """
        try:
            import keyboard
        except Exception as e:
            self.log(f"[錯誤] keyboard 模組載入失敗: {e}")
            return
        
        method_map = {
            "start": "start_record",
            "pause": "toggle_pause",
            "stop": "stop_all",
            "play": "play_record",
            "mini": "toggle_mini_mode",
            "force_quit": "force_quit"
        }
        
        # ✅ 清除舊 handler（只移除本程式註冊的）
        for handler in self._hotkey_handlers.values():
            try:
                keyboard.remove_hotkey(handler)
            except Exception:
                pass  # 忽略移除失敗
        self._hotkey_handlers.clear()
        
        # 註冊所有快捷鍵
        for key, hotkey in self.hotkey_map.items():
            try:
                method_name = method_map.get(key)
                if not method_name:
                    continue
                    
                callback = getattr(self, method_name, None)
                if not callable(callback):
                    continue
                
                # ✅ 註冊並儲存 handle
                handler = keyboard.add_hotkey(
                    hotkey, 
                    callback,
                    suppress=False,
                    trigger_on_release=False
                )
                self._hotkey_handlers[key] = handler
                
                if self._is_first_run:
                    self.log(f"已註冊快捷鍵: {hotkey} → {key}")
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")
        
        # 提示：首次運行後不再顯示註冊訊息
        if self._is_first_run:
            self.log("✅ 系統快捷鍵註冊完成（錄製時仍然有效）")


    def _register_script_hotkeys(self):
        """
        註冊所有腳本的快捷鍵（使用 keyboard 模組）
        
        【PyInstaller 兼容性增強】
        - 添加 keyboard 模組載入檢查
        - 詳細的錯誤處理和日誌
        """
        try:
            import keyboard
        except ImportError as e:
            self.log(f"[錯誤] 無法載入 keyboard 模組用於腳本快捷鍵: {e}")
            return
        except Exception as e:
            self.log(f"[錯誤] keyboard 模組初始化失敗: {e}")
            return
        
        # 移除舊的腳本快捷鍵
        for script, info in self._script_hotkey_handlers.items():
            try:
                if "handler" in info:
                    keyboard.remove_hotkey(info["handler"])
            except Exception as ex:
                # 忽略移除失敗
                pass
        self._script_hotkey_handlers.clear()

        # 掃描所有腳本並註冊快捷鍵
        if not os.path.exists(self.script_dir):
            return
        
        scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        registered_scripts = 0
        failed_scripts = 0
        
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
                    try:
                        # 使用 lambda 捕獲當前的 script 值
                        handler = keyboard.add_hotkey(
                            hotkey,
                            lambda s=script: self._play_script_by_hotkey(s),
                            suppress=False,
                            trigger_on_release=False
                        )
                        
                        self._script_hotkey_handlers[script] = {
                            "script": script,
                            "hotkey": hotkey,
                            "handler": handler
                        }
                        registered_scripts += 1
                        self.log(f"已註冊腳本快捷鍵: {hotkey} → {script}")
                    except Exception as ex:
                        failed_scripts += 1
                        self.log(f"註冊腳本快捷鍵失敗 ({script}): {ex}")
            except Exception as ex:
                self.log(f"讀取腳本檔案失敗 ({script}): {ex}")
        
        # 總結註冊結果
        if registered_scripts > 0 or failed_scripts > 0:
            self.log(f"[腳本快捷鍵] 註冊完成: 成功 {registered_scripts}, 失敗 {failed_scripts}")

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
        """刷新腳本設定區左側列表（顯示檔名、快捷鍵和定時）"""
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
                
                # 讀取快捷鍵和定時
                hotkey = ""
                schedule_time = ""
                try:
                    path = os.path.join(self.script_dir, script_file)
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if "settings" in data:
                            if "script_hotkey" in data["settings"]:
                                hotkey = data["settings"]["script_hotkey"]
                            if "schedule_time" in data["settings"]:
                                schedule_time = data["settings"]["schedule_time"]
                except Exception:
                    pass
                
                # 插入到 Treeview（三欄：名稱、快捷鍵、定時）
                self.script_treeview.insert("", "end", values=(
                    script_name, 
                    hotkey if hotkey else "", 
                    schedule_time if schedule_time else ""
                ))
                
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
            self.refresh_script_listbox()
        elif idx == 2:
            self.global_setting_frame.place(x=0, y=0, anchor="nw")

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
        """刪除選中的腳本（支援多選）"""
        # 從 Treeview 獲取所有選中的項目
        selection = self.script_treeview.selection()
        
        if not selection:
            self.log("請先選擇要刪除的腳本。")
            return
        
        # 收集要刪除的腳本名稱
        scripts_to_delete = []
        for item in selection:
            values = self.script_treeview.item(item, "values")
            if values:
                script_name = values[0]  # 腳本名稱（不含副檔名）
                # 確保有 .json 副檔名
                if not script_name.endswith('.json'):
                    script_file = script_name + '.json'
                else:
                    script_file = script_name
                
                path = os.path.join(self.script_dir, script_file)
                if os.path.exists(path):
                    scripts_to_delete.append((script_name, script_file, path))
        
        if not scripts_to_delete:
            self.log("找不到可刪除的腳本檔案。")
            return
        
        # 確認刪除
        import tkinter.messagebox as messagebox
        if len(scripts_to_delete) == 1:
            # 單個腳本刪除
            script_name = scripts_to_delete[0][0]
            message = f"確定要刪除腳本「{script_name}」嗎？\n此操作無法復原！"
        else:
            # 多個腳本刪除
            script_list = "\n".join([f"• {s[0]}" for s in scripts_to_delete])
            message = f"確定要刪除以下 {len(scripts_to_delete)} 個腳本嗎？\n\n{script_list}\n\n此操作無法復原！"
        
        result = messagebox.askyesno(
            "確認刪除",
            message,
            icon='warning'
        )
        
        if not result:
            return
        
        # 執行刪除
        deleted_count = 0
        failed_count = 0
        
        for script_name, script_file, path in scripts_to_delete:
            try:
                os.remove(path)
                self.log(f"✓ 已刪除腳本：{script_name}")
                deleted_count += 1
                
                # 取消註冊此腳本的快捷鍵（如果有的話）
                if script_file in self._script_hotkey_handlers:
                    handler_info = self._script_hotkey_handlers[script_file]
                    try:
                        keyboard.remove_hotkey(handler_info.get('handler'))
                    except:
                        pass
                    del self._script_hotkey_handlers[script_file]
                    
            except Exception as ex:
                self.log(f"✗ 刪除腳本失敗 [{script_name}]: {ex}")
                failed_count += 1
        
        # 顯示總結
        if deleted_count > 0:
            self.log(f"[完成] 成功刪除 {deleted_count} 個腳本" + 
                    (f"，{failed_count} 個失敗" if failed_count > 0 else ""))
        
        # 重新整理列表
        self.refresh_script_listbox()
        self.refresh_script_list()
        
        # 清除相關 UI
        self.script_var.set('')
        self.hotkey_capture_var.set('')
        if hasattr(self, 'selected_script_line'):
            self.selected_script_line = None


    def open_visual_editor(self):
        """開啟腳本編輯器"""
        try:
            # ✅ 檢查編輯器模組是否可用
            if VisualScriptEditor is None:
                self.log("❌ 編輯器模組不可用，請檢查 text_script_editor.py 檔案")
                messagebox.showerror("錯誤", "無法載入腳本編輯器模組")
                return
            
            # 獲取當前選中的腳本
            script_path = None
            current_script = self.script_var.get()
            if current_script:
                script_path = os.path.join(self.script_dir, f"{current_script}.json")
                if not os.path.exists(script_path):
                    self.log(f"[警告] 找不到腳本檔案: {current_script}.json")
                    script_path = None
            
            # 檢查是否已經有編輯器視窗開啟
            if hasattr(self, 'visual_editor_window') and self.visual_editor_window and self.visual_editor_window.winfo_exists():
                # 如果已存在，將焦點切到該視窗
                self.visual_editor_window.focus_force()
                self.visual_editor_window.lift()
                self.log("[資訊] 編輯器已開啟,切換至視窗")
            else:
                # 建立新視窗並儲存引用
                self.visual_editor_window = VisualScriptEditor(self, script_path)
                self.log("[資訊] 已開啟腳本編輯器")
        except Exception as e:
            self.log(f"[錯誤] 無法開啟編輯器：{e}")
            import traceback
            error_detail = traceback.format_exc()
            self.log(f"錯誤詳情: {error_detail}")
            messagebox.showerror("錯誤", f"無法開啟腳本編輯器：\n\n{e}\n\n請查看日誌獲取詳細資訊")

    def open_schedule_settings(self):
        """開啟排程設定視窗"""
        # 檢查是否有選中的腳本
        selection = self.script_treeview.selection()
        if not selection:
            self.log("請先選擇一個腳本")
            return
        
        item = selection[0]
        values = self.script_treeview.item(item, "values")
        script_name = values[0]
        script_file = f"{script_name}.json"
        script_path = os.path.join(self.script_dir, script_file)
        
        if not os.path.exists(script_path):
            self.log(f"腳本檔案不存在：{script_file}")
            return
        
        # 讀取現有排程
        current_schedule = ""
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "settings" in data and "schedule_time" in data["settings"]:
                    current_schedule = data["settings"]["schedule_time"]
        except Exception as e:
            self.log(f"讀取腳本失敗：{e}")
            return
        
        # 創建排程設定視窗
        schedule_win = tk.Toplevel(self)
        schedule_win.title(f"設定排程 - {script_name}")
        schedule_win.geometry("500x350")  # 增加尺寸避免按鈕被遮住
        schedule_win.resizable(True, True)  # 允許調整大小
        schedule_win.minsize(450, 320)  # 設定最小尺寸
        schedule_win.grab_set()
        schedule_win.transient(self)
        set_window_icon(schedule_win)  # 設定視窗圖示
        
        # 居中顯示
        schedule_win.update_idletasks()
        x = (schedule_win.winfo_screenwidth() // 2) - (schedule_win.winfo_width() // 2)
        y = (schedule_win.winfo_screenheight() // 2) - (schedule_win.winfo_height() // 2)
        schedule_win.geometry(f"+{x}+{y}")
        
        # 標題
        title_frame = tb.Frame(schedule_win)
        title_frame.pack(fill="x", padx=20, pady=15)
        tb.Label(title_frame, text=f"腳本：{script_name}", 
                font=("Microsoft JhengHei", 12, "bold")).pack(anchor="w")
        
        # 時間選擇框架
        time_frame = tb.Frame(schedule_win)
        time_frame.pack(fill="x", padx=20, pady=10)
        
        tb.Label(time_frame, text="執行時間：", 
                font=("Microsoft JhengHei", 11)).pack(side="left", padx=5)
        
        # 小時下拉選單
        hour_var = tk.StringVar()
        hour_combo = tb.Combobox(time_frame, textvariable=hour_var, 
                                 values=[f"{i:02d}" for i in range(24)], 
                                 width=5, state="readonly")
        hour_combo.pack(side="left", padx=5)
        
        tb.Label(time_frame, text=":", font=("Microsoft JhengHei", 11)).pack(side="left")
        
        # 分鐘下拉選單
        minute_var = tk.StringVar()
        minute_combo = tb.Combobox(time_frame, textvariable=minute_var,
                                   values=[f"{i:02d}" for i in range(60)],
                                   width=5, state="readonly")
        minute_combo.pack(side="left", padx=5)
        
        # 設定當前值
        if current_schedule:
            try:
                parts = current_schedule.split(":")
                if len(parts) == 2:
                    hour_var.set(parts[0])
                    minute_var.set(parts[1])
                else:
                    hour_var.set("09")
                    minute_var.set("00")
            except:
                hour_var.set("09")
                minute_var.set("00")
        else:
            hour_var.set("09")
            minute_var.set("00")
        
        # 說明文字
        info_frame = tb.Frame(schedule_win)
        info_frame.pack(fill="x", padx=20, pady=10)
        info_text = "設定後，程式將在每天指定時間\n自動執行此腳本"
        tb.Label(info_frame, text=info_text, 
                font=("Microsoft JhengHei", 9), 
                foreground="#666").pack(anchor="w")
        
        # 按鈕框架
        btn_frame = tb.Frame(schedule_win)
        btn_frame.pack(fill="x", padx=20, pady=20)
        
        def save_schedule():
            hour = hour_var.get()
            minute = minute_var.get()
            
            if not hour or not minute:
                self.log("請選擇時間")
                return
            
            schedule_time = f"{hour}:{minute}"
            
            # 儲存到腳本
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if "settings" not in data:
                    data["settings"] = {}
                
                data["settings"]["schedule_time"] = schedule_time
                
                with open(script_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 更新排程管理器
                if hasattr(self, 'schedule_manager') and self.schedule_manager:
                    schedule_id = f"script_{script_name}"
                    self.schedule_manager.add_schedule(schedule_id, {
                        'name': script_name,
                        'type': 'daily',
                        'time': f"{hour}:{minute}:00",
                        'script': script_file,
                        'enabled': True,
                        'callback': self._execute_scheduled_script
                    })
                    self.log(f"✓ 已設定排程：{script_name} 每天 {schedule_time}")
                
                # 刷新列表
                self.refresh_script_listbox()
                schedule_win.destroy()
                
            except Exception as e:
                self.log(f"儲存排程失敗：{e}")
        
        def clear_schedule():
            # 清除排程
            try:
                with open(script_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if "settings" in data and "schedule_time" in data["settings"]:
                    del data["settings"]["schedule_time"]
                
                with open(script_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # 移除排程管理器中的排程
                if hasattr(self, 'schedule_manager') and self.schedule_manager:
                    schedule_id = f"script_{script_name}"
                    self.schedule_manager.remove_schedule(schedule_id)
                    self.log(f"✓ 已清除排程：{script_name}")
                
                # 刷新列表
                self.refresh_script_listbox()
                schedule_win.destroy()
                
            except Exception as e:
                self.log(f"清除排程失敗：{e}")
        
        tb.Button(btn_frame, text="確定", width=10, bootstyle=SUCCESS,
                 command=save_schedule).pack(side="left", padx=5)
        tb.Button(btn_frame, text="清除排程", width=10, bootstyle=WARNING,
                 command=clear_schedule).pack(side="left", padx=5)
        tb.Button(btn_frame, text="取消", width=10, bootstyle=SECONDARY,
                 command=schedule_win.destroy).pack(side="left", padx=5)

    def _load_all_schedules(self):
        """從所有腳本中載入排程設定"""
        if not hasattr(self, 'schedule_manager') or not self.schedule_manager:
            return
        
        try:
            if not os.path.exists(self.script_dir):
                return
            
            scripts = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
            loaded_count = 0
            
            for script_file in scripts:
                script_path = os.path.join(self.script_dir, script_file)
                try:
                    with open(script_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if "settings" in data and "schedule_time" in data["settings"]:
                        schedule_time = data["settings"]["schedule_time"]
                        script_name = os.path.splitext(script_file)[0]
                        schedule_id = f"script_{script_name}"
                        
                        self.schedule_manager.add_schedule(schedule_id, {
                            'name': script_name,
                            'type': 'daily',
                            'time': f"{schedule_time}:00",
                            'script': script_file,
                            'enabled': True,
                            'callback': self._execute_scheduled_script
                        })
                        loaded_count += 1
                except Exception as e:
                    self.log(f"載入排程失敗 ({script_file}): {e}")
            
            if loaded_count > 0:
                self.log(f"✓ 已載入 {loaded_count} 個排程")
        except Exception as e:
            self.log(f"載入排程失敗: {e}")
    
    def _execute_scheduled_script(self, script_file):
        """執行排程腳本的回調函數"""
        try:
            script_path = os.path.join(self.script_dir, script_file)
            if not os.path.exists(script_path):
                self.log(f"排程腳本不存在：{script_file}")
                return
            
            # 載入腳本
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.events = data.get("events", [])
            self.script_settings = data.get("settings", {})
            
            # 更新設定
            if "loop_count" in self.script_settings:
                try:
                    self.loop_count_var.set(str(self.script_settings["loop_count"]))
                except:
                    pass
            
            if "interval" in self.script_settings:
                try:
                    self.interval_var.set(str(self.script_settings["interval"]))
                except:
                    pass
            
            self.log(f"⏰ [排程執行] {script_file}")
            self.log(f"載入 {len(self.events)} 筆事件")
            
            # 自動開始回放
            self.after(500, self.play_record)
            
        except Exception as e:
            self.log(f"執行排程腳本失敗：{e}")
            import traceback
            self.log(f"錯誤詳情: {traceback.format_exc()}")

    def select_target_window(self):
        """開啟視窗選擇器，選定後只錄製該視窗內的滑鼠動作"""
        try:
            if WindowSelectorDialog is None:
                self.log("❌ 視窗選擇器模組不可用，無法選擇視窗。")
                messagebox.showerror("錯誤", "無法載入視窗選擇器模組")
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
        except Exception as e:
            self.log(f"[錯誤] 無法開啟視窗選擇器：{e}")
            import traceback
            self.log(f"錯誤詳情: {traceback.format_exc()}")
            messagebox.showerror("錯誤", f"無法開啟視窗選擇器：\n\n{e}")
    
    def _clear_target_window(self, event=None):
        """清除目標視窗設定（可由右鍵點擊觸發）"""
        self.target_hwnd = None
        self.target_title = None
        self.target_label.config(text="")
        # 告訴 core_recorder 取消視窗限定
        if hasattr(self.core_recorder, 'set_target_window'):
            self.core_recorder.set_target_window(None)
        self.log("已清除目標視窗設定")

    def _refresh_target_window(self, event=None):
        """刷新目標視窗（可由左鍵點擊觸發）- 以相同視窗名稱重新指定"""
        if not self.target_title:
            self.log("沒有目標視窗可刷新")
            return
        
        original_title = self.target_title
        self.log(f"正在搜尋視窗：{original_title}")
        
        # 搜尋所有可見視窗，找到符合標題的第一個
        found_hwnd = None
        
        def enum_callback(hwnd, _):
            nonlocal found_hwnd
            if found_hwnd:
                return True  # 已經找到，繼續枚舉但不處理
            
            try:
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                
                window_text = win32gui.GetWindowText(hwnd)
                if window_text and window_text == original_title:
                    found_hwnd = hwnd
                    return False  # 找到了，停止枚舉
            except Exception:
                pass
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, None)
        except Exception as e:
            self.log(f"枚舉視窗時發生錯誤：{e}")
        
        if found_hwnd:
            # 更新視窗控制碼
            self.target_hwnd = found_hwnd
            self.target_title = original_title
            self.target_label.config(text=f"視窗：{original_title}")
            
            # 通知 core_recorder
            if hasattr(self.core_recorder, 'set_target_window'):
                self.core_recorder.set_target_window(found_hwnd)
            
            # 顯示高亮邊框
            self.show_window_highlight(found_hwnd)
            self.log(f"已重新指定視窗：{original_title}")
        else:
            self.log(f"找不到名為「{original_title}」的視窗，請檢查視窗是否已關閉或更名")

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
            
            # 中央顯示提示文字（使用 Canvas 以避免被視窗大小限制）
            canvas = tk.Canvas(frm, bg="#000000", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            
            # 計算適當的字體大小（根據視窗大小）
            font_size = max(12, min(24, min(w, h) // 20))
            
            # 在 Canvas 上繪製文字（不受視窗大小限制）
            text = "✓ 已設定目標視窗"
            canvas.create_text(
                w // 2, h // 2,
                text=text,
                font=("Microsoft JhengHei", font_size, "bold"),
                fill="#00ff00",
                anchor="center"
            )
            
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