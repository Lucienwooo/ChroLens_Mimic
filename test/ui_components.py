"""
UI 元件管理器 - UI Components Manager
負責建立和管理所有 UI 元件
"""

import ttkbootstrap as tb
import tkinter as tk
from ttkbootstrap.constants import *

try:
    from lang import LANG_MAP
except ImportError:
    LANG_MAP = {
        "繁體中文": {
            "開始錄製": "開始錄製",
            "暫停/繼續": "暫停/繼續",
            "停止": "停止",
            "回放": "回放",
            "MiniMode": "MiniMode",
            "關於": "關於",
            "回放速度:": "回放速度:",
            "快捷鍵": "快捷鍵",
            "總運作": "總運作: ",
            "單次": "單次: ",
            "錄製": "錄製: ",
            "重複次數:": "重複次數:",
            "重複時間": "重複時間",
            "重複間隔": "重複間隔",
            "Script:": "腳本選單:",
            "儲存": "儲存"
        }
    }

try:
    import tkinter.font as tkfont
    
    def font_tuple(size, weight=None, monospace=False):
        """字體 tuple 建構函式"""
        fam = "Consolas" if monospace else "LINESeedTW_TTF_Rg"
        try:
            for f in tkfont.families():
                if f.lower().startswith("lineseed"):
                    fam = f
                    break
            else:
                if not monospace:
                    for f in tkfont.families():
                        if f.lower().startswith("microsoft jhenghei"):
                            fam = f
                            break
        except Exception:
            pass
        if weight:
            return (fam, size, weight)
        return (fam, size)
except ImportError:
    def font_tuple(size, weight=None, monospace=False):
        fam = "Consolas" if monospace else "Microsoft JhengHei"
        if weight:
            return (fam, size, weight)
        return (fam, size)


class UIComponentManager:
    """UI 元件管理器類別"""
    
    def __init__(self, parent, app):
        """
        初始化 UI 元件管理器
        
        Args:
            parent: 父視窗（通常是 RecorderApp 實例）
            app: 應用程式實例（用於存取變數和方法）
        """
        self.parent = parent
        self.app = app
        
        # 元件引用字典
        self.widgets = {}
    
    def setup_styles(self):
        """設定統一的字體樣式"""
        self.parent.style.configure("My.TButton", font=font_tuple(9))
        self.parent.style.configure("My.TLabel", font=font_tuple(9))
        self.parent.style.configure("My.TEntry", font=font_tuple(9))
        self.parent.style.configure("My.TCombobox", font=font_tuple(9))
        self.parent.style.configure("My.TCheckbutton", font=font_tuple(9))
        self.parent.style.configure("miniBold.TButton", font=font_tuple(9, "bold"))
    
    def create_top_frame(self):
        """建立上方控制按鈕區"""
        frm_top = tb.Frame(self.parent, padding=(8, 10, 8, 5))
        frm_top.pack(fill="x")
        
        # 開始錄製按鈕
        self.app.btn_start = tb.Button(
            frm_top,
            text=f"開始錄製 ({self.app.hotkey_map['start']})",
            command=self.app.start_record,
            bootstyle=PRIMARY,
            width=14,
            style="My.TButton"
        )
        self.app.btn_start.grid(row=0, column=0, padx=(0, 4))
        
        # 暫停/繼續按鈕
        self.app.btn_pause = tb.Button(
            frm_top,
            text=f"暫停/繼續 ({self.app.hotkey_map['pause']})",
            command=self.app.toggle_pause,
            bootstyle=INFO,
            width=14,
            style="My.TButton"
        )
        self.app.btn_pause.grid(row=0, column=1, padx=4)
        
        # 停止按鈕
        self.app.btn_stop = tb.Button(
            frm_top,
            text=f"停止 ({self.app.hotkey_map['stop']})",
            command=self.app.stop_all,
            bootstyle=WARNING,
            width=14,
            style="My.TButton"
        )
        self.app.btn_stop.grid(row=0, column=2, padx=4)
        
        # 回放按鈕
        self.app.btn_play = tb.Button(
            frm_top,
            text=f"回放 ({self.app.hotkey_map['play']})",
            command=self.app.play_record,
            bootstyle=SUCCESS,
            width=10,
            style="My.TButton"
        )
        self.app.btn_play.grid(row=0, column=3, padx=4)
        
        # MiniMode 按鈕
        self.app.mini_mode_btn = tb.Button(
            frm_top,
            text="MiniMode",
            style="My.TButton",
            command=self.app.toggle_mini_mode,
            width=10
        )
        self.app.mini_mode_btn.grid(row=0, column=7, padx=4)
        
        return frm_top
    
    def create_bottom_frame(self):
        """建立下方參數設定區"""
        frm_bottom = tb.Frame(self.parent, padding=(8, 0, 8, 5))
        frm_bottom.pack(fill="x")
        
        # 回放速度
        self.app.lbl_speed = tb.Label(frm_bottom, text="回放速度:", style="My.TLabel")
        self.app.lbl_speed.grid(row=0, column=0, padx=(0, 6))
        
        # Tooltip 需要從主程式匯入，或在此定義簡化版
        # 這裡先跳過 tooltip，稍後在主程式中設定
        
        self.app.speed_var = tk.StringVar(value=self.app.user_config.get("speed", "100"))
        tb.Entry(frm_bottom, textvariable=self.app.speed_var, width=6, style="My.TEntry").grid(row=0, column=1, padx=6)
        
        # 重複次數
        self.app.repeat_label = tb.Label(frm_bottom, text="重複次數:", style="My.TLabel")
        self.app.repeat_label.grid(row=0, column=2, padx=(8, 2))
        self.app.repeat_var = tk.StringVar(value=self.app.user_config.get("repeat", "1"))
        entry_repeat = tb.Entry(frm_bottom, textvariable=self.app.repeat_var, width=6, style="My.TEntry")
        entry_repeat.grid(row=0, column=3, padx=2)
        
        # 重複時間
        self.app.repeat_time_var = tk.StringVar(value="00:00:00")
        entry_repeat_time = tb.Entry(
            frm_bottom,
            textvariable=self.app.repeat_time_var,
            width=10,
            style="My.TEntry",
            justify="center"
        )
        entry_repeat_time.grid(row=0, column=5, padx=(10, 2))
        self.app.repeat_time_label = tb.Label(frm_bottom, text="重複時間", style="My.TLabel")
        self.app.repeat_time_label.grid(row=0, column=6, padx=(0, 2))
        
        # 重複間隔
        self.app.repeat_interval_var = tk.StringVar(value="00:00:00")
        repeat_interval_entry = tb.Entry(
            frm_bottom,
            textvariable=self.app.repeat_interval_var,
            width=10,
            style="My.TEntry",
            justify="center"
        )
        repeat_interval_entry.grid(row=0, column=7, padx=(10, 2))
        self.app.repeat_interval_label = tb.Label(frm_bottom, text="重複間隔", style="My.TLabel")
        self.app.repeat_interval_label.grid(row=0, column=8, padx=(0, 2))
        
        # 隨機勾選
        self.app.random_interval_var = tk.BooleanVar(value=False)
        self.app.random_interval_check = tb.Checkbutton(
            frm_bottom,
            text="隨機",
            variable=self.app.random_interval_var,
            style="My.TCheckbutton"
        )
        self.app.random_interval_check.grid(row=0, column=9, padx=(8, 2))
        
        # 儲存按鈕
        saved_lang = self.app.user_config.get("language", "繁體中文")
        self.app.save_script_btn_text = tk.StringVar(
            value=LANG_MAP.get(saved_lang, LANG_MAP["繁體中文"])["儲存"]
        )
        self.app.save_script_btn = tb.Button(
            frm_bottom,
            textvariable=self.app.save_script_btn_text,
            width=8,
            bootstyle=SUCCESS,
            style="My.TButton",
            command=self.app.save_script_settings
        )
        self.app.save_script_btn.grid(row=0, column=10, padx=(8, 0))
        
        # 設定驗證器
        def validate_time_input(P):
            import re
            return re.fullmatch(r"[\d:]*", P) is not None
        
        vcmd = (self.parent.register(validate_time_input), "%P")
        entry_repeat_time.config(validate="key", validatecommand=vcmd)
        repeat_interval_entry.config(validate="key", validatecommand=vcmd)
        
        # 右鍵清除
        entry_repeat.bind("<Button-3>", lambda e: self.app.repeat_var.set("0"))
        entry_repeat_time.bind("<Button-3>", lambda e: self.app.repeat_time_var.set("00:00:00"))
        repeat_interval_entry.bind("<Button-3>", lambda e: self.app.repeat_interval_var.set("00:00:00"))
        
        # 重複時間變動時更新顯示
        def on_repeat_time_change(*args):
            t = self.app.repeat_time_var.get()
            seconds = self.app._parse_time_to_seconds(t)
            if seconds > 0:
                self.app.update_total_time_label(seconds)
            else:
                self.app.update_total_time_label(0)
        
        self.app.repeat_time_var.trace_add("write", on_repeat_time_change)
        
        return frm_bottom
    
    def create_script_frame(self):
        """建立腳本選單區"""
        frm_script = tb.Frame(self.parent, padding=(8, 0, 8, 5))
        frm_script.pack(fill="x")
        
        # 腳本選單標籤
        self.app.script_menu_label = tb.Label(frm_script, text="腳本選單:", style="My.TLabel")
        self.app.script_menu_label.grid(row=0, column=0, sticky="w", padx=(0, 2))
        
        # 腳本下拉選單
        self.app.script_var = tk.StringVar(value=self.app.user_config.get("last_script", ""))
        self.app.script_combo = tb.Combobox(
            frm_script,
            textvariable=self.app.script_var,
            width=20,
            state="readonly",
            style="My.TCombobox"
        )
        self.app.script_combo.grid(row=0, column=1, sticky="w", padx=4)
        self.app.script_combo.bind("<<ComboboxSelected>>", self.app.on_script_selected)
        
        # 重新命名輸入框
        self.app.rename_var = tk.StringVar()
        self.app.rename_entry = tb.Entry(frm_script, textvariable=self.app.rename_var, width=20, style="My.TEntry")
        self.app.rename_entry.grid(row=0, column=2, padx=4)
        
        # Rename 按鈕
        tb.Button(
            frm_script,
            text="Rename",
            command=self.app.rename_script,
            bootstyle=WARNING,
            width=12,
            style="My.TButton"
        ).grid(row=0, column=3, padx=4)
        
        # 選擇視窗按鈕
        self.app.select_target_btn = tb.Button(
            frm_script,
            text="選擇視窗",
            command=self.app.select_target_window,
            bootstyle=INFO,
            width=14,
            style="My.TButton"
        )
        self.app.select_target_btn.grid(row=0, column=4, padx=4)
        
        return frm_script
    
    def create_log_frame(self):
        """建立日誌顯示區（含時間標籤）"""
        frm_log = tb.Frame(self.parent, padding=(10, 0, 10, 10))
        frm_log.pack(fill="both", expand=True)
        
        log_title_frame = tb.Frame(frm_log)
        log_title_frame.pack(fill="x")
        
        # 滑鼠座標
        self.app.mouse_pos_label = tb.Label(
            log_title_frame,
            text="( X:0, Y:0 )",
            font=("Consolas", 11),
            foreground="#668B9B"
        )
        self.app.mouse_pos_label.pack(side="left", padx=8)
        
        # 目標視窗標籤
        self.app.target_label = tb.Label(
            log_title_frame,
            text="",
            font=font_tuple(9),
            foreground="#FF9500",
            anchor="w",
            width=25
        )
        self.app.target_label.pack(side="left", padx=(0, 4))
        
        # 錄製時間
        self.app.time_label_time = tb.Label(
            log_title_frame,
            text="00:00:00",
            font=font_tuple(12, monospace=True),
            foreground="#888888"
        )
        self.app.time_label_time.pack(side="right", padx=0)
        
        self.app.time_label_prefix = tb.Label(
            log_title_frame,
            text="錄製: ",
            font=font_tuple(12, monospace=True),
            foreground="#15D3BD"
        )
        self.app.time_label_prefix.pack(side="right", padx=0)
        
        # 單次剩餘
        self.app.countdown_label_time = tb.Label(
            log_title_frame,
            text="00:00:00",
            font=font_tuple(12, monospace=True),
            foreground="#888888"
        )
        self.app.countdown_label_time.pack(side="right", padx=0)
        
        self.app.countdown_label_prefix = tb.Label(
            log_title_frame,
            text="單次: ",
            font=font_tuple(12, monospace=True),
            foreground="#DB0E59"
        )
        self.app.countdown_label_prefix.pack(side="right", padx=0)
        
        # 總運作
        self.app.total_time_label_time = tb.Label(
            log_title_frame,
            text="00:00:00",
            font=font_tuple(12, monospace=True),
            foreground="#888888"
        )
        self.app.total_time_label_time.pack(side="right", padx=0)
        
        self.app.total_time_label_prefix = tb.Label(
            log_title_frame,
            text="總運作: ",
            font=font_tuple(12, monospace=True),
            foreground="#FF95CA"
        )
        self.app.total_time_label_prefix.pack(side="right", padx=0)
        
        return frm_log
    
    def create_page_frame(self):
        """建立分頁區域（日誌、腳本設定、整體設定）"""
        frm_page = tb.Frame(self.parent, padding=(10, 0, 10, 10))
        frm_page.pack(fill="both", expand=True)
        frm_page.grid_rowconfigure(0, weight=1)
        frm_page.grid_columnconfigure(0, weight=0)
        frm_page.grid_columnconfigure(1, weight=1)
        
        # 左側選單
        self.app.page_menu = tk.Listbox(frm_page, width=18, font=("Microsoft JhengHei", 11), height=5)
        self.app.page_menu.insert(0, "1.日誌顯示")
        self.app.page_menu.insert(1, "2.腳本設定")
        self.app.page_menu.insert(2, "3.整體設定")
        self.app.page_menu.grid(row=0, column=0, sticky="ns", padx=(0, 8), pady=4)
        self.app.page_menu.bind("<<ListboxSelect>>", self.app.on_page_selected)
        
        # 右側內容區
        self.app.page_content_frame = tb.Frame(frm_page)
        self.app.page_content_frame.grid(row=0, column=1, sticky="nsew")
        self.app.page_content_frame.grid_rowconfigure(0, weight=1)
        self.app.page_content_frame.grid_columnconfigure(0, weight=1)
        
        # 建立各分頁內容
        self._create_log_page()
        self._create_script_settings_page()
        self._create_global_settings_page()
        
        # 預設選擇第一項
        self.app.page_menu.selection_set(0)
        self.app.show_page(0)
        
        return frm_page
    
    def _create_log_page(self):
        """建立日誌顯示頁"""
        self.app.log_text = tb.Text(self.app.page_content_frame, state="disabled", font=font_tuple(9))
        self.app.log_text.grid(row=0, column=0, sticky="nsew")
        
        log_scroll = tb.Scrollbar(self.app.page_content_frame, command=self.app.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.app.log_text.config(yscrollcommand=log_scroll.set)
    
    def _create_script_settings_page(self):
        """建立腳本設定頁"""
        self.app.script_setting_frame = tb.Frame(self.app.page_content_frame)
        self.app.script_setting_frame.grid_rowconfigure(0, weight=1)
        self.app.script_setting_frame.grid_columnconfigure(0, weight=1)
        self.app.script_setting_frame.grid_columnconfigure(1, weight=0)
        
        # 左側腳本列表
        self.app.script_listbox = tk.Listbox(
            self.app.script_setting_frame,
            width=35,
            font=font_tuple(9)
        )
        self.app.script_listbox.grid(row=0, column=0, rowspan=8, sticky="nsew", padx=(8, 6), pady=8)
        self.app.script_listbox.bind("<<ListboxSelect>>", self.app.on_script_listbox_select)
        
        # 右側控制區
        self.app.script_right_frame = tb.Frame(self.app.script_setting_frame, padding=6)
        self.app.script_right_frame.grid(row=0, column=1, sticky="nw", padx=(6, 8), pady=8)
        
        # 快捷鍵捕捉
        self.app.hotkey_capture_var = tk.StringVar(value="")
        hotkey_label = tb.Label(self.app.script_right_frame, text="捕捉快捷鍵：", style="My.TLabel")
        hotkey_label.pack(anchor="w", pady=(2, 2))
        
        hotkey_entry = tb.Entry(
            self.app.script_right_frame,
            textvariable=self.app.hotkey_capture_var,
            font=font_tuple(10, monospace=True),
            width=16
        )
        hotkey_entry.pack(pady=(0, 8))
        hotkey_entry.bind("<KeyPress>", self.app.on_hotkey_entry_key)
        hotkey_entry.bind("<FocusIn>", lambda e: self.app.hotkey_capture_var.set("輸入按鍵"))
        hotkey_entry.bind("<FocusOut>", lambda e: None)
        
        # 設定快捷鍵按鈕
        set_hotkey_btn = tb.Button(
            self.app.script_right_frame,
            text="設定快捷鍵",
            width=16,
            bootstyle=SUCCESS,
            command=self.app.set_script_hotkey
        )
        set_hotkey_btn.pack(pady=4)
        
        # 開啟資料夾按鈕
        open_dir_btn = tb.Button(
            self.app.script_right_frame,
            text="開啟資料夾",
            width=16,
            bootstyle=SECONDARY,
            command=self.app.open_scripts_dir
        )
        open_dir_btn.pack(pady=4)
        
        # 刪除腳本按鈕
        del_btn = tb.Button(
            self.app.script_right_frame,
            text="刪除腳本",
            width=16,
            bootstyle=DANGER,
            command=self.app.delete_selected_script
        )
        del_btn.pack(pady=4)
    
    def _create_global_settings_page(self):
        """建立整體設定頁"""
        self.app.global_setting_frame = tb.Frame(self.app.page_content_frame)
        self.app.global_setting_frame.grid_rowconfigure(0, weight=1)
        self.app.global_setting_frame.grid_columnconfigure(0, weight=1)
        
        # 快捷鍵按鈕
        self.app.btn_hotkey = tb.Button(
            self.app.global_setting_frame,
            text="快捷鍵",
            command=self.app.open_hotkey_settings,
            bootstyle=SECONDARY,
            width=12,
            style="My.TButton"
        )
        self.app.btn_hotkey.pack(pady=6)
        
        # 關於按鈕
        self.app.about_btn = tb.Button(
            self.app.global_setting_frame,
            text="關於",
            width=12,
            style="My.TButton",
            command=self.app.show_about_dialog,
            bootstyle=SECONDARY
        )
        self.app.about_btn.pack(pady=6)
        
        # 語言下拉選單
        saved_lang = self.app.user_config.get("language", "繁體中文")
        self.app.language_var = tk.StringVar(self.parent, value=saved_lang)
        
        lang_combo_global = tb.Combobox(
            self.app.global_setting_frame,
            textvariable=self.app.language_var,
            values=["繁體中文", "日本語", "English"],
            state="readonly",
            width=12,
            style="My.TCombobox"
        )
        lang_combo_global.pack(pady=6)
        lang_combo_global.bind("<<ComboboxSelected>>", self.app.change_language)
        self.app.language_combo = lang_combo_global
