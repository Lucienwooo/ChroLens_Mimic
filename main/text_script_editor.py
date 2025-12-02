# -*- coding: utf-8 -*-
"""
ChroLens 文字指令式腳本編輯器
將JSON事件轉換為簡單的文字指令格式
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
from tkinter import font as tkfont
import json
import os
import re
import sys
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageGrab, ImageTk

# 🔧 載入 LINE Seed 字體
LINE_SEED_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TTF", "LINESeedTW_TTF_Rg.ttf")
try:
    import pyglet
    if os.path.exists(LINE_SEED_FONT_PATH):
        pyglet.font.add_file(LINE_SEED_FONT_PATH)
        LINE_SEED_FONT_LOADED = True
    else:
        LINE_SEED_FONT_LOADED = False
except:
    LINE_SEED_FONT_LOADED = False

# 🔧 導入主程式的字體系統
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ChroLens_Mimic import font_tuple
except:
    # 如果無法導入，使用預設字體函數
    def font_tuple(size, weight=None, monospace=False):
        # 優先使用 LINE Seed 字體
        if LINE_SEED_FONT_LOADED:
            fam = "LINE Seed TW"
        else:
            fam = "Consolas" if monospace else "Microsoft JhengHei"
        if weight:
            return (fam, size, weight)
        return (fam, size)


class TextCommandEditor(tk.Toplevel):
    """文字指令式腳本編輯器"""
    
    def __init__(self, parent=None, script_path=None):
        super().__init__(parent)
        
        self.parent = parent
        self.script_path = script_path
        self.title("文字指令編輯器")
        self.geometry("800x920")  # 增加高度以容納三行按鈕和狀態列
        
        # 設定最小視窗尺寸，確保按鈕群不被遮住
        self.minsize(800, 820)
        
        # 設定視窗圖標(與主程式相同)
        try:
            from ChroLens_Mimic import get_icon_path
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            pass  # 圖標設定失敗不影響功能
        
        # 預設按鍵持續時間 (毫秒)
        self.default_key_duration = 50
        
        # 初始化 original_settings（防止儲存時找不到屬性）
        self.original_settings = {
            "speed": "100",
            "repeat": "1",
            "repeat_time": "00:00:00",
            "repeat_interval": "00:00:00",
            "random_interval": False,
            "script_hotkey": "",
            "script_actions": [],
            "window_info": None
        }
        
        # 圖片辨識相關資料夾
        self.images_dir = self._get_images_dir()
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 自訂模組資料夾
        self.modules_dir = self._get_modules_dir()
        os.makedirs(self.modules_dir, exist_ok=True)
        
        # 圖片編號計數器（自動命名 pic01, pic02...）
        self._pic_counter = self._get_next_pic_number()
        
        self._create_ui()
        
        # 刷新腳本列表
        self._refresh_script_list()
        
        # 如果有指定腳本路徑，載入它
        if self.script_path:
            script_name = os.path.splitext(os.path.basename(self.script_path))[0]
            self.script_var.set(script_name)
            self._load_script()
        
        # 確保編輯器視窗顯示並獲得焦點（但不強制置頂避免覆蓋問題）
        self.focus_set()
    
    def _get_images_dir(self):
        """獲取圖片儲存目錄"""
        if self.script_path:
            script_dir = os.path.dirname(self.script_path)
            return os.path.join(script_dir, "images")
        return os.path.join(os.getcwd(), "scripts", "images")
    
    def _get_modules_dir(self):
        """獲取自訂模組目錄"""
        if self.script_path:
            script_dir = os.path.dirname(self.script_path)
            return os.path.join(script_dir, "modules")
        return os.path.join(os.getcwd(), "scripts", "modules")
    
    def _get_next_pic_number(self):
        """獲取下一個可用的圖片編號（pic01, pic02...）"""
        if not os.path.exists(self.images_dir):
            return 1
        
        # 掃描現有圖片檔案，找出最大編號
        max_num = 0
        try:
            for filename in os.listdir(self.images_dir):
                if filename.startswith("pic") and filename.endswith(".png"):
                    # 提取編號部分，例如 pic01.png -> 01
                    try:
                        num_str = filename[3:-4]  # 移除 "pic" 和 ".png"
                        num = int(num_str)
                        max_num = max(max_num, num)
                    except:
                        continue
        except:
            pass
        
        return max_num + 1
    
    def _create_ui(self):
        """創建UI"""
        # 配置 ttk.Combobox 樣式（使用獨立實例避免影響主程式）
        self.editor_style = ttk.Style(self)
        self.editor_style.configure('Editor.TCombobox', 
                       fieldbackground='white',
                       background='white',
                       foreground='black',
                       selectbackground='#0078d7',
                       selectforeground='white')
        
        # 頂部工具列
        toolbar = tk.Frame(self, bg="#f0f0f0", height=50)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # 腳本選單區域（不顯示"腳本:"文字）
        # 下拉選單
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.script_var, 
            width=25, 
            height=10,
            state="readonly", 
            font=font_tuple(9),
            style='Editor.TCombobox'
        )
        self.script_combo.pack(side="left", padx=5, pady=2)
        self.script_combo.bind("<<ComboboxSelected>>", self._on_script_selected)
        self.script_combo.bind("<Button-1>", self._on_combo_click)
        
        # 操作按鈕（移除圖片辨識，移到底部指令區）
        buttons = [
            ("重新載入", self._load_script, "#2196F3"),
            ("儲存", self._save_script, "#4CAF50")
        ]
        for text, cmd, color in buttons:
            tk.Button(toolbar, text=text, command=cmd, bg=color, fg="white", font=font_tuple(9, "bold"), padx=15, pady=5).pack(side="left", padx=5)
        
        # 主編輯區（移除設定區和提示）區（移除設定區和提示）
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左側: 文字編輯器 (固定寬度,減少1/3)
        left_frame = tk.Frame(main_frame, width=450)  # 原約500,減少1/3約350
        left_frame.pack(side="left", fill="both", expand=False)
        left_frame.pack_propagate(False)
        
        tk.Label(
            left_frame,
            text="文字指令 (可直接編輯)",
            font=font_tuple(10, "bold")
        ).pack(anchor="w", pady=5)
        
        # 使用 LINE Seed 字體
        editor_font = ("LINE Seed TW", 10) if LINE_SEED_FONT_LOADED else font_tuple(10, monospace=True)
        
        self.text_editor = scrolledtext.ScrolledText(
            left_frame,
            font=editor_font,
            wrap="none",
            bg="#ffffff",
            fg="#000000",
            insertbackground="#000000",
            selectbackground="#3399ff",
            undo=True,
            maxundo=-1
        )
        self.text_editor.pack(fill="both", expand=True)
        
        # 設定語法高亮標籤 (Dracula 配色)
        self.text_editor.tag_config("syntax_symbol", foreground="#BD93F9")      # 淡紫色 - 符號
        self.text_editor.tag_config("syntax_time", foreground="#FF79C6")        # 粉紅色 - 時間參數
        self.text_editor.tag_config("syntax_label", foreground="#8BE9FD")       # 青色 - 標籤
        self.text_editor.tag_config("syntax_keyboard", foreground="#BD93F9")    # 淡紫色 - 鍵盤操作
        self.text_editor.tag_config("syntax_mouse", foreground="#6272A4")       # 藍色 - 滑鼠座標
        self.text_editor.tag_config("syntax_image", foreground="#50FA7B")       # 綠色 - 圖片辨識
        self.text_editor.tag_config("syntax_condition", foreground="#FFB86C")   # 橘色 - 條件判斷
        self.text_editor.tag_config("syntax_ocr", foreground="#8BE9FD")         # 青色 - OCR 文字
        self.text_editor.tag_config("syntax_delay", foreground="#FFB86C")       # 橘色 - 延遲控制
        self.text_editor.tag_config("syntax_flow", foreground="#FF5555")        # 紅色 - 流程控制
        self.text_editor.tag_config("syntax_picname", foreground="#F1FA8C")     # 黃色 - 圖片名稱
        
        # 綁定內容變更事件以觸發語法高亮
        self.text_editor.bind("<<Modified>>", self._on_text_modified)
        
        # 綁定右鍵選單
        self.text_editor.bind("<Button-3>", self._show_context_menu)
        
        # 右側: 自訂模組管理 (自動擴展填滿剩餘空間)
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            right_frame,
            text="自訂模組",
            font=font_tuple(10, "bold")
        ).pack(anchor="w", pady=5)
        
        # 按鈕列
        module_btn_frame = tk.Frame(right_frame)
        module_btn_frame.pack(fill="x", pady=5)
        
        tk.Button(
            module_btn_frame,
            text="儲存新模組",
            command=self._save_new_module_inline,
            bg="#4CAF50",
            fg="white",
            font=font_tuple(9, "bold"),
            padx=10,
            pady=3
        ).pack(side="left", padx=2)
        
        tk.Button(
            module_btn_frame,
            text="插入模組",
            command=self._insert_module_inline,
            bg="#2196F3",
            fg="white",
            font=font_tuple(9, "bold"),
            padx=10,
            pady=3
        ).pack(side="left", padx=2)
        
        tk.Button(
            module_btn_frame,
            text="刪除",
            command=self._delete_module_inline,
            bg="#F44336",
            fg="white",
            font=font_tuple(9, "bold"),
            padx=10,
            pady=3
        ).pack(side="left", padx=2)
        
        # 模組列表
        tk.Label(
            right_frame,
            text="已儲存的模組 (雙擊插入):",
            font=font_tuple(9)
        ).pack(anchor="w", pady=(10, 5))
        
        list_container = tk.Frame(right_frame)
        list_container.pack(fill="both", expand=True, pady=5)
        
        list_scrollbar = tk.Scrollbar(list_container)
        list_scrollbar.pack(side="right", fill="y")
        
        self.module_listbox = tk.Listbox(
            list_container,
            font=font_tuple(9),
            yscrollcommand=list_scrollbar.set,
            height=8
        )
        self.module_listbox.pack(side="left", fill="both", expand=True)
        list_scrollbar.config(command=self.module_listbox.yview)
        
        self.module_listbox.bind("<Double-Button-1>", lambda e: self._insert_module_inline())
        self.module_listbox.bind("<<ListboxSelect>>", self._on_module_selected_inline)
        
        # 模組預覽
        tk.Label(
            right_frame,
            text="模組內容預覽:",
            font=font_tuple(9)
        ).pack(anchor="w", pady=(10, 5))
        
        self.module_preview = scrolledtext.ScrolledText(
            right_frame,
            font=font_tuple(8, monospace=True),
            height=6,
            wrap="none",
            state="disabled",
            bg="#f9f9f9"
        )
        self.module_preview.pack(fill="both", expand=True)
        
        # 載入模組列表
        self._load_modules_inline()
        
        # 底部狀態列（先創建，讓指令按鈕區可以放在它上方）
        self.status_label = tk.Label(
            self,
            text="就緒",
            font=font_tuple(9),
            bg="#e8f5e9",
            fg="#2e7d32",
            anchor="w",
            padx=10,
            pady=5
        )
        self.status_label.pack(fill="x", side="bottom")
        
        # 底部指令按鈕區（在狀態列之後創建，會自動顯示在它上方）
        self._create_command_buttons()
    
    def _show_message(self, title, message, msg_type="info"):
        """顯示自訂訊息對話框，不會改變父視窗位置"""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)  # 設定為編輯器的子視窗
        dialog.grab_set()  # 模態對話框
        
        # 警告/錯誤/資訊對應的文字符號
        icon_map = {"info": "[資訊]", "warning": "[警告]", "error": "[錯誤]"}
        color_map = {"info": "#1976d2", "warning": "#f57c00", "error": "#d32f2f"}
        
        icon = icon_map.get(msg_type, "[資訊]")
        color = color_map.get(msg_type, "#1976d2")
        
        # 主框架
        frame = tk.Frame(dialog, bg="white", padx=20, pady=15)
        frame.pack(fill="both", expand=True)
        
        # 標題列（圖示+訊息）
        msg_frame = tk.Frame(frame, bg="white")
        msg_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        icon_label = tk.Label(msg_frame, text=icon, font=font_tuple(20), bg="white", fg=color)
        icon_label.pack(side="left", padx=(0, 10))
        
        msg_label = tk.Label(msg_frame, text=message, font=font_tuple(10), bg="white", fg="#333", justify="left", wraplength=300)
        msg_label.pack(side="left", fill="both", expand=True)
        
        # 確認按鈕
        btn = tk.Button(frame, text="確定", font=font_tuple(10), bg=color, fg="white", 
                       command=dialog.destroy, relief="flat", padx=20, pady=5, cursor="hand2")
        btn.pack()
        
        # 置中顯示
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
    
    def _show_confirm(self, title, message):
        """顯示確認對話框（是/否）"""
        result = [False]  # 使用列表來儲存結果（可變對象）
        
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self)
        dialog.grab_set()
        
        # 主框架
        frame = tk.Frame(dialog, bg="white", padx=20, pady=15)
        frame.pack(fill="both", expand=True)
        
        # 訊息
        msg_frame = tk.Frame(frame, bg="white")
        msg_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        icon_label = tk.Label(msg_frame, text="[確認]", font=font_tuple(14, "bold"), bg="white", fg="#f57c00")
        icon_label.pack(side="left", padx=(0, 10))
        
        msg_label = tk.Label(msg_frame, text=message, font=font_tuple(10), bg="white", fg="#333", justify="left", wraplength=300)
        msg_label.pack(side="left", fill="both", expand=True)
        
        # 按鈕列
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack()
        
        def on_yes():
            result[0] = True
            dialog.destroy()
        
        def on_no():
            result[0] = False
            dialog.destroy()
        
        yes_btn = tk.Button(btn_frame, text="是", font=font_tuple(10), bg="#4caf50", fg="white",
                           command=on_yes, relief="flat", padx=20, pady=5, cursor="hand2")
        yes_btn.pack(side="left", padx=5)
        
        no_btn = tk.Button(btn_frame, text="否", font=font_tuple(10), bg="#757575", fg="white",
                          command=on_no, relief="flat", padx=20, pady=5, cursor="hand2")
        no_btn.pack(side="left", padx=5)
        
        # 置中顯示
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.wait_window()
        return result[0]
    
    def _update_status(self, text, status_type="info"):
        """更新狀態列，支持不同類型的狀態顯示"""
        status_colors = {
            "info": {"bg": "#e3f2fd", "fg": "#1976d2"},
            "success": {"bg": "#e8f5e9", "fg": "#2e7d32"},
            "warning": {"bg": "#fff3e0", "fg": "#e65100"},
            "error": {"bg": "#ffebee", "fg": "#c62828"}
        }
        
        colors = status_colors.get(status_type, status_colors["info"])
        self.status_label.config(text=text, bg=colors["bg"], fg=colors["fg"])
    
    def _create_command_buttons(self):
        """創建底部指令按鈕區（三行佈局）"""
        # 主容器框架（增加高度以容納三行按鈕）
        cmd_frame = tk.Frame(self, bg="#2b2b2b", height=150)
        cmd_frame.pack(fill="x", side="bottom")
        cmd_frame.pack_propagate(False)
        
        # 標題
        title_label = tk.Label(
            cmd_frame,
            text="快速指令",
            font=font_tuple(9, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        title_label.pack(anchor="w", padx=10, pady=(3, 3))
        
        # 按鈕容器（不使用滾動條，直接三行佈局）
        button_container = tk.Frame(cmd_frame, bg="#2b2b2b")
        button_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        
        # 定義三行按鈕（行索引, 列表）
        button_rows = [
            # 第一行：圖片相關指令
            [
                ("圖片辨識", "#9C27B0", self._capture_and_recognize, None),  # 截圖+辨識
                ("範圍辨識", "#7B1FA2", self._capture_region_for_recognition, None),  # 新增：範圍辨識
                ("移動至圖片", "#673AB7", None, ">移動至>pic01, T=0s000"),
                ("點擊圖片", "#3F51B5", None, ">左鍵點擊>pic01, T=0s000"),
                ("條件判斷", "#2196F3", None, ">if>pic01, T=0s000\n>>#標籤\n>>>#標籤"),
                ("找圖迴圈", "#E91E63", None, "#找圖\n>if>pic01, T=0s000\n>>#點擊*3\n>>>#找圖*7\n\n#點擊\n>左鍵點擊>pic01, T=0s000"),
            ],
            # 第二行：滑鼠和鍵盤指令
            [
                ("左鍵點擊", "#03A9F4", None, ">左鍵點擊(0,0), 延遲50ms, T=0s000"),
                ("右鍵點擊", "#00BCD4", None, ">右鍵點擊(0,0), 延遲50ms, T=0s000"),
                ("滑鼠移動", "#009688", None, ">移動至(0,0), 延遲0ms, T=0s000"),
                ("滑鼠滾輪", "#4CAF50", None, ">滾輪(1), 延遲0ms, T=0s000"),
                ("按下按鍵", "#8BC34A", None, ">按下a, 延遲50ms, T=0s000"),
                ("放開按鍵", "#CDDC39", None, ">放開a, 延遲0ms, T=0s000"),
            ],
            # 第三行：流程控制和組合指令
            [
                ("新增標籤", "#FFC107", None, "#標籤名稱"),
                ("跳轉標籤", "#FF9800", None, ">>#標籤名稱"),
                ("條件失敗跳轉", "#FF5722", None, ">>>#標籤名稱"),
                ("OCR文字判斷", "#00BCD4", None, ">if文字>確認, T=0s000\n>>#找到\n>>>#沒找到"),
                ("OCR等待文字", "#009688", None, ">等待文字>載入完成, 最長10s, T=0s000"),
                ("OCR點擊文字", "#4CAF50", None, ">點擊文字>登入, T=0s000"),
                ("延遲等待", "#795548", None, ">延遲1000ms, T=0s000"),
            ]
        ]
        
        # 創建三行按鈕
        for row_idx, row_buttons in enumerate(button_rows):
            for col_idx, (text, color, command, template) in enumerate(row_buttons):
                if command:
                    # 特殊功能按鈕（如圖片辨識）
                    btn = tk.Button(
                        button_container,
                        text=text,
                        bg=color,
                        fg="white",
                        font=font_tuple(8, "bold"),
                        padx=8,
                        pady=3,
                        relief="raised",
                        bd=2,
                        cursor="hand2",
                        command=command
                    )
                else:
                    # 插入模板的按鈕
                    btn = tk.Button(
                        button_container,
                        text=text,
                        bg=color,
                        fg="white",
                        font=font_tuple(8, "bold"),
                        padx=8,
                        pady=3,
                        relief="raised",
                        bd=2,
                        cursor="hand2",
                        command=lambda t=template: self._insert_command_template(t)
                    )
                
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="ew")
            
            # 設定列權重，讓按鈕平均分配空間
            for col in range(len(row_buttons)):
                button_container.columnconfigure(col, weight=1)
    
    def _insert_command_template(self, template):
        """插入指令模板到編輯器"""
        if not template:
            return
        
        # 獲取當前游標位置
        try:
            cursor_pos = self.text_editor.index(tk.INSERT)
        except:
            cursor_pos = "end"
        
        # 在游標位置插入模板
        self.text_editor.insert(cursor_pos, template + "\n")
        
        # 更新狀態
        self._update_status(f"已插入指令模板", "success")
        
        # 聚焦到編輯器
        self.text_editor.focus_set()
    
    def _on_combo_click(self, event):
        """點擊下拉選單時刷新列表"""
        self._refresh_script_list()
    
    def _refresh_script_list(self):
        """刷新腳本下拉選單內容"""
        script_dir = os.path.join(os.getcwd(), "scripts")
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
        
        # 獲取所有腳本（去除副檔名）
        scripts = [f for f in os.listdir(script_dir) if f.endswith('.json')]
        display_scripts = [os.path.splitext(f)[0] for f in scripts]
        
        # 第一個選項固定為"新增腳本"
        all_options = ["新增腳本"] + sorted(display_scripts)
        self.script_combo['values'] = all_options
    
    def _on_script_selected(self, event):
        """處理腳本選擇事件"""
        selected = self.script_var.get()
        
        if selected == "新增腳本":
            # 彈出簡單命名對話框
            self._show_create_script_dialog()
        else:
            # 載入選中的腳本
            script_dir = os.path.join(os.getcwd(), "scripts")
            self.script_path = os.path.join(script_dir, selected + ".json")
            
            # 載入前檢查檔案是否存在且有效
            if os.path.exists(self.script_path):
                try:
                    with open(self.script_path, 'r', encoding='utf-8') as f:
                        test_data = json.load(f)
                    # 檢查是否為有效的腳本格式
                    if isinstance(test_data, dict) and ("events" in test_data or "settings" in test_data):
                        self._load_script()
                    else:
                        self._show_message("錯誤", f"腳本格式不正確：{selected}", "error")
                except Exception as e:
                    self._show_message("錯誤", f"無法讀取腳本：{e}", "error")
            else:
                self._show_message("警告", f"腳本檔案不存在：{selected}", "warning")
    
    def _show_create_script_dialog(self):
        """顯示新增腳本命名對話框"""
        dialog = tk.Toplevel(self)
        dialog.title("")
        dialog.geometry("300x100")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # 文字輸入框
        entry_var = tk.StringVar()
        entry = tk.Entry(dialog, textvariable=entry_var, font=font_tuple(11), width=25)
        entry.pack(padx=20, pady=20)
        entry.focus()
        
        # 確定按鈕
        def on_confirm():
            name = entry_var.get().strip()
            if name:
                dialog.result = name
                dialog.destroy()
        
        btn = tk.Button(dialog, text="確定", command=on_confirm, 
                       font=font_tuple(10), bg="#4CAF50", fg="white",
                       padx=30, pady=5)
        btn.pack(pady=5)
        
        # 綁定 Enter 鍵
        entry.bind('<Return>', lambda e: on_confirm())
        
        # 置中顯示
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        dialog.result = None
        dialog.wait_window()
        
        # 如果有輸入名稱，創建腳本
        if dialog.result:
            self._create_custom_script(dialog.result)
    
    def _create_custom_script(self, custom_name):
        """建立自訂腳本"""
        custom_name = custom_name.strip()
        
        # 檢查檔名是否合法
        if any(char in custom_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            self._show_message("錯誤", "檔名包含非法字元", "error")
            return
        
        script_dir = os.path.join(os.getcwd(), "scripts")
        script_path = os.path.join(script_dir, custom_name + ".json")
        
        # 檢查檔案是否已存在
        if os.path.exists(script_path):
            self._show_message("提示", f"腳本「{custom_name}」已存在", "warning")
            return
        
        # 建立空白腳本
        try:
            empty_script = {
                "events": [],
                "settings": {
                    "speed": "100",
                    "repeat": "1",
                    "repeat_time": "00:00:00",
                    "repeat_interval": "00:00:00"
                }
            }
            
            with open(script_path, 'w', encoding='utf-8') as f:
                json.dump(empty_script, f, ensure_ascii=False, indent=2)
            
            # 設定為當前腳本
            self.script_path = script_path
            
            # 載入空白腳本
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", f"# ChroLens 文字指令腳本\n# 預設按鍵持續時間: 50ms\n# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            
            # 刷新列表並選中新腳本
            self._refresh_script_list()
            self.script_var.set(custom_name)
            
            self.status_label.config(
                text=f"已建立新腳本: {custom_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
            
        except Exception as e:
            self._show_message("錯誤", f"建立腳本失敗:\n{e}", "error")
    
    def _load_script(self):
        """載入腳本並轉換為文字指令"""
        if not self.script_path or not os.path.exists(self.script_path):
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", "# ChroLens 文字指令腳本\n# 預設按鍵持續時間: 50ms\n# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            return
        
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 保存原始設定（防止儲存時被預設值覆蓋）
            if isinstance(data, dict) and "settings" in data:
                self.original_settings = data["settings"].copy()
            elif isinstance(data, dict) and "events" in data:
                # 舊格式：沒有 settings 區塊，使用預設值
                self.original_settings = {
                    "speed": "100",
                    "repeat": "1",
                    "repeat_time": "00:00:00",
                    "repeat_interval": "00:00:00",
                    "random_interval": False,
                    "script_hotkey": "",
                    "script_actions": [],
                    "window_info": None
                }
            else:
                # 純 events 陣列格式
                self.original_settings = {
                    "speed": "100",
                    "repeat": "1",
                    "repeat_time": "00:00:00",
                    "repeat_interval": "00:00:00",
                    "random_interval": False,
                    "script_hotkey": "",
                    "script_actions": [],
                    "window_info": None
                }
            
            # 轉換為文字指令（增加錯誤處理）
            try:
                text_commands = self._json_to_text(data)
                
                # 檢查轉換結果是否有效（避免載入空內容）
                if not text_commands or text_commands.strip() == "":
                    raise ValueError("轉換結果為空")
                
                # 只有轉換成功且有內容才更新編輯器
                self.text_editor.delete("1.0", "end")
                self.text_editor.insert("1.0", text_commands)
                
                # 載入後套用語法高亮
                self._apply_syntax_highlighting()
                
                self._update_status(
                    f"已載入: {os.path.basename(self.script_path)} ({len(data.get('events', []))}筆事件)",
                    "success"
                )
            except Exception as convert_error:
                # 轉換失敗不清空編輯器，顯示錯誤訊息
                import traceback
                error_detail = traceback.format_exc()
                
                error_msg = f"# 轉換失敗：{convert_error}\n\n"
                error_msg += f"# 錯誤詳情：\n# {error_detail.replace(chr(10), chr(10) + '# ')}\n\n"
                error_msg += "# 原始 JSON 資料：\n"
                error_msg += json.dumps(data, ensure_ascii=False, indent=2)
                
                self.text_editor.delete("1.0", "end")
                self.text_editor.insert("1.0", error_msg)
                
                self._update_status(f"警告: 轉換失敗: {convert_error}", "warning")
                
                self._show_message(
                    "警告", 
                    f"腳本轉換失敗，可能包含異常資料：\n\n{convert_error}\n\n"
                    f"已顯示原始 JSON 資料，請查看日誌或手動修復。",
                    "warning"
                )
            
        except Exception as e:
            self._show_message("錯誤", f"載入腳本失敗:\n{e}", "error")
            self._update_status(f"錯誤: 載入失敗: {e}", "error")
    
    def _json_to_text(self, data: Dict) -> str:
        """將JSON事件轉換為文字指令"""
        events = data.get("events", [])
        lines = ["# ChroLens 文字指令腳本\n"]
        lines.append(f"# 預設按鍵持續時間: {self.default_key_duration}ms\n")
        lines.append("# ←←可用\"#\"來進行備註 \n")
        lines.append("# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
        
        # 空腳本處理
        if not events:
            lines.append("# 此腳本無事件\n")
            lines.append("# 請先錄製操作或手動新增指令\n")
            return "".join(lines)
        
        # 記錄按下但未放開的按鍵
        pressed_keys = {}
        start_time = events[0]["time"] if events else 0
        
        # 逐迴所有事件，增加異常處理
        for idx, event in enumerate(events):
            try:
                event_type = event.get("type")
                event_name = event.get("event")
                time_offset = event.get("time", 0) - start_time
                
                # 格式化時間
                time_str = self._format_time(time_offset)
                
                # 標籤事件 (跳轉目標)
                if event_type == "label":
                    label_name = event.get("name", "")
                    lines.append(f"#{label_name}\n")
                
                elif event_type == "keyboard":
                    key_name = event.get("name", "")
                    
                    if event_name == "down":
                        # 記錄按下時間
                        pressed_keys[key_name] = time_offset
                        
                    elif event_name == "up" and key_name in pressed_keys:
                        # 計算持續時間
                        press_time = pressed_keys[key_name]
                        duration = int((time_offset - press_time) * 1000)  # 轉為毫秒
                        
                        # 格式化按下時間
                        press_time_str = self._format_time(press_time)
                        
                        # 生成指令
                        lines.append(f">按{key_name}, 延遲{duration}ms, T={press_time_str}\n")
                        
                        del pressed_keys[key_name]
                
                elif event_type == "mouse":
                    x = event.get("x", 0)
                    y = event.get("y", 0)
                    
                    if event_name == "move":
                        lines.append(f">移動至({x},{y}), 延遲0ms, T={time_str}\n")
                    
                    elif event_name == "down":
                        button = event.get("button", "left")
                        lines.append(f">按下{button}鍵({x},{y}), 延遲0ms, T={time_str}\n")
                    
                    elif event_name == "up":
                        button = event.get("button", "left")
                        lines.append(f">放開{button}鍵({x},{y}), 延遲0ms, T={time_str}\n")
                
                # 圖片辨識指令
                elif event_type == "recognize_image":
                    pic_name = event.get("image", "")
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    
                    # 建構指令
                    cmd = f">辨識>{pic_name}"
                    if show_border:
                        cmd += ", 邊框"
                    if region:
                        cmd += f", 範圍({region[0]},{region[1]},{region[2]},{region[3]})"
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                
                elif event_type == "move_to_image":
                    pic_name = event.get("image", "")
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    
                    cmd = f">移動至>{pic_name}"
                    if show_border:
                        cmd += ", 邊框"
                    if region:
                        cmd += f", 範圍({region[0]},{region[1]},{region[2]},{region[3]})"
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                
                # ==================== OCR 文字辨識事件格式化 ====================
                elif event_type == "if_text_exists":
                    target_text = event.get("target_text", "")
                    lines.append(f">if文字>{target_text}, T={time_str}\n")
                    
                    # 成功分支
                    on_success = event.get("on_success", {})
                    if on_success:
                        branch_text = self._format_branch_action(on_success)
                        lines.append(f">>{branch_text}\n")
                    
                    # 失敗分支
                    on_failure = event.get("on_failure", {})
                    if on_failure:
                        branch_text = self._format_branch_action(on_failure)
                        lines.append(f">>>{branch_text}\n")
                
                elif event_type == "wait_text":
                    target_text = event.get("target_text", "")
                    timeout = event.get("timeout", 10.0)
                    lines.append(f">等待文字>{target_text}, 最長{timeout}s, T={time_str}\n")
                
                elif event_type == "click_text":
                    target_text = event.get("target_text", "")
                    lines.append(f">點擊文字>{target_text}, T={time_str}\n")
                
                elif event_type == "click_image":
                    pic_name = event.get("image", "")
                    button = event.get("button", "left")
                    button_name = "左鍵" if button == "left" else "右鍵"
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    
                    cmd = f">{button_name}點擊>{pic_name}"
                    if show_border:
                        cmd += ", 邊框"
                    if region:
                        cmd += f", 範圍({region[0]},{region[1]},{region[2]},{region[3]})"
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                
                elif event_type == "if_image_exists":
                    pic_name = event.get("image", "")
                    on_success = event.get("on_success", {})
                    on_failure = event.get("on_failure", {})
                    show_border = event.get("show_border", False)
                    region = event.get("region", None)
                    
                    # 使用新的簡化格式：>if>pic01, T=xxx
                    cmd = f">if>{pic_name}"
                    if show_border:
                        cmd += ", 邊框"
                    if region:
                        cmd += f", 範圍({region[0]},{region[1]},{region[2]},{region[3]})"
                    cmd += f", T={time_str}\n"
                    lines.append(cmd)
                    
                    # 格式化分支動作（使用 >> 和 >>> 格式）
                    if on_success:
                        success_action = self._format_branch_action(on_success)
                        # 只在有實際內容時才添加分支行
                        if success_action or on_success.get("action") != "continue":
                            lines.append(f">>{success_action}\n")
                    
                    if on_failure:
                        failure_action = self._format_branch_action(on_failure)
                        # 只在有實際內容時才添加分支行
                        if failure_action or on_failure.get("action") != "continue":
                            lines.append(f">>>{failure_action}\n")
                
                elif event_type == "recognize_any":
                    images = event.get("images", [])
                    pic_names = [img.get("name", "") for img in images]
                    pic_list = "|".join(pic_names)
                    lines.append(f">辨識任一>{pic_list}, T={time_str}\n")
                
                # 延遲事件
                elif event_type == "delay":
                    duration_ms = int(event.get("duration", 0) * 1000)
                    lines.append(f">延遲{duration_ms}ms, T={time_str}\n")
                
                # 戰鬥指令
                elif event_type in ["start_combat", "find_and_attack", "loop_attack", "smart_combat", "set_combat_region", "pause_combat", "resume_combat", "stop_combat"]:
                    combat_line = self._format_combat_event(event)
                    if combat_line:
                        lines.append(f">{combat_line}, T={time_str}\n")
            
            except Exception as event_error:
                # 異常事件跳過，記錄錯誤
                lines.append(f"# 事件{idx}轉換失敗: {event_error}\n")
                lines.append(f"# 異常事件: {event}\n\n")
                continue
        
        # 處理未放開的按鍵
        if pressed_keys:
            lines.append("\n# 警告: 以下按鍵被按下但未放開\n")
            for key, time in pressed_keys.items():
                time_str = self._format_time(time)
                lines.append(f"# >按下{key}, T={time_str} (未放開)\n")
        
        return "".join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """格式化時間為易讀格式"""
        total_ms = int(seconds * 1000)
        s = total_ms // 1000
        ms = total_ms % 1000
        
        if s >= 60:
            m = s // 60
            s = s % 60
            return f"{m}m{s:02d}s{ms:03d}"
        else:
            return f"{s}s{ms:03d}"
    
    def _parse_time(self, time_str: str) -> float:
        """解析時間字串為秒數"""
        # T=17s500 或 T=1m30s500
        time_str = time_str.replace("T=", "").strip()
        
        total_seconds = 0.0
        
        # 解析分鐘
        if "m" in time_str:
            parts = time_str.split("m")
            total_seconds += float(parts[0]) * 60
            time_str = parts[1]
        
        # 解析秒和毫秒
        if "s" in time_str:
            parts = time_str.split("s")
            total_seconds += float(parts[0])
            if len(parts) > 1 and parts[1]:
                total_seconds += float(parts[1]) / 1000
        
        return total_seconds
    
    def _text_to_json(self, text: str) -> Dict:
        """將文字指令轉換回JSON格式 (支援圖片指令)"""
        import time
        lines = text.split("\n")
        events = []
        labels = {}  # 標籤映射
        start_time = time.time()  # 使用當前時間戳
        
        # 第一遍: 掃描標籤
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("#") and not line.startswith("# "):
                # 這是標籤定義
                label_name = line[1:].strip()
                labels[label_name] = i
        
        # 第二遍: 解析指令
        i = 0
        pending_label = None  # 暫存標籤,等待下一個事件的時間
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳過註釋和空行
            if not line or line.startswith("# "):
                i += 1
                continue
            
            # 標籤定義
            if line.startswith("#"):
                label_name = line[1:].strip()
                # 暫存標籤,使用下一個事件的時間
                pending_label = label_name
                i += 1
                continue
            
            # 解析指令
            if line.startswith(">"):
                # 跳過分支指令（>> 和 >>>），這些會在條件指令中處理
                if line.startswith(">>"):
                    i += 1
                    continue
                
                # 處理 >範圍結束 指令
                if "範圍結束" in line:
                    # 解析時間
                    time_str = line.split(",")[-1].strip() if "," in line and "T=" in line else "T=0s000"
                    abs_time = start_time + self._parse_time(time_str)
                    
                    events.append({
                        "type": "region_end",
                        "time": abs_time
                    })
                    i += 1
                    continue
                
                try:
                    # 檢查是否為戰鬥指令
                    if any(keyword in line for keyword in ["啟動自動戰鬥", "尋找並攻擊", "循環攻擊", "智能戰鬥", "設定戰鬥區域", "暫停戰鬥", "恢復戰鬥", "停止戰鬥"]):
                        # 戰鬥指令處理
                        event = self._parse_combat_command_to_json(line, start_time)
                        if event:
                            # 如果有待處理的標籤,先加入標籤事件
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": event.get("time", start_time)
                                })
                                pending_label = None
                            events.append(event)
                        i += 1
                        continue
                    
                    # 檢查是否為圖片指令或OCR指令（支援舊格式和新格式）
                    # 重要：OCR指令（if文字>、等待文字>、點擊文字>）也要在這裡處理
                    if any(keyword in line for keyword in [
                        "等待圖片", "點擊圖片", "如果存在", 
                        "辨識>", "移動至>", "左鍵點擊>", "右鍵點擊>", 
                        "如果存在>", "辨識任一>", "if>",
                        "if文字>", "等待文字>", "點擊文字>",  # OCR指令
                        "延遲"  # 延遲指令
                    ]):
                        # 圖片指令和OCR指令處理
                        event = self._parse_image_command_to_json(line, lines[i+1:i+6], start_time)
                        if event:
                            # 如果有待處理的標籤,先加入標籤事件
                            if pending_label:
                                events.append({
                                    "type": "label",
                                    "name": pending_label,
                                    "time": event.get("time", start_time)
                                })
                                pending_label = None
                            events.append(event)
                        i += 1
                        continue
                    
                    # 移除 ">" 並智能分割（保護括號內的逗號）
                    line_content = line[1:]
                    
                    # 先保護括號內的內容
                    protected = re.sub(r'\(([^)]+)\)', lambda m: f"({m.group(1).replace(',', '§')})", line_content)
                    parts_raw = protected.split(",")
                    # 還原括號內的逗號
                    parts = [p.replace('§', ',') for p in parts_raw]
                    
                    # 修復：更寬鬆的格式處理，允許只有動作和時間（缺少延遲）
                    if len(parts) >= 2:
                        action = parts[0].strip()
                        
                        # 智能判斷：如果第二部分包含 T=，則視為時間（缺少延遲欄位）
                        if len(parts) == 2 and "T=" in parts[1]:
                            delay_str = "0ms"
                            time_str = parts[1].strip()
                        else:
                            delay_str = parts[1].strip() if len(parts) > 1 else "0ms"
                            time_str = parts[2].strip() if len(parts) > 2 else "T=0s000"
                        
                        # 解析時間
                        abs_time = start_time + self._parse_time(time_str)
                        
                        # 如果有待處理的標籤,先加入標籤事件
                        if pending_label:
                            events.append({
                                "type": "label",
                                "name": pending_label,
                                "time": abs_time
                            })
                            pending_label = None
                        
                        # 解析延遲
                        delay_ms = int(re.search(r'\d+', delay_str).group()) if re.search(r'\d+', delay_str) else 0
                        delay_s = delay_ms / 1000.0
                        
                        # 解析動作類型
                        # 優先檢查滑鼠操作（避免誤判為鍵盤操作）
                        # 修復：先嘗試提取座標，如果成功就是滑鼠操作
                        coords = re.search(r'\((\d+),(\d+)\)', action)
                        if coords:
                            # 確定是滑鼠操作（有座標）
                            x, y = int(coords.group(1)), int(coords.group(2))
                            
                            if "移動至" in action:
                                events.append({"type": "mouse", "event": "move", "x": x, "y": y, "time": abs_time, "in_target": True})
                            elif "點擊" in action or "鍵" in action:
                                # 解析按鍵類型
                                button = "right" if "右鍵" in action else "middle" if "中鍵" in action else "left"
                                
                                # 判斷是點擊還是按下/放開
                                if "點擊" in action:
                                    # 點擊 = 按下 + 放開
                                    events.append({"type": "mouse", "event": "down", "button": button, "x": x, "y": y, "time": abs_time, "in_target": True})
                                    events.append({"type": "mouse", "event": "up", "button": button, "x": x, "y": y, "time": abs_time + 0.05, "in_target": True})
                                elif "按下" in action:
                                    events.append({"type": "mouse", "event": "down", "button": button, "x": x, "y": y, "time": abs_time, "in_target": True})
                                elif "放開" in action:
                                    events.append({"type": "mouse", "event": "up", "button": button, "x": x, "y": y, "time": abs_time, "in_target": True})
                        
                        elif action.startswith("按") and "按下" not in action and "按鍵" not in action:
                            # 鍵盤操作（按 = 按下 + 放開）
                            key = action.replace("按", "").strip()
                            
                            # 按下事件
                            events.append({
                                "type": "keyboard",
                                "event": "down",
                                "name": key,
                                "time": abs_time
                            })
                            
                            # 放開事件
                            events.append({
                                "type": "keyboard",
                                "event": "up",
                                "name": key,
                                "time": abs_time + delay_s
                            })
                        
                        elif "按下" in action:
                            # 單純按下按鍵
                            key = action.replace("按下", "").strip()
                            events.append({
                                "type": "keyboard",
                                "event": "down",
                                "name": key,
                                "time": abs_time
                            })
                        
                        elif "放開" in action:
                            # 單純放開按鍵
                            key = action.replace("放開", "").strip()
                            events.append({
                                "type": "keyboard",
                                "event": "up",
                                "name": key,
                                "time": abs_time
                            })
                
                except Exception as e:
                    print(f"解析行失敗: {line}\n錯誤: {e}")
                    i += 1
                    continue
            
            i += 1
        
        # 按時間排序
        events.sort(key=lambda x: x["time"])
        
        # 使用保存的原始設定，而非硬編碼預設值（修復儲存時覆蓋設定的問題）
        settings = self.original_settings if self.original_settings else {
            "speed": "100",
            "repeat": "1",
            "repeat_time": "00:00:00",
            "repeat_interval": "00:00:00",
            "random_interval": False,
            "script_hotkey": "",
            "script_actions": [],
            "window_info": None
        }
        
        return {
            "events": events,
            "settings": settings
        }
    
    def _parse_image_command_to_json(self, command_line: str, next_lines: list, start_time: float) -> dict:
        """
        解析圖片指令並轉換為JSON格式
        :param command_line: 圖片指令行
        :param next_lines: 後續行 (用於讀取分支)
        :param start_time: 起始時間戳
        :return: JSON事件字典
        """
        # 辨識圖片指令（新格式：>辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s100）
        recognize_pattern = r'>辨識>([^,]+)(?:,\s*([^T]+))?,\s*T=(\d+)s(\d+)'
        match = re.match(recognize_pattern, command_line)
        if match:
            pic_name = match.group(1).strip()
            options_str = match.group(2).strip() if match.group(2) else ""
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in options_str
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', options_str)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 檢查後續行是否有分支（>> 或 >>>）
            branches = self._parse_simple_condition_branches(next_lines)
            
            # 如果有分支，則視為條件判斷
            if branches.get('success') or branches.get('failure'):
                result = {
                    "type": "if_image_exists",
                    "image": pic_name,
                    "image_file": image_file,
                    "confidence": 0.7,
                    "on_success": branches.get('success'),
                    "on_failure": branches.get('failure'),
                    "time": abs_time
                }
                if show_border:
                    result["show_border"] = True
                if region:
                    result["region"] = region
                return result
            
            # 否則視為普通辨識指令
            result = {
                "type": "recognize_image",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result        # 移動至圖片指令（>移動至>pic01, 邊框, 範圍(x1,y1,x2,y2), T=1s000）
        move_pattern = r'>移動至>([^,]+)(?:,\s*([^T]+))?,\s*T=(\d+)s(\d+)'
        match = re.match(move_pattern, command_line)
        if match:
            pic_name = match.group(1).strip()
            options_str = match.group(2).strip() if match.group(2) else ""
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in options_str
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', options_str)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            result = {
                "type": "move_to_image",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result        # 點擊圖片指令（>左鍵點擊>pic01, 邊框, 範圍(x1,y1,x2,y2), T=1s200）
        click_pattern = r'>(左鍵|右鍵)點擊>([^,]+)(?:,\s*([^T]+))?,\s*T=(\d+)s(\d+)'
        match = re.match(click_pattern, command_line)
        if match:
            button = "left" if match.group(1) == "左鍵" else "right"
            pic_name = match.group(2).strip()
            options_str = match.group(3).strip() if match.group(3) else ""
            seconds = int(match.group(4))
            millis = int(match.group(5))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in options_str
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', options_str)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            result = {
                "type": "click_image",
                "button": button,
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.7,
                "return_to_origin": True,
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result        # 新格式條件判斷：>if>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s100
        if_simple_pattern = r'>if>([^,]+)(?:,\s*([^T]+))?,\s*T=(\d+)s(\d+)'
        match = re.match(if_simple_pattern, command_line)
        if match:
            pic_name = match.group(1).strip()
            options_str = match.group(2).strip() if match.group(2) else ""
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析選項
            show_border = '邊框' in options_str
            region = None
            region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', options_str)
            if region_match:
                region = (
                    int(region_match.group(1)),
                    int(region_match.group(2)),
                    int(region_match.group(3)),
                    int(region_match.group(4))
                )
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 解析後續行的 >> 和 >>> 分支
            branches = self._parse_simple_condition_branches(next_lines)
            
            # >if> 指令預期有分支，如果沒有則添加預設值
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            result = {
                "type": "if_image_exists",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
            if show_border:
                result["show_border"] = True
            if region:
                result["region"] = region
            return result
        
        # 新增：如果存在圖片（條件判斷）>如果存在>pic01, T=0s100
        if_exists_pattern = r'>如果存在>([^,]+),\s*T=(\d+)s(\d+)'
        match = re.match(if_exists_pattern, command_line)
        if match:
            pic_name = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 查找對應的圖片檔案
            image_file = self._find_pic_image_file(pic_name)
            
            # 解析後續行的成功/失敗分支
            branches = self._parse_condition_branches(next_lines)
            
            return {
                "type": "if_image_exists",
                "image": pic_name,
                "image_file": image_file,
                "confidence": 0.75,
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # ==================== OCR 文字辨識指令 ====================
        
        # OCR 條件判斷：>if文字>確認, T=0s000
        ocr_if_pattern = r'>if文字>([^,]+),\s*T=(\d+)s(\d+)'
        match = re.match(ocr_if_pattern, command_line)
        if match:
            target_text = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 解析後續行的 >> 和 >>> 分支
            branches = self._parse_simple_condition_branches(next_lines)
            
            # 預設分支
            if "success" not in branches:
                branches["success"] = {"action": "continue"}
            if "failure" not in branches:
                branches["failure"] = {"action": "continue"}
            
            return {
                "type": "if_text_exists",
                "target_text": target_text,
                "timeout": 10.0,  # 預設等待10秒
                "match_mode": "contains",  # contains/exact/regex
                "on_success": branches.get('success'),
                "on_failure": branches.get('failure'),
                "time": abs_time
            }
        
        # 等待文字出現：>等待文字>確認, 最長10s, T=0s000
        ocr_wait_pattern = r'>等待文字>([^,]+),\s*最長(\d+(?:\.\d+)?)[sS],\s*T=(\d+)s(\d+)'
        match = re.match(ocr_wait_pattern, command_line)
        if match:
            target_text = match.group(1).strip()
            timeout = float(match.group(2))
            seconds = int(match.group(3))
            millis = int(match.group(4))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "wait_text",
                "target_text": target_text,
                "timeout": timeout,
                "match_mode": "contains",
                "time": abs_time
            }
        
        # 點擊文字位置：>點擊文字>登入, T=0s000
        ocr_click_pattern = r'>點擊文字>([^,]+),\s*T=(\d+)s(\d+)'
        match = re.match(ocr_click_pattern, command_line)
        if match:
            target_text = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "click_text",
                "target_text": target_text,
                "timeout": 5.0,
                "time": abs_time
            }
        
        # 延遲指令：>延遲1000ms, T=0s000
        delay_pattern = r'>延遲(\d+)ms,\s*T=(\d+)s(\d+)'
        match = re.match(delay_pattern, command_line)
        if match:
            delay_ms = int(match.group(1))
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            return {
                "type": "delay",
                "duration": delay_ms / 1000.0,  # 轉為秒
                "time": abs_time
            }
        
        # 新增：辨識任一圖片（多圖同時辨識）>辨識任一>pic01|pic02|pic03, T=0s100
        recognize_any_pattern = r'>辨識任一>([^,]+),\s*T=(\d+)s(\d+)'
        match = re.match(recognize_any_pattern, command_line)
        if match:
            pic_names = match.group(1).strip().split('|')
            seconds = int(match.group(2))
            millis = int(match.group(3))
            abs_time = start_time + seconds + millis / 1000.0
            
            # 為每張圖片建立配置
            images = []
            for pic_name in pic_names:
                pic_name = pic_name.strip()
                images.append({
                    'name': pic_name,
                    'action': 'click',  # 預設點擊
                    'button': 'left',
                    'return_to_origin': True
                })
            
            return {
                "type": "recognize_any",
                "images": images,
                "confidence": 0.75,
                "timeout": 10,  # 預設10秒逾時
                "time": abs_time
            }
        
        event = {"time": start_time}
        
        # 等待圖片
        wait_pattern = r'>等待圖片\[([^\]]+)\],?\s*超時(\d+(?:\.\d+)?)[sS]?'
        match = re.match(wait_pattern, command_line)
        if match:
            event["type"] = "wait_image"
            event["image"] = match.group(1)
            event["timeout"] = float(match.group(2))
            event["confidence"] = 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 點擊圖片
        click_pattern = r'>點擊圖片\[([^\]]+)\](?:,?\s*信心度([\d.]+))?'
        match = re.match(click_pattern, command_line)
        if match:
            event["type"] = "click_image"
            event["image"] = match.group(1)
            event["confidence"] = float(match.group(2)) if match.group(2) else 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 移動到圖片（新增）
        move_pattern = r'>移動到圖片\[([^\]]+)\](?:,?\s*信心度([\d.]+))?'
        match = re.match(move_pattern, command_line)
        if match:
            event["type"] = "move_to_image"
            event["image"] = match.group(1)
            event["confidence"] = float(match.group(2)) if match.group(2) else 0.75
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        # 條件判斷
        exists_pattern = r'>如果存在\[([^\]]+)\]'
        match = re.match(exists_pattern, command_line)
        if match:
            event["type"] = "if_exists"
            event["image"] = match.group(1)
            event["branches"] = self._parse_branches(next_lines)
            return event
        
        return None
    
    def _parse_branches(self, next_lines: list) -> dict:
        """
        解析分支指令
        :param next_lines: 後續行列表
        :return: 分支字典
        """
        branches = {}
        
        for line in next_lines[:5]:  # 只看接下來5行
            line = line.strip()
            if not line or line.startswith(">") or line.startswith("#"):
                break
            
            # 成功分支
            success_pattern = r'\s*成功→(.+)'
            match = re.match(success_pattern, line)
            if match:
                branches["success"] = self._parse_branch_action(match.group(1).strip())
                continue
            
            # 失敗分支
            failure_pattern = r'\s*失敗→(.+)'
            match = re.match(failure_pattern, line)
            if match:
                branches["failure"] = self._parse_branch_action(match.group(1).strip())
                continue
            
            # 執行分支
            execute_pattern = r'\s*執行→(.+)'
            match = re.match(execute_pattern, line)
            if match:
                branches["execute"] = self._parse_branch_action(match.group(1).strip())
                continue
        
        return branches
    
    def _parse_condition_branches(self, next_lines: list) -> dict:
        """
        解析條件判斷的分支（成功/失敗）
        :param next_lines: 後續行列表
        :return: 分支字典 {'success': {...}, 'failure': {...}}
        """
        branches = {}
        
        for line in next_lines[:5]:  # 只看接下來5行
            line = line.strip()
            if not line:
                continue
            if line.startswith(">") or line.startswith("#"):
                break
            
            # 成功分支：成功→繼續 / 成功→停止 / 成功→跳到#標籤
            success_pattern = r'成功→(.+)'
            match = re.match(success_pattern, line)
            if match:
                action_str = match.group(1).strip()
                if action_str == "繼續":
                    branches["success"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["success"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    label = action_str.replace("跳到#", "").strip()
                    branches["success"] = {"action": "jump", "target": label}
                continue
            
            # 失敗分支：失敗→繼續 / 失敗→停止 / 失敗→跳到#標籤
            failure_pattern = r'失敗→(.+)'
            match = re.match(failure_pattern, line)
            if match:
                action_str = match.group(1).strip()
                if action_str == "繼續":
                    branches["failure"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["failure"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    label = action_str.replace("跳到#", "").strip()
                    branches["failure"] = {"action": "jump", "target": label}
                continue
        
        return branches
    
    def _parse_simple_condition_branches(self, next_lines: list) -> dict:
        """
        解析簡化條件判斷的分支（>> 成功，>>> 失敗）
        :param next_lines: 後續行列表
        :return: 分支字典 {'success': {...}, 'failure': {...}}
        """
        branches = {}
        
        for line in next_lines[:5]:  # 只看接下來5行
            line_stripped = line.strip()
            
            # 空行跳過
            if not line_stripped:
                continue
            
            # 遇到新指令就停止
            if line_stripped.startswith(">") and not line_stripped.startswith(">>"):
                break
            if line_stripped.startswith("#") and not line_stripped.startswith("##"):
                break
            
            # 失敗分支（三個>）
            if line_stripped.startswith(">>>"):
                action_str = line_stripped[3:].strip()
                
                if not action_str or action_str == "繼續":
                    branches["failure"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["failure"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    # 跳轉到標籤（完整格式：'跳到#標籤'）
                    label = action_str[3:].strip()
                    branches["failure"] = {"action": "jump", "target": label}
                elif action_str.startswith("#"):
                    # 簡化格式：直接寫 '>>>#標籤' 或 '>>>#標籤*N' 表示跳轉到該標籤並執行N次
                    label_with_count = action_str[1:].strip()
                    if "*" in label_with_count:
                        label, count_str = label_with_count.split("*", 1)
                        try:
                            count = int(count_str.strip())
                            branches["failure"] = {"action": "jump", "target": label.strip(), "repeat_count": count}
                        except ValueError:
                            branches["failure"] = {"action": "jump", "target": label_with_count}
                    else:
                        branches["failure"] = {"action": "jump", "target": label_with_count}
                else:
                    # 其他文字視為註解，保存下來（保留用戶的註解內容）
                    branches["failure"] = {"action": "continue", "comment": action_str}
                continue
            
            # 成功分支（兩個>）
            elif line_stripped.startswith(">>"):
                action_str = line_stripped[2:].strip()
                
                if not action_str or action_str == "繼續":
                    branches["success"] = {"action": "continue"}
                elif action_str == "停止":
                    branches["success"] = {"action": "stop"}
                elif action_str.startswith("跳到#"):
                    # 跳轉到標籤（完整格式：'跳到#標籤'）
                    label = action_str[3:].strip()
                    branches["success"] = {"action": "jump", "target": label}
                elif action_str.startswith("#"):
                    # 簡化格式：直接寫 '>>#標籤' 或 '>>#標籤*N' 表示跳轉到該標籤並執行N次
                    label_with_count = action_str[1:].strip()
                    if "*" in label_with_count:
                        label, count_str = label_with_count.split("*", 1)
                        try:
                            count = int(count_str.strip())
                            branches["success"] = {"action": "jump", "target": label.strip(), "repeat_count": count}
                        except ValueError:
                            branches["success"] = {"action": "jump", "target": label_with_count}
                    else:
                        branches["success"] = {"action": "jump", "target": label_with_count}
                else:
                    # 其他文字視為註解，保存下來（保留用戶的註解內容）
                    branches["success"] = {"action": "continue", "comment": action_str}
                continue
        
        # 不設定預設值，讓呼叫者決定是否需要預設行為
        return branches
    
    def _parse_branch_action(self, action: str) -> dict:
        """
        解析分支動作
        :param action: 動作字串
        :return: 動作字典
        """
        # 跳到標籤
        jump_pattern = r'跳到\s*#(.+)'
        match = re.match(jump_pattern, action)
        if match:
            return {"action": "jump", "label": match.group(1).strip()}
        
        # 重試
        retry_pattern = r'重試(\d+)次(?:,?\s*間隔([\d.]+)[sS])?'
        match = re.match(retry_pattern, action)
        if match:
            return {
                "action": "retry",
                "count": int(match.group(1)),
                "interval": float(match.group(2)) if match.group(2) else 1.0
            }
        
        # 繼續
        if action == "繼續":
            return {"action": "continue"}
    
    def _parse_combat_command_to_json(self, command_line: str, start_time: float) -> dict:
        """
        解析戰鬥指令並轉換為JSON格式
        :param command_line: 戰鬥指令行
        :param start_time: 起始時間戳
        :return: JSON事件字典
        """
        from combat_command_parser import CombatCommandParser
        
        parser = CombatCommandParser()
        result = parser.parse_combat_command(command_line)
        
        if result:
            # 添加時間戳
            result["time"] = start_time
            return result
        
        return None
    
    def _format_combat_event(self, event: dict) -> str:
        """
        將戰鬥事件轉換為文字指令格式
        :param event: 戰鬥事件字典
        :return: 文字指令字串
        """
        event_type = event.get("type")
        
        # 啟動自動戰鬥
        if event_type == "start_combat":
            enemies = event.get("enemies", [])
            attack_key = event.get("attack_key", "1")
            skills = event.get("skills", [])
            
            parts = ["啟動自動戰鬥"]
            if enemies:
                parts.append(f"敵人[{', '.join(enemies)}]")
            parts.append(f"攻擊鍵{attack_key}")
            if skills:
                parts.append(f"技能[{','.join(skills)}]")
            
            return ", ".join(parts)
        
        # 尋找並攻擊
        elif event_type == "find_and_attack":
            template = event.get("template", "")
            move_duration = event.get("move_duration", 0.3)
            
            return f"尋找並攻擊[{template}], 移動時間{move_duration}s"
        
        # 循環攻擊
        elif event_type == "loop_attack":
            templates = event.get("templates", [])
            attack_key = event.get("attack_key", "1")
            interval = event.get("interval", 1.0)
            
            return f"循環攻擊[{', '.join(templates)}], 攻擊鍵{attack_key}, 間隔{interval}s"
        
        # 智能戰鬥
        elif event_type == "smart_combat":
            priority = event.get("priority", [])
            attack_key = event.get("attack_key", "1")
            skills = event.get("skills", [])
            
            parts = ["智能戰鬥"]
            if priority:
                parts.append(f"優先順序[{' > '.join(priority)}]")
            parts.append(f"攻擊鍵{attack_key}")
            if skills:
                parts.append(f"技能[{','.join(skills)}]")
            
            return ", ".join(parts)
        
        # 設定戰鬥區域
        elif event_type == "set_combat_region":
            region = event.get("region", {})
            x = region.get("x", 0)
            y = region.get("y", 0)
            w = region.get("width", 0)
            h = region.get("height", 0)
            
            return f"設定戰鬥區域[X={x}, Y={y}, W={w}, H={h}]"
        
        # 暫停/恢復/停止
        elif event_type == "pause_combat":
            return "暫停戰鬥"
        elif event_type == "resume_combat":
            return "恢復戰鬥"
        elif event_type == "stop_combat":
            return "停止戰鬥"
        
        return ""
    
    def _format_branch_action(self, branch: dict) -> str:
        """
        將分支動作字典轉換為文字格式（簡化版，不帶→符號）
        :param branch: 分支字典 {"action": "continue"/"stop"/"jump", "target": "label"}
        :return: 文字格式的分支動作
        """
        action = branch.get("action", "continue")
        
        if action == "continue":
            # 如果有註解內容，輸出註解；否則不輸出
            comment = branch.get("comment", "")
            return comment if comment else ""
        elif action == "stop":
            return "停止"
        elif action == "jump":
            target = branch.get("target", "")
            repeat_count = branch.get("repeat_count", 1)
            # 使用簡化格式：直接輸出 '#標籤*N' 或 '#標籤'
            if repeat_count > 1:
                return f"#{target}*{repeat_count}"
            return f"#{target}"
        
        return ""  # 預設值
    
    def _save_script(self):
        """儲存文字指令回JSON格式（雙向驗證增強版）"""
        if not self.script_path:
            self._show_message("警告", "沒有指定要儲存的腳本檔案", "warning")
            return
        
        try:
            # 獲取編輯器內容
            text_content = self.text_editor.get("1.0", "end-1c")
            
            # 檢查是否只有註解和空行（避免保存空腳本）
            has_commands = False
            for line in text_content.split("\n"):
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith("#"):
                    has_commands = True
                    break
            
            if not has_commands:
                self._show_message(
                    "警告", 
                    "腳本沒有任何指令，無法儲存！\n\n請先添加指令（以 > 或 # 開頭的行）",
                    "warning"
                )
                self._update_status("警告: 無法儲存：腳本無指令", "warning")
                return
            
            # 轉換為JSON
            json_data = self._text_to_json(text_content)
            
            # 二次檢查：確保轉換後的events不為空
            if not json_data.get("events") or len(json_data.get("events", [])) == 0:
                self._show_message(
                    "錯誤", 
                    "指令解析失敗，無法產生有效的事件！\n\n可能原因：\n"
                    "• 指令格式不正確\n"
                    "• 缺少必要欄位（如時間T=）\n"
                    "• 座標或按鍵名稱解析失敗\n\n"
                    "請檢查編輯器中的指令格式。",
                    "error"
                )
                self._update_status("錯誤: 解析失敗：events為空", "error")
                return
            
            # ✅ 雙向驗證：將JSON轉回文字，確保可以正確還原
            try:
                verification_text = self._json_to_text(json_data)
                # 簡單檢查：確保轉換後有內容
                if not verification_text or len(verification_text.strip()) < 10:
                    raise ValueError("JSON轉文字驗證失敗：內容過短")
            except Exception as verify_error:
                self._show_message(
                    "錯誤",
                    f"雙向驗證失敗！\n\n儲存的JSON無法正確轉回文字格式。\n\n錯誤：{verify_error}\n\n請檢查指令格式。",
                    "error"
                )
                self._update_status("錯誤: 雙向驗證失敗", "error")
                return
            
            # 備份原檔案
            backup_path = self.script_path + ".backup"
            if os.path.exists(self.script_path):
                try:
                    with open(self.script_path, 'r', encoding='utf-8') as f:
                        with open(backup_path, 'w', encoding='utf-8') as bf:
                            bf.write(f.read())
                except:
                    pass  # 備份失敗不影響儲存流程
            
            # 使用臨時檔案儲存（防止寫入失敗損毀原檔案）
            temp_path = self.script_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            
            # 驗證臨時檔案內容
            with open(temp_path, 'r', encoding='utf-8') as f:
                verify_data = json.load(f)
                if not verify_data.get("events") or len(verify_data.get("events", [])) == 0:
                    raise ValueError("儲存後驗證失敗：events為空")
                
                # ✅ 再次雙向驗證：確保儲存的檔案可以正確讀取
                verify_text_2 = self._json_to_text(verify_data)
                if not verify_text_2 or len(verify_text_2.strip()) < 10:
                    raise ValueError("儲存檔案二次驗證失敗")
            
            # 驗證成功後才替換原檔案
            if os.path.exists(self.script_path):
                os.remove(self.script_path)
            os.rename(temp_path, self.script_path)
            
            event_count = len(json_data.get("events", []))
            self._update_status(
                f"已儲存: {os.path.basename(self.script_path)} ({event_count}筆事件)",
                "success"
            )
            
        except ValueError as ve:
            # 解析/驗證錯誤
            self._show_message("錯誤", f"儲存驗證失敗:\n{ve}", "error")
            self._update_status(f"錯誤: 驗證失敗: {ve}", "error")
            # 清理臨時檔案
            temp_path = self.script_path + ".tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
        except Exception as e:
            # 其他錯誤
            self._show_message("錯誤", f"儲存腳本失敗:\n{e}", "error")
            self._update_status(f"錯誤: 儲存失敗: {e}", "error")
            # 清理臨時檔案
            temp_path = self.script_path + ".tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
    
    # ==================== 內嵌自訂模組功能 ====================
    
    def _load_modules_inline(self):
        """載入模組列表"""
        self.module_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.modules_dir):
            os.makedirs(self.modules_dir, exist_ok=True)
            return
        
        modules = [f for f in os.listdir(self.modules_dir) if f.endswith('.txt')]
        for module in sorted(modules):
            display_name = os.path.splitext(module)[0]
            self.module_listbox.insert(tk.END, display_name)
    
    def _on_module_selected_inline(self, event):
        """模組選取事件"""
        selection = self.module_listbox.curselection()
        if not selection:
            return
        
        module_name = self.module_listbox.get(selection[0])
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.module_preview.config(state="normal")
            self.module_preview.delete("1.0", tk.END)
            self.module_preview.insert("1.0", content)
            self.module_preview.config(state="disabled")
        except Exception as e:
            self.module_preview.config(state="normal")
            self.module_preview.delete("1.0", tk.END)
            self.module_preview.insert("1.0", f"讀取失敗: {e}")
            self.module_preview.config(state="disabled")
    
    def _save_new_module_inline(self):
        """儲存新模組（內嵌版）"""
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            self._show_message("提示", "請先在編輯器中選取（反白）要儲存的指令", "warning")
            return
        
        if not selected_text.strip():
            self._show_message("提示", "選取的內容為空", "warning")
            return
        
        # 詢問模組名稱
        module_name = simpledialog.askstring(
            "模組名稱",
            "請輸入自訂模組的名稱：",
            parent=self
        )
        
        if not module_name:
            return
        
        # 儲存模組
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(selected_text)
            
            # 重新載入列表
            self._load_modules_inline()
            
            # 選中新建的模組
            for i in range(self.module_listbox.size()):
                if self.module_listbox.get(i) == module_name:
                    self.module_listbox.selection_clear(0, tk.END)
                    self.module_listbox.selection_set(i)
                    self.module_listbox.see(i)
                    self._on_module_selected_inline(None)
                    break
            
            self.status_label.config(
                text=f"模組已儲存：{module_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"儲存模組失敗：{e}", "error")
    
    def _insert_module_inline(self):
        """插入選取的模組（內嵌版）"""
        selection = self.module_listbox.curselection()
        if not selection:
            self._show_message("提示", "請先選擇要插入的模組", "warning")
            return
        
        module_name = self.module_listbox.get(selection[0])
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, content + "\n")
            
            self.status_label.config(
                text=f"已插入模組：{module_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"插入模組失敗：{e}", "error")
    
    def _delete_module_inline(self):
        """刪除選取的模組（內嵌版）"""
        selection = self.module_listbox.curselection()
        if not selection:
            self._show_message("提示", "請先選擇要刪除的模組", "warning")
            return
        
        module_name = self.module_listbox.get(selection[0])
        
        # 確認刪除
        if not self._show_confirm("確認刪除", f"確定要刪除模組「{module_name}」嗎？"):
            return
        
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            os.remove(module_path)
            
            # 清空預覽
            self.module_preview.config(state="normal")
            self.module_preview.delete("1.0", tk.END)
            self.module_preview.config(state="disabled")
            
            # 重新載入列表
            self._load_modules_inline()
            
            self.status_label.config(
                text=f"已刪除模組：{module_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"刪除模組失敗：{e}", "error")
    
    # ==================== 右鍵選單功能 ====================
    
    
    def _on_text_modified(self, event=None):
        """文字內容修改時觸發語法高亮"""
        # 重置 modified 標誌
        self.text_editor.edit_modified(False)
        # 延遲執行語法高亮以提高效能
        self.after(50, self._apply_syntax_highlighting)
    
    def _apply_syntax_highlighting(self):
        """套用語法高亮 (Dracula 配色)"""
        try:
            # 移除所有現有標籤
            for tag in ["syntax_symbol", "syntax_time", "syntax_label", "syntax_keyboard",
                       "syntax_mouse", "syntax_image", "syntax_condition", "syntax_ocr",
                       "syntax_delay", "syntax_flow", "syntax_picname"]:
                self.text_editor.tag_remove(tag, "1.0", tk.END)
            
            # 獲取所有文字內容
            content = self.text_editor.get("1.0", tk.END)
            
            # 定義需要高亮的模式 (Dracula 配色方案)
            # 流程控制 (紅色) - 優先順序最高
            patterns_flow = [
                (r'跳到#\S+', 'syntax_flow'),
                (r'停止', 'syntax_flow'),
            ]
            
            # 條件判斷 (橘色)
            patterns_condition = [
                (r'if>', 'syntax_condition'),
                (r'如果存在>', 'syntax_condition'),
            ]
            
            # 延遲控制 (橘色)
            patterns_delay = [
                (r'延遲\d+ms', 'syntax_delay'),
                (r'延遲時間', 'syntax_delay'),
            ]
            
            # OCR 文字辨識 (青色)
            patterns_ocr = [
                (r'if文字>', 'syntax_ocr'),
                (r'等待文字>', 'syntax_ocr'),
                (r'點擊文字>', 'syntax_ocr'),
            ]
            
            # 鍵盤操作 (淡紫色)
            patterns_keyboard = [
                (r'按下\w+', 'syntax_keyboard'),
                (r'放開\w+', 'syntax_keyboard'),
                (r'按(?![下放])\S+', 'syntax_keyboard'),  # 按但不是按下/按放
            ]
            
            # 滑鼠座標操作 (藍色)
            patterns_mouse = [
                (r'移動至\(', 'syntax_mouse'),
                (r'左鍵點擊\(', 'syntax_mouse'),
                (r'右鍵點擊\(', 'syntax_mouse'),
                (r'中鍵點擊\(', 'syntax_mouse'),
                (r'雙擊\(', 'syntax_mouse'),
                (r'按下left鍵\(', 'syntax_mouse'),
                (r'放開left鍵\(', 'syntax_mouse'),
                (r'滾輪\(', 'syntax_mouse'),
            ]
            
            # 圖片辨識 (綠色)
            patterns_image = [
                (r'辨識>', 'syntax_image'),
                (r'移動至>', 'syntax_image'),
                (r'左鍵點擊>', 'syntax_image'),
                (r'右鍵點擊>', 'syntax_image'),
                (r'辨識任一>', 'syntax_image'),
            ]
            
            # 圖片名稱 (黃色) - pic + 數字
            patterns_picname = [
                (r'pic\d+', 'syntax_picname'),
            ]
            
            # 時間參數 (粉紅色)
            patterns_time = [
                (r'T=\d+[smh]\d*', 'syntax_time'),
            ]
            
            # 標籤 (青色)
            patterns_label = [
                (r'^#\S+', 'syntax_label'),           # 行首的 # 標籤
                (r'>>#\S+', 'syntax_label'),          # >> 後的 # 標籤
                (r'>>>#\S+', 'syntax_label'),         # >>> 後的 # 標籤
            ]
            
            # 符號 (淡紫色) - 最後處理
            patterns_symbol = [
                (r'^>>>', 'syntax_symbol'),           # 行首的 >>>
                (r'^>>', 'syntax_symbol'),            # 行首的 >>
                (r'^>', 'syntax_symbol'),             # 行首的 >
                (r',', 'syntax_symbol'),              # 逗號
            ]
            
            # 按順序合併所有模式 (優先順序從高到低)
            all_patterns = (patterns_flow + patterns_condition + patterns_delay + 
                          patterns_ocr + patterns_keyboard + patterns_mouse + 
                          patterns_image + patterns_picname + patterns_time + 
                          patterns_label + patterns_symbol)
            
            # 逐行處理
            lines = content.split('\n')
            for line_num, line in enumerate(lines, start=1):
                for pattern, tag in all_patterns:
                    for match in re.finditer(pattern, line):
                        start_idx = f"{line_num}.{match.start()}"
                        end_idx = f"{line_num}.{match.end()}"
                        self.text_editor.tag_add(tag, start_idx, end_idx)
        
        except Exception as e:
            # 靜默處理錯誤，避免影響編輯器使用
            pass
    
    def _show_context_menu(self, event):
        """顯示右鍵選單"""
        # 檢查是否有選取文字
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            has_selection = bool(selected_text.strip())
        except:
            has_selection = False
        
        # 創建右鍵選單
        context_menu = tk.Menu(self, tearoff=0)
        
        if has_selection:
            context_menu.add_command(
                label="儲存為自訂模組",
                command=self._save_selection_as_module
            )
            context_menu.add_separator()
        
        # 載入已存在的模組子選單
        modules_menu = tk.Menu(context_menu, tearoff=0)
        
        # 取得所有模組
        module_files = []
        if os.path.exists(self.modules_dir):
            module_files = [f for f in os.listdir(self.modules_dir) if f.endswith('.txt')]
        
        if module_files:
            for module_file in sorted(module_files):
                module_name = os.path.splitext(module_file)[0]
                modules_menu.add_command(
                    label=module_name,
                    command=lambda name=module_name: self._insert_module_from_menu(name)
                )
            context_menu.add_cascade(label="插入自訂模組", menu=modules_menu)
        else:
            context_menu.add_command(
                label="插入自訂模組 (無可用模組)",
                state="disabled"
            )
        
        # 顯示選單
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def _save_selection_as_module(self):
        """將選取的文字儲存為自訂模組"""
        try:
            selected_text = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            self._show_message("提示", "請先選取（反白）要儲存的指令", "warning")
            return
        
        if not selected_text.strip():
            self._show_message("提示", "選取的內容為空", "warning")
            return
        
        # 詢問模組名稱
        module_name = simpledialog.askstring(
            "自訂模組名稱",
            "請輸入模組名稱：",
            parent=self
        )
        
        if not module_name:
            return
        
        # 儲存模組
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(selected_text)
            
            # 重新載入右側模組列表
            self._load_modules_inline()
            
            # 選中新建的模組
            for i in range(self.module_listbox.size()):
                if self.module_listbox.get(i) == module_name:
                    self.module_listbox.selection_clear(0, tk.END)
                    self.module_listbox.selection_set(i)
                    self.module_listbox.see(i)
                    self._on_module_selected_inline(None)
                    break
            
            self.status_label.config(
                text=f"模組已儲存：{module_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
        except Exception as e:
            self._show_message("錯誤", f"儲存失敗：{e}", "error")
    
    def _insert_module_from_menu(self, module_name):
        """從右鍵選單插入模組"""
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, content + "\n")
        except Exception as e:
            self._show_message("錯誤", f"讀取模組失敗：{e}", "error")
    
    # ==================== 執行功能 ====================
    
    def _execute_script(self):
        """執行當前文字指令（先儲存再執行）"""
        if not self.parent:
            self.status_label.config(text="錯誤: 無法執行：找不到主程式")
            return
        
        # 1. 先儲存腳本
        if not self.script_path:
            self._show_message("提示", "請先建立或選擇一個腳本", "warning")
            return
        
        # 儲存當前內容
        self._save_script()
        
        # 2. 確認儲存成功後再執行
        if not os.path.exists(self.script_path):
            self.status_label.config(text="錯誤: 執行失敗：腳本未儲存")
            return
        
        try:
            # 3. 讀取儲存後的腳本
            with open(self.script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 4. 載入到主程式
            if hasattr(self.parent, 'events'):
                self.parent.events = data.get("events", [])
            else:
                self.status_label.config(text="錯誤: 主程式缺少events屬性")
                return
            
            if hasattr(self.parent, 'metadata'):
                self.parent.metadata = data.get("settings", {})
            
            # 載入到 core_recorder（關鍵：確保錄製器有事件）
            if hasattr(self.parent, 'core_recorder'):
                self.parent.core_recorder.events = data.get("events", [])
                # 同時確保 core_recorder 的 images_dir 已設定
                if hasattr(self.parent.core_recorder, 'set_images_dir'):
                    images_dir = os.path.join(os.path.dirname(self.script_path), "images")
                    if os.path.exists(images_dir):
                        self.parent.core_recorder.set_images_dir(images_dir)
            
            # 5. 更新主程式設定
            settings = data.get("settings", {})
            if hasattr(self.parent, 'speed_var'):
                self.parent.speed_var.set(settings.get("speed", "100"))
            if hasattr(self.parent, 'repeat_var'):
                self.parent.repeat_var.set(settings.get("repeat", "1"))
            if hasattr(self.parent, 'repeat_time_var'):
                self.parent.repeat_time_var.set(settings.get("repeat_time", "00:00:00"))
            if hasattr(self.parent, 'repeat_interval_var'):
                self.parent.repeat_interval_var.set(settings.get("repeat_interval", "00:00:00"))
            
            # 同步更新主程式的腳本選擇（避免選擇不一致）
            if hasattr(self.parent, 'script_var'):
                script_name = os.path.splitext(os.path.basename(self.script_path))[0]
                self.parent.script_var.set(script_name)
            
            # 6. 記錄視窗資訊（避免回放時彈窗）
            if hasattr(self.parent, 'target_hwnd') and self.parent.target_hwnd:
                from utils import get_window_info
                current_info = get_window_info(self.parent.target_hwnd)
                if current_info:
                    self.parent.recorded_window_info = current_info
            
            # 7. 確認狀態並執行腳本
            event_count = len(data.get("events", []))
            if event_count == 0:
                self.status_label.config(text="錯誤: 腳本無事件")
                if hasattr(self.parent, 'log'):
                    self.parent.log("錯誤: 腳本無事件，無法執行")
                return
            
            # 確保不在錄製或播放狀態
            if hasattr(self.parent, 'recording') and self.parent.recording:
                self.status_label.config(text="錯誤: 請先停止錄製")
                return
            if hasattr(self.parent, 'playing') and self.parent.playing:
                self.status_label.config(text="錯誤: 已在播放中")
                return
            
            self.status_label.config(text=f"執行中... ({event_count}筆事件)")
            
            # 記錄日誌
            if hasattr(self.parent, 'log'):
                script_name = os.path.splitext(os.path.basename(self.script_path))[0]
                self.parent.log(f"從編輯器執行腳本：{script_name}（{event_count}筆事件）")
            
            # 調用 play_record（直接播放）
            if hasattr(self.parent, 'play_record'):
                self.parent.play_record()
            else:
                self.status_label.config(text="錯誤: 主程式缺少play_record方法")
                
        except Exception as e:
            self.status_label.config(text=f"錯誤: 執行失敗：{e}")
            if hasattr(self.parent, 'log'):
                self.parent.log(f"錯誤: 編輯器執行失敗：{e}")
    
    # ==================== 圖片辨識功能 ====================
    
    def _show_image_help(self):
        """顯示圖片使用說明"""
        help_text = """
📷 圖片辨識使用說明

【方法1: 使用截圖功能（推薦新手）】
1. 點擊「圖片辨識」按鈕
2. 框選螢幕上要辨識的目標區域
3. 系統自動命名為 pic01, pic02... 並插入指令

【方法2: 自行放入圖片（進階用戶）】
1. 準備圖片檔案（建議使用去背景或純淨的圖片）
   - 支援格式: .png
   - 建議大小: 50x50 ~ 200x200 px
   - 圖片越純淨,辨識越準確

2. 圖片命名規則:
   - 必須以 "pic" 開頭
   - 後接數字或名稱
   - 例如: pic01.png, pic_button.png, pic_monster.png

3. 放入圖片資料夾:
   📁 {images_path}

4. 在編輯器中輸入指令:
   >辨識>pic01, T=0s000
   >移動至>pic_button, T=0s000
   >左鍵點擊>pic_monster, T=0s000

【注意事項】
✓ 圖片名稱必須以 "pic" 開頭才能被辨識
✓ 使用去背景或高對比圖片可提升辨識準確度
✓ 避免過小的圖片（建議 > 30x30 px）
✓ 系統會自動搜尋 images 資料夾中的圖片

【範例】
假設你放入了 pic_login.png
在編輯器中輸入:
  >辨識>pic_login, T=0s000
  >>=點擊
  >>>=找

系統會自動找到並使用 pic_login.png 進行辨識
"""
        
        help_text = help_text.replace("{images_path}", self.images_dir)
        
        # 創建說明視窗
        help_win = tk.Toplevel(self)
        help_win.title("圖片辨識使用說明")
        help_win.geometry("600x550")
        help_win.resizable(False, False)
        
        # 文字區域
        text_area = tk.Text(
            help_win,
            wrap="word",
            font=font_tuple(9),
            bg="#f5f5f5",
            fg="#333333",
            padx=15,
            pady=15,
            relief="flat"
        )
        text_area.pack(fill="both", expand=True, padx=10, pady=10)
        text_area.insert("1.0", help_text)
        text_area.config(state="disabled")
        
        # 關閉按鈕
        close_btn = tk.Button(
            help_win,
            text="知道了",
            font=font_tuple(10, "bold"),
            bg="#4CAF50",
            fg="white",
            padx=30,
            pady=8,
            cursor="hand2",
            command=help_win.destroy
        )
        close_btn.pack(pady=10)
        
        # 居中顯示
        help_win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - help_win.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - help_win.winfo_height()) // 2
        help_win.geometry(f"+{x}+{y}")
    
    def _capture_and_recognize(self):
        """截圖並儲存，插入辨識指令"""
        # 儲存視窗狀態和位置
        self.editor_geometry = self.geometry()
        if self.parent:
            self.parent_geometry = self.parent.geometry()
        
        # 策略1: 將視窗移至最底層 (lower)
        self.lower()
        if self.parent:
            self.parent.lower()
        
        # 強制更新
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        # 策略2: 隱藏視窗 (withdraw 取代 iconify)
        # 🔥 使用 withdraw 以避免 transient 視窗無法 iconify 的錯誤
        self.withdraw()
        if self.parent:
            self.parent.withdraw()
        
        # 再次強制更新
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        # 給系統時間完成隱藏(300ms)
        self.after(300, self._do_capture)
    
    def _do_capture(self):
        """執行截圖"""
        try:
            # 創建截圖選取視窗
            capture_win = ScreenCaptureSelector(self, self._on_capture_complete)
            capture_win.wait_window()
        except Exception as e:
            self._show_message("錯誤", f"截圖失敗：{e}", "error")
            self._restore_windows()
    
    def _restore_windows(self):
        """恢復視窗顯示"""
        # 從隱藏狀態恢復 (deiconify 可以同時處理 withdraw 和 iconify)
        self.deiconify()
        self.lift()  # 提升到最上層
        if self.parent:
            self.parent.deiconify()
            self.parent.lift()
        
        # 恢復位置
        if hasattr(self, 'editor_geometry'):
            self.geometry(self.editor_geometry)
        
        if self.parent and hasattr(self, 'parent_geometry'):
            self.parent.geometry(self.parent_geometry)
        
        # 強制更新
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        # 將視窗提升到最上層
        self.lift()
        if self.parent:
            self.parent.lift()
        
        # 設定焦點
        self.focus_force()
    
    def _on_capture_complete(self, image_region):
        """截圖完成回調"""
        # 恢復視窗
        self._restore_windows()
        
        if image_region is None:
            return
        
        try:
            x1, y1, x2, y2 = image_region
            
            # 截取螢幕區域
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # 顯示合併的命名+預覽對話框
            self._show_name_and_preview_dialog(screenshot)
            
        except Exception as e:
            self._show_message("錯誤", f"儲存圖片失敗：{e}", "error")
    
    def _show_name_and_preview_dialog(self, screenshot):
        """顯示圖片預覽和命名的合併對話框"""
        dialog = tk.Toplevel(self)
        dialog.title("圖片辨識 - 命名與預覽")
        dialog.resizable(False, False)
        dialog.attributes('-topmost', True)
        dialog.transient(self)
        dialog.grab_set()
        
        result = {"confirmed": False, "name": None}
        
        # 主框架
        main_frame = tk.Frame(dialog, bg="white", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # ========== 命名區域 ==========
        name_frame = tk.Frame(main_frame, bg="white")
        name_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            name_frame,
            text="請輸入圖片名稱",
            font=font_tuple(11, "bold"),
            bg="white",
            fg="#1976d2"
        ).pack(anchor="w", pady=(0, 10))
        
        # 輸入框
        input_frame = tk.Frame(name_frame, bg="white")
        input_frame.pack(anchor="w")
        
        tk.Label(input_frame, text="pic", font=font_tuple(10, "bold"), bg="white").pack(side="left")
        
        name_entry = tk.Entry(input_frame, width=25, font=font_tuple(10))
        name_entry.pack(side="left", padx=5)
        name_entry.insert(0, f"{self._pic_counter:02d}")
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
        
        # ========== 分隔線 ==========
        tk.Frame(main_frame, height=1, bg="#e0e0e0").pack(fill="x", pady=10)
        
        # ========== 預覽區域 ==========
        preview_frame = tk.Frame(main_frame, bg="white")
        preview_frame.pack(fill="both", expand=True)
        
        tk.Label(
            preview_frame,
            text="圖片預覽",
            font=font_tuple(11, "bold"),
            bg="white",
            fg="#1976d2"
        ).pack(anchor="w", pady=(0, 10))
        
        # 圖片預覽（調整大小以適應對話框）
        max_width, max_height = 500, 350
        img_width, img_height = screenshot.size
        
        scale = min(max_width / img_width, max_height / img_height, 1.0)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        resized_img = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized_img)
        
        img_label = tk.Label(preview_frame, image=photo, bg="white", relief="solid", borderwidth=1)
        img_label.image = photo  # 保持引用
        img_label.pack(pady=(0, 15))
        
        # ========== 按鈕區域 ==========
        btn_frame = tk.Frame(main_frame, bg="white")
        btn_frame.pack(fill="x")
        
        def on_confirm():
            custom_name = name_entry.get().strip()
            if not custom_name:
                custom_name = f"{self._pic_counter:02d}"
            result["name"] = f"pic{custom_name}"
            result["confirmed"] = True
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        tk.Button(
            btn_frame,
            text="✓ 確認儲存",
            command=on_confirm,
            bg="#4caf50",
            fg="white",
            font=font_tuple(10, "bold"),
            relief="flat",
            padx=30,
            pady=8,
            cursor="hand2"
        ).pack(side="left", padx=(0, 10))
        
        tk.Button(
            btn_frame,
            text="✗ 取消",
            command=on_cancel,
            bg="#757575",
            fg="white",
            font=font_tuple(10),
            relief="flat",
            padx=30,
            pady=8,
            cursor="hand2"
        ).pack(side="left")
        
        # 快捷鍵
        name_entry.bind('<Return>', lambda e: on_confirm())
        dialog.bind('<Escape>', lambda e: on_cancel())
        
        # 置中顯示
        dialog.update_idletasks()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() - dialog_width) // 2
        y = (dialog.winfo_screenheight() - dialog_height) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 等待對話框關閉
        dialog.wait_window()
        
        # 如果確認，儲存圖片並插入指令
        if result["confirmed"] and result["name"]:
            self._save_and_insert_commands(screenshot, result["name"])
    
    def _save_and_insert_commands(self, screenshot, display_name):
        """儲存圖片並自動插入指令"""
        try:
            # 檔案名稱使用完整的 display_name
            image_filename = f"{display_name}.png"
            image_path = os.path.join(self.images_dir, image_filename)
            
            # 儲存圖片
            screenshot.save(image_path)
            
            # 更新計數器
            self._pic_counter += 1
            
            # 自動插入三條指令（辨識、移動、點擊）
            current_time = self._get_next_available_time()
            
            # 計算三條指令的時間
            time_parts = re.match(r'(\d+)s(\d+)', current_time)
            if time_parts:
                base_seconds = int(time_parts.group(1))
                base_millis = int(time_parts.group(2))
                base_total_ms = base_seconds * 1000 + base_millis
                
                # 第一條：辨識（T=current_time）
                time1 = current_time
                
                # 第二條：移動至（+900ms）
                time2_ms = base_total_ms + 900
                time2 = f"{time2_ms // 1000}s{time2_ms % 1000:03d}"
                
                # 第三條：左鍵點擊（+1200ms）
                time3_ms = base_total_ms + 1200
                time3 = f"{time3_ms // 1000}s{time3_ms % 1000:03d}"
            else:
                time1 = "0s100"
                time2 = "1s000"
                time3 = "1s200"
            
            # 生成指令文字
            commands = (
                f">辨識>{display_name}, T={time1}\n"
                f">移動至>{display_name}, T={time2}\n"
                f">左鍵點擊>{display_name}, T={time3}\n"
            )
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, commands)
            
            # 更新狀態列
            self._update_status(f"圖片已儲存並插入指令：{display_name}", "success")
            
        except Exception as e:
            self._show_message("錯誤", f"儲存圖片失敗：{e}", "error")
    
    def _capture_region_for_recognition(self):
        """選擇範圍用於圖片辨識"""
        # 儲存視窗狀態
        self.editor_geometry = self.geometry()
        if self.parent:
            self.parent_geometry = self.parent.geometry()
        
        # 隱藏視窗
        self.lower()
        if self.parent:
            self.parent.lower()
        
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        self.withdraw()
        if self.parent:
            self.parent.withdraw()
        
        self.update_idletasks()
        if self.parent:
            self.parent.update_idletasks()
        
        # 延遲後選擇範圍
        self.after(300, self._do_region_selection)
    
    def _do_region_selection(self):
        """執行範圍選擇"""
        try:
            # 創建範圍選擇視窗
            region_selector = RegionSelector(self, self._on_region_selected)
            region_selector.wait_window()
        except Exception as e:
            self._show_message("錯誤", f"範圍選擇失敗：{e}", "error")
            self._restore_windows()
    
    def _on_region_selected(self, region):
        """範圍選擇完成回調"""
        # 恢復視窗
        self._restore_windows()
        
        if region is None:
            return
        
        try:
            x1, y1, x2, y2 = region
            
            # 在游標位置插入範圍辨識指令
            # 格式: >辨識>pic01, 範圍(x1,y1,x2,y2), T=0s000
            current_time = self._get_next_available_time()
            
            # 插入範圍辨識指令和範圍結束標記
            command = f">辨識>pic01, 範圍({x1},{y1},{x2},{y2}), T={current_time}\n>範圍結束\n"
            
            self.text_editor.insert(tk.INSERT, command)
            
            # 更新狀態列
            self._update_status(f"已插入範圍辨識指令：({x1},{y1},{x2},{y2})", "success")
            
        except Exception as e:
            self._show_message("錯誤", f"插入指令失敗：{e}", "error")
    
    def _get_next_available_time(self):
        """獲取下一個可用的時間戳記"""
        content = self.text_editor.get("1.0", "end-1c")
        lines = content.split('\n')
        
        max_time = 0
        for line in lines:
            match = re.search(r'T=(\d+)s(\d+)', line)
            if match:
                seconds = int(match.group(1))
                millis = int(match.group(2))
                total_ms = seconds * 1000 + millis
                max_time = max(max_time, total_ms)
        
        # 下一個時間點（+100ms）
        next_time_ms = max_time + 100
        seconds = next_time_ms // 1000
        millis = next_time_ms % 1000
        return f"{seconds}s{millis}"
    
    # ==================== 已棄用：舊的彈窗式自訂模組管理器 ====================
    # 保留作為備份，但不再使用（已整合到右側面板）
    
    def _open_custom_module(self):
        """開啟自訂模組管理視窗（已棄用）"""
        # 此功能已整合到右側面板，不再需要彈窗
        pass
    
    # ==================== 圖片辨識指令解析 ====================
    
    def _parse_image_command(self, line: str) -> Dict[str, Any]:
        """解析圖片辨識相關指令
        
        支援格式：
        >辨識>pic01, T=時間（新格式）
        >辨識>pic01, 邊框, T=時間（顯示邊框）
        >辨識>pic01, 範圍(x1,y1,x2,y2), T=時間（範圍辨識）
        >辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=時間（邊框+範圍）
        >辨識>pic01>img_001.png, T=時間（舊格式，相容性）
        >移動至>pic01, T=時間
        >左鍵點擊>pic01, T=時間
        >右鍵點擊>pic02, T=時間
        """
        # 辨識指令（新格式，支援邊框和範圍）
        # 格式: >辨識>pic01, 邊框, 範圍(x1,y1,x2,y2), T=0s000
        match = re.match(r'>辨識>([^>,]+)(?:,\s*([^,T]+))*,\s*T=(\d+)s(\d+)', line)
        if match:
            display_name = match.group(1).strip()
            options_str = match.group(2) if match.group(2) else ""
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            # 解析選項
            show_border = False
            region = None
            
            if options_str:
                # 檢查是否有"邊框"
                if '邊框' in options_str:
                    show_border = True
                
                # 檢查是否有"範圍"
                region_match = re.search(r'範圍\((\d+),(\d+),(\d+),(\d+)\)', options_str)
                if region_match:
                    region = (
                        int(region_match.group(1)),
                        int(region_match.group(2)),
                        int(region_match.group(3)),
                        int(region_match.group(4))
                    )
            
            # 自動查找pic對應的圖片檔案
            image_file = self._find_pic_image_file(display_name)
            
            return {
                "type": "image_recognize",
                "display_name": display_name,
                "image_file": image_file,
                "show_border": show_border,
                "region": region,
                "time": seconds * 1000 + millis
            }
        
        # 辨識指令（舊格式，相容性）
        match = re.match(r'>辨識>([^>]+)>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            display_name = match.group(1).strip()
            image_file = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            return {
                "type": "image_recognize",
                "display_name": display_name,
                "image_file": image_file,
                "time": seconds * 1000 + millis
            }
        
        # 移動至圖片
        match = re.match(r'>移動至>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            target = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            
            return {
                "type": "move_to_image",
                "target": target,
                "time": seconds * 1000 + millis
            }
        
        # 點擊圖片
        match = re.match(r'>(左鍵|右鍵)點擊>([^,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            button = "left" if match.group(1) == "左鍵" else "right"
            target = match.group(2).strip()
            seconds = int(match.group(3))
            millis = int(match.group(4))
            
            return {
                "type": "click_image",
                "button": button,
                "target": target,
                "time": seconds * 1000 + millis
            }
        
        return None
    
    def _find_pic_image_file(self, pic_name: str) -> str:
        """根據pic名稱查找對應的圖片檔案
        
        Args:
            pic_name: pic名稱（例如：pic01）
        
        Returns:
            圖片檔名（例如：img_001.png），如果找不到則返回 pic_name.png
        """
        if not os.path.exists(self.images_dir):
            return f"{pic_name}.png"
        
        # 查找該pic名稱對應的圖片檔案
        try:
            for filename in os.listdir(self.images_dir):
                # pic01.png 或 pic01_xxx.png 等格式
                if filename.startswith(pic_name) and filename.endswith('.png'):
                    return filename
        except:
            pass
        
        # 找不到時返回預設檔名
        return f"{pic_name}.png"


class ScreenCaptureSelector(tk.Toplevel):
    """螢幕截圖選取工具"""
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.canvas_start_x = None
        self.canvas_start_y = None
        self.rect_id = None
        self.result = None
        self.ready = False  # 是否準備好截圖
        
        # 全螢幕置頂
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        self.text_id = self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            50,
            text="正在準備截圖...",
            font=font_tuple(18, "bold"),
            fill="yellow"
        )
        
        # 綁定事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self._cancel())
        
        self.focus_force()
        
        # 延遲100ms後才允許截圖(視窗已在螢幕外，不需要太長延遲)
        self.after(100, self._enable_capture)
    
    def _enable_capture(self):
        """啟用截圖功能"""
        self.ready = True
        self.canvas.itemconfig(self.text_id, text="拖曳滑鼠選取要辨識的區域 (ESC取消)")
    
    def _on_press(self, event):
        """滑鼠按下"""
        if not self.ready:  # 尚未準備好，忽略點擊
            return
        # 使用螢幕絕對座標
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        # 轉換為canvas相對座標用於繪製
        canvas_x = event.x
        canvas_y = event.y
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            canvas_x, canvas_y, canvas_x, canvas_y,
            outline="red", width=3
        )
        self.canvas_start_x = canvas_x
        self.canvas_start_y = canvas_y
    
    def _on_drag(self, event):
        """滑鼠拖曳"""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.canvas_start_x, self.canvas_start_y,
                event.x, event.y
            )
    
    def _on_release(self, event):
        """滑鼠放開"""
        # 使用螢幕絕對座標
        end_x = event.x_root
        end_y = event.y_root
        
        # 計算實際螢幕座標
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)
        
        if x2 - x1 > 10 and y2 - y1 > 10:  # 最小10x10像素
            self.result = (x1, y1, x2, y2)
        
        self._finish()
    
    def _cancel(self):
        """取消截圖"""
        self.result = None
        self._finish()
    
    def _finish(self):
        """完成截圖"""
        self.destroy()
        if self.callback:
            self.callback(self.result)


class RegionSelector(tk.Toplevel):
    """區域選擇工具（用於範圍辨識）"""
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.canvas_start_x = None
        self.canvas_start_y = None
        self.rect_id = None
        self.result = None
        self.ready = False
        
        # 全螢幕置頂
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        self.text_id = self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            50,
            text="正在準備選擇範圍...",
            font=font_tuple(18, "bold"),
            fill="yellow"
        )
        
        # 綁定事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self._cancel())
        
        self.focus_force()
        
        # 延遲100ms後才允許選擇
        self.after(100, self._enable_selection)
    
    def _enable_selection(self):
        """啟用選擇功能"""
        self.ready = True
        self.canvas.itemconfig(self.text_id, text="拖曳滑鼠選取辨識範圍 (ESC取消)")
    
    def _on_press(self, event):
        """滑鼠按下"""
        if not self.ready:
            return
        
        self.start_x = event.x_root
        self.start_y = event.y_root
        
        canvas_x = event.x
        canvas_y = event.y
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            canvas_x, canvas_y, canvas_x, canvas_y,
            outline="blue", width=3
        )
        self.canvas_start_x = canvas_x
        self.canvas_start_y = canvas_y
    
    def _on_drag(self, event):
        """滑鼠拖曳"""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.canvas_start_x, self.canvas_start_y,
                event.x, event.y
            )
    
    def _on_release(self, event):
        """滑鼠放開"""
        if not self.ready or not self.rect_id:
            return
        
        end_x = event.x_root
        end_y = event.y_root
        
        # 確保 x1 < x2, y1 < y2
        x1, x2 = min(self.start_x, end_x), max(self.start_x, end_x)
        y1, y2 = min(self.start_y, end_y), max(self.start_y, end_y)
        
        # 檢查範圍是否足夠大
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            self.canvas.itemconfig(self.text_id, text="範圍太小，請重新選擇")
            self.canvas.delete(self.rect_id)
            self.rect_id = None
            return
        
        # 返回範圍座標 (x1, y1, x2, y2)
        self.result = (x1, y1, x2, y2)
        self._finish()
    
    def _cancel(self):
        """取消選擇"""
        self.result = None
        self._finish()
    
    def _finish(self):
        """完成選擇"""
        self.destroy()
        if self.callback:
            self.callback(self.result)


# ==================== 舊版彈出式模組管理器（已廢棄） ====================
# 現已改用內嵌式模組管理（在編輯器右側面板）
# 此類別保留供參考，但不再使用

# ==================== 舊版彈出式模組管理器（已移除） ====================
# 現已改用內嵌式模組管理（在編輯器右側面板）


# 測試用
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # 測試用腳本路徑
    test_script = r"c:\Users\Lucien\Documents\GitHub\scripts\2025_1117_1540_20.json"
    
    editor = TextCommandEditor(root, test_script)
    root.mainloop()

