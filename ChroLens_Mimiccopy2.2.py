#ChroLens Studio - Lucienwooo
#pyinstaller --noconsole --onedir --icon=觸手眼鏡貓.ico --add-data "觸手眼鏡貓.ico;." ChroLens_Mimic2.1.py
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
import copy

SCRIPTS_DIR = "scripts"
LAST_SCRIPT_FILE = "last_script.txt"
LAST_SKIN_FILE = "last_skin.txt"
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
    _repeat_time_limit = None
    _total_play_time = 0
    _play_start_time = None
    _record_start_time = None
    events = []
    playing = False
    paused = False
    recording = False
    speed = 1.0
    script_dir = SCRIPTS_DIR

    def _parse_time_to_seconds(self, time_str):
        try:
            parts = [int(x) for x in time_str.strip().split(":")]
            if len(parts) == 3:
                h, m, s = parts
            elif len(parts) == 2:
                h = 0
                m, s = parts
            elif len(parts) == 1:
                h = 0
                m = 0
                s = parts[0]
            else:
                return 0
            return h * 3600 + m * 60 + s
        except Exception:
            return 0

    def use_default_script_dir(self):
        import tkinter.filedialog
        path = tkinter.filedialog.askdirectory(title="選擇Script資料夾")
        if path:
            self.script_dir = path
            self.refresh_script_list()
            self.save_config()

    # TinyMode 完整功能
    def toggle_tiny_mode(self):
        if not hasattr(self, "tiny_mode_on"):
            self.tiny_mode_on = False
        self.tiny_mode_on = not self.tiny_mode_on
        if self.tiny_mode_on:
            if getattr(self, "tiny_window", None) is None or not self.tiny_window.winfo_exists():
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
        if getattr(self, "tiny_window", None) and self.tiny_window.winfo_exists():
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

    def open_merge_window(self):
        import tkinter.messagebox
        from tkinter import ttk
        lang_map = LANG_MAP[self.language_var.get()]
        win = tb.Toplevel(self)
        win.title(lang_map["Script工具"])
        win.geometry("1000x550")
        win.resizable(True, True)
        win.configure(bg=self.style.colors.bg)

        main_frame = tb.Frame(win, padding=10)
        main_frame.pack(fill="both", expand=True)

        # 左側：Script清單
        left_frame = tb.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        # 移除「所有Script」Label，直接放排序選單
        sort_var = tk.StringVar(value="建立時間(新→舊)")
        sort_options = [
            "建立時間(新→舊)", "建立時間(舊→新)",
            "名稱A-Z", "名稱Z-A"
        ]
        def get_sorted_files():
            files = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
            if sort_var.get() == "建立時間(新→舊)":
                files.sort(key=lambda f: os.path.getctime(os.path.join(self.script_dir, f)), reverse=True)
            elif sort_var.get() == "建立時間(舊→新)":
                files.sort(key=lambda f: os.path.getctime(os.path.join(self.script_dir, f)))
            elif sort_var.get() == "名稱A-Z":
                files.sort()
            elif sort_var.get() == "名稱Z-A":
                files.sort(reverse=True)
            return files

        def refresh_all_listbox():
            all_listbox.delete(0, "end")
            files = get_sorted_files()
            for f in files:
                all_listbox.insert("end", os.path.splitext(f)[0])

        sort_combo = tb.Combobox(left_frame, textvariable=sort_var, values=sort_options, state="readonly", width=14)
        sort_combo.pack(anchor="w", pady=(2, 2))
        sort_combo.bind("<<ComboboxSelected>>", lambda e: refresh_all_listbox())

        all_files = get_sorted_files()
        all_listbox = tk.Listbox(left_frame, selectmode="extended", width=21, height=15, font=("Consolas", 11))
        for f in all_files:
            all_listbox.insert("end", os.path.splitext(f)[0])
        all_listbox.pack(fill="y", expand=True, pady=(4, 0))

        # 中間按鈕
        btn_frame = tb.Frame(main_frame)
        btn_frame.grid(row=0, column=1, sticky="ns")
        btn_add = tb.Button(btn_frame, text=lang_map["加入"], width=8)
        btn_add.pack(pady=(30, 6))
        btn_remove = tb.Button(btn_frame, text=lang_map["移除"], width=8)
        btn_remove.pack(pady=6)
        btn_up = tb.Button(btn_frame, text="↑ " + lang_map.get("", ""), width=8)
        btn_up.pack(pady=6)
        btn_down = tb.Button(btn_frame, text="↓ " + lang_map.get("", ""), width=8)
        btn_down.pack(pady=6)
        btn_clear = tb.Button(btn_frame, text=lang_map["清空"], width=8)
        btn_clear.pack(pady=6)

        # 新增紅色「刪除」按鈕
        def on_delete_script():
            selected = all_listbox.curselection()
            files = get_sorted_files()
            if not selected:
                tkinter.messagebox.showinfo("提示", "請先選擇要刪除的Script。")
                return
            for i in reversed(selected):
                fname = files[i]
                path = os.path.join(self.script_dir, fname)
                try:
                    os.remove(path)
                    self.log(f"已刪除Script：{display_filename(fname)}")
                except Exception as e:
                    tkinter.messagebox.showerror("錯誤", f"刪除 {fname} 失敗: {e}")
            refresh_all_listbox()
            self.refresh_script_list()

        btn_delete = tb.Button(
            btn_frame,
            text=lang_map["刪除"],
            width=8,
            bootstyle="danger",  # 紅色
            command=on_delete_script
        )
        btn_delete.pack(pady=6)

        # 右側：合併清單（Treeview）
        right_frame = tb.Frame(main_frame)
        right_frame.grid(row=0, column=2, sticky="ns", padx=(8, 0))
        tb.Label(right_frame, text="編輯列表", font=("Microsoft JhengHei", 10, "bold")).pack(anchor="w")
        merge_tree = ttk.Treeview(right_frame, columns=("name", "repeat", "delay"), show="headings", height=15)
        merge_tree.heading("name", text="Script名稱")
        merge_tree.heading("repeat", text="重複")
        merge_tree.heading("delay", text="延遲")
        merge_tree.column("name", width=180, anchor="w")
        merge_tree.column("repeat", width=50, anchor="center")
        merge_tree.column("delay", width=50, anchor="center")
        merge_tree.pack(fill="y", expand=True, pady=(4, 0))

        # 編輯區
        edit_frame = tb.Frame(main_frame)
        edit_frame.grid(row=1, column=2, sticky="ew", pady=(8, 0))
        tb.Label(edit_frame, text=lang_map["重複次數:"], font=("Microsoft JhengHei", 9)).grid(row=0, column=0, padx=2)
        repeat_var = tk.IntVar(value=1)
        repeat_entry = tb.Entry(edit_frame, textvariable=repeat_var, width=5, font=("Consolas", 10))
        repeat_entry.grid(row=0, column=1, padx=2)
        tb.Label(edit_frame, text=lang_map.get("延遲秒數:", "Delay(s):"), font=("Microsoft JhengHei", 9)).grid(row=0, column=2, padx=2)
        delay_var = tk.IntVar(value=0)
        delay_entry = tb.Entry(edit_frame, textvariable=delay_var, width=5, font=("Consolas", 10))
        delay_entry.grid(row=0, column=3, padx=2)
        btn_apply = tb.Button(edit_frame, text=lang_map["確定"], width=8)
        btn_apply.grid(row=0, column=4, padx=6)

        # 新Script名稱與合併按鈕
        options_frame = tb.Frame(win, padding=(10, 0, 10, 10))
        options_frame.pack(fill="x", side="bottom")
        tb.Label(options_frame, text=lang_map["新Script名稱："], font=("Microsoft JhengHei", 9)).grid(row=0, column=0, sticky="e")
        new_name_var = tk.StringVar(value="merged_script")
        tb.Entry(options_frame, textvariable=new_name_var, width=32).grid(row=0, column=1, sticky="w", padx=(4, 8))
        btn_merge_save = tb.Button(options_frame, text=lang_map["合併並儲存"], width=16, bootstyle=SUCCESS)
        btn_merge_save.grid(row=0, column=2, padx=8)

        # 資料結構：每一項為 dict {"fname":..., "repeat":..., "delay":...}
        merge_items = []

        def refresh_merge_tree():
            merge_tree.delete(*merge_tree.get_children())
            for idx, item in enumerate(merge_items):
                name = os.path.splitext(item['fname'])[0]
                merge_tree.insert("", "end", iid=idx, values=(name, item['repeat'], item['delay']))

        def on_add():
            selected = all_listbox.curselection()
            files = get_sorted_files()
            for i in selected:
                fname = files[i]
                merge_items.append({"fname": fname, "repeat": 1, "delay": 0})
            refresh_merge_tree()

        def on_remove():
            selected = merge_tree.selection()
            for iid in reversed(selected):
                merge_items.pop(int(iid))
            refresh_merge_tree()

        def on_clear():
            merge_items.clear()
            refresh_merge_tree()

        def on_up():
            selected = list(map(int, merge_tree.selection()))
            if not selected: return
            for i in selected:
                if i > 0:
                    merge_items[i-1], merge_items[i] = merge_items[i], merge_items[i-1]
            refresh_merge_tree()
            for i in [max(0, x-1) for x in selected]:
                merge_tree.selection_add(i)

        def on_down():
            selected = list(map(int, merge_tree.selection()))
            if not selected: return
            for i in reversed(selected):
                if i < len(merge_items)-1:
                    merge_items[i+1], merge_items[i] = merge_items[i], merge_items[i+1]
            refresh_merge_tree()
            for i in [min(len(merge_items)-1, x+1) for x in selected]:
                merge_tree.selection_add(i)

        def on_apply():
            selected = merge_tree.selection()
            if not selected: return
            try:
                repeat = max(1, int(repeat_var.get()))
            except Exception:
                repeat = 1
            try:
                delay = max(0, int(delay_var.get()))
            except Exception:
                delay = 0
            for iid in selected:
                idx = int(iid)
                merge_items[idx]["repeat"] = repeat
                merge_items[idx]["delay"] = delay
            refresh_merge_tree()

        def on_merge_save():
            merged = []
            current_time = 0
            for item in merge_items:
                try:
                    with open(os.path.join(self.script_dir, item["fname"]), "r", encoding="utf-8") as f:
                        events = json.load(f)
                    for _ in range(item["repeat"]):
                        if events:
                            base = events[0]['time']
                            for e in events:
                                # 每次都做 deepcopy，且直接 append 到 merged
                                new_event = copy.deepcopy(e)
                                new_event['time'] = (e['time'] - base) + current_time
                                merged.append(new_event)
                            current_time = merged[-1]['time']
                            if item["delay"] > 0:
                                current_time += item["delay"]
                except Exception as e:
                    tkinter.messagebox.showerror("錯誤", f"讀取 {item['fname']} 失敗: {e}")
                    return
            new_name = new_name_var.get().strip()
            if not new_name:
                tkinter.messagebox.showerror("錯誤", "請輸入新Script名稱。")
                return
            if not new_name.endswith(".json"):
                new_name += ".json"
            new_path = os.path.join(self.script_dir, new_name)
            if os.path.exists(new_path):
                tkinter.messagebox.showerror("錯誤", "檔案已存在，請換個新名稱。")
                return
            try:
                with open(new_path, "w", encoding="utf-8") as f:
                    json.dump(merged, f, ensure_ascii=False, indent=2)
                self.log(f"合併完成並儲存為：{new_name}，共 {len(merged)} 筆事件。")
                self.refresh_script_list()
                win.destroy()
            except Exception as e:
                tkinter.messagebox.showerror("錯誤", f"儲存失敗: {e}")

        def on_tree_select(event):
            selected = merge_tree.selection()
            if not selected: return
            idx = int(selected[0])
            repeat_var.set(merge_items[idx]["repeat"])
            delay_var.set(merge_items[idx]["delay"])

        btn_add.config(command=on_add)
        btn_remove.config(command=on_remove)
        btn_clear.config(command=on_clear)
        btn_up.config(command=on_up)
        btn_down.config(command=on_down)
        btn_apply.config(command=on_apply)
        btn_merge_save.config(command=on_merge_save)
        merge_tree.bind("<<TreeviewSelect>>", on_tree_select)

        refresh_merge_tree()
        # 在 open_merge_window 結尾呼叫 refresh_all_listbox 以確保初始排序
        refresh_all_listbox()

    def update_speed_tooltip(self):
        # 根據語言切換 Tooltip 內容
        lang = self.language_var.get()
        tips = {
            "繁體中文": "正常速度1倍=100,範圍1~1000",
            "日本語": "標準速度1倍=100、範囲1～1000",
            "English": "Normal speed 1x=100, range 1~1000"
        }
        tip_text = tips.get(lang, tips["繁體中文"])
        if hasattr(self, "speed_tooltip") and self.speed_tooltip:
            self.speed_tooltip.text = tip_text

    def change_language(self, event=None):
        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        self.btn_start.config(text=lang_map["開始錄製"] + f" ({self.hotkey_map['start']})")
        self.btn_pause.config(text=lang_map["暫停/繼續"] + f" ({self.hotkey_map['pause']})")
        self.btn_stop.config(text=lang_map["停止"] + f" ({self.hotkey_map['stop']})")
        self.btn_play.config(text=lang_map["回放"] + f" ({self.hotkey_map['play']})")
        self.tiny_mode_btn.config(text=lang_map["TinyMode"])
        self.btn_script_dir.config(text=lang_map["Script路徑"])
        self.btn_hotkey.config(text=lang_map["快捷鍵"])
        self.about_btn.config(text=lang_map["關於"])
        self.lbl_repeat.config(text=lang_map["重複次數:"])
        self.lbl_times.config(text=lang_map["次"])
        self.lbl_interval.config(text=lang_map["重複時間"])
        self.lbl_script.config(text=lang_map["Script:"])
        self.btn_rename.config(text=lang_map["重新命名"])
        self.btn_merge.config(text=lang_map["Script"])
        self.language_combo.config(values=list(LANG_MAP.keys()))
        self.lbl_speed.config(text=lang_map["回放速度:"] if "回放速度:" in lang_map else "回放速度:")
        self.update_speed_tooltip()
        # 只換前綴，保留原本時間格式
        self.total_time_label.config(text=f"{lang_map['總運作']}: 00:00:00")
        self.countdown_label.config(text=f"{lang_map['單次']}: 00:00:00")
        self.time_label.config(text=f"{lang_map['錄製']}: 00:00:00")
        self.lbl_single_time.config(text=f"{lang_map['單次']}: 00:00:00")
        self.save_config()
        self.update_idletasks()
        width = max(self.winfo_reqwidth() - 50, 400)
        self.geometry(f"{width}x{self.winfo_height()}")

    # 完整 About 視窗
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
        # 先初始化語言變數
        self.user_config = load_user_config()
        skin = self.user_config.get("skin", "darkly")
        super().__init__(themename=skin)
        self.language_var = tk.StringVar(self, value="繁體中文")
        self._hotkey_handlers = {}
        self.tiny_window = None
        self.language_var = tk.StringVar(self, value=self.user_config.get("language", "繁體中文"))
        self.hotkey_map = self.user_config.get("hotkey_map", {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "tiny": "alt+`"
        })
        self.speed_var = tk.StringVar(value=self.user_config.get("speed", "100"))

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

        self.icon_tip_label = tk.Label(self, width=2, height=1, bg=self.cget("background"))
        self.icon_tip_label.place(x=0, y=0)
        Tooltip(self.icon_tip_label, f"{self.title()}_By_Lucien")

        # 主視窗寬度自動調整
        self.update_idletasks()
        width = self.winfo_reqwidth() + 20
        height = 550
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
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

        themes = ["darkly", "cyborg", "superhero", "journal","minty", "united", "morph", "lumen"]
        self.theme_var = tk.StringVar(value=self.style.theme_use())
        theme_combo = tb.Combobox(frm_top, textvariable=self.theme_var, values=themes, state="readonly", width=6, style="My.TCombobox")
        theme_combo.grid(row=0, column=8, padx=(0, 4), sticky="e")
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.change_theme())

        self.tiny_mode_btn = tb.Button(
            frm_top, text="TinyMode", style="My.TButton",
            command=self.toggle_tiny_mode, width=10
        )
        self.tiny_mode_btn.grid(row=0, column=7, padx=(0, 4), sticky="e")

        # ====== 下方操作區 ======
        frm_bottom = tb.Frame(self, padding=(10, 0, 10, 5))
        frm_bottom.pack(fill="x")
        self.lbl_speed = tb.Label(frm_bottom, text="回放速度:", style="My.TLabel")
        self.lbl_speed.grid(row=0, column=0, padx=(0,2))
        self.speed_tooltip = Tooltip(self.lbl_speed, "正常速度1倍=100,範圍1~1000")
        self.update_speed_tooltip()
        self.speed_var = tk.StringVar(value="100")
        tb.Entry(frm_bottom, textvariable=self.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=2)
        self.btn_script_dir = tb.Button(frm_bottom, text="Script路徑", command=self.open_scripts_dir, bootstyle=SECONDARY, width=10, style="My.TButton")
        self.btn_script_dir.grid(row=0, column=3, padx=4)
        self.btn_hotkey = tb.Button(frm_bottom, text="快捷鍵", command=self.open_hotkey_settings, bootstyle=SECONDARY, width=10, style="My.TButton")
        self.btn_hotkey.grid(row=0, column=4, padx=4)
        self.about_btn = tb.Button(frm_bottom, text="關於", width=6, style="My.TButton", command=self.show_about_dialog, bootstyle=SECONDARY)
        self.about_btn.grid(row=0, column=5, padx=(0, 2), sticky="e")
        self.language_var = tk.StringVar(value="繁體中文")
        lang_combo = tb.Combobox(frm_bottom, textvariable=self.language_var, values=["繁體中文", "日本語", "English"], state="readonly", width=10, style="My.TCombobox")
        lang_combo.grid(row=0, column=6, padx=(0, 2), sticky="e")
        lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        self.language_combo = lang_combo

        # ====== 重複次數設定 ======
        frm_repeat = tb.Frame(self, padding=(10, 0, 10, 5))
        frm_repeat.pack(fill="x")
        self.lbl_repeat = tb.Label(frm_repeat, text="重複次數:", style="My.TLabel")
        self.lbl_repeat.grid(row=0, column=0, padx=(0,2))
        self.repeat_var = tk.StringVar(value="1")
        tb.Entry(frm_repeat, textvariable=self.repeat_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=2)
        self.lbl_times = tb.Label(frm_repeat, text="次", style="My.TLabel")
        self.lbl_times.grid(row=0, column=2, padx=(0,2))
        self.repeat_time_var = tk.StringVar(value="00:00:00")
        repeat_time_entry = tb.Entry(frm_repeat, textvariable=self.repeat_time_var, width=10, style="My.TEntry", justify="center")
        repeat_time_entry.grid(row=0, column=3, padx=(10,2))
        self.lbl_interval = tb.Label(frm_repeat, text="重複時間", style="My.TLabel")
        self.lbl_interval.grid(row=0, column=4, padx=(0,2))

        # ====== Script選單區 ======
        frm_script = tb.Frame(self, padding=(10, 0, 10, 5))
        frm_script.pack(fill="x")
        self.lbl_script = tb.Label(frm_script, text="Script:", style="My.TLabel")
        self.lbl_script.grid(row=0, column=0, sticky="w")
        self.script_var = tk.StringVar(value="")
        self.script_combo = tb.Combobox(frm_script, textvariable=self.script_var, width=24, style="My.TCombobox", state="readonly")
        self.script_combo.grid(row=0, column=1, padx=(2, 0))
        self.rename_var = tk.StringVar()
        self.rename_entry = tb.Entry(frm_script, textvariable=self.rename_var, width=20, style="My.TEntry")
        self.rename_entry.grid(row=0, column=2, padx=4)
        self.btn_rename = tb.Button(frm_script, text="重新命名", command=self.rename_script, bootstyle=WARNING, width=12, style="My.TButton")
        self.btn_rename.grid(row=0, column=3, padx=4)
        self.btn_merge = tb.Button(frm_script, text="Script", command=self.open_merge_window, bootstyle=INFO, width=8, style="My.TButton")
        self.btn_merge.grid(row=0, column=4, padx=4)

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
        self.mouse_pos_label.pack(side="left", padx=0)  # 取消間隔

        # 右側時間區用一個Frame包起來，讓三個時間靠右且彼此緊湊
        time_frame = tb.Frame(log_title_frame)
        time_frame.pack(side="right", padx=0)

        # 錄製
        self.time_label_title = tb.Label(time_frame, text="錄製", font=("Consolas", 12), foreground="#15D3BD")
        self.time_label_title.pack(side="left", padx=0)
        self.time_label_h = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.time_label_h.pack(side="left", padx=0)
        self.time_label_colon1 = tb.Label(time_frame, text=":", font=("Consolas", 12), foreground="#888888")
        self.time_label_colon1.pack(side="left", padx=0)
        self.time_label_m = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.time_label_m.pack(side="left", padx=0)
        self.time_label_colon2 = tb.Label(time_frame, text=":", font=("Consolas", 12), foreground="#888888")
        self.time_label_colon2.pack(side="left", padx=0)
        self.time_label_s = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.time_label_s.pack(side="left", padx=0)

        # 單次
        self.countdown_label_title = tb.Label(time_frame, text="單次", font=("Consolas", 12), foreground="#DB0E59")
        self.countdown_label_title.pack(side="left", padx=0)
        self.countdown_label_h = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.countdown_label_h.pack(side="left", padx=0)
        self.countdown_label_colon1 = tb.Label(time_frame, text=":", font=("Consolas", 12), foreground="#888888")
        self.countdown_label_colon1.pack(side="left", padx=0)
        self.countdown_label_m = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.countdown_label_m.pack(side="left", padx=0)
        self.countdown_label_colon2 = tb.Label(time_frame, text=":", font=("Consolas", 12), foreground="#888888")
        self.countdown_label_colon2.pack(side="left", padx=0)
        self.countdown_label_s = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.countdown_label_s.pack(side="left", padx=0)

        # 總運作
        self.total_time_label_title = tb.Label(time_frame, text="總運作", font=("Consolas", 12), foreground="#FF95CA")
        self.total_time_label_title.pack(side="left", padx=0)
        self.total_time_label_h = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.total_time_label_h.pack(side="left", padx=0)
        self.total_time_label_colon1 = tb.Label(time_frame, text=":", font=("Consolas", 12), foreground="#888888")
        self.total_time_label_colon1.pack(side="left", padx=0)
        self.total_time_label_m = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.total_time_label_m.pack(side="left", padx=0)
        self.total_time_label_colon2 = tb.Label(time_frame, text=":", font=("Consolas", 12), foreground="#888888")
        self.total_time_label_colon2.pack(side="left", padx=0)
        self.total_time_label_s = tb.Label(time_frame, text="00", font=("Consolas", 12), foreground="#888888")
        self.total_time_label_s.pack(side="left", padx=0)

        self.log_text = tb.Text(frm_log, height=8, width=95, state="disabled", font=("Microsoft JhengHei", 9))  # 高度縮短
        self.log_text.pack(fill="both", expand=True, pady=(4,0))
        log_scroll = tb.Scrollbar(frm_log, command=self.log_text.yview)
        log_scroll.pack(side="left", fill="y")
        self.log_text.config(yscrollcommand=log_scroll.set)

        self.refresh_script_list()
        if self.script_var.get():
            self.on_script_selected()

        self.after(1500, self._delayed_init)
        self.update_idletasks()
        width = max(self.winfo_reqwidth() - 50, 400)  # 寬度減少50，最小400
        height = int(self.winfo_reqheight() * 2 / 3) + 100  # 高度縮短1/3再+100
        self.geometry(f"{width}x{height}")

    def _delayed_init(self):
        # self.after(1600, self._register_hotkeys)  # ←移除這行
        self.after(1700, self.refresh_script_list)
        self.after(1800, self.load_last_script)
        self.after(1900, self.update_mouse_pos)

    def save_config(self):
        self.user_config["skin"] = self.theme_var.get()
        self.user_config["last_script"] = self.script_var.get()
        self.user_config["repeat"] = self.repeat_var.get()
        self.user_config["speed"] = self.speed_var.get()
        self.user_config["script_dir"] = self.script_dir
        self.user_config["language"] = self.language_var.get()
        self.user_config["hotkey_map"] = self.hotkey_map
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
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        gray = "#888888"
        color = "#15D3BD"
        self.time_label_h.config(text=f"{h:02d}", foreground=color if h else gray)
        self.time_label_m.config(text=f"{m:02d}", foreground=color if m else gray)
        self.time_label_s.config(text=f"{s:02d}", foreground=color if s else gray)
        self.time_label_colon1.config(foreground=gray)
        self.time_label_colon2.config(foreground=gray)

    def update_countdown_label(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        gray = "#888888"
        color = "#DB0E59"
        self.countdown_label_h.config(text=f"{h:02d}", foreground=color if h else gray)
        self.countdown_label_m.config(text=f"{m:02d}", foreground=color if m else gray)
        self.countdown_label_s.config(text=f"{s:02d}", foreground=color if s else gray)
        self.countdown_label_colon1.config(foreground=gray)
        self.countdown_label_colon2.config(foreground=gray)

    def update_total_time_label(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        gray = "#888888"
        color = "#FF95CA"
        self.total_time_label_h.config(text=f"{h:02d}", foreground=color if h else gray)
        self.total_time_label_m.config(text=f"{m:02d}", foreground=color if m else gray)
        self.total_time_label_s.config(text=f"{s:02d}", foreground=color if s else gray)
        self.total_time_label_colon1.config(foreground=gray)
        self.total_time_label_colon2.config(foreground=gray)

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
        from pynput.mouse import Controller, Listener
        try:
            self._mouse_events = []
            self._recording_mouse = True
            self._record_start_time = time.time()
            keyboard.start_recording()
            mouse_ctrl = Controller()
            last_pos = mouse_ctrl.position

            def now_rel():
                return time.time() - self._record_start_time

            def on_click(x, y, button, pressed):
                if self._recording_mouse and not self.paused:
                    self._mouse_events.append({
                        'type': 'mouse',
                        'event': 'down' if pressed else 'up',
                        'button': str(button).replace('Button.', ''),
                        'x': x,
                        'y': y,
                        'time': now_rel()
                    })
            def on_scroll(x, y, dx, dy):
                if self._recording_mouse and not self.paused:
                    self._mouse_events.append({
                        'type': 'mouse',
                        'event': 'wheel',
                        'delta': dy,
                        'x': x,
                        'y': y,
                        'time': now_rel()
                    })
            import pynput.mouse
            mouse_listener = pynput.mouse.Listener(
                on_click=on_click,
                on_scroll=on_scroll
            )
            mouse_listener.start()

            self._mouse_events.append({
                'type': 'mouse',
                'event': 'move',
                'x': last_pos[0],
                'y': last_pos[1],
                'time': 0.0
            })

            while self.recording:
                if self.paused:
                    time.sleep(0.05)
                    continue
                now = now_rel()
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

            exclude_keys = set([
                self.hotkey_map.get("start", "F10").lower(),
                self.hotkey_map.get("pause", "F11").lower(),
                self.hotkey_map.get("stop", "F9").lower()
            ])
            filtered_k_events = [
                e for e in k_events
                if not (e.name and e.name.lower() in exclude_keys and e.event_type in ('down', 'up'))
            ]
            # 這裡也要把鍵盤事件的 time 轉成相對時間
            events = [
                {'type': 'keyboard', 'event': e.event_type, 'name': e.name, 'time': e.time - self._record_start_time}
                for e in filtered_k_events
            ] + self._mouse_events

            self.events = sorted(events, key=lambda e: e['time'])
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
        self.on_script_selected()
        import keyboard
        import mouse
        if self.playing:
            return
        if not self.events:
            self.log("沒有可回放的事件，請先錄製或載入Script。")
            return
        try:
            speed_input = int(self.speed_var.get())
            if speed_input < 1 or speed_input > 1000:
                speed_input = 100
                self.speed_var.set("100")
        except:
            speed_input = 100
            self.speed_var.set("100")
        self.speed = speed_input / 100.0  # 100=1.0x, 25=0.25x, 1000=10x

        # 取得重複時間（秒）
        repeat_time_sec = self._parse_time_to_seconds(self.repeat_time_var.get())
        self._repeat_time_limit = repeat_time_sec if repeat_time_sec > 0 else None

        # 只要有填寫重複時間，強制 repeat = -1（無限次數，讓時間控制）
        if self._repeat_time_limit:
            repeat = -1
            self._total_play_time = self._repeat_time_limit
        else:
            try:
                repeat = int(self.repeat_var.get())
                if repeat == 0:
                    repeat = -1  # -1 代表無限次數
                elif repeat < 0:
                    repeat = 1
            except:
                repeat = 1
            if self.events:
                total = (self.events[-1]['time'] - self.events[0]['time']) / self.speed
                self._total_play_time = total * (99999 if repeat == -1 else repeat)
            else:
                self._total_play_time = 0

        self._repeat_times = repeat  # <--- 新增這行

        self._play_start_time = time.time()
        self._play_total_time = self._total_play_time
        self.update_total_time_label(self._total_play_time)
        self.log(f"[{format_time(time.time())}] 開始回放，速度倍率: {self.speed}")
        self.playing = True
        self.paused = False
        self._current_play_index = 0  # 新增：初始化回放索引
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
            # 單次剩餘
            total = self.events[-1]['time'] - self.events[0]['time'] if self.events else 0
            remain = max(0, total - elapsed)
            h = int(remain // 3600)
            m = int((remain % 3600) // 60)
            s = int(remain % 60)
            self.countdown_label.config(text=f"單次: {h:02d}:{m:02d}:{s:02d}")
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
            self.countdown_label.config(text="單次: 00:00:00")
            self.update_total_time_label(0)

    def update_total_time_label(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) % 60)
        s = int(seconds % 60)
        gray = "#888888"
        color = "#FF95CA"
        self.total_time_label_h.config(text=f"{h:02d}", foreground=color if h else gray)
        self.total_time_label_m.config(text=f"{m:02d}", foreground=color if m else gray)
        self.total_time_label_s.config(text=f"{s:02d}", foreground=color if s else gray)
        self.total_time_label_colon1.config(foreground=gray)
        self.total_time_label_colon2.config(foreground=gray)

    def _play_thread(self):
        self.playing = True
        self.paused = False
        repeat = getattr(self, "_repeat_times", 1)
        count = 0
        play_start_time = time.time()
        while self.playing and (repeat == -1 or count < repeat):
            # 強制時間到就結束所有動作
            if hasattr(self, "_repeat_time_limit") and self._repeat_time_limit:
                if time.time() - play_start_time >= self._repeat_time_limit:
                    self.log("重複時間到，已強制停止所有動作。")
                    self.playing = False
                    break
            self._current_play_index = 0
            total_events = len(self.events)
            if total_events == 0 or not self.playing:
                break
            base_time = self.events[0]['time']
            play_start = time.time()
            while self._current_play_index < total_events:
                # 強制時間到就結束所有動作
                if hasattr(self, "_repeat_time_limit") and self._repeat_time_limit:
                    if time.time() - play_start_time >= self._repeat_time_limit:
                        self.log("重複時間到，已強制停止所有動作。")
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
                    # 強制時間到就結束所有動作
                    if hasattr(self, "_repeat_time_limit") and self._repeat_time_limit:
                        if now - play_start_time >= self._repeat_time_limit:
                            self.log("重複時間到，已強制停止所有動作。")
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
                    # 取得目前設定的暫停與停止快捷鍵（全部轉小寫）
                    exclude_keys = set([
                        self.hotkey_map.get("pause", "F11").lower(),
                        self.hotkey_map.get("stop", "F9").lower()
                    ])
                    if e['name'].lower() in exclude_keys:
                        # 跳過暫停/停止按键，不執行也不記錄
                        self.log(f"[{format_time(e['time'])}] 跳過控制鍵: {e['name']}")
                        self._current_play_index += 1
                        continue
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
            self.log(f"[{format_time(time.time())}] 自動存檔：{display_filename(filename)}，事件數：{len(self.events)}")
            self.refresh_script_list()
            self.script_var.set(os.path.splitext(filename)[0])
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(filename)
            self.log(f"[{format_time(time.time())}] Script已載入：{display_filename(filename)}，共 {len(self.events)} 筆事件。")
            # self.on_script_selected()  # ← 移除這行
        except Exception as ex:
            self.log(f"[{format_time(time.time())}] 存檔失敗: {ex}")
            self.on_script_selected()

    def load_script(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")], initialdir=SCRIPTS_DIR)
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.events = json.load(f)
            self.log(f"[{format_time(time.time())}] Script已載入：{os.path.basename(path)}，共 {len(self.events)} 筆事件。")
            self.refresh_script_list()
            # 只設檔名（不含副檔名）
            self.script_var.set(os.path.splitext(os.path.basename(path))[0])
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(os.path.basename(path))

    def on_script_selected(self, event=None):
        script_name = self.script_var.get()
        if script_name:
            filename = script_name + ".json"
            path = os.path.join(SCRIPTS_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                self.events = json.load(f)
            self.log(f"[{format_time(time.time())}] Script已載入：{filename}，共 {len(self.events)} 筆事件。")
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(filename)
            # 讀取Script後，顯示單次Script時間

    def refresh_script_list(self):
        files = [f for f in os.listdir(self.script_dir) if f.endswith('.json')]
        # 只顯示檔名（不含副檔名）
        script_names = [os.path.splitext(f)[0] for f in files]
        current_script = self.script_var.get()
        current_script_name = os.path.splitext(current_script)[0] if current_script else ""
        self.script_combo['values'] = script_names
        # 若目前選擇的Script不存在於新資料夾，清空選擇
        if current_script_name not in script_names:
            self.script_var.set("")
        else:
            self.script_var.set(current_script_name)

    def load_last_script(self):
        if os.path.exists(LAST_SCRIPT_FILE):
            with open(LAST_SCRIPT_FILE, "r", encoding="utf-8") as f:
                last_script = f.read().strip()
            if last_script:
                script_path = os.path.join(SCRIPTS_DIR, last_script)
                if os.path.exists(script_path):
                    with open(script_path, "r", encoding="utf-8") as f:
                        self.events = json.load(f)
                    # 只設檔名（不含副檔名）
                    self.script_var.set(os.path.splitext(last_script)[0])
                    self.log(f"[{format_time(time.time())}] 已自動載入上次Script：{display_filename(last_script)}，共 {len(self.events)} 筆事件。")

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
            self.log(f"[{format_time(time.time())}] 請選擇Script並輸入新名稱。")
            return
        if not new_name.endswith('.json'):
            new_name += '.json'
        # 修正：old_name 需加上 .json
        if not old_name.endswith('.json'):
            old_name += '.json'
        old_path = os.path.join(SCRIPTS_DIR, old_name)
        new_path = os.path.join(SCRIPTS_DIR, new_name)
        if os.path.exists(new_path):
            self.log(f"[{format_time(time.time())}] 檔案已存在，請換個名稱。")
            return
        try:
            os.rename(old_path, new_path)
            self.log(f"[{format_time(time.time())}] Script已更名為：{display_filename(new_name)}")
            self.refresh_script_list()
            self.script_var.set(new_name)
            with open(LAST_SCRIPT_FILE, "w", encoding="utf-8") as f:
                f.write(new_name)
        except Exception as e:
            self.log(f"[{format_time(time.time())}] 更名失敗: {e}")
        self.rename_var.set("")  # 更名後清空輸入框

    def open_scripts_dir(self):
        path = os.path.abspath(self.script_dir)
        os.startfile(path)

    def register_hotkeys(self):
        # 先移除所有已註冊的快捷鍵
        for key, handler in self._hotkey_handlers.items():
            try:
                keyboard.remove_hotkey(handler)
            except Exception:
                pass
        self._hotkey_handlers.clear()
        # 重新註冊
        for key, hotkey in self.hotkey_map.items():
            try:
                handler = keyboard.add_hotkey(hotkey, getattr(self, {
                    "start": "start_record",
                    "pause": "toggle_pause",
                    "stop": "stop_all",
                    "play": "play_record",
                    "tiny": "toggle_tiny_mode"
                }[key]))
                self._hotkey_handlers[key] = handler
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")
        # 停止支援多組熱鍵
        stop_hotkeys = [self.hotkey_map["stop"], "ctrl+f9", "alt+f9"]
        for hotkey in stop_hotkeys:
            try:
                handler = keyboard.add_hotkey(hotkey, self.stop_all)
                self._hotkey_handlers[f"stop_{hotkey}"] = handler
            except Exception as ex:
                self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")

    def open_hotkey_settings(self):
        win = tb.Toplevel(self)
        lang = self.language_var.get()
        lang_map = LANG_MAP.get(lang, LANG_MAP["繁體中文"])
        win.title(lang_map["快捷鍵"])
        win.geometry("400x320")  # 視窗高度加大，確保按鈕顯示
        win.resizable(False, False)

        labels = {
            "start": lang_map["開始錄製"],
            "pause": lang_map["暫停/繼續"],
            "stop": lang_map["停止"],
            "play": lang_map["回放"],
            "tiny": lang_map["TinyMode"]
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

        def update_main_buttons():
            lang_map = LANG_MAP.get(self.language_var.get(), LANG_MAP["繁體中文"])
            self.btn_start.config(text=lang_map["開始錄製"] + f" ({self.hotkey_map['start']})")
            self.btn_pause.config(text=lang_map["暫停/繼續"] + f" ({self.hotkey_map['pause']})")
            self.btn_stop.config(text=lang_map["停止"] + f" ({self.hotkey_map['stop']})")
            self.btn_play.config(text=lang_map["回放"] + f" ({self.hotkey_map['play']})")
            self.tiny_mode_btn.config(text=lang_map["TinyMode"])

        for key, label in labels.items():
            tb.Label(win, text=label, font=("Microsoft JhengHei", 11)).grid(row=row, column=0, padx=10, pady=8, sticky="w")
            var = tk.StringVar(value=self.hotkey_map[key])
            entry = tb.Entry(win, textvariable=var, width=16, font=("Consolas", 11), state="normal")
            entry.grid(row=row, column=1, padx=10)
            vars[key] = var
            entries[key] = entry
            entry.bind("<KeyRelease>", lambda e, k=key, v=var: on_entry_release(e, k, v))
            entry.bind("<FocusIn>", lambda e, v=var: on_entry_focus_in(e, v))
            entry.bind("<FocusOut>", lambda e, k=key, v=var: on_entry_focus_out(e, k, v))
            row += 1

        def save_and_close():
            # 先移除所有已註冊的快捷鍵
            for key, handler in self._hotkey_handlers.items():
                try:
                    keyboard.remove_hotkey(handler)
                except Exception:
                    pass
            self._hotkey_handlers.clear()
            # 設定新快捷鍵
            for key, var in vars.items():
                hotkey = var.get().strip()
                if hotkey:
                    self.hotkey_map[key] = hotkey  # 更新 hotkey_map
                    try:
                        handler = keyboard.add_hotkey(hotkey, getattr(self, {
                            "start": "start_record",
                            "pause": "toggle_pause",
                            "stop": "stop_all",
                            "play": "play_record",
                            "tiny": "toggle_tiny_mode"
                        }[key]))
                        self._hotkey_handlers[key] = handler
                    except Exception as ex:
                        self.log(f"快捷鍵 {hotkey} 註冊失敗: {ex}")
            self.save_config()
            update_main_buttons()  # 新增：即時更新主介面按鈕文字
            win.destroy()

        # 加回「儲存並關閉」按鈕
        tb.Button(
            win,
            text=lang_map.get("儲存並關閉", "儲存並關閉"),
            command=save_and_close,
            bootstyle=SUCCESS,
            width=16
        ).grid(row=row, column=0, columnspan=2, pady=18)

        self.register_hotkeys()

    def register_global_hotkeys(self):
        # 用 thread 避免卡住主程式
        threading.Thread(target=self._hotkey_listener, daemon=True).start()

    def _hotkey_listener(self):
        keyboard.add_hotkey('f8', self.start_record)
        keyboard.add_hotkey('f9', self.stop_all)  # 修正這一行
        keyboard.add_hotkey('f10', self.play_record)
        keyboard.wait()  # 保持監聽

    def get_script_duration(self):
        if self.events and "time" in self.events[-1]:
            return self.events[-1]["time"] - self.events[0]["time"]
        return 0

LANG_MAP = {
    "繁體中文": {
        "開始錄製": "開始錄製",
        "暫停/繼續": "暫停/繼續",
        "停止": "停止",
        "回放": "回放",
        "TinyMode": "TinyMode",
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
        "合併清單（可拖曳排序，點擊次數可編輯）": "合併清單（可拖曳排序，點擊次數可編輯）",
        "清空": "清空",
        "加入": "加入",
        "移除": "移除",
        "Script工具": "Script工具",
        "延遲秒數:": "遲延秒數:",
        "Language": "Language",
        "回放速度:": "回放速度:",
        "目前Script": "目前Script",
        "選擇合併Script": "選擇合併Script",
        "目前Script在前": "目前Script在前",
        "合併Script在前": "合併Script在前",
        "總運作": "總運作",
        "單次": "單次",
        "錄製": "錄製",
        "刪除": "刪除",
    },
    "日本語": {
        "開始錄製": "マクロ記録",
        "暫停/繼續": "一時停止/再開",
        "停止": "停止",
        "回放": "再生",
        "TinyMode": "Tinyモード",
        "Script路徑": "Scriptパス",
        "快捷鍵": "ショートカット",
        "關於": "情報",
        "重複次數:": "繰り返し回数:",
        "次": "回",
        "重複時間": "繰り返し間隔",
        "Script:": "Script:",
        "重新命名": "名前変更",
        "Script": "Script",
        "合併並儲存": "結合して保存",
        "所有Script": "全Script",
        "新Script名稱：": "新しいScript名：",
        "確定": "決定",
        "所有Script": "全Script",
        "合併清單（可拖曳排序，點擊次數可編輯）": "結合リスト（ドラッグで並べ替え、ダブルクリックで編集）",
        "清空": "クリア",
        "加入": "追加",
        "移除": "削除",
        "Script工具": "Script結合ツール",
        "延遲秒數:": "遅延秒数:",
        "Language": "言語",
        "回放速度:": "再生速度:",
        "目前Script": "現在のScript",
        "選擇合併Script": "結合Script選択",
        "目前Script在前": "現在のScriptが先",
        "合併Script在前": "結合Scriptが先",
        "總運作": "総運用",
        "單次": "単回",
        "錄製": "記録",
        "刪除": "削除",
    },
    "English": {
        "開始錄製": "Start Recording",
        "暫停/繼續": "Pause/Resume",
        "停止": "Stop",
        "回放": "Play",
        "TinyMode": "TinyMode",
        "Script路徑": "Script Path",
        "快捷鍵": "Hotkey",
        "關於": "About",
        "重複次數:": "Repeat Count:",
        "次": "times",
        "重複時間": "Repeat Interval",
        "Script:": "Script:",
        "重新命名": "Rename",
        "Script": "Script",
        "合併並儲存": "Merge & Save",
        "所有Script": "All Scripts",
        "新Script名稱：": "New Script Name:",
        "確定": "OK",
        "所有Script": "All Scripts",
        "合併清單（可拖曳排序，點擊次數可編輯）": "Merge List (drag to sort, double-click to edit)",
        "清空": "Clear",
        "加入": "Add",
        "移除": "Remove",
        "Script工具": "Script Merge Tool",
        "延遲秒數:": "Delay (sec):",
        "Language": "Language",
        "回放速度:": "Speed:",
        "目前Script": "Current Script",
        "選擇合併Script": "Select Script to Merge",
        "目前Script在前": "Current Script First",
        "合併Script在前": "Merge Script First",
        "總運作": "Total",
        "單次": "Single",
        "錄製": "Record",
        "刪除": "Delete",
    }
}

def load_user_config():
    if os.path.exists("user_config.json"):
        try:
            with open("user_config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "skin": "darkly",
        "last_script": "",
        "repeat": "1",
        "speed": "100",
        "script_dir": SCRIPTS_DIR,
        "language": "繁體中文",
        "hotkey_map": {
            "start": "F10",
            "pause": "F11",
            "stop": "F9",
            "play": "F12",
            "tiny": "alt+`"
        }
    }

def save_user_config(config):
    try:
        with open("user_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def move_mouse_abs(x, y):
    """將滑鼠移動到絕對座標 (x, y)"""
    ctypes.windll.user32.SetCursorPos(int(x), int(y))

def mouse_event_win(event, button='left', delta=0):
    """模擬滑鼠事件"""
    import win32api
    import win32con
    btn_map = {'left': win32con.MOUSEEVENTF_LEFTDOWN, 'right': win32con.MOUSEEVENTF_RIGHTDOWN, 'middle': win32con.MOUSEEVENTF_MIDDLEDOWN}
    btn_map = {'left': win32con.MOUSEEVENTF_LEFTDOWN, 'right': win32con.MOUSEEVENTF_RIGHTDOWN, 'middle': win32con.MOUSEEVENTF_MIDDLEDOWN}
    btn_up_map = {'left': win32con.MOUSEEVENTF_LEFTUP, 'right': win32con.MOUSEEVENTF_RIGHTUP, 'middle': win32con.MOUSEEVENTF_MIDDLEUP}
    if event == 'down':
        win32api.mouse_event(btn_map.get(button, win32con.MOUSEEVENTF_LEFTDOWN), 0, 0, 0, 0)
    elif event == 'up':
        win32api.mouse_event(btn_up_map.get(button, win32con.MOUSEEVENTF_LEFTUP), 0, 0, 0, 0)
    elif event == 'wheel':
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, int(delta), 0)

def display_filename(filename):
    return os.path.splitext(filename)[0]

if __name__ == "__main__":
    app = RecorderApp()
    app.mainloop()
