"""
自動戰鬥控制視窗 - 管理和控制自動戰鬥系統
"""

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
import os
import threading
from auto_combat_system import AutoCombatSystem
from image_recognition import ImageRecognition

# ✅ 導入響應式佈局模組
try:
    from responsive_layout import make_window_responsive
except ImportError:
    def make_window_responsive(window, *args, **kwargs):
        window.resizable(True, True)
        return window

class CombatControlWindow(tb.Toplevel):
    """自動戰鬥控制視窗"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.title("自動戰鬥控制 - ChroLens Mimic")
        self.geometry("700x800")
        
        # 設定為模態視窗並保持在最上層
        self.transient(parent)
        self.grab_set()
        
        # ✅ 啟用響應式佈局 (Responsive Layout)
        make_window_responsive(self, min_width=700, min_height=800, max_screen_ratio=0.9)
        
        # 設定視窗置中
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
        # 自動戰鬥系統
        self.combat_system = None
        self.image_recognizer = ImageRecognition()
        
        # 戰鬥統計
        self.stats = {
            'enemies_found': 0,
            'attacks_made': 0,
            'skills_used': 0,
            'items_looted': 0,
            'errors': 0
        }
        
        self.create_widgets()
        self.update_stats_display()
        
    def create_widgets(self):
        """創建UI元件"""
        
        # ==================== 標題區 ====================
        title_frame = tb.Frame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = tb.Label(title_frame, text="⚔️ 自動戰鬥控制", font=("", 16, "bold"))
        title_label.pack(side="left")
        
        # 狀態指示器
        self.status_label = tb.Label(title_frame, text="● 未啟動", font=("", 12), foreground="gray")
        self.status_label.pack(side="right", padx=10)
        
        # ==================== 敵人模板區 ====================
        enemy_frame = tb.LabelFrame(self, text="敵人模板設定", bootstyle=PRIMARY, padding=10)
        enemy_frame.pack(fill="x", padx=10, pady=5)
        
        # 模板列表
        list_frame = tb.Frame(enemy_frame)
        list_frame.pack(fill="both", expand=True)
        
        tb.Label(list_frame, text="已選擇的敵人圖片:", font=("", 10)).pack(anchor="w", pady=5)
        
        # 使用Listbox顯示模板
        list_container = tb.Frame(list_frame)
        list_container.pack(fill="both", expand=True)
        
        self.enemy_listbox = tk.Listbox(list_container, height=5, font=("", 10))
        scrollbar = tb.Scrollbar(list_container, orient="vertical", command=self.enemy_listbox.yview)
        self.enemy_listbox.config(yscrollcommand=scrollbar.set)
        
        self.enemy_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 按鈕列
        btn_frame = tb.Frame(enemy_frame)
        btn_frame.pack(fill="x", pady=5)
        
        tb.Button(btn_frame, text="➕ 新增模板", command=self.add_enemy_template, 
                 bootstyle=SUCCESS, width=12).pack(side="left", padx=2)
        tb.Button(btn_frame, text="➖ 移除模板", command=self.remove_enemy_template, 
                 bootstyle=DANGER, width=12).pack(side="left", padx=2)
        tb.Button(btn_frame, text="🖼️ 圖片管理", command=self.open_image_manager, 
                 bootstyle=INFO, width=12).pack(side="left", padx=2)
        tb.Button(btn_frame, text="📝 腳本編輯器", command=self.open_action_editor, 
                 bootstyle=WARNING, width=12).pack(side="left", padx=2)
        
        # ==================== 攻擊設定區 ====================
        attack_frame = tb.LabelFrame(self, text="攻擊設定", bootstyle=INFO, padding=10)
        attack_frame.pack(fill="x", padx=10, pady=5)
        
        # 攻擊鍵
        key_frame = tb.Frame(attack_frame)
        key_frame.pack(fill="x", pady=3)
        
        tb.Label(key_frame, text="攻擊鍵:", width=15, anchor="w").pack(side="left")
        self.attack_key_var = tb.StringVar(value="1")
        attack_entry = tb.Entry(key_frame, textvariable=self.attack_key_var, width=10)
        attack_entry.pack(side="left", padx=5)
        tb.Label(key_frame, text="(普通攻擊按鍵)", foreground="gray").pack(side="left")
        
        # 技能鍵
        skill_frame = tb.Frame(attack_frame)
        skill_frame.pack(fill="x", pady=3)
        
        tb.Label(skill_frame, text="技能鍵:", width=15, anchor="w").pack(side="left")
        self.skill_keys_var = tb.StringVar(value="")
        skill_entry = tb.Entry(skill_frame, textvariable=self.skill_keys_var, width=30)
        skill_entry.pack(side="left", padx=5)
        tb.Label(skill_frame, text="(用逗號分隔,例: Q,W,E)", foreground="gray").pack(side="left")
        
        # 移動時間
        move_frame = tb.Frame(attack_frame)
        move_frame.pack(fill="x", pady=3)
        
        tb.Label(move_frame, text="移動時間:", width=15, anchor="w").pack(side="left")
        self.move_duration_var = tb.DoubleVar(value=0.3)
        move_spinbox = tb.Spinbox(move_frame, from_=0.1, to=2.0, increment=0.1, 
                                   textvariable=self.move_duration_var, width=10)
        move_spinbox.pack(side="left", padx=5)
        tb.Label(move_frame, text="秒 (游標移動速度)", foreground="gray").pack(side="left")
        
        # 掃描間隔
        scan_frame = tb.Frame(attack_frame)
        scan_frame.pack(fill="x", pady=3)
        
        tb.Label(scan_frame, text="掃描間隔:", width=15, anchor="w").pack(side="left")
        self.scan_interval_var = tb.DoubleVar(value=1.0)
        scan_spinbox = tb.Spinbox(scan_frame, from_=0.5, to=5.0, increment=0.5,
                                  textvariable=self.scan_interval_var, width=10)
        scan_spinbox.pack(side="left", padx=5)
        tb.Label(scan_frame, text="秒 (偵測敵人頻率)", foreground="gray").pack(side="left")
        
        # ==================== 進階設定區 ====================
        advanced_frame = tb.LabelFrame(self, text="進階設定", bootstyle=WARNING, padding=10)
        advanced_frame.pack(fill="x", padx=10, pady=5)
        
        # 自動撿取
        self.auto_loot_var = tb.BooleanVar(value=False)
        loot_check = tb.Checkbutton(advanced_frame, text="啟用自動撿取", 
                                    variable=self.auto_loot_var, bootstyle="round-toggle")
        loot_check.pack(anchor="w", pady=3)
        
        # 血量監控
        self.hp_monitor_var = tb.BooleanVar(value=False)
        hp_check = tb.Checkbutton(advanced_frame, text="啟用血量監控", 
                                  variable=self.hp_monitor_var, bootstyle="round-toggle")
        hp_check.pack(anchor="w", pady=3)
        
        # 死亡偵測
        self.death_detect_var = tb.BooleanVar(value=False)
        death_check = tb.Checkbutton(advanced_frame, text="啟用死亡偵測", 
                                     variable=self.death_detect_var, bootstyle="round-toggle")
        death_check.pack(anchor="w", pady=3)
        
        # ==================== 控制按鈕區 ====================
        control_frame = tb.Frame(self)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_start = tb.Button(control_frame, text="▶️ 開始戰鬥", 
                                   command=self.start_combat, bootstyle=SUCCESS, width=20)
        self.btn_start.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_pause = tb.Button(control_frame, text="⏸️ 暫停", 
                                   command=self.pause_combat, bootstyle=WARNING, width=20, state="disabled")
        self.btn_pause.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_stop = tb.Button(control_frame, text="⏹️ 停止", 
                                  command=self.stop_combat, bootstyle=DANGER, width=20, state="disabled")
        self.btn_stop.pack(side="left", padx=5, expand=True, fill="x")
        
        # ==================== 統計資訊區 ====================
        stats_frame = tb.LabelFrame(self, text="戰鬥統計", bootstyle=SUCCESS, padding=10)
        stats_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 建立統計標籤
        self.stats_labels = {}
        stats_items = [
            ('enemies_found', '發現敵人', '👾'),
            ('attacks_made', '攻擊次數', '⚔️'),
            ('skills_used', '技能使用', '✨'),
            ('items_looted', '撿取物品', '💎'),
            ('errors', '錯誤次數', '❌')
        ]
        
        for key, label_text, icon in stats_items:
            stat_frame = tb.Frame(stats_frame)
            stat_frame.pack(fill="x", pady=2)
            
            tb.Label(stat_frame, text=f"{icon} {label_text}:", width=15, anchor="w", 
                    font=("", 10)).pack(side="left")
            
            label = tb.Label(stat_frame, text="0", font=("", 10, "bold"), foreground="blue")
            label.pack(side="left", padx=10)
            
            self.stats_labels[key] = label
        
        # ==================== 日誌區 ====================
        log_frame = tb.LabelFrame(self, text="戰鬥日誌", bootstyle=SECONDARY, padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 文字框
        log_container = tb.Frame(log_frame)
        log_container.pack(fill="both", expand=True)
        
        self.log_text = tb.Text(log_container, height=8, font=("Consolas", 9), wrap="word")
        log_scrollbar = tb.Scrollbar(log_container, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # 底部按鈕
        bottom_frame = tb.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=10)
        
        tb.Button(bottom_frame, text="清除統計", command=self.reset_stats, 
                 bootstyle=SECONDARY, width=15).pack(side="left", padx=5)
        tb.Button(bottom_frame, text="清除日誌", command=self.clear_log, 
                 bootstyle=SECONDARY, width=15).pack(side="left", padx=5)
        tb.Button(bottom_frame, text="關閉", command=self.close_window, 
                 bootstyle=SECONDARY, width=15).pack(side="right", padx=5)
    
    def add_enemy_template(self):
        """新增敵人模板"""
        from tkinter import filedialog
        
        image_folder = os.path.join(os.path.dirname(__file__), "combat_images")
        
        filepaths = filedialog.askopenfilenames(
            title="選擇敵人圖片",
            initialdir=image_folder if os.path.exists(image_folder) else None,
            filetypes=[
                ("圖片檔案", "*.png *.jpg *.jpeg *.bmp"),
                ("所有檔案", "*.*")
            ]
        )
        
        if filepaths:
            for filepath in filepaths:
                filename = os.path.basename(filepath)
                # 檢查是否已存在
                if filename not in self.enemy_listbox.get(0, 'end'):
                    self.enemy_listbox.insert('end', filename)
            self.log(f"已新增 {len(filepaths)} 個敵人模板")
    
    def remove_enemy_template(self):
        """移除敵人模板"""
        selection = self.enemy_listbox.curselection()
        if selection:
            for idx in reversed(selection):
                removed = self.enemy_listbox.get(idx)
                self.enemy_listbox.delete(idx)
                self.log(f"已移除模板: {removed}")
        else:
            messagebox.showwarning("警告", "請先選擇要移除的模板")
    
    def open_image_manager(self):
        """打開圖片管理器"""
        try:
            from image_manager import ImageManager
            ImageManager(self)
        except Exception as e:
            self.log(f"開啟圖片管理失敗: {e}")
            messagebox.showerror("錯誤", f"開啟圖片管理失敗:\n{e}")
    
    def open_action_editor(self):
        """打開戰鬥動作編輯器"""
        try:
            from combat_action_editor import CombatActionEditor
            CombatActionEditor(self)
            self.log("📝 已開啟戰鬥腳本編輯器")
        except Exception as e:
            self.log(f"開啟腳本編輯器失敗: {e}")
            messagebox.showerror("錯誤", f"開啟腳本編輯器失敗:\n{e}")
    
    def start_combat(self):
        """開始戰鬥"""
        # 檢查是否有敵人模板
        enemy_templates = list(self.enemy_listbox.get(0, 'end'))
        if not enemy_templates:
            messagebox.showwarning("警告", "請先新增至少一個敵人模板")
            return
        
        # 取得技能鍵
        skill_keys_str = self.skill_keys_var.get().strip()
        skill_keys = [k.strip() for k in skill_keys_str.split(',') if k.strip()] if skill_keys_str else []
        
        # 建立自動戰鬥系統
        try:
            self.combat_system = AutoCombatSystem(
                image_recognizer=self.image_recognizer,
                enemy_templates=enemy_templates,
                attack_key=self.attack_key_var.get(),
                skill_keys=skill_keys,
                move_duration=self.move_duration_var.get(),
                scan_interval=self.scan_interval_var.get()
            )
            
            # 設定回調
            self.combat_system.on_enemy_found = self.on_enemy_found_callback
            self.combat_system.on_attack = self.on_attack_callback
            self.combat_system.on_skill_used = self.on_skill_used_callback
            self.combat_system.on_loot = self.on_loot_callback
            self.combat_system.on_error = self.on_error_callback
            
            # 啟動戰鬥
            self.combat_system.start()
            
            # 更新UI
            self.status_label.config(text="● 戰鬥中", foreground="green")
            self.btn_start.config(state="disabled")
            self.btn_pause.config(state="normal")
            self.btn_stop.config(state="normal")
            
            self.log("⚔️ 自動戰鬥已啟動!")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"啟動戰鬥失敗:\n{e}")
            self.log(f"❌ 啟動失敗: {e}")
    
    def pause_combat(self):
        """暫停/恢復戰鬥"""
        if not self.combat_system:
            return
        
        if self.combat_system.is_paused:
            self.combat_system.resume()
            self.status_label.config(text="● 戰鬥中", foreground="green")
            self.btn_pause.config(text="⏸️ 暫停")
            self.log("▶️ 戰鬥已恢復")
        else:
            self.combat_system.pause()
            self.status_label.config(text="● 已暫停", foreground="orange")
            self.btn_pause.config(text="▶️ 恢復")
            self.log("⏸️ 戰鬥已暫停")
    
    def stop_combat(self):
        """停止戰鬥"""
        if self.combat_system:
            self.combat_system.stop()
            self.combat_system = None
        
        # 更新UI
        self.status_label.config(text="● 未啟動", foreground="gray")
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled", text="⏸️ 暫停")
        self.btn_stop.config(state="disabled")
        
        self.log("⏹️ 自動戰鬥已停止")
    
    def reset_stats(self):
        """重置統計"""
        for key in self.stats:
            self.stats[key] = 0
        self.update_stats_display()
        self.log("📊 統計已重置")
    
    def clear_log(self):
        """清除日誌"""
        self.log_text.delete(1.0, 'end')
    
    def update_stats_display(self):
        """更新統計顯示"""
        for key, label in self.stats_labels.items():
            label.config(text=str(self.stats[key]))
    
    def log(self, message):
        """記錄日誌"""
        self.log_text.insert('end', message + '\n')
        self.log_text.see('end')
    
    # ==================== 回調函數 ====================
    def on_enemy_found_callback(self, template):
        self.stats['enemies_found'] += 1
        self.update_stats_display()
        self.log(f"👾 發現敵人: {template}")
    
    def on_attack_callback(self):
        self.stats['attacks_made'] += 1
        self.update_stats_display()
    
    def on_skill_used_callback(self, skill_key):
        self.stats['skills_used'] += 1
        self.update_stats_display()
        self.log(f"✨ 使用技能: {skill_key}")
    
    def on_loot_callback(self):
        self.stats['items_looted'] += 1
        self.update_stats_display()
        self.log(f"💎 撿取物品")
    
    def on_error_callback(self, error_msg):
        self.stats['errors'] += 1
        self.update_stats_display()
        self.log(f"❌ 錯誤: {error_msg}")
    
    def close_window(self):
        """關閉視窗"""
        if self.combat_system and self.combat_system.is_running:
            response = messagebox.askyesno(
                "確認",
                "戰鬥正在進行中，確定要關閉嗎？"
            )
            if not response:
                return
            self.stop_combat()
        
        self.destroy()


# 添加缺少的import
import tkinter as tk


if __name__ == "__main__":
    # 測試視窗
    root = tb.Window(themename="superhero")
    root.title("測試")
    root.geometry("400x300")
    
    def open_combat():
        CombatControlWindow(root)
    
    btn = tb.Button(root, text="開啟自動戰鬥", command=open_combat)
    btn.pack(pady=50)
    
    root.mainloop()
