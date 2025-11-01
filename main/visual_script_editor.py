"""
ChroLens 視覺化拖放式腳本編輯器
類似 Scratch 的拖放式程式設計介面
支援直接執行和編輯錄製的腳本
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import json
import os
import sys
import time
import threading
import mouse
import keyboard


def get_icon_path():
    """取得圖示檔案路徑（打包後和開發環境通用）"""
    try:
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


class ActionButton:
    """動作按鈕類別 - 定義可用的動作類型"""
    
    # 動作類型定義
    ACTIONS = {
        # 滑鼠動作
        "mouse": {
            "move_to": {
                "name": "移動滑鼠",
                "icon": "🖱️",
                "params": [
                    {"name": "X座標", "type": "int", "default": "0"},
                    {"name": "Y座標", "type": "int", "default": "0"}
                ],
                "color": "#4A90E2",
                "description": "移動滑鼠到指定座標"
            },
            "click": {
                "name": "左鍵點擊",
                "icon": "👆",
                "params": [],
                "color": "#4A90E2",
                "description": "執行滑鼠左鍵點擊"
            },
            "double_click": {
                "name": "雙擊",
                "icon": "👆👆",
                "params": [],
                "color": "#4A90E2",
                "description": "執行滑鼠雙擊"
            },
            "right_click": {
                "name": "右鍵點擊",
                "icon": "👉",
                "params": [],
                "color": "#4A90E2",
                "description": "執行滑鼠右鍵點擊"
            },
            "press_down": {
                "name": "按住滑鼠",
                "icon": "👇",
                "params": [
                    {"name": "按鍵", "type": "string", "default": "left"}
                ],
                "color": "#4A90E2",
                "description": "按住滑鼠按鍵（拖曳用）"
            },
            "release": {
                "name": "放開滑鼠",
                "icon": "👆",
                "params": [
                    {"name": "按鍵", "type": "string", "default": "left"}
                ],
                "color": "#4A90E2",
                "description": "放開滑鼠按鍵"
            },
            "scroll": {
                "name": "滾輪滾動",
                "icon": "🎡",
                "params": [
                    {"name": "滾動量", "type": "int", "default": "3"}
                ],
                "color": "#4A90E2",
                "description": "滾動滑鼠滾輪"
            }
        },
        # 鍵盤動作
        "keyboard": {
            "type_text": {
                "name": "輸入文字",
                "icon": "⌨️",
                "params": [
                    {"name": "文字內容", "type": "string", "default": ""}
                ],
                "color": "#7ED321",
                "description": "輸入指定的文字"
            },
            "press_key": {
                "name": "按下按鍵",
                "icon": "🔘",
                "params": [
                    {"name": "按鍵", "type": "string", "default": "enter"}
                ],
                "color": "#7ED321",
                "description": "按下指定的按鍵"
            },
            "hotkey": {
                "name": "快捷鍵",
                "icon": "⚡",
                "params": [
                    {"name": "按鍵組合", "type": "string", "default": "ctrl+c"}
                ],
                "color": "#7ED321",
                "description": "執行快捷鍵組合"
            }
        },
        # 控制流程
        "control": {
            "delay": {
                "name": "延遲等待",
                "icon": "⏱️",
                "params": [
                    {"name": "毫秒數", "type": "int", "default": "1000"}
                ],
                "color": "#F5A623",
                "description": "暫停執行指定時間"
            },
            "repeat": {
                "name": "重複執行",
                "icon": "🔄",
                "params": [
                    {"name": "次數", "type": "int", "default": "1"}
                ],
                "color": "#F5A623",
                "description": "重複執行下方動作"
            },
            "wait_for": {
                "name": "等待條件",
                "icon": "⏳",
                "params": [
                    {"name": "條件類型", "type": "string", "default": "image"}
                ],
                "color": "#F5A623",
                "description": "等待特定條件滿足"
            }
        },
        # 日誌與偵錯
        "debug": {
            "log": {
                "name": "輸出日誌",
                "icon": "📝",
                "params": [
                    {"name": "訊息", "type": "string", "default": ""}
                ],
                "color": "#BD10E0",
                "description": "在輸出區顯示訊息"
            },
            "screenshot": {
                "name": "截圖",
                "icon": "📸",
                "params": [
                    {"name": "檔案名稱", "type": "string", "default": "screenshot.png"}
                ],
                "color": "#BD10E0",
                "description": "截取螢幕畫面"
            },
            "comment": {
                "name": "註解",
                "icon": "💬",
                "params": [
                    {"name": "註解內容", "type": "string", "default": ""}
                ],
                "color": "#9013FE",
                "description": "添加註解說明"
            }
        }
    }


class ActionCard(tb.Frame):
    """動作卡片 - 在左側列表中顯示的單個動作"""
    
    def __init__(self, parent, action_data, index, on_edit, on_delete, on_move, **kwargs):
        super().__init__(parent, **kwargs)
        self.action_data = action_data
        self.index = index
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_move = on_move
        
        # 移除背景色樣式 (問題3)
        self.configure(relief="flat", borderwidth=1)
        
        # 拖放相關
        self.drag_start_y = 0
        self.is_dragging = False
        
        self._create_ui()
        
        # 綁定事件
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Double-Button-1>", self.on_double_click)  # 雙擊編輯 (問題6)
    
    def _create_ui(self):
        """建立卡片UI"""
        # 從動作資料取得資訊
        command = self.action_data.get("command", "")
        params = self.action_data.get("params", "")
        delay = self.action_data.get("delay", "0")
        
        # 查找動作定義
        action_def = self._find_action_definition(command)
        
        if action_def:
            icon = action_def.get("icon", "❓")
            name = action_def.get("name", command)
            color = action_def.get("color", "#999999")
        else:
            icon = "❓"
            name = command
            color = "#999999"
        
        # 設定背景色 - 移除背景色，只保留邊框 (問題3)
        # self.configure(bootstyle="secondary")
        
        # 主容器 - 使用透明背景
        main_frame = tb.Frame(self, relief="solid", borderwidth=1)
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # 左側：拖放手柄 + 圖示 + 動作名稱
        left_frame = tb.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # 拖放手柄
        handle_label = tb.Label(left_frame, text="⋮⋮", font=("Arial", 12), cursor="hand2")
        handle_label.pack(side="left", padx=(0, 5))
        handle_label.bind("<Button-1>", self.on_press)
        handle_label.bind("<B1-Motion>", self.on_drag)
        handle_label.bind("<ButtonRelease-1>", self.on_release)
        
        # 圖示 + 名稱
        info_frame = tb.Frame(left_frame)
        info_frame.pack(side="left", fill="both", expand=True)
        
        title_label = tb.Label(info_frame, text=f"{icon} {name}", font=("Arial", 10, "bold"))
        title_label.pack(anchor="w")
        title_label.bind("<Double-Button-1>", self.on_double_click)
        
        # 參數顯示
        if params:
            # 特殊處理軌跡數據顯示
            if command == "move_to_path":
                try:
                    path_data = json.loads(params)
                    param_text = f"🌊 軌跡: {len(path_data)} 個點"
                except:
                    param_text = f"參數: {params[:50]}..."
            elif len(params) > 50:
                param_text = f"參數: {params[:50]}..."
            else:
                param_text = f"參數: {params}"
            
            param_label = tb.Label(info_frame, text=param_text, font=("Arial", 8), foreground="#666666")
            param_label.pack(anchor="w")
            param_label.bind("<Double-Button-1>", self.on_double_click)
        
        # 延遲顯示
        if delay and int(delay) > 0:
            delay_label = tb.Label(info_frame, text=f"⏱️ {delay}ms", font=("Arial", 8))
            delay_label.pack(anchor="w")
            delay_label.bind("<Double-Button-1>", self.on_double_click)
        
        # 右側：編輯和刪除按鈕
        right_frame = tb.Frame(main_frame)
        right_frame.pack(side="right", padx=5, pady=5)
        
        edit_btn = tb.Button(right_frame, text="✏️", width=3, bootstyle="info-outline", 
                            command=lambda: self.on_edit(self.index))
        edit_btn.pack(side="left", padx=2)
        
        delete_btn = tb.Button(right_frame, text="🗑️", width=3, bootstyle="danger-outline",
                              command=lambda: self.on_delete(self.index))
        delete_btn.pack(side="left", padx=2)
    
    def _find_action_definition(self, command):
        """查找動作定義"""
        for category in ActionButton.ACTIONS.values():
            if command in category:
                return category[command]
        return None
    
    def on_press(self, event):
        """按下時記錄位置"""
        self.drag_start_y = event.y_root
        self.original_index = self.index
        self.is_dragging = False
    
    def on_drag(self, event):
        """拖動時改變外觀並實現拖放排序 (問題4)"""
        # 檢查是否移動超過閾值
        if abs(event.y_root - self.drag_start_y) > 5:
            self.is_dragging = True
            self.configure(relief="raised", borderwidth=2)
            
            # 計算新位置
            delta = event.y_root - self.drag_start_y
            if abs(delta) > 30:  # 移動超過一個卡片高度
                new_index = self.index + (1 if delta > 0 else -1)
                if self.on_move and 0 <= new_index < len(self.master.winfo_children()):
                    self.on_move(self.index, new_index)
                    self.drag_start_y = event.y_root
    
    def on_release(self, event):
        """釋放時恢復外觀"""
        if self.is_dragging:
            self.configure(relief="flat", borderwidth=1)
            self.is_dragging = False
    
    def on_double_click(self, event):
        """雙擊編輯 (問題6)"""
        if not self.is_dragging:
            self.on_edit(self.index)


class VisualScriptEditor(tk.Toplevel):
    """視覺化腳本編輯器主視窗"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("ChroLens 視覺化腳本編輯器")
        self.geometry("1400x800")
        # 設定視窗圖示
        set_window_icon(self)
        
        # 動作列表
        self.actions = []
        self.action_cards = []
        
        # 拖放狀態
        self.drag_data = {"item": None, "index": None}
        
        # 執行狀態
        self.is_executing = False
        self.is_paused = False
        self.execution_thread = None
        
        self._create_ui()
    
    def _create_ui(self):
        """建立主要UI"""
        # 頂部工具列
        self._create_toolbar()
        
        # 主要內容區域
        main_container = tb.Frame(self)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 左側：動作列表區域 (60%)
        self._create_action_list(main_container)
        
        # 右側：動作按鈕面板 (40%)
        self._create_action_palette(main_container)
    
    def _create_toolbar(self):
        """建立頂部工具列"""
        toolbar = tb.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # 左側按鈕
        left_frame = tb.Frame(toolbar)
        left_frame.pack(side="left")
        
        tb.Button(left_frame, text="▶️ 執行", bootstyle="success", width=12,
                 command=self.run_script).pack(side="left", padx=2)
        tb.Button(left_frame, text="⏸️ 暫停", bootstyle="warning", width=12,
                 command=self.pause_script).pack(side="left", padx=2)
        tb.Button(left_frame, text="⏹️ 停止", bootstyle="danger", width=12,
                 command=self.stop_script).pack(side="left", padx=2)
        
        # 分隔線
        tb.Separator(left_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        tb.Button(left_frame, text="💾 儲存", bootstyle="primary", width=12,
                 command=self.save_script).pack(side="left", padx=2)
        tb.Button(left_frame, text="📂 載入", bootstyle="primary", width=12,
                 command=self.load_script).pack(side="left", padx=2)
        
        # 右側按鈕
        right_frame = tb.Frame(toolbar)
        right_frame.pack(side="right")
        
        tb.Button(right_frame, text="🗑️ 清空列表", bootstyle="secondary-outline", width=12,
                 command=self.clear_actions).pack(side="left", padx=2)
        tb.Button(right_frame, text="❓ 說明", bootstyle="info-outline", width=12,
                 command=self.show_help).pack(side="left", padx=2)
    
    def _create_action_list(self, parent):
        """建立左側動作列表區域"""
        # 左側容器
        left_container = tb.Frame(parent)
        left_container.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 標題
        title_frame = tb.Frame(left_container)
        title_frame.pack(fill="x", pady=(0, 5))
        
        tb.Label(title_frame, text="腳本動作列表", font=("Arial", 14, "bold")).pack(side="left")
        
        self.action_count_label = tb.Label(title_frame, text="(0 個動作)", font=("Arial", 10))
        self.action_count_label.pack(side="left", padx=10)
        
        # 動作列表容器（帶滾動條）
        list_frame = tb.Frame(left_container)
        list_frame.pack(fill="both", expand=True)
        
        # Canvas + Scrollbar
        self.list_canvas = tk.Canvas(list_frame, bg="#f0f0f0", highlightthickness=0)
        list_scrollbar = tb.Scrollbar(list_frame, command=self.list_canvas.yview)
        
        self.list_canvas.pack(side="left", fill="both", expand=True)
        list_scrollbar.pack(side="right", fill="y")
        
        self.list_canvas.configure(yscrollcommand=list_scrollbar.set)
        
        # 可滾動框架
        self.action_list_frame = tb.Frame(self.list_canvas)
        self.list_canvas_window = self.list_canvas.create_window((0, 0), window=self.action_list_frame, anchor="nw")
        
        # 綁定事件
        self.action_list_frame.bind("<Configure>", self._on_frame_configure)
        self.list_canvas.bind("<Configure>", self._on_canvas_configure)
        
        # 提示文字（當列表為空時顯示）
        self.empty_hint = tb.Label(self.action_list_frame, 
                                   text="👈 從右側拖放或點擊動作按鈕來建立腳本\n\n支援拖放排序、點擊編輯",
                                   font=("Arial", 12),
                                   foreground="#999999")
        self.empty_hint.pack(expand=True, pady=100)
    
    def _create_action_palette(self, parent):
        """建立右側動作按鈕面板"""
        # 右側容器
        right_container = tb.Frame(parent, width=500)
        right_container.pack(side="right", fill="both")
        right_container.pack_propagate(False)
        
        # 標題
        tb.Label(right_container, text="動作面板", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # 分類標籤頁
        self.palette_notebook = tb.Notebook(right_container)
        self.palette_notebook.pack(fill="both", expand=True)
        
        # 為每個類別建立標籤頁
        categories = {
            "mouse": ("🖱️ 滑鼠", ActionButton.ACTIONS["mouse"]),
            "keyboard": ("⌨️ 鍵盤", ActionButton.ACTIONS["keyboard"]),
            "control": ("🎮 控制", ActionButton.ACTIONS["control"]),
            "debug": ("🐛 偵錯", ActionButton.ACTIONS["debug"])
        }
        
        for cat_key, (cat_name, actions) in categories.items():
            tab = self._create_palette_tab(actions)
            self.palette_notebook.add(tab, text=cat_name)
    
    def _create_palette_tab(self, actions):
        """建立單個動作面板標籤頁"""
        # 可滾動框架
        tab_frame = tb.Frame(self.palette_notebook)
        
        canvas = tk.Canvas(tab_frame, highlightthickness=0)
        scrollbar = tb.Scrollbar(tab_frame, command=canvas.yview)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        inner_frame = tb.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        # 建立動作按鈕
        for action_key, action_def in actions.items():
            self._create_action_button(inner_frame, action_key, action_def)
        
        inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        return tab_frame
    
    def _create_action_button(self, parent, action_key, action_def):
        """建立單個動作按鈕"""
        # 按鈕容器 - 使用細邊框樣式 (問題7)
        btn_frame = tb.Frame(parent, borderwidth=1, relief="solid")
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        # 內容框架
        content_frame = tb.Frame(btn_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 圖示 + 名稱
        title_frame = tb.Frame(content_frame)
        title_frame.pack(fill="x")
        
        icon_label = tb.Label(title_frame, text=action_def["icon"], font=("Arial", 20))
        icon_label.pack(side="left", padx=(0, 10))
        
        name_label = tb.Label(title_frame, text=action_def["name"], font=("Arial", 12, "bold"))
        name_label.pack(side="left")
        
        # 說明
        desc_label = tb.Label(content_frame, text=action_def["description"], 
                             font=("Arial", 9), foreground="#666666")
        desc_label.pack(anchor="w", pady=(5, 0))
        
        # 拖曳相關變數
        btn_frame.drag_data = {
            "action_key": action_key,
            "action_def": action_def,
            "is_dragging": False,
            "start_x": 0,
            "start_y": 0
        }
        
        # 設定游標
        btn_frame.configure(cursor="hand2")
        for widget in [content_frame, title_frame, icon_label, name_label, desc_label]:
            widget.configure(cursor="hand2")
        
        # 綁定事件 - 點擊直接新增
        btn_frame.bind("<Button-1>", lambda e: self._on_palette_press(e, btn_frame))
        btn_frame.bind("<B1-Motion>", lambda e: self._on_palette_drag(e, btn_frame))
        btn_frame.bind("<ButtonRelease-1>", lambda e: self._on_palette_release(e, btn_frame))
        
        # 綁定到所有子元件
        for widget in [content_frame, title_frame, icon_label, name_label, desc_label]:
            widget.bind("<Button-1>", lambda e: self._on_palette_press(e, btn_frame))
            widget.bind("<B1-Motion>", lambda e: self._on_palette_drag(e, btn_frame))
            widget.bind("<ButtonRelease-1>", lambda e: self._on_palette_release(e, btn_frame))
    
    def _on_frame_configure(self, event):
        """更新滾動區域"""
        self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """調整內部框架寬度"""
        self.list_canvas.itemconfig(self.list_canvas_window, width=event.width)
    
    def _on_palette_press(self, event, btn_frame):
        """面板按鈕按下"""
        btn_frame.drag_data["is_dragging"] = False
        btn_frame.drag_data["start_x"] = event.x_root
        btn_frame.drag_data["start_y"] = event.y_root
    
    def _on_palette_drag(self, event, btn_frame):
        """面板按鈕拖曳中"""
        # 計算拖曳距離
        dx = event.x_root - btn_frame.drag_data["start_x"]
        dy = event.y_root - btn_frame.drag_data["start_y"]
        distance = (dx**2 + dy**2) ** 0.5
        
        # 超過閾值才視為拖曳 (問題5)
        if distance > 10 and not btn_frame.drag_data["is_dragging"]:
            btn_frame.drag_data["is_dragging"] = True
            # 視覺回饋 - 改變邊框顏色
            btn_frame.configure(borderwidth=2, relief="solid")
    
    def _on_palette_release(self, event, btn_frame):
        """面板按鈕放開"""
        action_key = btn_frame.drag_data["action_key"]
        action_def = btn_frame.drag_data["action_def"]
        
        if btn_frame.drag_data["is_dragging"]:
            # 拖曳放開 - 檢查是否在動作列表區域內 (問題5)
            list_x = self.action_list_frame.winfo_rootx()
            list_y = self.action_list_frame.winfo_rooty()
            list_width = self.action_list_frame.winfo_width()
            list_height = self.action_list_frame.winfo_height()
            
            if (list_x <= event.x_root <= list_x + list_width and
                list_y <= event.y_root <= list_y + list_height):
                # 在列表區域內，新增動作
                self.add_action_from_palette(action_key, action_def)
            
            # 恢復邊框樣式
            btn_frame.configure(borderwidth=1, relief="solid")
            btn_frame.drag_data["is_dragging"] = False
        else:
            # 點擊放開 - 直接新增動作 (問題6)
            self.add_action_from_palette(action_key, action_def)
    
    def add_action_from_palette(self, action_key, action_def):
        """從面板新增動作到列表"""
        # 取得參數
        dialog_result = self._show_param_dialog(action_def)
        
        if dialog_result is not None:  # 使用者沒有取消
            # 檢查是否為軌跡移動
            if isinstance(dialog_result, dict) and dialog_result.get("action_type") == "move_to_path":
                # 建立軌跡移動動作
                action_data = {
                    "command": "move_to_path",
                    "params": dialog_result["params"],
                    "delay": "0"
                }
            else:
                # 一般動作
                params = dialog_result if isinstance(dialog_result, str) else dialog_result.get("params", "")
                action_data = {
                    "command": action_key,
                    "params": params,
                    "delay": "0"
                }
            
            # 新增到列表
            self.actions.append(action_data)
            self.refresh_action_list()
    
    def _show_param_dialog(self, action_def):
        """顯示參數輸入對話框"""
        params_list = action_def.get("params", [])
        
        if not params_list:
            return ""  # 沒有參數
        
        # 建立對話框
        dialog = tk.Toplevel(self)
        dialog.title(f"設定參數 - {action_def['name']}")
        
        # 根據動作類型調整對話框大小
        if action_def.get("name") == "移動滑鼠":
            dialog.geometry("480x550")
        else:
            dialog.geometry("400x300")
            
        dialog.transient(self)
        dialog.grab_set()
        # 設定視窗圖示
        set_window_icon(dialog)
        
        # 結果變數
        result = {"params": None}
        param_entries = []
        path_status = {"recording": False, "path_data": None}  # 初始化軌跡狀態
        
        # 內容框架
        content_frame = tb.Frame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 標題
        tb.Label(content_frame, text=f"{action_def['icon']} {action_def['name']}", 
                font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # 參數輸入欄位
        for param in params_list:
            param_frame = tb.Frame(content_frame)
            param_frame.pack(fill="x", pady=5)
            
            tb.Label(param_frame, text=f"{param['name']}:", width=15, anchor="w").pack(side="left")
            
            entry = tb.Entry(param_frame)
            entry.insert(0, param.get("default", ""))
            entry.pack(side="left", fill="x", expand=True)
            param_entries.append(entry)
        
        # 如果是移動滑鼠動作，新增軌跡錄製按鈕
        if action_def.get("name") == "移動滑鼠":
            separator = tb.Separator(content_frame, orient="horizontal")
            separator.pack(fill="x", pady=15)
            
            path_info_frame = tb.Frame(content_frame)
            path_info_frame.pack(fill="x", pady=10)
            
            tb.Label(path_info_frame, text="🌊 滑鼠軌跡錄製", 
                    font=("Arial", 11, "bold")).pack(anchor="w")
            
            path_desc = tb.Label(path_info_frame, 
                                text="點擊下方按鈕開始錄製滑鼠軌跡\n左鍵點擊一次開始，再次點擊停止", 
                                font=("Arial", 9), foreground="#666666")
            path_desc.pack(anchor="w", pady=5)
            
            path_status = {"recording": False, "path_data": None}
            record_btn = tb.Button(path_info_frame, text="🎬 開始軌跡錄製", 
                                  bootstyle="info-outline", width=20)
            record_btn.pack(pady=10)
            
            def start_path_recording():
                """開始錄製滑鼠軌跡"""
                if not path_status["recording"]:
                    path_status["recording"] = True
                    record_btn.config(text="⏺ 錄製中...", bootstyle="danger")
                    path_desc.config(text="錄製中：移動滑鼠，左鍵點擊停止錄製", foreground="#E74C3C")
                    dialog.withdraw()  # 隱藏對話框
                    
                    # 在新執行緒中錄製
                    def record_thread():
                        path_data = self._record_mouse_path()
                        if path_data:
                            path_status["path_data"] = path_data
                            # 更新參數欄位為軌跡動作
                            dialog.after(0, lambda: finish_recording(path_data))
                        else:
                            dialog.after(0, cancel_recording)
                    
                    threading.Thread(target=record_thread, daemon=True).start()
            
            def finish_recording(path_data):
                """完成錄製"""
                path_status["recording"] = False
                record_btn.config(text="✓ 軌跡已錄製", bootstyle="success")
                path_desc.config(text=f"已錄製 {len(path_data)} 個軌跡點", foreground="#27AE60")
                dialog.deiconify()  # 顯示對話框
            
            def cancel_recording():
                """取消錄製"""
                path_status["recording"] = False
                record_btn.config(text="🎬 開始軌跡錄製", bootstyle="info-outline")
                path_desc.config(text="錄製已取消，請重新嘗試", foreground="#E67E22")
                dialog.deiconify()  # 顯示對話框
            
            record_btn.config(command=start_path_recording)
        
        # 按鈕
        btn_frame = tb.Frame(content_frame)
        btn_frame.pack(pady=20)
        
        def on_ok():
            # 收集參數
            params = []
            
            # 如果是移動滑鼠且有錄製軌跡，則使用軌跡數據
            if action_def.get("name") == "移動滑鼠" and path_status.get("path_data"):
                # 將軌跡數據轉換為 JSON 字串
                result["params"] = json.dumps(path_status["path_data"])
                result["action_type"] = "move_to_path"  # 標記為軌跡移動
                result["return_dict"] = True
            else:
                for entry in param_entries:
                    params.append(entry.get())
                result["params"] = ", ".join(params)
                result["return_dict"] = False
            
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        tb.Button(btn_frame, text="✓ 確定", bootstyle="success", width=12,
                 command=on_ok).pack(side="left", padx=5)
        tb.Button(btn_frame, text="✗ 取消", bootstyle="secondary", width=12,
                 command=on_cancel).pack(side="left", padx=5)
        
        # 等待對話框關閉
        dialog.wait_window()
        
        # 根據類型返回結果
        if result["params"] is not None:
            if result.get("return_dict"):
                return {"params": result["params"], "action_type": result.get("action_type")}
            else:
                return result["params"]
        return None
    
    def _record_mouse_path(self):
        """錄製滑鼠移動軌跡
        
        Returns:
            list: 軌跡點列表 [{"x": x, "y": y, "time": t}, ...]
        """
        from pynput.mouse import Controller, Listener as MouseListener
        import pynput.mouse
        
        path_data = []
        recording = {"active": False, "start_time": None}
        mouse_ctrl = Controller()
        
        def on_click(x, y, button, pressed):
            """滑鼠點擊事件"""
            if button == pynput.mouse.Button.left and pressed:
                if not recording["active"]:
                    # 第一次點擊：開始錄製
                    recording["active"] = True
                    recording["start_time"] = time.time()
                    path_data.append({"x": x, "y": y, "time": 0.0})
                else:
                    # 第二次點擊：停止錄製
                    elapsed = time.time() - recording["start_time"]
                    path_data.append({"x": x, "y": y, "time": elapsed})
                    return False  # 停止監聽
        
        # 建立監聽器
        listener = MouseListener(on_click=on_click)
        listener.start()
        
        # 等待開始錄製
        while not recording["active"]:
            time.sleep(0.01)
        
        # 錄製滑鼠移動軌跡
        last_pos = mouse_ctrl.position
        while recording["active"] and listener.running:
            time.sleep(0.01)  # 10ms 採樣間隔
            pos = mouse_ctrl.position
            if pos != last_pos:
                elapsed = time.time() - recording["start_time"]
                path_data.append({"x": pos[0], "y": pos[1], "time": elapsed})
                last_pos = pos
        
        listener.join()
        
        return path_data if len(path_data) > 1 else None
    
    def _replay_mouse_path(self, path_data):
        """回放滑鼠移動軌跡
        
        Args:
            path_data: 軌跡點列表 [{"x": x, "y": y, "time": t}, ...]
        """
        if not path_data or len(path_data) < 2:
            return
        
        # 移動到起點
        mouse.move(path_data[0]["x"], path_data[0]["y"])
        
        # 回放軌跡
        for i in range(1, len(path_data)):
            prev_point = path_data[i-1]
            curr_point = path_data[i]
            
            # 計算時間差
            time_diff = curr_point["time"] - prev_point["time"]
            if time_diff > 0:
                time.sleep(time_diff)
            
            # 移動滑鼠
            mouse.move(curr_point["x"], curr_point["y"])
    
    
    def refresh_action_list(self):
        """重新整理動作列表顯示 - 優化速度 (問題1)"""
        # 暫停視窗更新以加快速度
        self.action_list_frame.update_idletasks()
        
        # 清空現有卡片
        for card in self.action_cards:
            card.destroy()
        self.action_cards.clear()
        
        # 隱藏/顯示提示文字
        if not self.actions:
            self.empty_hint.pack(expand=True, pady=100)
        else:
            self.empty_hint.pack_forget()
        
        # 建立新卡片 - 批次處理以提升速度
        for i, action in enumerate(self.actions):
            card = ActionCard(self.action_list_frame, action, i, 
                            self.edit_action, self.delete_action, self.move_action)
            card.pack(fill="x", pady=2)
            self.action_cards.append(card)
        
        # 更新計數
        self.action_count_label.config(text=f"({len(self.actions)} 個動作)")
        
        # 強制更新顯示
        self.action_list_frame.update_idletasks()
    
    def move_action(self, from_index, to_index):
        """移動動作位置 (問題4)"""
        if 0 <= from_index < len(self.actions) and 0 <= to_index < len(self.actions):
            # 移動動作
            action = self.actions.pop(from_index)
            self.actions.insert(to_index, action)
            # 快速刷新
            self.refresh_action_list()
    
    def edit_action(self, index):
        """編輯指定動作"""
        if 0 <= index < len(self.actions):
            action = self.actions[index]
            command = action.get("command", "")
            
            # 查找動作定義
            action_def = None
            for category in ActionButton.ACTIONS.values():
                if command in category:
                    action_def = category[command]
                    break
            
            if action_def:
                # 顯示參數對話框
                new_params = self._show_param_dialog(action_def)
                if new_params is not None:
                    action["params"] = new_params
                    self.refresh_action_list()
    
    def delete_action(self, index):
        """刪除指定動作"""
        if 0 <= index < len(self.actions):
            self.actions.pop(index)
            self.refresh_action_list()
    
    def run_script(self):
        """執行腳本 - 直接執行動作列表"""
        if not self.actions:
            messagebox.showinfo("提示", "動作列表為空，請先新增動作")
            return
        
        if self.is_executing:
            messagebox.showinfo("提示", "腳本正在執行中")
            return
        
        # 在新線程中執行
        self.is_executing = True
        self.is_paused = False
        self.execution_thread = threading.Thread(target=self._execute_actions, daemon=True)
        self.execution_thread.start()
    
    def _execute_actions(self):
        """執行動作的實際邏輯"""
        try:
            for i, action in enumerate(self.actions):
                # 檢查是否被停止
                if not self.is_executing:
                    break
                
                # 檢查暫停
                while self.is_paused and self.is_executing:
                    time.sleep(0.1)
                
                if not self.is_executing:
                    break
                
                # 更新狀態（在主線程中）
                self.after(0, lambda idx=i: self._highlight_current_action(idx))
                
                # 執行動作
                command = action.get("command", "")
                params = action.get("params", "")
                delay = action.get("delay", "0")
                
                try:
                    self._execute_single_action(command, params)
                    
                    # 執行後延遲
                    if delay and int(delay) > 0:
                        time.sleep(int(delay) / 1000.0)
                    
                except Exception as e:
                    print(f"執行動作 {command} 時發生錯誤: {e}")
            
            # 執行完成
            self.is_executing = False
            self.after(0, lambda: messagebox.showinfo("完成", "腳本執行完成！"))
            
        except Exception as e:
            self.is_executing = False
            self.after(0, lambda: messagebox.showerror("錯誤", f"執行失敗：{e}"))
    
    def _highlight_current_action(self, index):
        """高亮顯示當前正在執行的動作"""
        try:
            # 取得所有卡片 widget
            cards = self.action_list_frame.winfo_children()
            
            # 清除所有高亮
            for card in cards:
                if hasattr(card, 'configure') and not isinstance(card, tb.Label):  # 跳過提示文字
                    try:
                        card.configure(bootstyle="")
                    except:
                        pass
            
            # 高亮當前動作卡片
            if 0 <= index < len(cards):
                target_card = cards[index]
                if hasattr(target_card, 'configure') and not isinstance(target_card, tb.Label):
                    try:
                        target_card.configure(bootstyle="warning")  # 使用警告色高亮
                        # 確保卡片在可見範圍內
                        self.list_canvas.yview_moveto(index / max(len(cards), 1))
                    except:
                        pass
        except Exception as e:
            print(f"高亮動作時發生錯誤: {e}")
    
    def _execute_single_action(self, command, params):
        """執行單一動作"""
        if command == "move_to":
            # 移動滑鼠
            try:
                coords = [int(x.strip()) for x in params.split(',')]
                if len(coords) >= 2:
                    mouse.move(coords[0], coords[1])
            except Exception as e:
                print(f"移動滑鼠錯誤: {e}")
        
        elif command == "move_to_path":
            # 軌跡移動
            try:
                path_data = json.loads(params)
                self._replay_mouse_path(path_data)
            except Exception as e:
                print(f"軌跡回放錯誤: {e}")
        
        elif command == "click":
            # 左鍵點擊
            mouse.click()
        
        elif command == "double_click":
            # 雙擊
            mouse.double_click()
        
        elif command == "right_click":
            # 右鍵點擊
            mouse.right_click()
        
        elif command == "press_down":
            # 按住滑鼠
            button = params if params else "left"
            mouse.press(button=button)
        
        elif command == "release":
            # 放開滑鼠
            button = params if params else "left"
            mouse.release(button=button)
        
        elif command == "scroll":
            # 滾輪滾動
            try:
                delta = int(params) if params else 3
                mouse.wheel(delta)
            except:
                mouse.wheel(3)
        
        elif command == "type_text":
            # 輸入文字
            if params:
                keyboard.write(params)
        
        elif command == "press_key":
            # 按下按鍵
            if params:
                keyboard.press_and_release(params)
        
        elif command == "hotkey":
            # 快捷鍵
            if params:
                keys = params.split('+')
                keyboard.press_and_release('+'.join(keys))
        
        elif command == "delay":
            # 延遲
            try:
                delay_ms = int(params) if params else 1000
                time.sleep(delay_ms / 1000.0)
            except:
                time.sleep(1.0)
        
        elif command == "log":
            # 日誌輸出
            print(f"[LOG] {params}")
    
    
    def _actions_to_events(self):
        """將動作列表轉換為事件格式"""
        events = []
        current_time = time.time()
        
        for action in self.actions:
            command = action.get("command", "")
            params = action.get("params", "")
            delay = int(action.get("delay", "0"))
            
            # 根據指令類型建立事件
            if command == "move_to" and params:
                try:
                    coords = [int(x.strip()) for x in params.split(',')]
                    if len(coords) >= 2:
                        events.append({
                            "type": "mouse",
                            "event": "move",
                            "x": coords[0],
                            "y": coords[1],
                            "time": current_time
                        })
                        current_time += delay / 1000.0
                except:
                    pass
            
            elif command == "click":
                events.append({
                    "type": "mouse",
                    "event": "down",
                    "button": "left",
                    "x": 0,
                    "y": 0,
                    "time": current_time
                })
                current_time += 0.05
                events.append({
                    "type": "mouse",
                    "event": "up",
                    "button": "left",
                    "x": 0,
                    "y": 0,
                    "time": current_time
                })
                current_time += delay / 1000.0
            
            elif command == "double_click":
                for _ in range(2):
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": "left",
                        "x": 0,
                        "y": 0,
                        "time": current_time
                    })
                    current_time += 0.05
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": "left",
                        "x": 0,
                        "y": 0,
                        "time": current_time
                    })
                    current_time += 0.05
                current_time += delay / 1000.0
            
            elif command == "right_click":
                events.append({
                    "type": "mouse",
                    "event": "down",
                    "button": "right",
                    "x": 0,
                    "y": 0,
                    "time": current_time
                })
                current_time += 0.05
                events.append({
                    "type": "mouse",
                    "event": "up",
                    "button": "right",
                    "x": 0,
                    "y": 0,
                    "time": current_time
                })
                current_time += delay / 1000.0
            
            elif command == "type_text" and params:
                events.append({
                    "type": "keyboard",
                    "event": "type",
                    "text": params,
                    "time": current_time
                })
                current_time += delay / 1000.0
            
            elif command == "press_key" and params:
                events.append({
                    "type": "keyboard",
                    "event": "press",
                    "key": params,
                    "time": current_time
                })
                current_time += delay / 1000.0
            
            elif command == "delay" and params:
                try:
                    delay_ms = int(params)
                    current_time += delay_ms / 1000.0
                except:
                    pass
            
            elif command == "log" and params:
                # 日誌事件
                events.append({
                    "type": "log",
                    "message": params,
                    "time": current_time
                })
        
        return events
    
    def pause_script(self):
        """暫停/繼續腳本"""
        if not self.is_executing:
            messagebox.showinfo("提示", "目前沒有腳本在執行")
            return
        
        self.is_paused = not self.is_paused
        status = "已暫停" if self.is_paused else "已繼續"
        messagebox.showinfo("狀態", status)
    
    def stop_script(self):
        """停止腳本"""
        if not self.is_executing:
            messagebox.showinfo("提示", "目前沒有腳本在執行")
            return
        
        self.is_executing = False
        self.is_paused = False
        messagebox.showinfo("停止", "腳本已停止")
    
    def save_script(self):
        """儲存腳本 - 轉換為標準 events 格式"""
        if not self.actions:
            messagebox.showwarning("警告", "動作列表為空，無法儲存")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("ChroLens Script", "*.json"), ("All Files", "*.*")],
            initialdir=self.parent.script_dir if hasattr(self.parent, 'script_dir') else "scripts"
        )
        
        if filepath:
            try:
                # 將 script_actions 轉換為標準 events 格式
                events = self._actions_to_events(self.actions)
                
                script_data = {
                    "events": events,
                    "speed": "100",
                    "repeat": "1",
                    "repeat_time": "00:00:00",
                    "repeat_interval": "00:00:00",
                    "random_interval": False,
                    "script_hotkey": ""
                }
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(script_data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"已儲存至：{filepath}\n轉換了 {len(events)} 個事件")
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存失敗：{e}")
                import traceback
                print(traceback.format_exc())
    
    def _actions_to_events(self, actions):
        """將視覺化編輯器的 actions 轉換為標準 events 格式
        
        Args:
            actions: script_actions 列表
            
        Returns:
            list: events 列表(標準錄製格式)
        """
        events = []
        current_time = time.time()
        
        for action in actions:
            command = action.get("command", "")
            params = action.get("params", "")
            delay = int(action.get("delay", "0"))
            
            # 添加延遲時間
            if delay > 0:
                current_time += delay / 1000.0
            
            # 根據命令類型轉換為事件
            if command == "move_to":
                # 普通滑鼠移動: "x, y"
                try:
                    parts = params.split(",", 1)
                    if len(parts) >= 2:
                        x = int(parts[0].strip())
                        y = int(parts[1].strip())
                        events.append({
                            "type": "mouse",
                            "event": "move",
                            "x": x,
                            "y": y,
                            "time": current_time,
                            "in_target": True
                        })
                        current_time += 0.01  # 10ms 間隔
                except:
                    pass
            
            elif command == "move_to_path":
                # 滑鼠軌跡移動: JSON 字串格式
                try:
                    trajectory = json.loads(params)
                    if isinstance(trajectory, list) and len(trajectory) > 0:
                        # 第一個點
                        first_point = trajectory[0]
                        base_time = current_time
                        
                        for point in trajectory:
                            events.append({
                                "type": "mouse",
                                "event": "move",
                                "x": point["x"],
                                "y": point["y"],
                                "time": base_time + point["time"],
                                "in_target": True
                            })
                        
                        # 更新當前時間為最後一個點的時間
                        if trajectory:
                            current_time = base_time + trajectory[-1]["time"]
                except Exception as e:
                    print(f"轉換 move_to_path 失敗: {e}")
                    import traceback
                    print(traceback.format_exc())
            
            elif command == "click":
                # 左鍵點擊
                events.append({
                    "type": "mouse",
                    "event": "down",
                    "button": "left",
                    "x": 0,  # 點擊使用當前滑鼠位置
                    "y": 0,
                    "time": current_time,
                    "in_target": True
                })
                current_time += 0.05
                events.append({
                    "type": "mouse",
                    "event": "up",
                    "button": "left",
                    "x": 0,
                    "y": 0,
                    "time": current_time,
                    "in_target": True
                })
                current_time += 0.01
            
            elif command == "double_click":
                # 雙擊 = 兩次點擊
                for _ in range(2):
                    events.append({
                        "type": "mouse",
                        "event": "down",
                        "button": "left",
                        "x": 0,
                        "y": 0,
                        "time": current_time,
                        "in_target": True
                    })
                    current_time += 0.05
                    events.append({
                        "type": "mouse",
                        "event": "up",
                        "button": "left",
                        "x": 0,
                        "y": 0,
                        "time": current_time,
                        "in_target": True
                    })
                    current_time += 0.05
            
            elif command == "right_click":
                # 右鍵點擊
                events.append({
                    "type": "mouse",
                    "event": "down",
                    "button": "right",
                    "x": 0,
                    "y": 0,
                    "time": current_time,
                    "in_target": True
                })
                current_time += 0.05
                events.append({
                    "type": "mouse",
                    "event": "up",
                    "button": "right",
                    "x": 0,
                    "y": 0,
                    "time": current_time,
                    "in_target": True
                })
                current_time += 0.01
            
            elif command == "scroll":
                # 滾輪
                try:
                    amount = int(params)
                    events.append({
                        "type": "mouse",
                        "event": "scroll",
                        "delta": amount,
                        "x": 0,
                        "y": 0,
                        "time": current_time,
                        "in_target": True
                    })
                    current_time += 0.01
                except:
                    pass
            
            elif command == "type_text":
                # 輸入文字
                text = params.strip('"\'')  # 移除引號
                for char in text:
                    events.append({
                        "type": "keyboard",
                        "event": "press",
                        "key": char,
                        "time": current_time,
                        "in_target": True
                    })
                    current_time += 0.01
                    events.append({
                        "type": "keyboard",
                        "event": "release",
                        "key": char,
                        "time": current_time,
                        "in_target": True
                    })
                    current_time += 0.01
            
            elif command == "press_key":
                # 按下按鍵
                key = params.strip('"\'')
                events.append({
                    "type": "keyboard",
                    "event": "press",
                    "key": key,
                    "time": current_time,
                    "in_target": True
                })
                current_time += 0.05
                events.append({
                    "type": "keyboard",
                    "event": "release",
                    "key": key,
                    "time": current_time,
                    "in_target": True
                })
                current_time += 0.01
            
            elif command == "hotkey":
                # 快捷鍵組合
                keys = params.strip('"\'').split("+")
                # 按下所有按鍵
                for key in keys:
                    events.append({
                        "type": "keyboard",
                        "event": "press",
                        "key": key.strip(),
                        "time": current_time,
                        "in_target": True
                    })
                    current_time += 0.01
                # 放開所有按鍵(反向順序)
                for key in reversed(keys):
                    events.append({
                        "type": "keyboard",
                        "event": "release",
                        "key": key.strip(),
                        "time": current_time,
                        "in_target": True
                    })
                    current_time += 0.01
            
            elif command == "delay":
                # 延遲(已在上面處理)
                pass
        
        return events

    
    def load_script(self):
        """載入腳本 - 支援事件格式和動作格式"""
        filepath = filedialog.askopenfilename(
            filetypes=[("ChroLens Script", "*.json"), ("All Files", "*.*")],
            initialdir=self.parent.script_dir if hasattr(self.parent, 'script_dir') else "scripts"
        )
        
        # 載入後視窗回到最上層 (問題2)
        self.lift()
        self.focus_force()
        
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # 優先檢查動作列表格式
                if "settings" in data and "script_actions" in data["settings"]:
                    self.actions = data["settings"]["script_actions"]
                    self.refresh_action_list()
                    messagebox.showinfo("成功", f"已載入 {len(self.actions)} 個動作")
                
                # 檢查事件格式（scripts 資料夾中的格式）
                elif "events" in data and isinstance(data["events"], list):
                    # 將事件轉換為動作
                    self.actions = self._events_to_actions(data["events"])
                    self.refresh_action_list()
                    messagebox.showinfo("成功", f"已從錄製腳本載入 {len(self.actions)} 個動作")
                
                else:
                    messagebox.showerror("錯誤", "無法識別的檔案格式")
            except Exception as e:
                messagebox.showerror("錯誤", f"載入失敗：{e}")
                import traceback
                print(traceback.format_exc())
    
    def _events_to_actions(self, events):
        """將錄製的事件轉換為動作列表（簡化版）"""
        actions = []
        last_time = events[0].get('time', 0) if events else 0
        last_pos = None
        
        i = 0
        while i < len(events):
            event = events[i]
            event_type = event.get('type', '')
            current_time = event.get('time', 0)
            
            # 計算延遲
            delay = int((current_time - last_time) * 1000) if current_time > last_time else 0
            
            if event_type == 'mouse':
                mouse_event = event.get('event', '')
                x = event.get('x', 0)
                y = event.get('y', 0)
                button = event.get('button', 'left')
                
                # 滑鼠移動
                if mouse_event == 'move':
                    # 只記錄顯著移動
                    if last_pos is None or (abs(x - last_pos[0]) > 10 or abs(y - last_pos[1]) > 10):
                        actions.append({
                            "command": "move_to",
                            "params": f"{x}, {y}",
                            "delay": str(delay)
                        })
                        last_pos = (x, y)
                        last_time = current_time
                
                # 滑鼠點擊
                elif mouse_event == 'down':
                    # 檢查是否為雙擊
                    is_double = False
                    if i + 3 < len(events):
                        if (events[i+2].get('event') == 'down' and 
                            events[i+3].get('event') == 'up' and
                            events[i+3].get('time', 0) - current_time < 0.5):
                            is_double = True
                    
                    if is_double:
                        actions.append({
                            "command": "double_click",
                            "params": "",
                            "delay": str(delay)
                        })
                        i += 3  # 跳過雙擊的其他事件
                    else:
                        if button == 'right':
                            actions.append({
                                "command": "right_click",
                                "params": "",
                                "delay": str(delay)
                            })
                        else:
                            actions.append({
                                "command": "click",
                                "params": "",
                                "delay": str(delay)
                            })
                        i += 1  # 跳過 up 事件
                    
                    last_time = current_time
            
            elif event_type == 'keyboard':
                keyboard_event = event.get('event', '')
                
                if keyboard_event == 'type':
                    text = event.get('text', '')
                    actions.append({
                        "command": "type_text",
                        "params": text,
                        "delay": str(delay)
                    })
                
                elif keyboard_event == 'press':
                    key = event.get('key', '')
                    actions.append({
                        "command": "press_key",
                        "params": key,
                        "delay": str(delay)
                    })
                
                last_time = current_time
            
            i += 1
        
        return actions
    
    def clear_actions(self):
        """清空動作列表"""
        if self.actions and messagebox.askyesno("確認", "確定要清空所有動作嗎？"):
            self.actions.clear()
            self.refresh_action_list()
    
    def show_help(self):
        """顯示說明"""
        help_text = """ChroLens 視覺化腳本編輯器
======================

📋 左側：腳本動作列表
- 顯示所有已新增的動作
- 支援拖放排序
- 點擊編輯按鈕可修改參數
- 點擊刪除按鈕可移除動作

🎨 右側：動作面板
- 分類顯示所有可用動作
- 點擊「新增到列表」按鈕將動作加入左側
- 可以拖放到左側列表中

⌨️ 快速操作：
- 點擊右側按鈕：輸入參數後新增到列表末尾
- 拖放到左側：精確插入到指定位置
- 拖放排序：在左側列表中調整順序

🖱️ 支援的動作類型：
- 滑鼠：移動、點擊、雙擊、右鍵、滾輪
- 鍵盤：輸入文字、按鍵、快捷鍵
- 控制：延遲、重複、等待條件
- 偵錯：日誌、截圖、註解
"""
        messagebox.showinfo("使用說明", help_text)


# 測試程式碼
if __name__ == "__main__":
    root = tb.Window(themename="cosmo")
    root.title("ChroLens Mimic")
    root.geometry("800x600")
    
    # 模擬 parent 物件
    root.script_dir = "scripts"
    
    # 建立測試按鈕
    tb.Button(root, text="開啟視覺化編輯器", 
             command=lambda: VisualScriptEditor(root)).pack(expand=True)
    
    root.mainloop()
