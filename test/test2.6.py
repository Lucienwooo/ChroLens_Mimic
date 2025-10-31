#ChroLens Studio - Lucienwooo
#python "c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\test\test2.6.py"
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


class ScriptEditorWindow(tk.Toplevel):
    """腳本編輯器視窗 - 使用動作列表方式編輯（參考 ChroLens_Sothoth）"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # 取得當前語言設定
        lang = parent.language_var.get() if hasattr(parent, 'language_var') else "繁體中文"
        self.lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        
        self.title(self.lang_map["ChroLens 腳本編輯器"])
        self.geometry("950x680")
        self.resizable(True, True)
        
        # 保持視窗在最上層（至少在主程式之上）
        self.transient(parent)
        self.attributes("-topmost", False)  # 不要永遠置頂，但保持在父視窗之上
        self.lift()  # 提升到最前面
        self.focus_force()  # 強制取得焦點
        
        # 動作列表
        self.actions = []
        
        # 匯入腳本解析器
        try:
            from script_parser import ScriptParser, ScriptExecutor
            self.parser = ScriptParser()
            self.executor = ScriptExecutor(logger=self.log_output)
        except ImportError as e:
            tk.messagebox.showerror("錯誤", f"無法載入 script_parser 模組：{e}")
            self.destroy()
            return
        
        self._create_ui()
        
    def _create_ui(self):
        """建立 UI 介面"""
        # 上方工具列
        toolbar = tb.Frame(self, padding=8)
        toolbar.pack(fill="x", side="top")
        
        tb.Button(toolbar, text="新增動作", bootstyle=PRIMARY, command=self.add_action, width=12).pack(side="left", padx=4)
        tb.Button(toolbar, text="▶ 執行", bootstyle=SUCCESS, command=self.run_script, width=10).pack(side="left", padx=4)
        tb.Button(toolbar, text="⏹ 停止", bootstyle=DANGER, command=self.stop_script, width=10).pack(side="left", padx=4)
        tb.Button(toolbar, text="� 儲存", bootstyle=INFO, command=self.save_script, width=10).pack(side="left", padx=4)
        tb.Button(toolbar, text="📂 載入", bootstyle=SECONDARY, command=self.load_script, width=10).pack(side="left", padx=4)
        tb.Button(toolbar, text="� 同步", bootstyle=WARNING, command=self.apply_to_parent, width=10).pack(side="left", padx=4)
        tb.Button(toolbar, text="�📖 語法說明", bootstyle=INFO, command=self.show_syntax_help, width=12).pack(side="left", padx=4)
        
        # 主要內容區（左右分割）
        main_frame = tb.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # 左側：動作列表區
        left_frame = tb.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)
        
        tb.Label(left_frame, text="動作列表：", font=("Microsoft JhengHei", 10, "bold")).pack(anchor="w", pady=(0,4))
        
        # 動作 Treeview
        tree_frame = tb.Frame(left_frame)
        tree_frame.pack(fill="both", expand=True)
        
        from tkinter import ttk
        columns = ("#", "command", "params", "delay")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20, selectmode="extended")
        self.tree.heading("#", text="序")
        self.tree.heading("command", text="指令")
        self.tree.heading("params", text="參數")
        self.tree.heading("delay", text="延遲(ms)")
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("command", width=150, anchor="w")
        self.tree.column("params", width=250, anchor="w")
        self.tree.column("delay", width=80, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        
        tree_scroll = tb.Scrollbar(tree_frame, command=self.tree.yview)
        tree_scroll.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=tree_scroll.set)
        
        # 綁定事件
        self.tree.bind("<Double-1>", self.on_tree_edit)
        self.tree.bind("<Delete>", self.on_tree_delete)
        
        # 右側：輸出區
        right_frame = tb.Frame(main_frame, width=300)
        right_frame.pack(side="right", fill="both", padx=(8,0))
        right_frame.pack_propagate(False)
        
        tb.Label(right_frame, text="執行輸出：", font=("Microsoft JhengHei", 10, "bold")).pack(anchor="w", pady=(0,4))
        
        # 輸出文字框
        output_frame = tb.Frame(right_frame)
        output_frame.pack(fill="both", expand=True)
        
        self.output_text = tk.Text(output_frame, font=("Microsoft JhengHei", 9), wrap="word", state="disabled")
        self.output_text.pack(side="left", fill="both", expand=True)
        
        output_scroll = tb.Scrollbar(output_frame, command=self.output_text.yview)
        output_scroll.pack(side="right", fill="y")
        self.output_text.config(yscrollcommand=output_scroll.set)
    
    def add_action(self):
        """新增空白動作到列表末端"""
        # 直接新增一個純空白動作
        self.actions.append({
            "command": "",
            "params": "",
            "delay": "0"
        })
        self.update_tree()
        
        # 自動選擇最後一個項目
        children = self.tree.get_children()
        if children:
            last_item = children[-1]
            self.tree.selection_set(last_item)
            self.tree.see(last_item)
    
    def update_tree(self):
        """更新 Treeview"""
        self.tree.delete(*self.tree.get_children())
        for idx, act in enumerate(self.actions, 1):
            self.tree.insert("", "end", values=(
                idx,
                act.get("command", ""),
                act.get("params", ""),
                act.get("delay", "0")
            ))
    
    def on_tree_edit(self, event):
        """雙擊編輯動作 - 開啟完整編輯視窗"""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        values = self.tree.item(item, "values")
        idx = int(values[0]) - 1
        act = self.actions[idx]
        
        # 開啟完整編輯視窗
        win = tk.Toplevel(self)
        win.title("編輯動作")
        win.geometry("550x550")  # 增大尺寸
        win.resizable(True, True)  # 允許調整大小
        win.grab_set()
        
        # 主框架（支持響應式布局）
        main_frame = tb.Frame(win)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 指令選擇區域
        tb.Label(main_frame, text="選擇指令：", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w", pady=(0, 10))
        
        command_var = tk.StringVar(value=act.get("command", ""))
        commands = [
            ("", "空白（無動作）"),
            ("move_to", "移動滑鼠"),
            ("click", "點擊"),
            ("double_click", "雙擊"),
            ("right_click", "右鍵"),
            ("type_text", "輸入文字"),
            ("press_key", "按鍵"),
            ("delay", "延遲"),
            ("log", "日誌")
        ]
        
        # 使用 Scrollable Frame 以防選項過多
        cmd_frame = tb.Frame(main_frame)
        cmd_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        for cmd, desc in commands:
            rb = tb.Radiobutton(cmd_frame, text=f"{cmd if cmd else '(空白)'} - {desc}", variable=command_var, value=cmd)
            rb.pack(anchor="w", padx=10, pady=2)
        
        # 分隔線
        separator1 = tb.Separator(main_frame, orient="horizontal")
        separator1.pack(fill="x", pady=10)
        
        # 參數輸入區域
        param_frame = tb.Frame(main_frame)
        param_frame.pack(fill="x", pady=5)
        
        tb.Label(param_frame, text="參數：", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w")
        params_var = tk.StringVar(value=act.get("params", ""))
        params_entry = tb.Entry(param_frame, textvariable=params_var, font=("Microsoft JhengHei", 10))
        params_entry.pack(fill="x", pady=5)
        
        tb.Label(param_frame, text="範例: move_to → 100, 200 | type_text → Hello", 
                font=("Microsoft JhengHei", 8), foreground="#888").pack(anchor="w")
        
        # 延遲輸入區域
        delay_frame = tb.Frame(main_frame)
        delay_frame.pack(fill="x", pady=10)
        
        tb.Label(delay_frame, text="延遲(1000=1秒)後執行：", font=("Microsoft JhengHei", 11, "bold")).pack(anchor="w")
        delay_var = tk.StringVar(value=act.get("delay", "0"))
        tb.Entry(delay_frame, textvariable=delay_var, width=20, font=("Microsoft JhengHei", 10)).pack(anchor="w", pady=5)
        
        # 分隔線
        separator2 = tb.Separator(main_frame, orient="horizontal")
        separator2.pack(fill="x", pady=10)
        
        def confirm():
            act["command"] = command_var.get()
            act["params"] = params_var.get().strip()
            act["delay"] = delay_var.get().strip()
            self.update_tree()
            win.destroy()
        
        # 按鈕框架
        btn_frame = tb.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        tb.Button(btn_frame, text="確定", bootstyle=SUCCESS, width=15, command=confirm).pack(side="left", padx=5)
        tb.Button(btn_frame, text="取消", bootstyle=SECONDARY, width=15, command=win.destroy).pack(side="left", padx=5)
    
    def on_tree_delete(self, event):
        """刪除選中的動作"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # 從後往前刪除以保持索引正確
        indices = [int(self.tree.item(item, "values")[0]) - 1 for item in selected]
        for idx in sorted(indices, reverse=True):
            self.actions.pop(idx)
        
        self.update_tree()
    
    def _get_example_script(self):
        """取得範例腳本"""
        return """# ChroLens 腳本範例
# 支援中文、日文、英文指令
# 支援的指令：
#   move_to(x, y) / 移動(x, y)     - 移動滑鼠到座標
#   click() / 點擊()               - 左鍵點擊
#   double_click() / 雙擊()        - 雙擊
#   right_click() / 右鍵()         - 右鍵點擊
#   type_text("文字") / 輸入("文字") - 輸入文字
#   press_key("按鍵") / 按鍵("按鍵") - 按鍵
#   delay(毫秒) / 延遲(毫秒)        - 延遲
#   log("訊息") / 日誌("訊息")     - 輸出日誌

# === 範例 1：使用中文指令 ===
日誌("開始執行腳本")
延遲(1000)

# 移動滑鼠到開始按鈕並點擊
移動(50, 1050)  # 這個是開始按鈕的位置
點擊()
延遲(500)

# 輸入 notepad 並按 Enter
輸入("notepad")
延遲(500)
按鍵("enter")
延遲(2000)

# 在記事本中輸入文字
輸入("Hello from ChroLens!")
延遲(500)

日誌("腳本執行完成")

# === 範例 2：混合使用中英文 ===
# log("可以混合使用不同語言的指令")
# move_to(500, 300)
# 點擊()
# delay(1000)
"""
    
    def run_script(self):
        """執行腳本（從動作列表轉換為腳本程式碼並執行）"""
        if not self.actions:
            self.log_output("[提示] 動作列表為空，請先新增動作")
            return
        
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.config(state="disabled")
        
        self.log_output("[資訊] 開始執行腳本...")
        
        # 將動作列表轉換為腳本程式碼
        script_code = self._actions_to_script()
        
        # 在新執行緒中執行
        import threading
        thread = threading.Thread(target=lambda: self.executor.execute(script_code))
        thread.daemon = True
        thread.start()
    
    def _actions_to_script(self):
        """將動作列表轉換為腳本程式碼"""
        lines = []
        for act in self.actions:
            command = act.get("command", "")
            params = act.get("params", "")
            delay = act.get("delay", "0")
            
            # 產生指令行
            if command in ["move_to", "click", "double_click", "right_click", "type_text", "press_key", "log"]:
                if params:
                    lines.append(f"{command}({params})")
                else:
                    lines.append(f"{command}()")
            elif command == "delay":
                delay_val = params if params else delay
                lines.append(f"delay({delay_val})")
            
            # 添加額外延遲（如果有的話且 > 0）
            if delay and delay != "0" and command != "delay":
                lines.append(f"delay({delay})")
        
        return "\n".join(lines)
    
    def stop_script(self):
        """停止腳本執行"""
        if hasattr(self, 'executor'):
            self.executor.stop()
            self.log_output("[資訊] 已停止腳本")
    
    def save_script(self):
        """儲存腳本到檔案（JSON格式），並同步回主程式"""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("ChroLens Script", "*.json"), ("All Files", "*.*")],
            initialdir=self.parent.script_dir
        )
        if filepath:
            try:
                # 將動作列表儲存為 JSON
                script_data = {
                    "events": [],  # 預留給錄製的事件
                    "settings": {
                        "script_actions": self.actions,  # 儲存動作列表
                        "script_code": self._actions_to_script(),  # 也儲存轉換後的腳本程式碼以供相容
                        "speed": 100,
                        "repeat": 1
                    }
                }
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(script_data, f, ensure_ascii=False, indent=2)
                self.log_output(f"[成功] 已儲存至：{filepath}")
                
                # 同步回主程式
                self.apply_to_parent()
                
                # 刷新主程式的腳本列表
                self.parent.refresh_script_list()
                self.parent.refresh_script_listbox()
            except Exception as e:
                self.log_output(f"[錯誤] 儲存失敗：{e}")
    
    def load_script(self):
        """從檔案載入腳本（支援JSON格式）"""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            filetypes=[("ChroLens Script", "*.json"), ("All Files", "*.*")],
            initialdir=self.parent.script_dir
        )
        
        # 重新聚焦到編輯器視窗
        self.lift()
        self.focus_force()
        
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self.log_output(f"[資訊] 檔案已載入，開始解析...")
                self.log_output(f"[資訊] 檔案包含的鍵: {list(data.keys())}")
                
                # 優先檢查是否包含動作列表
                if "settings" in data and "script_actions" in data["settings"]:
                    self.actions = data["settings"]["script_actions"]
                    self.log_output(f"[資訊] 檢測到動作列表格式，共 {len(self.actions)} 個動作")
                    self.update_tree()
                    self.log_output(f"[成功] 已載入動作列表：{filepath}")
                # 檢查是否包含 script_code（舊格式相容）
                elif "settings" in data and "script_code" in data["settings"]:
                    # 將腳本程式碼轉換為動作列表
                    code = data["settings"]["script_code"]
                    self.log_output(f"[資訊] 檢測到腳本程式碼格式")
                    self.actions = self._script_to_actions(code)
                    self.update_tree()
                    self.log_output(f"[成功] 已載入腳本（已轉換為動作列表）：{filepath}")
                elif "events" in data:
                    # 如果是錄製的 JSON，轉換為動作列表
                    self.log_output(f"[資訊] 檢測到錄製事件格式，共 {len(data['events'])} 個事件")
                    self.actions = self._events_to_actions(data["events"])
                    self.log_output(f"[資訊] 轉換後得到 {len(self.actions)} 個動作")
                    self.update_tree()
                    self.log_output(f"[成功] 已從錄製事件轉換為動作列表：{filepath}")
                else:
                    self.log_output("[錯誤] 無法識別的檔案格式")
                    self.log_output(f"[錯誤] 預期包含 'script_actions'、'script_code' 或 'events' 鍵")
                    return
            except Exception as e:
                self.log_output(f"[錯誤] 載入失敗：{e}")
                import traceback
                self.log_output(f"[錯誤] 詳細錯誤: {traceback.format_exc()}")
    
    def _script_to_actions(self, code):
        """將腳本程式碼轉換為動作列表（簡單解析）"""
        actions = []
        for line in code.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 簡單解析
            if '(' in line and ')' in line:
                command = line[:line.index('(')].strip()
                params = line[line.index('(')+1:line.rindex(')')].strip()
                actions.append({
                    "command": command,
                    "params": params,
                    "delay": "0"
                })
        return actions
    
    def _events_to_actions(self, events):
        """將錄製的事件轉換為動作列表"""
        if not events:
            self.log_output("[警告] 事件列表為空")
            return []
        
        actions = []
        last_time = events[0].get('time', 0)
        
        self.log_output(f"[資訊] 開始轉換 {len(events)} 個事件...")
        
        # 添加詳細調試：檢查前3個事件的結構
        for i in range(min(3, len(events))):
            self.log_output(f"[調試] 事件 #{i}: {events[i]}")
        
        # 統計事件類型
        event_types = {}
        for event in events:
            event_type = event.get('type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        self.log_output(f"[資訊] 事件類型統計: {event_types}")
        
        for idx, event in enumerate(events):
            try:
                event_type = event.get('type', '')
                x, y = event.get('x', 0), event.get('y', 0)
                current_time = event.get('time', 0)
                
                # 計算延遲
                delay_ms = int((current_time - last_time) * 1000) if current_time > last_time else 0
                last_time = current_time
                
                # 轉換事件為動作
                if event_type == 'mouse_move':
                    actions.append({
                        "command": "move_to",
                        "params": f"{x}, {y}",
                        "delay": str(max(0, delay_ms))
                    })
                elif event_type == 'mouse_click':
                    button = event.get('button', 'left')
                    pressed = event.get('pressed', True)
                    # 只處理按下事件，避免重複
                    if pressed:
                        if button == 'left':
                            actions.append({
                                "command": "click",
                                "params": f"{x}, {y}",
                                "delay": str(max(0, delay_ms))
                            })
                        elif button == 'right':
                            actions.append({
                                "command": "right_click",
                                "params": f"{x}, {y}",
                                "delay": str(max(0, delay_ms))
                            })
                elif event_type == 'mouse_double_click':
                    actions.append({
                        "command": "double_click",
                        "params": f"{x}, {y}",
                        "delay": str(max(0, delay_ms))
                    })
                elif event_type == 'key_press':
                    key = event.get('key', '')
                    if key:
                        # 特殊按鍵
                        actions.append({
                            "command": "press_key",
                            "params": key,
                            "delay": str(max(0, delay_ms))
                        })
                elif event_type == 'scroll':
                    # 滾輪事件
                    delta = event.get('delta', 0)
                    actions.append({
                        "command": "scroll",
                        "params": str(delta),
                        "delay": str(max(0, delay_ms))
                    })
            except Exception as e:
                self.log_output(f"[錯誤] 轉換事件 #{idx} 時發生錯誤: {e}")
                continue
        
        self.log_output(f"[成功] 已轉換 {len(actions)} 個動作")
        return actions
    
    def show_syntax_help(self):
        """顯示語法說明（可複製的列表視窗）"""
        help_text = """ChroLens 腳本語法說明
====================

基本指令（支援中英日文）：
------------------------
move_to(x, y) / 移動(x, y) / 移動する(x, y)
    移動滑鼠到螢幕座標 (x, y)

click() / 點擊() / クリック()
    滑鼠左鍵點擊

double_click() / 雙擊() / ダブルクリック()
    滑鼠左鍵雙擊

right_click() / 右鍵() / 右クリック()
    滑鼠右鍵點擊

type_text("文字") / 輸入("文字") / 入力("文字")
    輸入文字（支援中英日文）

press_key("按鍵") / 按鍵("按鍵") / キー押下("按鍵")
    按下指定按鍵
    範例: "enter", "tab", "esc", "f1"

delay(毫秒) / 延遲(毫秒) / 待機(毫秒)
    延遲指定時間（1000 = 1秒）

log("訊息") / 日誌("訊息") / ログ("訊息")
    在輸出區顯示訊息

註解：
-----
# 這是單行註解
# 可以用來說明腳本內容，不影響執行

範例腳本：
---------
# 開啟小畫家並畫圖（中文指令）
移動(50, 1050)
點擊()
延遲(500)
輸入("mspaint")
按鍵("enter")
延遲(2000)
日誌("小畫家已開啟")

# 混合使用也可以
move_to(100, 200)  # 這個是遊戲選單的X
點擊()             # 點擊開始
delay(1000)        # 等待載入
"""
        
        # 建立語法說明視窗
        help_window = tk.Toplevel(self)
        help_window.title("ChroLens 腳本語法說明")
        help_window.geometry("750x650")  # 增大尺寸
        help_window.resizable(True, True)  # 允許調整大小
        help_window.minsize(600, 400)  # 設置最小尺寸
        
        # 建立文字框（可選取和複製）
        text_frame = tb.Frame(help_window)
        text_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        help_text_widget = tk.Text(text_frame, font=("Consolas", 10), wrap="word")
        help_text_widget.pack(side="left", fill="both", expand=True)
        
        scrollbar = tb.Scrollbar(text_frame, command=help_text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        help_text_widget.config(yscrollcommand=scrollbar.set)
        
        # 插入語法說明文字
        help_text_widget.insert("1.0", help_text)
        help_text_widget.config(state="disabled")  # 設為唯讀但仍可選取
        
        # 關閉按鈕
        tb.Button(help_window, text="關閉", bootstyle=SECONDARY, command=help_window.destroy, width=15).pack(pady=(0, 10))
    
    def log_output(self, message):
        """輸出日誌到輸出區"""
        self.output_text.config(state="normal")
        self.output_text.insert("end", message + "\n")
        self.output_text.see("end")
        self.output_text.config(state="disabled")
    
    def load_from_events(self, events):
        """從主程式載入事件並轉換為動作列表"""
        self.actions = self._events_to_actions(events)
        self.update_tree()
    
    def apply_to_parent(self):
        """將編輯後的動作列表應用回主程式"""
        if not hasattr(self, 'parent') or not self.parent:
            self.log_output("[錯誤] 無法連結到主程式")
            return
        
        # 檢查主程式是否有目標視窗（用於判斷是否使用相對座標）
        has_target_window = hasattr(self.parent, 'target_hwnd') and self.parent.target_hwnd
        
        # 將動作列表轉換為事件格式
        events = []
        current_time = time.time()
        
        for act in self.actions:
            command = act.get("command", "")
            params = act.get("params", "")
            delay = int(act.get("delay", "0"))
            
            # 跳過空白指令
            if not command:
                continue
            
            # 根據指令類型建立事件
            if command == "move_to" and params:
                try:
                    coords = [int(x.strip()) for x in params.split(',')]
                    if len(coords) >= 2:
                        event = {
                            "type": "mouse_move",
                            "x": coords[0],
                            "y": coords[1],
                            "time": current_time
                        }
                        # 如果有目標視窗，標記為相對座標
                        if has_target_window:
                            event["relative_to_window"] = True
                        events.append(event)
                        current_time += delay / 1000.0
                except:
                    pass
            elif command == "click":
                # 檢查是否有座標參數
                x, y = 0, 0
                if params:
                    try:
                        coords = [int(c.strip()) for c in params.split(',')]
                        if len(coords) >= 2:
                            x, y = coords[0], coords[1]
                    except:
                        pass
                
                event = {
                    "type": "mouse_click",
                    "button": "left",
                    "pressed": True,
                    "x": x,
                    "y": y,
                    "time": current_time
                }
                if has_target_window and (x != 0 or y != 0):
                    event["relative_to_window"] = True
                events.append(event)
                current_time += delay / 1000.0
            elif command == "double_click":
                # 檢查座標
                x, y = 0, 0
                if params:
                    try:
                        coords = [int(c.strip()) for c in params.split(',')]
                        if len(coords) >= 2:
                            x, y = coords[0], coords[1]
                    except:
                        pass
                
                event = {
                    "type": "mouse_double_click",
                    "button": "left",
                    "x": x,
                    "y": y,
                    "time": current_time
                }
                if has_target_window and (x != 0 or y != 0):
                    event["relative_to_window"] = True
                events.append(event)
                current_time += delay / 1000.0
            elif command == "right_click":
                # 檢查座標
                x, y = 0, 0
                if params:
                    try:
                        coords = [int(c.strip()) for c in params.split(',')]
                        if len(coords) >= 2:
                            x, y = coords[0], coords[1]
                    except:
                        pass
                
                event = {
                    "type": "mouse_click",
                    "button": "right",
                    "pressed": True,
                    "x": x,
                    "y": y,
                    "time": current_time
                }
                if has_target_window and (x != 0 or y != 0):
                    event["relative_to_window"] = True
                events.append(event)
                current_time += delay / 1000.0
            elif command in ["type_text", "press_key"] and params:
                # 移除引號
                text = params.strip('"').strip("'")
                events.append({
                    "type": "key_press" if command == "press_key" else "text_input",
                    "key" if command == "press_key" else "text": text,
                    "time": current_time
                })
                current_time += delay / 1000.0
        
        # 更新主程式的事件
        self.parent.events = events
        self.parent.log(f"[腳本編輯器] 已同步 {len(events)} 個事件到主程式")
        self.log_output(f"[成功] 已同步 {len(events)} 個事件到主程式")



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

        # 設定最小視窗尺寸並允許彈性調整
        self.minsize(900, 550)  # 最小尺寸限制，確保功能不被遮擋
        self.geometry("900x550")  # 初始尺寸
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

        self.script_combo.bind("<<ComboboxSelected>>", self.on_script_selected)


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
            width=25  # 限制最大寬度
        )
        self.target_label.pack(side="left", padx=(0, 4))

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
        
        # d) 腳本編輯器按鈕：開啟腳本編輯器視窗
        self.edit_script_btn = tb.Button(self.script_right_frame, text="腳本編輯器", width=16, bootstyle=INFO, command=self.open_script_editor)
        self.edit_script_btn.pack(anchor="w", pady=4)

        # 初始化清單
        self.refresh_script_listbox()

        # ====== 整體設定頁面 ======
        self.global_setting_frame = tb.Frame(self.page_content_frame)
        
        self.btn_hotkey = tb.Button(self.global_setting_frame, text="快捷鍵", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=15, style="My.TButton")
        self.btn_hotkey.pack(anchor="w", pady=4, padx=8)
        
        self.about_btn = tb.Button(self.global_setting_frame, text="關於", width=15, style="My.TButton", command=self.show_about_dialog, bootstyle=SECONDARY)
        self.about_btn.pack(anchor="w", pady=4, padx=8)
        
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
        # 腳本管理按鈕
        if hasattr(self, 'rename_btn'):
            self.rename_btn.config(text=lang_map["重新命名"])
        if hasattr(self, 'select_target_btn'):
            self.select_target_btn.config(text=lang_map["選擇視窗"])
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
            
            idx = getattr(self, "_current_play_index", 0)
            if idx == 0 or not self.events:
                elapsed = 0
            else:
                # 防止 index 超出範圍
                if idx > len(self.events):
                    idx = len(self.events)
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
                if hasattr(self, 'mini_window') and self.mini_window and self.mini_window.winfo_exists():
                    if hasattr(self, "mini_countdown_label"):
                        lang = self.language_var.get()
                        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
                        h = int(total_remain // 3600)
                        m = int((total_remain % 3600) // 60)
                        s = int(total_remain % 60)
                        time_str = f"{h:02d}:{m:02d}:{s:02d}"
                        try:
                            self.mini_countdown_label.config(text=f"{lang_map['剩餘']}: {time_str}")
                        except Exception:
                            pass
            self.after(100, self._update_play_time)
        else:
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
        
        # 記錄目標視窗的大小和位置
        self.recorded_window_size = None
        self.recorded_window_pos = None
        if self.target_hwnd:
            try:
                import win32gui
                rect = win32gui.GetWindowRect(self.target_hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                self.recorded_window_size = (width, height)
                self.recorded_window_pos = (rect[0], rect[1])
                self.log(f"記錄視窗大小: {width} x {height}, 位置: ({rect[0]}, {rect[1]})")
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
        
        # 檢查視窗大小和位置（如果有記錄的話）
        if self.target_hwnd:
            try:
                import win32gui
                from tkinter import messagebox
                rect = win32gui.GetWindowRect(self.target_hwnd)
                current_width = rect[2] - rect[0]
                current_height = rect[3] - rect[1]
                current_x, current_y = rect[0], rect[1]
                
                size_mismatch = False
                pos_mismatch = False
                
                # 檢查大小
                if hasattr(self, 'recorded_window_size') and self.recorded_window_size:
                    recorded_width, recorded_height = self.recorded_window_size
                    if current_width != recorded_width or current_height != recorded_height:
                        size_mismatch = True
                
                # 檢查位置
                if hasattr(self, 'recorded_window_pos') and self.recorded_window_pos:
                    recorded_x, recorded_y = self.recorded_window_pos
                    if current_x != recorded_x or current_y != recorded_y:
                        pos_mismatch = True
                
                # 如果大小或位置不同，詢問使用者
                if size_mismatch or pos_mismatch:
                    # 創建自定義對話框
                    dialog = tk.Toplevel(self)
                    dialog.title("視窗狀態不符")
                    dialog.geometry("550x400")  # 增大高度以容納所有內容
                    dialog.resizable(True, True)  # 允許調整大小
                    dialog.grab_set()
                    dialog.transient(self)
                    
                    # 居中顯示
                    dialog.update_idletasks()
                    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
                    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
                    dialog.geometry(f"+{x}+{y}")
                    
                    # 主框架（使用 pack 布局以支持響應式）
                    main_frame = tb.Frame(dialog)
                    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
                    
                    # 標題
                    title_label = tb.Label(main_frame, 
                        text="⚠️ 偵測到視窗狀態不同！", 
                        font=("Microsoft JhengHei", 12, "bold"))
                    title_label.pack(pady=(0, 15))
                    
                    # 訊息內容框架
                    msg_frame = tb.Frame(main_frame)
                    msg_frame.pack(fill="both", expand=True)
                    
                    # 訊息內容
                    msg = ""
                    if size_mismatch:
                        msg += f"大小 - 錄製時: {recorded_width} x {recorded_height}\n"
                        msg += f"        目前: {current_width} x {current_height}\n\n"
                    if pos_mismatch:
                        msg += f"位置 - 錄製時: ({recorded_x}, {recorded_y})\n"
                        msg += f"        目前: ({current_x}, {current_y})\n"
                    
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
                    
                    def on_relative():
                        user_choice["action"] = "relative"
                        dialog.destroy()
                    
                    def on_cancel():
                        user_choice["action"] = "cancel"
                        dialog.destroy()
                    
                    btn_frame = tb.Frame(main_frame)
                    btn_frame.pack(fill="x", pady=10)
                    
                    tb.Button(btn_frame, text="強制歸位並回放", bootstyle=PRIMARY, 
                             command=on_force_adjust, width=20).pack(pady=5, fill="x")
                    tb.Button(btn_frame, text="保持當前位置回放", bootstyle=SUCCESS, 
                             command=on_relative, width=20).pack(pady=5, fill="x")
                    tb.Button(btn_frame, text="取消回放", bootstyle=DANGER, 
                             command=on_cancel, width=20).pack(pady=5, fill="x")
                    
                    # 添加說明（放在最下方）
                    info_label = tb.Label(main_frame, 
                        text="💡 提示：選擇「保持當前位置回放」會使用視窗內相對座標", 
                        font=("Microsoft JhengHei", 9), 
                        foreground="#666",
                        wraplength=500)  # 自動換行
                    info_label.pack(pady=(10, 0))
                    
                    dialog.wait_window()
                    
                    # 處理使用者選擇
                    if user_choice["action"] == "cancel":
                        self.log("已取消回放")
                        return
                    elif user_choice["action"] == "adjust":
                        # 強制歸位
                        try:
                            target_x = recorded_x if pos_mismatch else current_x
                            target_y = recorded_y if pos_mismatch else current_y
                            target_width = recorded_width if size_mismatch else current_width
                            target_height = recorded_height if size_mismatch else current_height
                            
                            win32gui.SetWindowPos(
                                self.target_hwnd,
                                0,  # HWND_TOP
                                target_x, target_y,
                                target_width, target_height,
                                0x0240  # SWP_SHOWWINDOW | SWP_ASYNCWINDOWPOS
                            )
                            
                            adjust_msg = []
                            if size_mismatch:
                                adjust_msg.append(f"大小至 {target_width} x {target_height}")
                            if pos_mismatch:
                                adjust_msg.append(f"位置至 ({target_x}, {target_y})")
                            
                            self.log(f"已調整視窗{' 和 '.join(adjust_msg)}")
                            self.log("將在 2 秒後開始回放...")
                            
                            # 延遲 2 秒後繼續
                            self.after(2000, self._continue_play_record)
                            return
                        except Exception as e:
                            self.log(f"無法調整視窗: {e}")
                    elif user_choice["action"] == "relative":
                        # 使用視窗內相對座標回放（不需要額外處理，因為座標已經是相對的）
                        self.log(f"將使用視窗內相對座標進行回放")
            except Exception as e:
                self.log(f"檢查視窗狀態時發生錯誤: {e}")
        
        # 直接開始回放
        self._continue_play_record()
    
    def _continue_play_record(self):
        """實際執行回放的內部方法"""
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
        
        # 轉換事件座標
        adjusted_events = []
        for event in self.events:
            event_copy = event.copy()
            
            # 檢查是否為視窗相對座標
            if event.get('relative_to_window', False) and 'x' in event and 'y' in event:
                # 將視窗相對座標轉換為當前螢幕絕對座標
                event_copy['x'] = event['x'] + current_window_x
                event_copy['y'] = event['y'] + current_window_y
            
            adjusted_events.append(event_copy)
        
        # 設定 core_recorder 的事件
        self.core_recorder.events = adjusted_events
        
        if self.target_hwnd and any(e.get('relative_to_window', False) for e in self.events):
            self.log(f"已將 {len(adjusted_events)} 個視窗相對座標轉換為當前螢幕座標")

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
            # 記錄視窗大小（如果有的話）
            if hasattr(self, 'recorded_window_size') and self.recorded_window_size:
                settings["window_size"] = self.recorded_window_size
            
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
                # 恢復參數
                self.speed_var.set(settings.get("speed", "100"))
                self.repeat_var.set(settings.get("repeat", "1"))
                self.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
                self.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
                self.random_interval_var.set(settings.get("random_interval", False))
                
                # 讀取視窗大小
                if "window_size" in settings:
                    self.recorded_window_size = tuple(settings["window_size"])
                else:
                    self.recorded_window_size = None
                
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
                        
                        # 讀取視窗大小
                        if "window_size" in settings:
                            self.recorded_window_size = tuple(settings["window_size"])
                        else:
                            self.recorded_window_size = None
                        
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
                hotkey = data.get("script_hotkey", "")
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
                self.mini_window.geometry("720x40")  # 增加寬度以容納勾選框
                self.mini_window.overrideredirect(True)
                self.mini_window.resizable(False, False)
                self.mini_window.attributes("-topmost", True)
                try:
                    import sys
                    if getattr(sys, 'frozen', False):
                        icon_path = os.path.join(sys._MEIPASS, "umi_奶茶色.ico")
                    else:
                        icon_path = "umi_奶茶色.ico"
                    self.mini_window.iconbitmap(icon_path)
                except Exception as e:
                    print(f"無法設定 MiniMode icon: {e}")
                
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
        script = self.script_var.get()
        hotkey = self.hotkey_capture_var.get().strip().lower()
        if not script or not hotkey or hotkey == "輸入按鍵":
            self.log("請先選擇腳本並輸入有效的快捷鍵。")
            return
        path = os.path.join(self.script_dir, script)
        try:
            # 讀取現有資料
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            
            # 儲存快捷鍵到腳本
            data["script_hotkey"] = hotkey
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 重新註冊所有腳本的快捷鍵
            self._register_script_hotkeys()
            
            self.log(f"已設定腳本 {script} 的快捷鍵：{hotkey}")
            self.log("提示：該快捷鍵將使用腳本內儲存的參數直接回放")
        except Exception as ex:
            self.log(f"設定腳本快捷鍵失敗: {ex}")

    def delete_selected_script(self):
        """刪除選中的腳本"""
        if not self.script_var.get():
            self.log("請先選擇要刪除的腳本。")
            return
        
        script = self.script_var.get()
        path = os.path.join(self.script_dir, script)
        
        try:
            os.remove(path)
            self.log(f"已刪除腳本：{script}")
            
            # 重新註冊腳本快捷鍵（會自動排除已刪除的腳本）
            self._register_script_hotkeys()
            
            self.refresh_script_listbox()
            self.refresh_script_list()
            
            # 清除相關 UI
            self.script_var.set('')
            self.hotkey_capture_var.set('')
            self.selected_script_line = None
        except Exception as ex:
            self.log(f"刪除腳本失敗: {ex}")

    def open_script_editor(self):
        """開啟腳本編輯器視窗（單例模式），並載入當前腳本"""
        # 檢查是否已經有腳本編輯器視窗開啟
        if hasattr(self, 'script_editor_window') and self.script_editor_window and self.script_editor_window.winfo_exists():
            # 如果已存在，將焦點切到該視窗
            self.script_editor_window.focus_force()
            self.script_editor_window.lift()
        else:
            # 建立新視窗並儲存引用
            self.script_editor_window = ScriptEditorWindow(self)
            
            # 如果當前有載入的腳本或事件，自動載入到編輯器
            if self.events:
                self.script_editor_window.load_from_events(self.events)
                self.script_editor_window.log_output(f"[資訊] 已載入當前腳本，共 {len(self.events)} 個事件")
    
    def sync_from_editor(self, actions):
        """從腳本編輯器同步動作回主程式"""
        # 將編輯器的動作列表轉換為事件並更新主程式
        self.script_editor_window.log_output("[資訊] 正在同步到主程式...")
        # 這裡可以實現從動作列表重建 events 的邏輯
        # 暫時保留原有事件結構
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
                self.target_hwnd = None
                self.target_title = None
                self.target_label.config(text="")
                # 告訴 core_recorder 取消視窗限定
                if hasattr(self.core_recorder, 'set_target_window'):
                    self.core_recorder.set_target_window(None)
                self.log("已清除目標視窗設定。")
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
            # 更新 UI 顯示
            short = title if len(title) <= 30 else title[:27] + "..."
            self.target_label.config(text=f"🎯 {short}")
            self.log(f"已選定目標視窗：{title} (hwnd={hwnd})")
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