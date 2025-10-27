#ChroLens Studio - Lucienwooo
#& C:/Users/Lucien/AppData/Local/Programs/Python/Python313/python.exe c:/Users/Lucien/Documents/GitHub/ChroLens_Mimic/main/ChroLens_Mimic2.6.py
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
from ui import RecorderApp

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
from ui import RecorderApp

if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()