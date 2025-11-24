# -*- coding: utf-8 -*-
"""
ChroLens 智能自動戰鬥系統 (Smart Auto Combat)
整合自適應導航 + 自動戰鬥 + 簡潔直覺的介面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import os
import json
from datetime import datetime
from screenshot_selector import capture_screen_region

# 使用 try-except 導入 AdaptiveNavigationSystem，避免因缺少 cv2 導致整個模組無法載入
try:
    from adaptive_navigation_system import AdaptiveNavigationSystem
    HAS_ADAPTIVE_NAV = True
except ImportError as e:
    print(f"⚠️ 無法載入自適應導航系統: {e}")
    print("⚠️ 自動戰鬥系統將以基礎模式運行（不含影像辨識功能）")
    HAS_ADAPTIVE_NAV = False
    AdaptiveNavigationSystem = None


class SmartAutoCombatUI:
    """智能自動戰鬥介面"""
    
    def __init__(self, parent_window=None):
        self.is_standalone = parent_window is None
        
        if parent_window:
            # 作為子視窗
            self.root = parent_window
            self.root.title("ChroLens 智能自動戰鬥")
            self.root.geometry("900x700")
            self.root.minsize(800, 600)
            # 設定視窗關閉時的處理
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        else:
            # 獨立視窗
            self.root = tb.Window(
                title="ChroLens 智能自動戰鬥",
                themename="darkly",
                size=(900, 700),
                minsize=(800, 600)
            )
        
        # 導航系統
        self.nav_system = None
        self.is_running = False
        self.start_time = None
        
        # 配置
        self.config = {
            'window_title': '',
            'character_template': '',
            'enemy_templates': {},
            'move_keys': {
                'left': 'left',
                'right': 'right',
                'up': 'up',
                'down': 'down',
                'jump': 'alt',
                'attack': 'ctrl',
                'skill1': 'a',
                'skill2': 's',
                'skill3': 'd',
                'hp_potion': 'pageup',
                'mp_potion': 'pagedown'
            },
            'combat': {
                'auto_attack': True,
                'attack_range': 120,
                'hp_threshold': 0.5,
                'use_potions': True
            },
            'exploration': {
                'priority': ['right', 'left', 'up', 'down'],
                'duration': 300
            }
        }
        
        self._create_ui()
        self._load_last_config()
        
    def _create_ui(self):
        """創建介面"""
        
        # ==================== 標題區 ====================
        title_frame = tb.Frame(self.root, bootstyle="dark")
        title_frame.pack(fill="x", padx=10, pady=10)
        
        tb.Label(
            title_frame,
            text="🎮 ChroLens 智能自動戰鬥",
            font=("Microsoft YaHei UI", 20, "bold"),
            bootstyle="inverse-dark"
        ).pack(side="left")
        
        tb.Label(
            title_frame,
            text="自適應導航 + 自動戰鬥",
            font=("Microsoft YaHei UI", 10),
            bootstyle="secondary"
        ).pack(side="left", padx=10)
        
        # ==================== 主內容區 ====================
        content = tb.Frame(self.root)
        content.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左側：配置區
        left_frame = tb.LabelFrame(content, text="⚙️ 系統配置", padding=15)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        self._create_config_section(left_frame)
        
        # 右側：狀態 + 控制
        right_frame = tb.Frame(content)
        right_frame.pack(side="right", fill="both", expand=False, padx=(5, 0))
        
        # 狀態顯示
        status_frame = tb.LabelFrame(right_frame, text="📊 即時狀態", padding=15, width=300)
        status_frame.pack(fill="both", expand=True, pady=(0, 10))
        self._create_status_section(status_frame)
        
        # 控制按鈕
        control_frame = tb.LabelFrame(right_frame, text="🎮 控制面板", padding=15, width=300)
        control_frame.pack(fill="both", expand=False)
        self._create_control_section(control_frame)
        
        # ==================== 日誌區 ====================
        log_frame = tb.LabelFrame(self.root, text="📝 運行日誌", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        
        self._create_log_section(log_frame)
        
        # ==================== 狀態列 ====================
        self.status_bar = tb.Label(
            self.root,
            text="就緒",
            relief="sunken",
            anchor="w",
            bootstyle="secondary"
        )
        self.status_bar.pack(side="bottom", fill="x")
    
    def _create_config_section(self, parent):
        """創建配置區"""
        
        # 滾動框架
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = tb.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tb.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # === 1. 遊戲視窗設定 ===
        game_frame = tb.Frame(scrollable_frame)
        game_frame.pack(fill="x", pady=5)
        
        tb.Label(game_frame, text="🎯 遊戲視窗標題:", font=("", 10, "bold")).pack(anchor="w")
        
        window_input_frame = tb.Frame(game_frame)
        window_input_frame.pack(fill="x", pady=5)
        
        self.window_title_var = tb.StringVar(value=self.config['window_title'])
        window_entry = tb.Entry(window_input_frame, textvariable=self.window_title_var, width=30, state="readonly")
        window_entry.pack(side="left", fill="x", expand=True)
        
        tb.Button(
            window_input_frame,
            text="🎯 選擇視窗",
            command=self._select_window,
            bootstyle="success-outline",
            width=12
        ).pack(side="right", padx=(5, 0))
        
        tb.Button(
            window_input_frame,
            text="🔍 測試連接",
            command=self._test_window_lock,
            bootstyle="info-outline",
            width=12
        ).pack(side="right", padx=(5, 0))
        
        # === 2. 角色模板 ===
        char_frame = tb.Frame(scrollable_frame)
        char_frame.pack(fill="x", pady=5)
        
        tb.Label(char_frame, text="👤 角色識別模板:", font=("", 10, "bold")).pack(anchor="w")
        
        char_input_frame = tb.Frame(char_frame)
        char_input_frame.pack(fill="x", pady=5)
        
        self.char_template_var = tb.StringVar(value=self.config['character_template'])
        tb.Entry(char_input_frame, textvariable=self.char_template_var, state="readonly").pack(side="left", fill="x", expand=True)
        
        tb.Button(
            char_input_frame,
            text="📸 截圖",
            command=lambda: self._capture_template('character'),
            bootstyle="info-outline",
            width=8
        ).pack(side="right", padx=(5, 0))
        
        tb.Button(
            char_input_frame,
            text="📁 檔案",
            command=lambda: self._select_image('character'),
            bootstyle="secondary-outline",
            width=8
        ).pack(side="right", padx=(5, 0))
        
        # === 3. 敵人模板 ===
        enemy_frame = tb.Frame(scrollable_frame)
        enemy_frame.pack(fill="x", pady=5)
        
        tb.Label(enemy_frame, text="👾 敵人識別模板:", font=("", 10, "bold")).pack(anchor="w")
        
        # 敵人列表
        self.enemy_list_frame = tb.Frame(enemy_frame)
        self.enemy_list_frame.pack(fill="x", pady=5)
        
        # 添加按鈕
        enemy_btn_frame = tb.Frame(enemy_frame)
        enemy_btn_frame.pack(anchor="w", pady=5)
        
        tb.Button(
            enemy_btn_frame,
            text="📸 截圖添加",
            command=lambda: self._capture_template('enemy'),
            bootstyle="info-outline",
            width=12
        ).pack(side="left", padx=(0, 5))
        
        tb.Button(
            enemy_btn_frame,
            text="📁 檔案添加",
            command=self._add_enemy_template,
            bootstyle="success-outline",
            width=12
        ).pack(side="left")
        
        self._refresh_enemy_list()
        
        # === 4. 按鍵配置 ===
        key_frame = tb.Frame(scrollable_frame)
        key_frame.pack(fill="x", pady=10)
        
        tb.Label(key_frame, text="⌨️ 按鍵設定:", font=("", 10, "bold")).pack(anchor="w")
        
        # 按鍵網格
        key_grid = tb.Frame(key_frame)
        key_grid.pack(fill="x", pady=5)
        
        self.key_entries = {}
        key_labels = [
            ('跳躍', 'jump'), ('攻擊', 'attack'),
            ('技能1', 'skill1'), ('技能2', 'skill2'), ('技能3', 'skill3'),
            ('補血', 'hp_potion'), ('補魔', 'mp_potion')
        ]
        
        for i, (label, key) in enumerate(key_labels):
            row = i // 2
            col = (i % 2) * 2
            
            tb.Label(key_grid, text=f"{label}:", width=8).grid(row=row, column=col, sticky="w", padx=5, pady=2)
            
            entry = tb.Entry(key_grid, width=10)
            entry.insert(0, self.config['move_keys'].get(key, ''))
            entry.grid(row=row, column=col+1, sticky="ew", padx=5, pady=2)
            
            self.key_entries[key] = entry
        
        key_grid.columnconfigure(1, weight=1)
        key_grid.columnconfigure(3, weight=1)
        
        # === 5. 戰鬥設定 ===
        combat_frame = tb.Frame(scrollable_frame)
        combat_frame.pack(fill="x", pady=10)
        
        tb.Label(combat_frame, text="⚔️ 戰鬥設定:", font=("", 10, "bold")).pack(anchor="w")
        
        # 自動攻擊
        self.auto_attack_var = tb.BooleanVar(value=self.config['combat']['auto_attack'])
        tb.Checkbutton(
            combat_frame,
            text="啟用自動攻擊",
            variable=self.auto_attack_var,
            bootstyle="round-toggle"
        ).pack(anchor="w", pady=2)
        
        # 攻擊範圍
        range_frame = tb.Frame(combat_frame)
        range_frame.pack(fill="x", pady=5)
        
        tb.Label(range_frame, text="攻擊範圍:").pack(side="left")
        self.attack_range_var = tb.IntVar(value=self.config['combat']['attack_range'])
        tb.Scale(
            range_frame,
            from_=50,
            to=200,
            variable=self.attack_range_var,
            orient="horizontal",
            bootstyle="info"
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.attack_range_label = tb.Label(range_frame, text=f"{self.attack_range_var.get()}px", width=6)
        self.attack_range_label.pack(side="right")
        self.attack_range_var.trace('w', lambda *_: self.attack_range_label.config(text=f"{self.attack_range_var.get()}px"))
        
        # 血量閾值
        hp_frame = tb.Frame(combat_frame)
        hp_frame.pack(fill="x", pady=5)
        
        tb.Label(hp_frame, text="補血閾值:").pack(side="left")
        self.hp_threshold_var = tb.DoubleVar(value=self.config['combat']['hp_threshold'])
        tb.Scale(
            hp_frame,
            from_=0.1,
            to=0.9,
            variable=self.hp_threshold_var,
            orient="horizontal",
            bootstyle="warning"
        ).pack(side="left", fill="x", expand=True, padx=5)
        
        self.hp_threshold_label = tb.Label(hp_frame, text=f"{int(self.hp_threshold_var.get()*100)}%", width=6)
        self.hp_threshold_label.pack(side="right")
        self.hp_threshold_var.trace('w', lambda *_: self.hp_threshold_label.config(text=f"{int(self.hp_threshold_var.get()*100)}%"))
        
        # 使用藥水
        self.use_potions_var = tb.BooleanVar(value=self.config['combat']['use_potions'])
        tb.Checkbutton(
            combat_frame,
            text="自動使用藥水",
            variable=self.use_potions_var,
            bootstyle="round-toggle"
        ).pack(anchor="w", pady=2)
        
        # === 6. 探索設定 ===
        explore_frame = tb.Frame(scrollable_frame)
        explore_frame.pack(fill="x", pady=10)
        
        tb.Label(explore_frame, text="🗺️ 探索設定:", font=("", 10, "bold")).pack(anchor="w")
        
        # 探索時長
        duration_frame = tb.Frame(explore_frame)
        duration_frame.pack(fill="x", pady=5)
        
        tb.Label(duration_frame, text="探索時長(分鐘):").pack(side="left")
        self.duration_var = tb.IntVar(value=self.config['exploration']['duration'] // 60)
        tb.Spinbox(
            duration_frame,
            from_=1,
            to=120,
            textvariable=self.duration_var,
            width=10,
            bootstyle="info"
        ).pack(side="left", padx=5)
        
        # 快捷設定按鈕
        quick_frame = tb.Frame(scrollable_frame)
        quick_frame.pack(fill="x", pady=10)
        
        tb.Button(
            quick_frame,
            text="💾 保存配置",
            command=self._save_config,
            bootstyle="success",
            width=15
        ).pack(side="left", padx=5)
        
        tb.Button(
            quick_frame,
            text="📂 載入配置",
            command=self._load_config,
            bootstyle="info",
            width=15
        ).pack(side="left", padx=5)
    
    def _create_status_section(self, parent):
        """創建狀態顯示區"""
        
        # 運行狀態
        self.status_label = tb.Label(
            parent,
            text="● 就緒",
            font=("", 12, "bold"),
            bootstyle="secondary"
        )
        self.status_label.pack(pady=5)
        
        tb.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        
        # 統計信息
        stats_frame = tb.Frame(parent)
        stats_frame.pack(fill="both", expand=True)
        
        self.stats_labels = {}
        stats_items = [
            ('運行時間', 'runtime', '00:00:00'),
            ('探索位置', 'explored', '0'),
            ('發現敵人', 'enemies', '0'),
            ('擊殺數量', 'kills', '0'),
            ('卡住次數', 'stuck', '0')
        ]
        
        for label, key, default in stats_items:
            frame = tb.Frame(stats_frame)
            frame.pack(fill="x", pady=3)
            
            tb.Label(frame, text=f"{label}:", width=10, anchor="w").pack(side="left")
            
            value_label = tb.Label(
                frame,
                text=default,
                font=("", 10, "bold"),
                bootstyle="info"
            )
            value_label.pack(side="right")
            
            self.stats_labels[key] = value_label
    
    def _create_control_section(self, parent):
        """創建控制按鈕區"""
        
        # 開始按鈕
        self.start_btn = tb.Button(
            parent,
            text="▶️ 開始運行",
            command=self._start_combat,
            bootstyle="success",
            width=25
        )
        self.start_btn.pack(pady=5, fill="x")
        
        # 停止按鈕
        self.stop_btn = tb.Button(
            parent,
            text="⏹️ 停止運行",
            command=self._stop_combat,
            bootstyle="danger",
            width=25,
            state="disabled"
        )
        self.stop_btn.pack(pady=5, fill="x")
        
        tb.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        
        # 快捷功能
        tb.Button(
            parent,
            text="📸 截取角色",
            command=lambda: self._quick_screenshot('character'),
            bootstyle="info-outline",
            width=25
        ).pack(pady=3, fill="x")
        
        tb.Button(
            parent,
            text="📸 截取敵人",
            command=lambda: self._quick_screenshot('enemy'),
            bootstyle="warning-outline",
            width=25
        ).pack(pady=3, fill="x")
        
        tb.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        
        tb.Button(
            parent,
            text="📊 查看地圖",
            command=self._show_map_viewer,
            bootstyle="secondary-outline",
            width=25
        ).pack(pady=3, fill="x")
        
        tb.Button(
            parent,
            text="🔧 進階設定",
            command=self._show_advanced_settings,
            bootstyle="secondary-outline",
            width=25
        ).pack(pady=3, fill="x")
    
    def _create_log_section(self, parent):
        """創建日誌區"""
        
        # 日誌文本框
        log_frame = tb.Frame(parent)
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            wrap="word",
            bg="#1e1e1e",
            fg="#d4d4d4",
            font=("Consolas", 9),
            relief="flat"
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = tb.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 日誌按鈕
        log_btn_frame = tb.Frame(parent)
        log_btn_frame.pack(fill="x", pady=(5, 0))
        
        tb.Button(
            log_btn_frame,
            text="🗑️ 清空日誌",
            command=self._clear_log,
            bootstyle="secondary-outline",
            width=12
        ).pack(side="left")
        
        tb.Button(
            log_btn_frame,
            text="💾 匯出日誌",
            command=self._export_log,
            bootstyle="secondary-outline",
            width=12
        ).pack(side="left", padx=5)
        
        self._log("系統初始化完成", "info")
    
    # ==================== 功能實現 ====================
    
    def _select_window(self):
        """使用視窗選擇器選擇遊戲視窗"""
        try:
            from window_selector import WindowSelectorDialog
            
            def on_selected(hwnd, title):
                if hwnd and title:
                    self.window_title_var.set(title)
                    self._log(f"✓ 已選擇視窗: {title}", "success")
                    self.config['window_title'] = title
            
            WindowSelectorDialog(self.root, on_selected)
        except Exception as e:
            self._log(f"❌ 視窗選擇器錯誤: {e}", "error")
            messagebox.showerror("錯誤", f"無法開啟視窗選擇器\n\n{str(e)}")
    
    def _test_window_lock(self):
        """測試視窗鎖定"""
        window_title = self.window_title_var.get().strip()
        if not window_title:
            messagebox.showwarning("提示", "請先輸入遊戲視窗標題!")
            return
        
        self._log(f"嘗試鎖定視窗: {window_title}", "info")
        
        # 檢查是否有導航系統
        if not HAS_ADAPTIVE_NAV:
            self._log("❌ 自適應導航系統未載入（缺少 cv2 模組）", "error")
            messagebox.showerror("錯誤", "自適應導航系統未載入\n\n請安裝 OpenCV:\npip install opencv-python")
            return
        
        # 創建臨時系統測試
        try:
            temp_nav = AdaptiveNavigationSystem()
            success = temp_nav.lock_game_window(window_title)
            
            if success:
                self._log(f"✅ 視窗鎖定成功! 位置: {temp_nav.game_rect}", "success")
                messagebox.showinfo("成功", f"視窗鎖定成功!\n位置: {temp_nav.game_rect}")
            else:
                self._log(f"❌ 找不到視窗: {window_title}", "error")
                messagebox.showerror("失敗", f"找不到視窗: {window_title}\n\n請確認:\n1. 遊戲已開啟\n2. 視窗標題正確")
        except Exception as e:
            self._log(f"❌ 錯誤: {e}", "error")
            messagebox.showerror("錯誤", str(e))
    
    def _capture_template(self, template_type):
        """截圖捕獲模板"""
        self._log(f"請在螢幕上框選{'角色' if template_type == 'character' else '敵人'}區域...", "info")
        
        def on_capture(image):
            """截圖完成回調"""
            try:
                # 創建 templates 目錄
                templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
                if not os.path.exists(templates_dir):
                    os.makedirs(templates_dir)
                
                if template_type == 'character':
                    # 保存角色模板
                    filename = os.path.join(templates_dir, 'character_template.png')
                    image.save(filename)
                    self.char_template_var.set(filename)
                    self.config['character_template'] = filename
                    self._log(f"✅ 已設定角色模板 (尺寸: {image.width}×{image.height})", "success")
                    
                elif template_type == 'enemy':
                    # 請求輸入敵人名稱
                    name = tk.simpledialog.askstring(
                        "敵人名稱",
                        "請輸入敵人名稱:",
                        parent=self.root
                    )
                    
                    if name:
                        # 保存敵人模板
                        filename = os.path.join(templates_dir, f'enemy_{name}.png')
                        image.save(filename)
                        self.config['enemy_templates'][name] = filename
                        self._refresh_enemy_list()
                        self._log(f"✅ 已添加敵人模板: {name} (尺寸: {image.width}×{image.height})", "success")
                    else:
                        self._log("⚠️ 已取消添加敵人模板", "warning")
                        
            except Exception as e:
                self._log(f"❌ 保存模板失敗: {e}", "error")
                messagebox.showerror("錯誤", f"保存模板失敗:\n{e}")
        
        # 啟動截圖選擇器
        capture_screen_region(on_capture)
    
    def _select_image(self, img_type):
        """選擇圖片檔案"""
        filename = filedialog.askopenfilename(
            title=f"選擇{'角色' if img_type == 'character' else '敵人'}圖片",
            filetypes=[("圖片檔案", "*.png *.jpg *.jpeg *.bmp"), ("所有檔案", "*.*")]
        )
        
        if filename:
            if img_type == 'character':
                self.char_template_var.set(filename)
                self.config['character_template'] = filename
                self._log(f"已設定角色模板: {os.path.basename(filename)}", "info")
            else:
                return filename
        return None
    
    def _add_enemy_template(self):
        """添加敵人模板"""
        filename = filedialog.askopenfilename(
            title="選擇敵人圖片",
            filetypes=[("圖片檔案", "*.png *.jpg *.jpeg *.bmp"), ("所有檔案", "*.*")]
        )
        
        if filename:
            # 輸入敵人名稱
            name = tk.simpledialog.askstring("敵人名稱", "請輸入敵人名稱:", parent=self.root)
            if name:
                self.config['enemy_templates'][name] = filename
                self._refresh_enemy_list()
                self._log(f"已添加敵人模板: {name}", "success")
    
    def _refresh_enemy_list(self):
        """刷新敵人列表"""
        # 清空現有列表
        for widget in self.enemy_list_frame.winfo_children():
            widget.destroy()
        
        # 顯示敵人
        if not self.config['enemy_templates']:
            tb.Label(
                self.enemy_list_frame,
                text="尚未添加敵人模板",
                bootstyle="secondary"
            ).pack(anchor="w", pady=2)
        else:
            for name, path in self.config['enemy_templates'].items():
                frame = tb.Frame(self.enemy_list_frame)
                frame.pack(fill="x", pady=2)
                
                tb.Label(
                    frame,
                    text=f"• {name}: {os.path.basename(path)}",
                    bootstyle="info"
                ).pack(side="left")
                
                tb.Button(
                    frame,
                    text="❌",
                    command=lambda n=name: self._remove_enemy(n),
                    bootstyle="danger-link",
                    width=3
                ).pack(side="right")
    
    def _remove_enemy(self, name):
        """移除敵人"""
        if name in self.config['enemy_templates']:
            del self.config['enemy_templates'][name]
            self._refresh_enemy_list()
            self._log(f"已移除敵人: {name}", "warning")
    
    def _quick_screenshot(self, target_type):
        """快速截圖"""
        import pyautogui
        
        messagebox.showinfo(
            "截圖提示",
            f"3秒後將自動截圖\n請將滑鼠移至要截取的{'角色' if target_type == 'character' else '敵人'}上方"
        )
        
        self.root.after(3000, lambda: self._do_screenshot(target_type))
    
    def _do_screenshot(self, target_type):
        """執行截圖"""
        try:
            import pyautogui
            
            # 取得滑鼠位置
            x, y = pyautogui.position()
            
            # 截取 80x80 區域
            screenshot = pyautogui.screenshot(region=(x-40, y-40, 80, 80))
            
            # 保存
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG圖片", "*.png")],
                initialfile=f"{target_type}_{int(time.time())}.png"
            )
            
            if filename:
                screenshot.save(filename)
                self._log(f"截圖已保存: {filename}", "success")
                
                if target_type == 'character':
                    self.char_template_var.set(filename)
                    self.config['character_template'] = filename
                
        except Exception as e:
            self._log(f"截圖失敗: {e}", "error")
    
    def _save_config(self):
        """保存配置"""
        # 更新配置
        self.config['window_title'] = self.window_title_var.get()
        self.config['combat']['auto_attack'] = self.auto_attack_var.get()
        self.config['combat']['attack_range'] = self.attack_range_var.get()
        self.config['combat']['hp_threshold'] = self.hp_threshold_var.get()
        self.config['combat']['use_potions'] = self.use_potions_var.get()
        self.config['exploration']['duration'] = self.duration_var.get() * 60
        
        # 更新按鍵
        for key, entry in self.key_entries.items():
            self.config['move_keys'][key] = entry.get()
        
        # 保存到檔案
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON檔案", "*.json")],
            initialfile="combat_config.json"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self._log(f"配置已保存: {filename}", "success")
            messagebox.showinfo("成功", "配置已保存!")
    
    def _load_config(self):
        """載入配置"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON檔案", "*.json"), ("所有檔案", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                # 更新介面
                self.window_title_var.set(self.config.get('window_title', ''))
                self.char_template_var.set(self.config.get('character_template', ''))
                self.auto_attack_var.set(self.config.get('combat', {}).get('auto_attack', True))
                self.attack_range_var.set(self.config.get('combat', {}).get('attack_range', 120))
                self.hp_threshold_var.set(self.config.get('combat', {}).get('hp_threshold', 0.5))
                self.use_potions_var.set(self.config.get('combat', {}).get('use_potions', True))
                self.duration_var.set(self.config.get('exploration', {}).get('duration', 300) // 60)
                
                # 更新按鍵
                for key, entry in self.key_entries.items():
                    entry.delete(0, tk.END)
                    entry.insert(0, self.config.get('move_keys', {}).get(key, ''))
                
                self._refresh_enemy_list()
                
                self._log(f"配置已載入: {filename}", "success")
                messagebox.showinfo("成功", "配置已載入!")
                
            except Exception as e:
                self._log(f"載入配置失敗: {e}", "error")
                messagebox.showerror("錯誤", f"載入配置失敗:\n{e}")
    
    def _load_last_config(self):
        """載入上次的配置"""
        try:
            if os.path.exists("last_combat_config.json"):
                with open("last_combat_config.json", 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                self._log("已載入上次配置", "info")
        except:
            pass
    
    def _start_combat(self):
        """開始自動戰鬥"""
        # 驗證配置
        if not self.window_title_var.get().strip():
            messagebox.showwarning("提示", "請先設定遊戲視窗標題!")
            return
        
        if not self.char_template_var.get().strip():
            messagebox.showwarning("提示", "請先設定角色識別模板!")
            return
        
        if not self.config['enemy_templates']:
            result = messagebox.askyesno(
                "提示",
                "尚未添加敵人模板,將只進行地圖探索。\n是否繼續?"
            )
            if not result:
                return
        
        # 更新配置
        self.config['window_title'] = self.window_title_var.get()
        self.config['combat']['auto_attack'] = self.auto_attack_var.get()
        self.config['combat']['attack_range'] = self.attack_range_var.get()
        self.config['combat']['hp_threshold'] = self.hp_threshold_var.get()
        self.config['combat']['use_potions'] = self.use_potions_var.get()
        self.config['exploration']['duration'] = self.duration_var.get() * 60
        
        for key, entry in self.key_entries.items():
            self.config['move_keys'][key] = entry.get()
        
        # 保存為上次配置
        with open("last_combat_config.json", 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        # 啟動
        self.is_running = True
        self.start_time = time.time()
        
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        self._update_status("running", "● 運行中")
        self._log("=" * 50, "info")
        self._log("🚀 開始自動戰鬥", "success")
        self._log("=" * 50, "info")
        
        # 在新線程中運行
        threading.Thread(target=self._run_combat_thread, daemon=True).start()
        
        # 啟動狀態更新
        self._update_stats_loop()
    
    def _stop_combat(self):
        """停止自動戰鬥"""
        self.is_running = False
        
        if self.nav_system:
            self.nav_system.stop()
        
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        self._update_status("stopped", "● 已停止")
        self._log("⏹️ 已停止運行", "warning")
    
    def _run_combat_thread(self):
        """運行戰鬥線程"""
        try:
            # 創建導航系統
            self._log("初始化導航系統...", "info")
            
            # 檢查是否有導航系統
            if not HAS_ADAPTIVE_NAV:
                self._log("❌ 自適應導航系統未載入（缺少 cv2 模組）", "error")
                messagebox.showerror("錯誤", "自適應導航系統未載入\n\n請安裝 OpenCV:\npip install opencv-python")
                self.root.after(0, self._stop_combat)
                return
            
            config = {
                'screen_scale': 1.0,
                'move_test_duration': 0.3,
                'move_keys': self.config['move_keys'],
                'exploration_priority': self.config['exploration']['priority']
            }
            
            self.nav_system = AdaptiveNavigationSystem(config=config)
            
            # 鎖定視窗
            self._log(f"鎖定遊戲視窗: {self.config['window_title']}", "info")
            success = self.nav_system.lock_game_window(self.config['window_title'])
            
            if not success:
                self._log("❌ 無法鎖定遊戲視窗!", "error")
                self.root.after(0, self._stop_combat)
                return
            
            # 設定角色模板
            self._log("設定角色識別模板...", "info")
            self.nav_system.set_character_template(self.config['character_template'])
            
            # 設定敵人模板
            for name, path in self.config['enemy_templates'].items():
                self._log(f"添加敵人模板: {name}", "info")
                self.nav_system.add_enemy_template(name, path)
            
            # 設定戰鬥配置
            self.nav_system.combat_config.update({
                'auto_attack': self.config['combat']['auto_attack'],
                'attack_range': self.config['combat']['attack_range'],
                'use_potions': self.config['combat']['use_potions'],
                'hp_potion_threshold': self.config['combat']['hp_threshold']
            })
            
            # 設定回調
            self.nav_system.set_callback('on_enemy_detected', self._on_enemy_detected)
            self.nav_system.set_callback('on_hp_low', self._on_hp_low)
            self.nav_system.set_callback('on_stuck', self._on_stuck)
            
            # 開始探索
            self._log("🗺️ 開始探索與戰鬥...", "success")
            self.nav_system.start()
            
            duration = self.config['exploration']['duration']
            auto_combat = self.config['combat']['auto_attack']
            
            self.nav_system.explore_surroundings(
                duration=duration,
                auto_combat=auto_combat
            )
            
            self._log("✅ 運行完成!", "success")
            
        except Exception as e:
            self._log(f"❌ 錯誤: {e}", "error")
            import traceback
            self._log(traceback.format_exc(), "error")
        
        finally:
            if self.nav_system:
                self.nav_system.stop()
            
            self.root.after(0, self._stop_combat)
    
    def _on_enemy_detected(self, enemy):
        """敵人偵測回調"""
        self._log(f"🎯 發現敵人: {enemy.enemy_type} at ({enemy.position.x}, {enemy.position.y})", "warning")
    
    def _on_hp_low(self, hp):
        """低血量回調"""
        self._log(f"⚠️ 血量過低: {hp*100:.0f}%", "error")
    
    def _on_stuck(self, position):
        """卡住回調"""
        self._log(f"🆘 角色卡住! 位置: ({position.x}, {position.y})", "warning")
    
    def _update_stats_loop(self):
        """更新統計循環"""
        if not self.is_running:
            return
        
        if self.nav_system:
            # 更新運行時間
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.stats_labels['runtime'].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # 更新統計
            stats = self.nav_system.stats
            self.stats_labels['explored'].config(text=str(stats.get('positions_explored', 0)))
            self.stats_labels['enemies'].config(text=str(stats.get('enemies_found', 0)))
            self.stats_labels['kills'].config(text=str(stats.get('enemies_killed', 0)))
            self.stats_labels['stuck'].config(text=str(stats.get('stuck_events', 0)))
        
        # 1秒後再次更新
        self.root.after(1000, self._update_stats_loop)
    
    def _update_status(self, status, text):
        """更新狀態"""
        colors = {
            'running': 'success',
            'stopped': 'secondary',
            'error': 'danger'
        }
        
        self.status_label.config(text=text, bootstyle=colors.get(status, 'secondary'))
    
    def _log(self, message, level="info"):
        """記錄日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            'info': '#61afef',
            'success': '#98c379',
            'warning': '#e5c07b',
            'error': '#e06c75'
        }
        
        self.log_text.insert("end", f"[{timestamp}] ", "timestamp")
        self.log_text.insert("end", f"{message}\n", level)
        
        # 配置標籤顏色
        self.log_text.tag_config("timestamp", foreground="#7d8590")
        for lvl, color in colors.items():
            self.log_text.tag_config(lvl, foreground=color)
        
        self.log_text.see("end")
    
    def _clear_log(self):
        """清空日誌"""
        self.log_text.delete(1.0, "end")
    
    def _export_log(self):
        """匯出日誌"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文字檔案", "*.txt")],
            initialfile=f"combat_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, "end"))
            
            messagebox.showinfo("成功", f"日誌已匯出至:\n{filename}")
    
    def _show_map_viewer(self):
        """顯示地圖查看器"""
        if not self.nav_system:
            messagebox.showinfo("提示", "請先開始運行後再查看地圖")
            return
        
        # TODO: 實作地圖查看器
        messagebox.showinfo("開發中", "地圖查看器功能開發中...")
    
    def _show_advanced_settings(self):
        """顯示進階設定"""
        # TODO: 實作進階設定
        messagebox.showinfo("開發中", "進階設定功能開發中...")
    
    def _on_closing(self):
        """視窗關閉時的處理"""
        if self.is_running:
            result = messagebox.askyesno(
                "確認",
                "系統正在運行中,確定要關閉嗎?\n(將自動停止並保存數據)"
            )
            if result:
                self._stop_combat()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """運行應用"""
        if self.is_standalone:
            self.root.mainloop()


# ==================== 主程式 ====================

if __name__ == "__main__":
    app = SmartAutoCombatUI()
    app.run()
