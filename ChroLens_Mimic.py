#ChroLens Studio - Lucienwooo
#pyinstaller --noconsole --onedir --icon=觸手眼鏡貓.ico --add-data "觸手眼鏡貓.ico;." ChroLens_Mimic.py
#--onefile 單一檔案，啟動時間過久，改以"--onedir "方式打包，啟動較快
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
import threading, time, json, os, datetime
import keyboard, mouse
import ctypes
import win32api
import tkinter.filedialog
import sys
# ====== UI 介面 row 對應說明 ======
# row 0 (frm_top):開始錄製（btn_start）、暫停/繼續（btn_pause）、停止（btn_stop）、回放（btn_play）、TinyMode（tiny_mode_btn）、skin下拉選單（theme_combo）、關於（about_btn）
# row 1 (frm_bottom):回放速度（speed_var 輸入框）、腳本路徑（open_scripts_dir 按鈕）、快捷鍵（open_hotkey_settings 按鈕）、關於（about_btn）
# row 2 (frm_repeat):重複次數（repeat_var 輸入框）、單位「次」
# row 3 (frm_script):腳本選單（script_combo）、腳本重新命名輸入框（rename_entry）、修改腳本名稱（rename_script 按鈕）
# row 4 (frm_log):滑鼠座標（mouse_pos_label）、錄製時間（time_label）、單次剩餘（countdown_label）、總運作時間（total_time_label）
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

def format_time(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")

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

class RecorderApp(tb.Window):
    def show_about_dialog(self):
        about_win = tb.Toplevel(self)
        about_win.title("關於 ChroLens_Mimic")
        about_win.geometry("450x300")
        about_win.resizable(False, False)
        about_win.grab_set()
        # 置中顯示
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 175
        y = self.winfo_y() + 80
        about_win.geometry(f"+{x}+{y}")

        # 設定icon與主程式相同
        try:
            import sys, os
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "觸手眼鏡貓.ico")
            else:
                icon_path = "觸手眼鏡貓.ico"
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

    def __init__(self):
        self.user_config = load_user_config()
        skin = self.user_config.get("skin", "darkly")
        super().__init__(themename=skin)
        self._hotkey_handlers = {}
        self.tiny_window = None

        # 統一字體 style
        self.style.configure("My.TButton", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TLabel", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TEntry", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TCombobox", font=("Microsoft JhengHei", 9))
        self.style.configure("My.TCheckbutton", font=("Microsoft JhengHei", 9))
        self.style.configure("TinyBold.TButton", font=("Microsoft JhengHei", 9, "bold"))

        self.title("ChroLens_Mimic_2.1")
        try:
            import sys, os
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "觸手眼鏡貓.ico")
            else:
                icon_path = "觸手眼鏡貓.ico"
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"無法設定 icon: {e}")

        # 在左上角建立一個小label作為icon區域的懸浮觸發點
        self.icon_tip_label = tk.Label(self, width=2, height=1, bg=self.cget("background"))
        self.icon_tip_label.place(x=0, y=0)
        Tooltip(self.icon_tip_label, f"{self.title()}_By_Lucien")

        self.geometry("900x550")
        self.resizable(False, False)
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

        # 快捷鍵設定，新增 tiny
        self.hotkey_map = {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "tiny": "alt+`"
        }

        # ====== 上方操作區 ======
        frm_top = tb.Frame(self, padding=(10, 10, 10, 5))
        frm_top.pack(fill="x")

        self.btn_start = tb.Button(frm_top, text=f"開始錄製 ({self.hotkey_map['start']})", command=self.start_record, bootstyle=PRIMARY, width=14, style="My.TButton")
        self.btn_start.grid(row=0, column=0, padx=4)
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
        theme_combo.grid(row=0, column=8, padx=(0, 4), sticky="e")
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.change_theme())

        # TinyMode 按鈕（skin下拉選單左側）
        self.tiny_mode_btn = tb.Button(
            frm_top, text="TinyMode", style="TinyBold.TButton",
            command=self.toggle_tiny_mode, width=10
        )
        self.tiny_mode_btn.grid(row=0, column=7, padx=(0, 4), sticky="e")

        # ====== 下方操作區 ======
        frm_bottom = tb.Frame(self, padding=(10, 0, 10, 5))
        frm_bottom.pack(fill="x")
        tb.Label(frm_bottom, text="回放速度:", style="My.TLabel").grid(row=0, column=0, padx=(0,2))
        self.speed_var = tk.StringVar(value=self.user_config.get("speed", "1.0"))
        tb.Entry(frm_bottom, textvariable=self.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=2)
        tb.Button(frm_bottom, text="腳本路徑", command=self.use_default_script_dir, bootstyle=SECONDARY, width=10, style="My.TButton").grid(row=0, column=3, padx=4)
        tb.Button(frm_bottom, text="快捷鍵", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=10, style="My.TButton").grid(row=0, column=4, padx=4)

        # ====== 新增「關於」按鈕（移到快捷鍵右側） ======
        self.about_btn = tb.Button(
            frm_bottom, text="關於", width=6, style="My.TButton",
            command=self.show_about_dialog, bootstyle=SECONDARY
        )
        self.about_btn.grid(row=0, column=5, padx=(0, 2), sticky="e")


        # ====== 重複次數設定 ======
        self.repeat_var = tk.StringVar(value=self.user_config.get("repeat", "1"))
        frm_repeat = tb.Frame(self, padding=(10, 0, 10, 5))
        frm_repeat.pack(fill="x")
        tb.Label(frm_repeat, text="重複次數:", style="My.TLabel").grid(row=0, column=0, padx=(0,2))
        self.repeat_var = tk.StringVar(value=self.user_config.get("repeat", "1"))
        tb.Entry(frm_repeat, textvariable=self.repeat_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=2)
        tb.Label(frm_repeat, text="次", style="My.TLabel").grid(row=0, column=2, padx=(0,2))

        # 新增重複時間欄位
        self.repeat_time_var = tk.StringVar(value="00:00:00")
        repeat_time_entry = tb.Entry(frm_repeat, textvariable=self.repeat_time_var, width=10, style="My.TEntry", justify="center")
        repeat_time_entry.grid(row=0, column=3, padx=(10,2))
        tb.Label(frm_repeat, text="重複時間", style="My.TLabel").grid(row=0, column=4, padx=(0,2))

        # 只允許輸入數字與冒號
        def validate_time_input(P):
            import re
            return re.fullmatch(r"[\d:]*", P) is not None
        vcmd = (self.register(validate_time_input), "%P")
        repeat_time_entry.config(validate="key", validatecommand=vcmd)

        # 當重複時間變動時，更新總運作時間顯示
        def on_repeat_time_change(*args):
            t = self.repeat_time_var.get()
            seconds = self._parse_time_to_seconds(t)
            if seconds > 0:
                self.update_total_time_label(seconds)
            else:
                # 若為 0 則恢復原本計算
                self.update_total_time_label(0)
        self.repeat_time_var.trace_add("write", on_repeat_time_change)

        # ====== 腳本選單區 ======
        frm_script = tb.Frame(self, padding=(10, 0, 10, 5))
        frm_script.pack(fill="x")
        tb.Label(frm_script, text="腳本選單:", style="My.TLabel").grid(row=0, column=0, sticky="w")
        self.script_var = tk.StringVar(value=self.user_config.get("last_script", ""))
        self.script_combo = tb.Combobox(frm_script, textvariable=self.script_var, width=30, state="readonly", style="My.TCombobox")
        self.script_combo.grid(row=0, column=1, sticky="w", padx=4)
        self.rename_var = tk.StringVar()
        self.rename_entry = tb.Entry(frm_script, textvariable=self.rename_var, width=20, style="My.TEntry")
        self.rename_entry.grid(row=0, column=2, padx=4)
        tb.Button(frm_script, text="修改腳本名稱", command=self.rename_script, bootstyle=WARNING, width=12, style="My.TButton").grid(row=0, column=3, padx=4)

        self.script_combo.bind("<<ComboboxSelected>>", self.on_script_selected)
        self.refresh_script_list()
        if self.script_var.get():
            self.on_script_selected()

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
        self.time_label = tb.Label(log_title_frame, text="錄製: 00:00.0", font=("Consolas", 12, ), foreground="#15D3BD")
        self.time_label.pack(side="right", padx=8)
        self.countdown_label = tb.Label(log_title_frame, text="單次: 00:00.0", font=("Consolas", 12, ), foreground="#DB0E59")
        self.countdown_label.pack(side="right", padx=8)
        self.total_time_label = tb.Label(log_title_frame, text="總共: 00:00.0", font=("Consolas", 12, ), foreground="#FF95CA")
        self.total_time_label.pack(side="right", padx=8)

        self.log_text = tb.Text(frm_log, height=24, width=110, state="disabled", font=("Microsoft JhengHei", 9))
        self.log_text.pack(fill="both", expand=True, pady=(4,0))
        log_scroll = tb.Scrollbar(frm_log, command=self.log_text.yview)
        log_scroll.pack(side="left", fill="y")
        self.log_text.config(yscrollcommand=log_scroll.set)

        # ====== 其餘初始化 ======
        # 這裡再呼叫 refresh_script_list 和 on_script_selected
        self.refresh_script_list()
        if self.script_var.get():
            self.on_script_selected()

        self.after(1500, self._delayed_init)  

    def _delayed_init(self):
        self.after(1600, self._register_hotkeys)         
        self.after(1700, self.refresh_script_list)      
        self.after(1800, self.load_last_script)         
        self.after(1900, self.update_mouse_pos)         

    def save_config(self):
        self.user_config["skin"] = self.theme_var.get()
        self.user_config["last_script"] = self.script_var.get()
        self.user_config["repeat"] = self.repeat_var.get()
        self.user_config["speed"] = self.speed_var.get()
        self.user_config["script_dir"] = self.script_dir
        save_user_config(self.user_config)

    def change_theme(self):
        self.style.theme_use(self.theme_var.get())
        self.save_config()

    def log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_time_label(self, seconds):
        m = int(seconds // 60)
        s = seconds % 60
        self.time_label.config(text=f"{m:02d}:{s:04.1f}")

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
        if self.recording or self.playing:
            self.paused = not self.paused
            state = "暫停" if self.paused else "繼續"
            mode = "錄製" if self.recording else "回放"
            self.log(f"[{format_time(time.time())}] {mode}{state}。")

    def _record_thread(self):
        import keyboard
        from pynput.mouse import Controller, Listener
        try:
            self._mouse_events = []
            self._recording_mouse = True
            self._record_start_time = time.time()

            # 先啟動 keyboard 與 mouse 監聽
            keyboard.start_recording()

            mouse_ctrl = Controller()
            last_pos = mouse_ctrl.position

            def on_click(x, y, button, pressed):
                if self._recording_mouse and not self.paused:
                    self._mouse_events.append({
                        'type': 'mouse',
                        'event': 'down' if pressed else 'up',
                        'button': str(button).replace('Button.', ''),
                        'x': x,
                        'y': y,
                        'time': time.time()
                    })
            def on_scroll(x, y, dx, dy):
                if self._recording_mouse and not self.paused:
                    self._mouse_events.append({
                        'type': 'mouse',
                        'event': 'wheel',
                        'delta': dy,
                        'x': x,
                        'y': y,
                        'time': time.time()
                    })
            import pynput.mouse
            mouse_listener = pynput.mouse.Listener(
                on_click=on_click,
                on_scroll=on_scroll
            )
            mouse_listener.start()

            # 立即記錄當下滑鼠位置（避免剛開始沒動作時漏記）
            now = time.time()
            self._mouse_events.append({
                'type': 'mouse',
                'event': 'move',
                'x': last_pos[0],
                'y': last_pos[1],
                'time': now
            })

            while self.recording:
                now = time.time()
                pos = mouse_ctrl.position
                if pos != last_pos:
                    self._mouse_events.append({
                        'type': 'mouse',
                        'event': 'move',
                        'x': pos[0],
                        'y': pos[1],
                        'time': now
                    })
                    last_pos = pos
                time.sleep(MOUSE_SAMPLE_INTERVAL)
            self._recording_mouse = False
            mouse_listener.stop()
            k_events = keyboard.stop_recording()

            filtered_k_events = [
                e for e in k_events
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

    def _wait_record_thread_finish(self):
        if hasattr(self, '_record_thread_handle') and self._record_thread_handle.is_alive():
            self.after(100, self._wait_record_thread_finish)
        else:
            self.auto_save_script()

    def play_record(self):
        import keyboard
        import mouse
        if self.playing or not self.events:
            return
        try:
            self.speed = float(self.speed_var.get())
        except:
            self.speed = 1.0

        # 取得重複時間（秒）
        repeat_time_sec = self._parse_time_to_seconds(self.repeat_time_var.get())
        self._repeat_time_limit = repeat_time_sec if repeat_time_sec > 0 else None

        try:
            repeat = int(self.repeat_var.get())
            if repeat == 0:
                repeat = -1  # -1 代表無限次數
            elif repeat < 0:
                repeat = 1
        except:
            repeat = 1

        # 設定總運作時間
        if self._repeat_time_limit:
            self._total_play_time = self._repeat_time_limit
        elif self.events:
            total = (self.events[-1]['time'] - self.events[0]['time']) / self.speed
            self._total_play_time = total * (99999 if repeat == -1 else repeat)
        else:
            self._total_play_time = 0

        self._play_start_time = time.time()
        self._play_total_time = self._total_play_time
        self.update_total_time_label(self._total_play_time)
        self.log(f"[{format_time(time.time())}] 開始回放，速度倍率: {self.speed}")
        self.playing = True
        self.paused = False
        self._repeat_times = repeat
        threading.Thread(target=self._play_thread, daemon=True).start()
        self.after(100, self._update_play_time)

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
            self.countdown_label.config(text=f"{int(remain//60):02d}:{remain%60:04.1f}")
            # 倒數顯示
            if hasattr(self, "_play_start_time"):
                if self._repeat_time_limit:
                    total_remain = max(0, self._repeat_time_limit - (time.time() - self._play_start_time))
                else:
                    total_remain = max(0, self._total_play_time - (time.time() - self._play_start_time))
                self.update_total_time_label(total_remain)
            self.after(100, self._update_play_time)
        else:
            self.update_time_label(0)
            self.countdown_label.config(text="00:00.0")
            self.update_total_time_label(0)

    def update_total_time_label(self, seconds):
        m = int(seconds // 60)
        s = seconds % 60
        self.total_time_label.config(text=f"總運作: {m:02d}:{s:04.1f}")

    def _play_thread(self):
        self.playing = True
        self.paused = False
        repeat = getattr(self, "_repeat_times", 1)
        count = 0
        play_start_time = time.time()
        while self.playing and (repeat == -1 or count < repeat):
            # 若有時間限制，檢查是否超時
            if hasattr(self, "_repeat_time_limit") and self._repeat_time_limit:
                if time.time() - play_start_time >= self._repeat_time_limit:
                    break
            self._current_play_index = 0
            total_events = len(self.events)
            if total_events == 0 or not self.playing:
                break
            base_time = self.events[0]['time']
            play_start = time.time()
            while self._current_play_index < total_events:
                # 若有時間限制，檢查是否超時
                if hasattr(self, "_repeat_time_limit") and self._repeat_time_limit:
                    if time.time() - play_start_time >= self._repeat_time_limit:
                        self.log("重複時間到，已自動停止回放。")
                        self.playing = False
                        break
                if not self.playing:
                    break  # 強制中斷回放
                while self.paused:
                    if not self.playing:
                        break  # 強制中斷回放
                    time.sleep(0.05)
                    play_start += 0.05  # 修正暫停期間的基準時間
                if not self.playing:
                    break  # 強制中斷回放
                i = self._current_play_index
                e = self.events[i]
                event_offset = (e['time'] - base_time) / self.speed
                target_time = play_start + event_offset
                while True:
                    now = time.time()
                    # 若有時間限制，檢查是否超時
                    if hasattr(self, "_repeat_time_limit") and self._repeat_time_limit:
                        if now - play_start_time >= self._repeat_time_limit:
                            self.log("重複時間到，已自動停止回放。")
                            self.playing = False
                            break
                    if not self.playing:
                        break  # 強制中斷回放
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
                    break  # 強制中斷回放
                if e['type'] == 'keyboard':
                    if e['event'] == 'down':
                        keyboard.press(e['name'])
                    elif e['event'] == 'up':
                        keyboard.release(e['name'])
                    self.log(f"[{format_time(e['time'])}] 鍵盤: {e['event']} {e['name']}")
                elif e['type'] == 'mouse':
                    if e.get('event') == 'move':
                        move_mouse_abs(e['x'], e['y'])
                    elif e.get('event') == 'down':
                        mouse_event_win('down', button=e.get('button', 'left'))
                        self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                    elif e.get('event') == 'up':
                        mouse_event_win('up', button=e.get('button', 'left'))
                        self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                    elif e.get('event') == 'wheel':
                        mouse_event_win('wheel', delta=e.get('delta', 0))
                        self.log(f"[{format_time(e['time'])}] 滑鼠: {e}")
                self._current_play_index += 1
            if not self.playing:
                break  # 強制中斷回放
            count += 1
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

    def auto_save_script(self):
        try:
            ts = datetime.datetime.now().strftime("%Y_%m%d_%H%M_%S")
            filename = f"{ts}.json"
            path = os.path.join(self.script_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.events, f, ensure_ascii=False, indent=2)
            self.log(f"[{format_time(time.time())}] 自動存檔：{filename}，事件數：{len(self.events)}")
            self.refresh_script_list()
            self.script_var.set(filename)
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(filename)
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] 存檔失敗: {ex}")

    def load_script(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], initialdir=SCRIPTS_DIR)
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.events = json.load(f)
            self.log(f"[{format_time(time.time())}] 腳本已載入：{os.path.basename(path)}，共 {len(self.events)} 筆事件。")
            self.refresh_script_list()
            self.script_var.set(os.path.basename(path))
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(os.path.basename(path))

    def on_script_selected(self, event=None):
        script = self.script_var.get()
        if script:
            path = os.path.join(SCRIPTS_DIR, script)
            with open(path, "r", encoding="utf-8") as f:
                self.events = json.load(f)
            self.log(f"[{format_time(time.time())}] 腳本已載入：{script}，共 {len(self.events)} 筆事件。")
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(script)
        self.save_config()

    def refresh_script_list(self):
        files = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        self.script_combo['values'] = files
        # 若目前選擇的腳本不存在於新資料夾，清空選擇
        if self.script_var.get() not in files:
            self.script_var.set("")

    def load_last_script(self):
        if os.path.exists(LAST_SCRIPT_FILE):
            with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
                last_script = f.read().strip()
            if last_script:
                script_path = os.path.join(SCRIPTS_DIR, last_script)
                if os.path.exists(script_path):
                    with open(script_path, "r", encoding="utf-8") as f:
                        self.events = json.load(f)
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
        old_path = os.path.join(SCRIPTS_DIR, old_name)
        new_path = os.path.join(SCRIPTS_DIR, new_name)
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
        path = os.path.abspath(SCRIPTS_DIR)
        os.startfile(path)

    def open_hotkey_settings(self):
        win = tb.Toplevel(self)
        win.title("快捷鍵設定")
        win.geometry("340x280")
        win.resizable(False, False)

        labels = {
            "start": "開始錄製",
            "pause": "暫停/繼續",
            "stop": "停止錄製",
            "play": "回放",
            "tiny": "TinyMode"
        }
        vars = {}
        entries = {}
        row = 0

        def on_entry_key(event, key, var):
            # 只記錄實際按下的組合鍵或單鍵
            keys = []
            # 只在有修飾鍵時才加
            if event.state & 0x0001: keys.append("shift")
            if event.state & 0x0004: keys.append("ctrl")
            if event.state & 0x0008: keys.append("alt")
            key_name = event.keysym.lower()
            # 避免 shift/ctrl/alt 單獨被記錄
            if key_name not in ("shift_l", "shift_r", "control_l", "control_r", "alt_l", "alt_r"):
                keys.append(key_name)
            # 組合成快捷鍵字串
            var.set("+".join(keys))
            return "break"

        def on_entry_release(event, key, var):
            # 只記錄釋放時的單一鍵
            key_name = event.keysym.lower()
            # 避免 shift/ctrl/alt 單獨被記錄
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
            entry = tb.Entry(win, textvariable=var, width=16, font=("Consolas", 11), state="normal")
            entry.grid(row=row, column=1, padx=10)
            vars[key] = var
            entries[key] = entry
            # 綁定事件
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
            self.log("快捷鍵設定已更新。")
            win.destroy()

        tb.Button(win, text="儲存", command=save_and_apply, width=10, bootstyle=SUCCESS).grid(row=row, column=0, columnspan=2, pady=16)

    # 不再需要 _make_hotkey_entry_handler

    def _register_hotkeys(self):
        for handler in self._hotkey_handlers.values():
            try:
                keyboard.remove_hotkey(handler)
            except Exception:
                pass
        self._hotkey_handlers.clear()
        for key, hotkey in self.hotkey_map.items():
            try:
                handler = keyboard.add_hotkey(hotkey, getattr(self, {
                    "start": "start_record",
                    "pause": "toggle_pause",
                    "stop": "stop_all",
                    "play": "play_record",
                    "tiny": "toggle_tiny_mode"  # <--- 加這行
                }[key]))
                self._hotkey_handlers[key] = handler
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")

    def _update_hotkey_labels(self):
        self.btn_start.config(text=f"開始錄製 ({self.hotkey_map['start']})")
        self.btn_pause.config(text=f"暫停/繼續 ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=f"停止 ({self.hotkey_map['stop']})")
        self.btn_play.config(text=f"回放 ({self.hotkey_map['play']})")
        # TinyMode 按鈕同步更新
        if hasattr(self, "tiny_btns"):
            for btn, icon, key in self.tiny_btns:
                btn.config(text=f"{icon} {self.hotkey_map[key]}")

    def toggle_tiny_mode(self):
        # 切換 TinyMode 狀態
        if not hasattr(self, "tiny_mode_on"):
            self.tiny_mode_on = False
        self.tiny_mode_on = not self.tiny_mode_on
        if self.tiny_mode_on:
            if self.tiny_window is None or not self.tiny_window.winfo_exists():
                self.tiny_window = tb.Toplevel(self)
                self.tiny_window.title("ChroLens_Mimic TinyMode")
                self.tiny_window.geometry("470x40")
                self.tiny_window.overrideredirect(True)
                self.tiny_window.resizable(False, False)
                self.tiny_window.attributes("-topmost", True)
                try:
                    self.tiny_window.iconbitmap("觸手眼鏡貓.ico")
                except Exception as e:
                    print(f"無法設定 TinyMode icon: {e}")
                self.tiny_btns = []
                # 拖曳功能
                self.tiny_window.bind("<ButtonPress-1>", self._start_move_tiny)
                self.tiny_window.bind("<B1-Motion>", self._move_tiny)
                btn_defs = [
                    ("⏺", "start"),
                    ("⏸", "pause"),
                    ("⏹", "stop"),
                    ("▶︎", "play"),
                    ("⤴︎", "tiny")
                ]
                for i, (icon, key) in enumerate(btn_defs):
                    btn = tb.Button(
                        self.tiny_window,
                        text=f"{icon} {self.hotkey_map[key]}",
                        width=7, style="My.TButton",
                        command=getattr(self, {
                            "start": "start_record",
                            "pause": "toggle_pause",
                            "stop": "stop_all",
                            "play": "play_record",
                            "tiny": "toggle_tiny_mode"
                        }[key])
                    )
                    btn.grid(row=0, column=i, padx=2, pady=5)
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

CONFIG_FILE = "user_config.json"

def load_user_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 預設值
    return {
        "skin": "darkly",
        "last_script": "",
        "repeat": "1",
        "speed": "1.0",
        "script_dir": SCRIPTS_DIR
    }

def save_user_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()