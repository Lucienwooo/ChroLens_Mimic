"""
視覺化戰鬥腳本編輯器 - 可拖曳排序、直接編輯的戰鬥動作管理器
"""

import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os

class CombatActionEditor(tb.Toplevel):
    """戰鬥動作編輯器 - 類似腳本編輯器的可視化界面"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        self.title("戰鬥腳本編輯器 - ChroLens Mimic")
        self.geometry("1000x700")
        
        # 設定為模態視窗
        self.transient(parent)
        self.grab_set()
        
        # 戰鬥動作列表
        self.actions = []
        self.selected_index = None
        
        # 動作類型定義
        self.action_types = {
            "尋找並攻擊": {"icon": "🎯", "color": "#FF5722"},
            "使用技能": {"icon": "✨", "color": "#9C27B0"},
            "等待": {"icon": "⏱️", "color": "#607D8B"},
            "移動到位置": {"icon": "🚶", "color": "#2196F3"},
            "點擊位置": {"icon": "👆", "color": "#4CAF50"},
            "循環攻擊": {"icon": "🔄", "color": "#FF9800"},
            "條件判斷": {"icon": "❓", "color": "#00BCD4"},
            "撿取物品": {"icon": "💎", "color": "#FFC107"},
        }
        
        self.create_widgets()
        
        # 置中顯示
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')
    
    def create_widgets(self):
        """創建UI元件"""
        
        # ==================== 頂部工具列 ====================
        toolbar = tb.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=10)
        
        # 標題
        title_label = tb.Label(toolbar, text="⚔️ 戰鬥腳本編輯器", font=("", 16, "bold"))
        title_label.pack(side="left")
        
        # 右側按鈕
        btn_frame = tb.Frame(toolbar)
        btn_frame.pack(side="right")
        
        tb.Button(btn_frame, text="💾 儲存", command=self.save_script, 
                 bootstyle=SUCCESS, width=10).pack(side="left", padx=2)
        tb.Button(btn_frame, text="📂 載入", command=self.load_script, 
                 bootstyle=INFO, width=10).pack(side="left", padx=2)
        tb.Button(btn_frame, text="🗑️ 清空", command=self.clear_all, 
                 bootstyle=DANGER, width=10).pack(side="left", padx=2)
        
        # ==================== 主要內容區 ====================
        main_frame = tb.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左側：動作列表 (60%)
        left_frame = tb.LabelFrame(main_frame, text="戰鬥動作序列", bootstyle=PRIMARY, padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 動作列表工具列
        list_toolbar = tb.Frame(left_frame)
        list_toolbar.pack(fill="x", pady=(0, 5))
        
        tb.Label(list_toolbar, text="動作總數:", font=("", 10)).pack(side="left", padx=5)
        self.action_count_label = tb.Label(list_toolbar, text="0", font=("", 10, "bold"), foreground="blue")
        self.action_count_label.pack(side="left")
        
        # 動作列表 (使用 Listbox)
        list_container = tb.Frame(left_frame)
        list_container.pack(fill="both", expand=True)
        
        # 使用 Text widget 來顯示動作，更容易實現拖曳和顏色
        self.action_text = tk.Text(list_container, font=("Consolas", 10), wrap="none")
        scrollbar_y = tb.Scrollbar(list_container, orient="vertical", command=self.action_text.yview)
        scrollbar_x = tb.Scrollbar(left_frame, orient="horizontal", command=self.action_text.xview)
        
        self.action_text.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.action_text.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        
        # 綁定點擊事件
        self.action_text.bind("<Button-1>", self.on_action_click)
        self.action_text.bind("<Double-Button-1>", self.edit_action)
        
        # 動作列表控制按鈕
        list_control_frame = tb.Frame(left_frame)
        list_control_frame.pack(fill="x", pady=(5, 0))
        
        tb.Button(list_control_frame, text="⬆️ 上移", command=self.move_up, 
                 bootstyle=SECONDARY, width=8).pack(side="left", padx=2)
        tb.Button(list_control_frame, text="⬇️ 下移", command=self.move_down, 
                 bootstyle=SECONDARY, width=8).pack(side="left", padx=2)
        tb.Button(list_control_frame, text="✏️ 編輯", command=self.edit_action, 
                 bootstyle=INFO, width=8).pack(side="left", padx=2)
        tb.Button(list_control_frame, text="🧪 測試", command=self.test_action, 
                 bootstyle=SUCCESS, width=8).pack(side="left", padx=2)
        tb.Button(list_control_frame, text="❌ 刪除", command=self.delete_action, 
                 bootstyle=DANGER, width=8).pack(side="left", padx=2)
        tb.Button(list_control_frame, text="📋 複製", command=self.duplicate_action, 
                 bootstyle=WARNING, width=8).pack(side="left", padx=2)
        
        # 右側：動作工具箱 (40%)
        right_frame = tb.LabelFrame(main_frame, text="動作工具箱", bootstyle=SUCCESS, padding=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # 說明文字
        info_label = tb.Label(right_frame, text="點擊下方按鈕來新增動作", 
                             font=("", 10), foreground="gray")
        info_label.pack(pady=5)
        
        # 創建動作按鈕
        for action_type, config in self.action_types.items():
            btn = tb.Button(
                right_frame,
                text=f"{config['icon']} {action_type}",
                command=lambda at=action_type: self.add_action(at),
                bootstyle=INFO,
                width=20
            )
            btn.pack(pady=3, fill="x")
        
        # 底部：快速預覽
        preview_frame = tb.LabelFrame(right_frame, text="動作預覽", bootstyle=WARNING, padding=10)
        preview_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        self.preview_text = tk.Text(preview_frame, height=8, font=("Consolas", 9), wrap="word")
        preview_scroll = tb.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.config(yscrollcommand=preview_scroll.set)
        
        self.preview_text.pack(side="left", fill="both", expand=True)
        preview_scroll.pack(side="right", fill="y")
        
        # ==================== 底部狀態列 ====================
        status_frame = tb.Frame(self)
        status_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.status_label = tb.Label(status_frame, text="就緒", font=("", 9), foreground="green")
        self.status_label.pack(side="left")
        
        tb.Button(status_frame, text="關閉", command=self.destroy, 
                 bootstyle=SECONDARY, width=10).pack(side="right")
    
    def add_action(self, action_type):
        """新增動作"""
        # 根據動作類型建立對話框
        action_data = self.show_action_dialog(action_type)
        
        if action_data:
            self.actions.append({
                "type": action_type,
                "data": action_data
            })
            self.refresh_action_list()
            self.status_label.config(text=f"已新增動作: {action_type}", foreground="green")
    
    def show_action_dialog(self, action_type, existing_data=None):
        """顯示動作編輯對話框"""
        dialog = tb.Toplevel(self)
        dialog.title(f"設定 - {action_type}")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # 置中
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        
        result = {"confirmed": False, "data": {}}
        
        # 標題
        title_frame = tb.Frame(dialog)
        title_frame.pack(fill="x", padx=20, pady=10)
        
        icon = self.action_types[action_type]["icon"]
        tb.Label(title_frame, text=f"{icon} {action_type}", 
                font=("", 14, "bold")).pack()
        
        # 內容區
        content_frame = tb.Frame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        fields = {}
        
        # 根據動作類型顯示不同的輸入欄位
        if action_type == "尋找並攻擊":
            tb.Label(content_frame, text="敵人圖片檔名:").grid(row=0, column=0, sticky="w", pady=5)
            fields["image"] = tb.Entry(content_frame, width=30)
            fields["image"].grid(row=0, column=1, pady=5)
            if existing_data:
                fields["image"].insert(0, existing_data.get("image", ""))
            
            tb.Label(content_frame, text="移動時間(秒):").grid(row=1, column=0, sticky="w", pady=5)
            fields["duration"] = tb.Spinbox(content_frame, from_=0.1, to=5.0, increment=0.1, width=28)
            fields["duration"].set(existing_data.get("duration", 0.3) if existing_data else 0.3)
            fields["duration"].grid(row=1, column=1, pady=5)
            
            tb.Label(content_frame, text="攻擊鍵:").grid(row=2, column=0, sticky="w", pady=5)
            fields["attack_key"] = tb.Entry(content_frame, width=30)
            fields["attack_key"].grid(row=2, column=1, pady=5)
            if existing_data:
                fields["attack_key"].insert(0, existing_data.get("attack_key", "1"))
            else:
                fields["attack_key"].insert(0, "1")
        
        elif action_type == "使用技能":
            tb.Label(content_frame, text="技能鍵:").grid(row=0, column=0, sticky="w", pady=5)
            fields["key"] = tb.Entry(content_frame, width=30)
            fields["key"].grid(row=0, column=1, pady=5)
            if existing_data:
                fields["key"].insert(0, existing_data.get("key", ""))
            
            tb.Label(content_frame, text="冷卻時間(秒):").grid(row=1, column=0, sticky="w", pady=5)
            fields["cooldown"] = tb.Spinbox(content_frame, from_=0, to=300, increment=1, width=28)
            fields["cooldown"].set(existing_data.get("cooldown", 0) if existing_data else 0)
            fields["cooldown"].grid(row=1, column=1, pady=5)
        
        elif action_type == "等待":
            tb.Label(content_frame, text="等待時間(秒):").grid(row=0, column=0, sticky="w", pady=5)
            fields["duration"] = tb.Spinbox(content_frame, from_=0.1, to=60, increment=0.5, width=28)
            fields["duration"].set(existing_data.get("duration", 1.0) if existing_data else 1.0)
            fields["duration"].grid(row=0, column=1, pady=5)
        
        elif action_type == "移動到位置":
            tb.Label(content_frame, text="X 座標:").grid(row=0, column=0, sticky="w", pady=5)
            fields["x"] = tb.Entry(content_frame, width=30)
            fields["x"].grid(row=0, column=1, pady=5)
            if existing_data:
                fields["x"].insert(0, existing_data.get("x", ""))
            
            tb.Label(content_frame, text="Y 座標:").grid(row=1, column=0, sticky="w", pady=5)
            fields["y"] = tb.Entry(content_frame, width=30)
            fields["y"].grid(row=1, column=1, pady=5)
            if existing_data:
                fields["y"].insert(0, existing_data.get("y", ""))
            
            tb.Label(content_frame, text="移動時間(秒):").grid(row=2, column=0, sticky="w", pady=5)
            fields["duration"] = tb.Spinbox(content_frame, from_=0.1, to=5.0, increment=0.1, width=28)
            fields["duration"].set(existing_data.get("duration", 0.5) if existing_data else 0.5)
            fields["duration"].grid(row=2, column=1, pady=5)
        
        elif action_type == "點擊位置":
            tb.Label(content_frame, text="X 座標:").grid(row=0, column=0, sticky="w", pady=5)
            fields["x"] = tb.Entry(content_frame, width=30)
            fields["x"].grid(row=0, column=1, pady=5)
            if existing_data:
                fields["x"].insert(0, existing_data.get("x", ""))
            
            tb.Label(content_frame, text="Y 座標:").grid(row=1, column=0, sticky="w", pady=5)
            fields["y"] = tb.Entry(content_frame, width=30)
            fields["y"].grid(row=1, column=1, pady=5)
            if existing_data:
                fields["y"].insert(0, existing_data.get("y", ""))
            
            tb.Label(content_frame, text="按鈕:").grid(row=2, column=0, sticky="w", pady=5)
            fields["button"] = tb.Combobox(content_frame, values=["left", "right", "middle"], 
                                          state="readonly", width=28)
            fields["button"].set(existing_data.get("button", "left") if existing_data else "left")
            fields["button"].grid(row=2, column=1, pady=5)
        
        elif action_type == "循環攻擊":
            tb.Label(content_frame, text="敵人圖片列表 (逗號分隔):").grid(row=0, column=0, sticky="w", pady=5)
            fields["images"] = tb.Entry(content_frame, width=30)
            fields["images"].grid(row=0, column=1, pady=5)
            if existing_data:
                fields["images"].insert(0, existing_data.get("images", ""))
            
            tb.Label(content_frame, text="攻擊鍵:").grid(row=1, column=0, sticky="w", pady=5)
            fields["attack_key"] = tb.Entry(content_frame, width=30)
            fields["attack_key"].grid(row=1, column=1, pady=5)
            if existing_data:
                fields["attack_key"].insert(0, existing_data.get("attack_key", "1"))
            else:
                fields["attack_key"].insert(0, "1")
            
            tb.Label(content_frame, text="掃描間隔(秒):").grid(row=2, column=0, sticky="w", pady=5)
            fields["interval"] = tb.Spinbox(content_frame, from_=0.5, to=10, increment=0.5, width=28)
            fields["interval"].set(existing_data.get("interval", 1.0) if existing_data else 1.0)
            fields["interval"].grid(row=2, column=1, pady=5)
        
        elif action_type == "條件判斷":
            tb.Label(content_frame, text="條件圖片:").grid(row=0, column=0, sticky="w", pady=5)
            fields["image"] = tb.Entry(content_frame, width=30)
            fields["image"].grid(row=0, column=1, pady=5)
            if existing_data:
                fields["image"].insert(0, existing_data.get("image", ""))
            
            tb.Label(content_frame, text="超時時間(秒):").grid(row=1, column=0, sticky="w", pady=5)
            fields["timeout"] = tb.Spinbox(content_frame, from_=1, to=300, increment=1, width=28)
            fields["timeout"].set(existing_data.get("timeout", 10) if existing_data else 10)
            fields["timeout"].grid(row=1, column=1, pady=5)
        
        elif action_type == "撿取物品":
            tb.Label(content_frame, text="物品圖片:").grid(row=0, column=0, sticky="w", pady=5)
            fields["image"] = tb.Entry(content_frame, width=30)
            fields["image"].grid(row=0, column=1, pady=5)
            if existing_data:
                fields["image"].insert(0, existing_data.get("image", ""))
            
            tb.Label(content_frame, text="掃描範圍(像素):").grid(row=1, column=0, sticky="w", pady=5)
            fields["range"] = tb.Spinbox(content_frame, from_=50, to=500, increment=50, width=28)
            fields["range"].set(existing_data.get("range", 200) if existing_data else 200)
            fields["range"].grid(row=1, column=1, pady=5)
        
        # 按鈕區
        button_frame = tb.Frame(dialog)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        def confirm():
            # 收集資料
            for key, widget in fields.items():
                if isinstance(widget, (tb.Entry, tb.Combobox)):
                    result["data"][key] = widget.get()
                elif isinstance(widget, tb.Spinbox):
                    result["data"][key] = float(widget.get())
            result["confirmed"] = True
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        tb.Button(button_frame, text="✓ 確定", command=confirm, 
                 bootstyle=SUCCESS, width=15).pack(side="left", padx=5, expand=True, fill="x")
        tb.Button(button_frame, text="✗ 取消", command=cancel, 
                 bootstyle=SECONDARY, width=15).pack(side="right", padx=5, expand=True, fill="x")
        
        # 等待對話框關閉
        self.wait_window(dialog)
        
        return result["data"] if result["confirmed"] else None
    
    def refresh_action_list(self):
        """刷新動作列表顯示"""
        self.action_text.config(state="normal")
        self.action_text.delete(1.0, "end")
        
        for idx, action in enumerate(self.actions, 1):
            action_type = action["type"]
            action_data = action["data"]
            icon = self.action_types[action_type]["icon"]
            
            # 格式化動作描述
            desc = self.format_action_description(action_type, action_data)
            
            line = f"{idx:3d}. {icon} {action_type}: {desc}\n"
            self.action_text.insert("end", line)
        
        self.action_text.config(state="disabled")
        self.action_count_label.config(text=str(len(self.actions)))
        
        # 更新預覽
        self.update_preview()
    
    def format_action_description(self, action_type, data):
        """格式化動作描述"""
        if action_type == "尋找並攻擊":
            return f"圖片=[{data.get('image', '')}], 移動={data.get('duration', 0.3)}s, 攻擊鍵={data.get('attack_key', '1')}"
        elif action_type == "使用技能":
            return f"按鍵=[{data.get('key', '')}], 冷卻={data.get('cooldown', 0)}s"
        elif action_type == "等待":
            return f"時間={data.get('duration', 1.0)}秒"
        elif action_type == "移動到位置":
            return f"座標=({data.get('x', '')}, {data.get('y', '')}), 時間={data.get('duration', 0.5)}s"
        elif action_type == "點擊位置":
            return f"座標=({data.get('x', '')}, {data.get('y', '')}), 按鈕={data.get('button', 'left')}"
        elif action_type == "循環攻擊":
            return f"圖片=[{data.get('images', '')}], 攻擊鍵={data.get('attack_key', '1')}, 間隔={data.get('interval', 1.0)}s"
        elif action_type == "條件判斷":
            return f"圖片=[{data.get('image', '')}], 超時={data.get('timeout', 10)}s"
        elif action_type == "撿取物品":
            return f"圖片=[{data.get('image', '')}], 範圍={data.get('range', 200)}px"
        return ""
    
    def update_preview(self):
        """更新預覽區域"""
        self.preview_text.config(state="normal")
        self.preview_text.delete(1.0, "end")
        
        if self.selected_index is not None and 0 <= self.selected_index < len(self.actions):
            action = self.actions[self.selected_index]
            preview = f"動作類型: {action['type']}\n\n"
            preview += "參數:\n"
            for key, value in action['data'].items():
                preview += f"  {key}: {value}\n"
            self.preview_text.insert("end", preview)
        else:
            self.preview_text.insert("end", "請選擇一個動作來查看詳細資訊")
        
        self.preview_text.config(state="disabled")
    
    def on_action_click(self, event):
        """處理動作點擊"""
        # 取得點擊的行號
        index = self.action_text.index("@%s,%s" % (event.x, event.y))
        line_num = int(index.split('.')[0]) - 1
        
        if 0 <= line_num < len(self.actions):
            self.selected_index = line_num
            self.update_preview()
            self.status_label.config(text=f"已選擇動作 #{line_num + 1}", foreground="blue")
    
    def edit_action(self, event=None):
        """編輯選中的動作"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "請先選擇要編輯的動作")
            return
        
        action = self.actions[self.selected_index]
        new_data = self.show_action_dialog(action["type"], action["data"])
        
        if new_data:
            self.actions[self.selected_index]["data"] = new_data
            self.refresh_action_list()
            self.status_label.config(text=f"已更新動作 #{self.selected_index + 1}", foreground="green")
    
    def delete_action(self):
        """刪除選中的動作"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "請先選擇要刪除的動作")
            return
        
        if messagebox.askyesno("確認刪除", f"確定要刪除動作 #{self.selected_index + 1} 嗎？"):
            del self.actions[self.selected_index]
            self.selected_index = None
            self.refresh_action_list()
            self.status_label.config(text="已刪除動作", foreground="orange")
    
    def move_up(self):
        """將選中的動作上移"""
        if self.selected_index is None or self.selected_index == 0:
            return
        
        # 交換位置
        self.actions[self.selected_index], self.actions[self.selected_index - 1] = \
            self.actions[self.selected_index - 1], self.actions[self.selected_index]
        
        self.selected_index -= 1
        self.refresh_action_list()
        self.status_label.config(text="已上移動作", foreground="blue")
    
    def move_down(self):
        """將選中的動作下移"""
        if self.selected_index is None or self.selected_index >= len(self.actions) - 1:
            return
        
        # 交換位置
        self.actions[self.selected_index], self.actions[self.selected_index + 1] = \
            self.actions[self.selected_index + 1], self.actions[self.selected_index]
        
        self.selected_index += 1
        self.refresh_action_list()
        self.status_label.config(text="已下移動作", foreground="blue")
    
    def duplicate_action(self):
        """複製選中的動作"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "請先選擇要複製的動作")
            return
        
        # 深拷貝動作
        import copy
        new_action = copy.deepcopy(self.actions[self.selected_index])
        self.actions.insert(self.selected_index + 1, new_action)
        self.refresh_action_list()
        self.status_label.config(text="已複製動作", foreground="green")
    
    def clear_all(self):
        """清空所有動作"""
        if not self.actions:
            return
        
        if messagebox.askyesno("確認清空", "確定要清空所有動作嗎？"):
            self.actions.clear()
            self.selected_index = None
            self.refresh_action_list()
            self.status_label.config(text="已清空所有動作", foreground="red")
    
    def save_script(self):
        """儲存腳本"""
        if not self.actions:
            messagebox.showwarning("警告", "沒有動作可以儲存")
            return
        
        from tkinter import filedialog
        
        filepath = filedialog.asksaveasfilename(
            title="儲存戰鬥腳本",
            defaultextension=".json",
            filetypes=[("JSON檔案", "*.json"), ("所有檔案", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "scripts")
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({"actions": self.actions}, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"腳本已儲存至:\n{filepath}")
                self.status_label.config(text="腳本已儲存", foreground="green")
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存失敗:\n{e}")
    
    def load_script(self):
        """載入腳本"""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            title="載入戰鬥腳本",
            filetypes=[("JSON檔案", "*.json"), ("所有檔案", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "scripts")
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.actions = data.get("actions", [])
                    self.selected_index = None
                    self.refresh_action_list()
                messagebox.showinfo("成功", f"腳本已載入:\n{filepath}")
                self.status_label.config(text="腳本已載入", foreground="green")
            except Exception as e:
                messagebox.showerror("錯誤", f"載入失敗:\n{e}")
    
    def test_action(self):
        """測試當前選中的動作"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "請先選擇要測試的動作")
            return
        
        action = self.actions[self.selected_index]
        
        # 確認測試
        if not messagebox.askyesno("確認測試", 
            f"即將執行動作:\n\n{self.action_types[action['type']]['icon']} {action['type']}\n{self.format_action_description(action['type'], action['data'])}\n\n確定要執行嗎？"):
            return
        
        # 倒數計時
        countdown_window = tb.Toplevel(self)
        countdown_window.title("準備測試")
        countdown_window.geometry("300x150")
        countdown_window.transient(self)
        countdown_window.grab_set()
        
        # 置中
        countdown_window.update_idletasks()
        x = (countdown_window.winfo_screenwidth() // 2) - (countdown_window.winfo_width() // 2)
        y = (countdown_window.winfo_screenheight() // 2) - (countdown_window.winfo_height() // 2)
        countdown_window.geometry(f'+{x}+{y}')
        
        countdown_label = tb.Label(countdown_window, text="3", font=("", 48, "bold"))
        countdown_label.pack(expand=True)
        
        info_label = tb.Label(countdown_window, text="準備執行動作...", font=("", 10))
        info_label.pack(pady=10)
        
        def countdown(n):
            if n > 0:
                countdown_label.config(text=str(n))
                countdown_window.after(1000, lambda: countdown(n - 1))
            else:
                countdown_window.destroy()
                self.execute_single_action(action)
        
        countdown(3)
    
    def execute_single_action(self, action):
        """執行單個戰鬥動作"""
        import pyautogui
        import time
        
        action_type = action["type"]
        data = action["data"]
        
        self.status_label.config(text=f"正在執行: {action_type}...", foreground="orange")
        self.update()
        
        try:
            if action_type == "尋找並攻擊":
                # 尋找並攻擊圖片
                image_name = data.get("image", "")
                duration = float(data.get("duration", 0.3))
                attack_key = data.get("attack_key", "1")
                
                # 尋找圖片
                image_path = self._find_image_path(image_name)
                if image_path:
                    try:
                        location = pyautogui.locateOnScreen(image_path, confidence=0.8)
                        if location:
                            center = pyautogui.center(location)
                            pyautogui.moveTo(center.x, center.y, duration=duration)
                            time.sleep(0.1)
                            pyautogui.press(attack_key)
                            self.status_label.config(text=f"✓ 找到並攻擊目標", foreground="green")
                        else:
                            self.status_label.config(text=f"✗ 未找到目標圖片", foreground="red")
                    except Exception as e:
                        self.status_label.config(text=f"✗ 圖片識別失敗: {e}", foreground="red")
                else:
                    self.status_label.config(text=f"✗ 找不到圖片檔案", foreground="red")
            
            elif action_type == "使用技能":
                # 按技能鍵
                key = data.get("key", "")
                cooldown = float(data.get("cooldown", 0))
                
                pyautogui.press(key)
                self.status_label.config(text=f"✓ 已按下技能鍵 [{key}]", foreground="green")
                
                if cooldown > 0:
                    time.sleep(cooldown)
            
            elif action_type == "等待":
                # 等待
                duration = float(data.get("duration", 1.0))
                time.sleep(duration)
                self.status_label.config(text=f"✓ 等待 {duration} 秒完成", foreground="green")
            
            elif action_type == "移動到位置":
                # 移動滑鼠
                x = int(data.get("x", 0))
                y = int(data.get("y", 0))
                duration = float(data.get("duration", 0.5))
                
                pyautogui.moveTo(x, y, duration=duration)
                self.status_label.config(text=f"✓ 已移動到 ({x}, {y})", foreground="green")
            
            elif action_type == "點擊位置":
                # 點擊座標
                x = int(data.get("x", 0))
                y = int(data.get("y", 0))
                button = data.get("button", "left")
                
                pyautogui.click(x, y, button=button)
                self.status_label.config(text=f"✓ 已點擊 ({x}, {y})", foreground="green")
            
            elif action_type == "循環攻擊":
                # 循環攻擊 (只執行一次作為測試)
                images = data.get("images", "").split(",")
                attack_key = data.get("attack_key", "1")
                
                found = False
                for image_name in images:
                    image_name = image_name.strip()
                    image_path = self._find_image_path(image_name)
                    if image_path:
                        try:
                            location = pyautogui.locateOnScreen(image_path, confidence=0.8)
                            if location:
                                center = pyautogui.center(location)
                                pyautogui.moveTo(center.x, center.y, duration=0.3)
                                time.sleep(0.1)
                                pyautogui.press(attack_key)
                                self.status_label.config(text=f"✓ 找到並攻擊 [{image_name}]", foreground="green")
                                found = True
                                break
                        except:
                            pass
                
                if not found:
                    self.status_label.config(text=f"✗ 未找到任何目標", foreground="red")
            
            elif action_type == "條件判斷":
                # 檢查圖片是否存在
                image_name = data.get("image", "")
                image_path = self._find_image_path(image_name)
                
                if image_path:
                    try:
                        location = pyautogui.locateOnScreen(image_path, confidence=0.8)
                        if location:
                            self.status_label.config(text=f"✓ 條件滿足: 找到圖片", foreground="green")
                        else:
                            self.status_label.config(text=f"✗ 條件不滿足: 未找到圖片", foreground="orange")
                    except:
                        self.status_label.config(text=f"✗ 圖片識別失敗", foreground="red")
                else:
                    self.status_label.config(text=f"✗ 找不到圖片檔案", foreground="red")
            
            elif action_type == "撿取物品":
                # 撿取物品 (尋找並點擊)
                image_name = data.get("image", "")
                image_path = self._find_image_path(image_name)
                
                if image_path:
                    try:
                        location = pyautogui.locateOnScreen(image_path, confidence=0.8)
                        if location:
                            center = pyautogui.center(location)
                            pyautogui.click(center.x, center.y)
                            self.status_label.config(text=f"✓ 已點擊物品", foreground="green")
                        else:
                            self.status_label.config(text=f"✗ 未找到物品", foreground="red")
                    except:
                        self.status_label.config(text=f"✗ 物品識別失敗", foreground="red")
                else:
                    self.status_label.config(text=f"✗ 找不到圖片檔案", foreground="red")
            
        except Exception as e:
            messagebox.showerror("執行錯誤", f"執行動作時發生錯誤:\n{e}")
            self.status_label.config(text=f"✗ 執行失敗: {e}", foreground="red")
    
    def _find_image_path(self, image_name):
        """尋找圖片檔案路徑"""
        if not image_name:
            return None
        
        # 可能的圖片路徑
        base_dir = os.path.dirname(__file__)
        possible_paths = [
            os.path.join(base_dir, "images", "templates", image_name),
            os.path.join(base_dir, "images", image_name),
            os.path.join(base_dir, "pic", image_name),
            image_name  # 絕對路徑
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None


if __name__ == "__main__":
    # 測試視窗
    root = tb.Window(themename="superhero")
    root.title("測試")
    root.geometry("400x300")
    
    def open_editor():
        CombatActionEditor(root)
    
    btn = tb.Button(root, text="開啟戰鬥腳本編輯器", command=open_editor, bootstyle=SUCCESS)
    btn.pack(expand=True)
    
    root.mainloop()
