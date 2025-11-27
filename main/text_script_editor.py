# -*- coding: utf-8 -*-
"""
ChroLens 文字指令式腳本編輯器
將JSON事件轉換為簡單的文字指令格式
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
import json
import os
import re
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageGrab, ImageTk


class TextCommandEditor(tk.Toplevel):
    """文字指令式腳本編輯器"""
    
    def __init__(self, parent=None, script_path=None):
        super().__init__(parent)
        
        self.parent = parent
        self.script_path = script_path
        self.title("文字指令編輯器")
        self.geometry("800x700")  # 增加寬度 (原600 + 1/3 = 800)
        
        # 預設按鍵持續時間 (毫秒)
        self.default_key_duration = 50
        
        # 圖片辨識相關資料夾
        self.images_dir = self._get_images_dir()
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 自訂模組資料夾
        self.modules_dir = self._get_modules_dir()
        os.makedirs(self.modules_dir, exist_ok=True)
        
        # 圖片編號計數器（自動命名 pic01, pic02...）
        self._pic_counter = self._get_next_pic_number()
        
        self._create_ui()
        
        # ✅ 刷新腳本列表
        self._refresh_script_list()
        
        # 如果有指定腳本路徑，載入它
        if self.script_path:
            script_name = os.path.splitext(os.path.basename(self.script_path))[0]
            self.script_var.set(script_name)
            self._load_script()
        
        # 置頂顯示
        self.lift()
        self.focus_force()
    
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
        # 頂部工具列
        toolbar = tk.Frame(self, bg="#f0f0f0", height=50)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # 腳本選單
        tk.Label(toolbar, text="腳本:", bg="#f0f0f0", font=("Microsoft JhengHei", 10)).pack(side="left", padx=5)
        
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(toolbar, textvariable=self.script_var, width=20, state="readonly", font=("Microsoft JhengHei", 10))
        self.script_combo.pack(side="left", padx=5)
        self.script_combo.bind("<<ComboboxSelected>>", self._on_script_selected)
        self.script_combo.bind("<Button-1>", self._on_combo_click)
        
        # 自訂腳本輸入框（初始隱藏）
        self.custom_name_var = tk.StringVar()
        self.custom_name_entry = tk.Entry(toolbar, textvariable=self.custom_name_var, width=20, font=("Microsoft JhengHei", 10))
        self.confirm_custom_btn = tk.Button(toolbar, text="✓", command=self._create_custom_script, bg="#4CAF50", fg="white", font=("Microsoft JhengHei", 10, "bold"), padx=10, pady=3)
        
        # 操作按鈕
        buttons = [
            ("🔄 重新載入", self._load_script, "#2196F3"),
            ("💾 儲存", self._save_script, "#4CAF50"),
            ("▶️ 執行", self._execute_script, "#E91E63")
        ]
        for text, cmd, color in buttons:
            tk.Button(toolbar, text=text, command=cmd, bg=color, fg="white", font=("Microsoft JhengHei", 10, "bold"), padx=15, pady=5).pack(side="left", padx=5)
        
        # 第二排工具列
        toolbar2 = tk.Frame(self, bg="#f0f0f0", height=50)
        toolbar2.pack(fill="x", padx=5, pady=(0, 5))
        
        feature_buttons = [
            ("📷 圖片辨識", self._capture_and_recognize, "#9C27B0"),
            ("🧩 自訂模組", self._open_custom_module, "#607D8B")
        ]
        for text, cmd, color in feature_buttons:
            tk.Button(toolbar2, text=text, command=cmd, bg=color, fg="white", font=("Microsoft JhengHei", 10, "bold"), padx=15, pady=5).pack(side="left", padx=5)
        
        # 主編輯區（移除設定區和提示）區（移除設定區和提示）
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左側: 文字編輯器 (固定寬度,減少1/3)
        left_frame = tk.Frame(main_frame, width=450)  # 原約500,減少1/3約350
        left_frame.pack(side="left", fill="both", expand=False)
        left_frame.pack_propagate(False)
        
        tk.Label(
            left_frame,
            text="📝 文字指令 (可直接編輯)",
            font=("Microsoft JhengHei", 11, "bold")
        ).pack(anchor="w", pady=5)
        
        self.text_editor = scrolledtext.ScrolledText(
            left_frame,
            font=("Consolas", 10),
            wrap="none",
            bg="#ffffff",
            fg="#000000",
            insertbackground="#000000",
            selectbackground="#3399ff",
            undo=True,
            maxundo=-1
        )
        self.text_editor.pack(fill="both", expand=True)
        
        # ✅ 綁定右鍵選單
        self.text_editor.bind("<Button-3>", self._show_context_menu)
        
        # 右側: 預覽和說明 (自動擴展填滿剩餘空間)
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            right_frame,
            text="📖 指令格式說明",
            font=("Microsoft JhengHei", 11, "bold")
        ).pack(anchor="w", pady=5)
        
        help_text = """
📖 指令格式說明
━━━━━━━━━━━━━━━━━━━

💡 基本格式:
>動作, 延遲時間(ms), T=絕對時間

⌨️ 按鍵操作:
>按Y, 延遲50ms, T=0s100
>按Enter, 延遲50ms, T=0s200
>按Space, 延遲50ms, T=0s300

🖱️ 滑鼠操作:
>移動至(1586,1034), T=1s000
>左鍵點擊(1586,1034), T=1s200
>右鍵點擊(1586,1034), T=1s400
>雙擊(1586,1034), T=1s600

🎮 組合鍵:
>按下Ctrl, 延遲0ms, T=2s000
>按C, 延遲100ms, T=2s000
>放開Ctrl, 延遲0ms, T=2s100

🖼️ 圖片辨識 (pic命名):
>辨識>pic01, T=0s100
>移動至>pic01, T=1s000
>左鍵點擊>pic01, T=1s200
>右鍵點擊>pic02, T=2s000

💡 圖片命名規則:
• pic01, pic02, ... pic999
• 截圖時自動命名
• 可自行修改編號

⏱️ 時間格式:
• T=0s100 = 0.1秒
• T=17s500 = 17.5秒
• 延遲50ms

━━━━━━━━━━━━━━━━━━━
⚡ 快速技巧:
• 反白文字→右鍵→儲存/載入模組
• 複製貼上重複動作
• 直接修改時間和參數

⌨️ 按鍵持續時間建議:
• 快速點擊: 30-50ms
• 正常輸入: 50-100ms
• 長按動作: 100-500ms
"""
        
        help_label = tk.Text(
            right_frame,
            font=("Consolas", 9),
            wrap="word",
            bg="#f9f9f9",
            relief="flat",
            padx=10,
            pady=10
        )
        help_label.pack(fill="both", expand=True)
        help_label.insert("1.0", help_text)
        help_label.config(state="disabled")
        
        # 底部狀態列
        self.status_label = tk.Label(
            self,
            text="✅ 就緒",
            font=("Microsoft JhengHei", 9),
            bg="#e8f5e9",
            fg="#2e7d32",
            anchor="w",
            padx=10,
            pady=5
        )
        self.status_label.pack(fill="x", side="bottom")
    
    
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
        
        # 第一個選項固定為"自訂腳本"
        all_options = ["自訂腳本"] + sorted(display_scripts)
        self.script_combo['values'] = all_options
    
    def _on_script_selected(self, event):
        """處理腳本選擇事件"""
        selected = self.script_var.get()
        
        if selected == "自訂腳本":
            # 顯示輸入框和確認按鈕
            self.script_combo.pack_forget()
            self.custom_name_entry.pack(side="left", padx=5)
            self.confirm_custom_btn.pack(side="left", padx=5)
            self.custom_name_var.set("")
            self.custom_name_entry.focus()
        else:
            # 載入選中的腳本
            script_dir = os.path.join(os.getcwd(), "scripts")
            self.script_path = os.path.join(script_dir, selected + ".json")
            self._load_script()
    
    def _create_custom_script(self):
        """建立自訂腳本"""
        custom_name = self.custom_name_var.get().strip()
        
        if not custom_name:
            messagebox.showwarning("提示", "請輸入腳本名稱")
            return
        
        # 檢查檔名是否合法
        if any(char in custom_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            messagebox.showerror("錯誤", "檔名包含非法字元")
            return
        
        script_dir = os.path.join(os.getcwd(), "scripts")
        script_path = os.path.join(script_dir, custom_name + ".json")
        
        # 檢查檔案是否已存在
        if os.path.exists(script_path):
            messagebox.showwarning("提示", f"腳本「{custom_name}」已存在")
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
            self.text_editor.insert("1.0", f"# 新腳本: {custom_name}\n# 請開始編輯您的指令...\n")
            
            # 恢復下拉選單顯示
            self.custom_name_entry.pack_forget()
            self.confirm_custom_btn.pack_forget()
            # 找到腳本標籤後的位置重新插入combo
            toolbar = self.winfo_children()[0]  # 第一個Frame是toolbar
            script_label = toolbar.winfo_children()[0]  # 第一個子元件是"腳本:"標籤
            self.script_combo.pack(side="left", padx=5, after=script_label)
            
            # 刷新列表並選中新腳本
            self._refresh_script_list()
            self.script_var.set(custom_name)
            
            self.status_label.config(
                text=f"✅ 已建立新腳本: {custom_name}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
            
        except Exception as e:
            messagebox.showerror("錯誤", f"建立腳本失敗:\n{e}")
    
    def _load_script(self):
        """載入腳本並轉換為文字指令"""
        if not self.script_path or not os.path.exists(self.script_path):
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", "# 請從下拉選單選擇一個腳本來編輯\n")
            return
        
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 轉換為文字指令
            text_commands = self._json_to_text(data)
            
            # 顯示在編輯器中
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", text_commands)
            
            self.status_label.config(
                text=f"✅ 已載入: {os.path.basename(self.script_path)}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入腳本失敗:\n{e}")
            self.status_label.config(
                text=f"❌ 載入失敗: {e}",
                bg="#ffebee",
                fg="#c62828"
            )
    
    def _json_to_text(self, data: Dict) -> str:
        """將JSON事件轉換為文字指令"""
        events = data.get("events", [])
        lines = ["# ChroLens 文字指令腳本\n"]
        lines.append(f"# 預設按鍵持續時間: {self.default_key_duration}ms\n")
        lines.append("# ←←可用\"#\"來進行備註 \n")
        lines.append("# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
        
        # 記錄按下但未放開的按鍵
        pressed_keys = {}
        start_time = events[0]["time"] if events else 0
        
        for event in events:
            event_type = event.get("type")
            event_name = event.get("event")
            time_offset = event.get("time", 0) - start_time
            
            # 格式化時間
            time_str = self._format_time(time_offset)
            
            if event_type == "keyboard":
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
                    lines.append(f">移動至({x},{y}), T={time_str}\n")
                
                elif event_name == "down":
                    button = event.get("button", "left")
                    lines.append(f">按下{button}鍵({x},{y}), T={time_str}\n")
                
                elif event_name == "up":
                    button = event.get("button", "left")
                    lines.append(f">放開{button}鍵({x},{y}), T={time_str}\n")
            
            # 戰鬥指令
            elif event_type in ["start_combat", "find_and_attack", "loop_attack", "smart_combat", "set_combat_region", "pause_combat", "resume_combat", "stop_combat"]:
                combat_line = self._format_combat_event(event)
                if combat_line:
                    lines.append(f">{combat_line}, T={time_str}\n")
        
        # 處理未放開的按鍵
        if pressed_keys:
            lines.append("\n# ⚠️ 警告: 以下按鍵被按下但未放開\n")
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
        lines = text.split("\n")
        events = []
        labels = {}  # 標籤映射
        start_time = 1763365215.0  # 使用當前時間戳
        
        # 第一遍: 掃描標籤
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("#") and not line.startswith("# "):
                # 這是標籤定義
                label_name = line[1:].strip()
                labels[label_name] = i
        
        # 第二遍: 解析指令
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 跳過註釋和空行
            if not line or line.startswith("# "):
                i += 1
                continue
            
            # 標籤定義
            if line.startswith("#"):
                label_name = line[1:].strip()
                events.append({
                    "type": "label",
                    "name": label_name,
                    "time": start_time
                })
                i += 1
                continue
            
            # 解析指令
            if line.startswith(">"):
                try:
                    # 檢查是否為戰鬥指令
                    if any(keyword in line for keyword in ["啟動自動戰鬥", "尋找並攻擊", "循環攻擊", "智能戰鬥", "設定戰鬥區域", "暫停戰鬥", "恢復戰鬥", "停止戰鬥"]):
                        # 戰鬥指令處理
                        event = self._parse_combat_command_to_json(line, start_time)
                        if event:
                            events.append(event)
                        i += 1
                        continue
                    
                    # 檢查是否為圖片指令
                    if any(keyword in line for keyword in ["等待圖片", "點擊圖片", "如果存在"]):
                        # 圖片指令處理
                        event = self._parse_image_command_to_json(line, lines[i+1:i+6], start_time)
                        if event:
                            events.append(event)
                        i += 1
                        continue
                    
                    # 移除 ">" 並分割
                    parts = line[1:].split(",")
                    
                    if len(parts) >= 2:
                        action = parts[0].strip()
                        delay_str = parts[1].strip() if len(parts) > 1 else "0ms"
                        time_str = parts[2].strip() if len(parts) > 2 else "T=0s000"
                        
                        # 解析時間
                        abs_time = start_time + self._parse_time(time_str)
                        
                        # 解析延遲
                        delay_ms = int(re.search(r'\d+', delay_str).group()) if re.search(r'\d+', delay_str) else 0
                        delay_s = delay_ms / 1000.0
                        
                        # 解析動作類型
                        if action.startswith("按") and not "按下" in action:
                            # 按鍵操作（按 = 按下 + 放開）
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
                        
                        elif "放開" in action and not "點擊" in action:
                            # 單純放開按鍵
                            key = action.replace("放開", "").strip()
                            events.append({
                                "type": "keyboard",
                                "event": "up",
                                "name": key,
                                "time": abs_time
                            })
                        
                        elif "移動至" in action or "點擊" in action or ("按下" in action and "(" in action) or ("放開" in action and "(" in action):
                            # 滑鼠操作
                            coords = re.search(r'\((\d+),(\d+)\)', action)
                            if coords:
                                x, y = int(coords.group(1)), int(coords.group(2))
                                
                                if "移動至" in action:
                                    events.append({"type": "mouse", "event": "move", "x": x, "y": y, "time": abs_time, "in_target": True})
                                else:
                                    button = "right" if "右" in action else "middle" if "中" in action else "left"
                                    
                                    if "點擊" in action:
                                        events.append({"type": "mouse", "event": "down", "button": button, "x": x, "y": y, "time": abs_time, "in_target": True})
                                        events.append({"type": "mouse", "event": "up", "button": button, "x": x, "y": y, "time": abs_time + 0.05, "in_target": True})
                                    else:
                                        event_type = "down" if "按下" in action else "up"
                                        events.append({"type": "mouse", "event": event_type, "button": button, "x": x, "y": y, "time": abs_time, "in_target": True})
                
                except Exception as e:
                    print(f"解析行失敗: {line}\n錯誤: {e}")
                    i += 1
                    continue
            
            i += 1
        
        # 按時間排序
        events.sort(key=lambda x: x["time"])
        
        return {
            "events": events,
            "settings": {
                "speed": "100",
                "repeat": "1",
                "repeat_time": "00:00:00",
                "repeat_interval": "00:00:00",
                "random_interval": False,
                "script_hotkey": "",
                "script_actions": [],
                "window_info": None
            }
        }
    
    def _parse_image_command_to_json(self, command_line: str, next_lines: list, start_time: float) -> dict:
        """
        解析圖片指令並轉換為JSON格式
        :param command_line: 圖片指令行
        :param next_lines: 後續行 (用於讀取分支)
        :param start_time: 起始時間戳
        :return: JSON事件字典
        """
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
        
        return {"action": "unknown", "raw": action}
    
    def _save_script(self):
        """儲存文字指令回JSON格式"""
        if not self.script_path:
            messagebox.showwarning("警告", "沒有指定要儲存的腳本檔案")
            return
        
        try:
            # 獲取編輯器內容
            text_content = self.text_editor.get("1.0", "end-1c")
            
            # 轉換為JSON
            json_data = self._text_to_json(text_content)
            
            # 備份原檔案
            backup_path = self.script_path + ".backup"
            if os.path.exists(self.script_path):
                with open(self.script_path, 'r', encoding='utf-8') as f:
                    with open(backup_path, 'w', encoding='utf-8') as bf:
                        bf.write(f.read())
            
            # 儲存新檔案
            with open(self.script_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.status_label.config(
                text=f"✅ 已儲存: {os.path.basename(self.script_path)}",
                bg="#e8f5e9",
                fg="#2e7d32"
            )
            
            # ✅ 移除 messagebox.showinfo("成功", "腳本已儲存!")
            # 靜默儲存，不顯示訊息框
            
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存腳本失敗:\n{e}")
            self.status_label.config(
                text=f"❌ 儲存失敗: {e}",
                bg="#ffebee",
                fg="#c62828"
            )
    
    # ==================== 右鍵選單功能 ====================
    
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
                label="💾 儲存為自訂模組",
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
            context_menu.add_cascade(label="📥 插入自訂模組", menu=modules_menu)
        else:
            context_menu.add_command(
                label="📥 插入自訂模組 (無可用模組)",
                state="disabled"
            )
        
        context_menu.add_separator()
        context_menu.add_command(label="🧩 管理自訂模組", command=self._open_custom_module)
        
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
            messagebox.showwarning("提示", "請先選取（反白）要儲存的指令")
            return
        
        if not selected_text.strip():
            messagebox.showwarning("提示", "選取的內容為空")
            return
        
        # 詢問模組名稱
        module_name = simpledialog.askstring(
            "自訂模組名稱",
            "請輸入模組名稱："
        )
        
        if not module_name:
            return
        
        # 儲存模組
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(selected_text)
            
            messagebox.showinfo("成功", f"✅ 模組已儲存：{module_name}")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗：{e}")
    
    def _insert_module_from_menu(self, module_name):
        """從右鍵選單插入模組"""
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, content + "\n")
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取模組失敗：{e}")
    
    # ==================== 執行功能 ====================
    
    def _execute_script(self):
        """✅ 執行當前文字指令（先儲存再執行）"""
        if not self.parent:
            self.status_label.config(text="❌ 無法執行：找不到主程式")
            return
        
        # 1. 先儲存腳本
        if not self.script_path:
            messagebox.showwarning("提示", "請先建立或選擇一個腳本")
            return
        
        # 儲存當前內容
        self._save_script()
        
        # 2. 確認儲存成功後再執行
        if not os.path.exists(self.script_path):
            self.status_label.config(text="❌ 執行失敗：腳本未儲存")
            return
        
        try:
            # 3. 讀取儲存後的腳本
            with open(self.script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 4. 載入到主程式
            if hasattr(self.parent, 'events'):
                self.parent.events = data.get("events", [])
            else:
                self.status_label.config(text="❌ 主程式缺少events屬性")
                return
            
            if hasattr(self.parent, 'metadata'):
                self.parent.metadata = data.get("settings", {})
            
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
            
            # 6. 記錄視窗資訊（避免回放時彈窗）
            if hasattr(self.parent, 'target_hwnd') and self.parent.target_hwnd:
                from utils import get_window_info
                current_info = get_window_info(self.parent.target_hwnd)
                if current_info:
                    self.parent.recorded_window_info = current_info
            
            # 7. 執行腳本
            if hasattr(self.parent, 'play_script'):
                event_count = len(data.get("events", []))
                self.status_label.config(text=f"▶️ 執行中... ({event_count}筆事件)")
                
                # 記錄日誌
                if hasattr(self.parent, 'log'):
                    script_name = os.path.splitext(os.path.basename(self.script_path))[0]
                    self.parent.log(f"▶️ 從編輯器執行腳本：{script_name}（{event_count}筆事件）")
                
                # 觸發播放（不切換視窗）
                self.parent.play_script()
            else:
                self.status_label.config(text="❌ 主程式缺少play_script方法")
                
        except Exception as e:
            self.status_label.config(text=f"❌ 執行失敗：{e}")
            if hasattr(self.parent, 'log'):
                self.parent.log(f"❌ 編輯器執行失敗：{e}")
    
    # ==================== 圖片辨識功能 ====================
    
    def _capture_and_recognize(self):
        """截圖並儲存，插入辨識指令"""
        # 隱藏編輯器視窗
        self.withdraw()
        self.update()
        
        # 延遲500ms讓視窗完全隱藏
        self.after(500, self._do_capture)
    
    def _do_capture(self):
        """執行截圖"""
        try:
            # 創建截圖選取視窗
            capture_win = ScreenCaptureSelector(self, self._on_capture_complete)
            capture_win.wait_window()
        except Exception as e:
            messagebox.showerror("錯誤", f"截圖失敗：{e}")
            self.deiconify()
    
    def _on_capture_complete(self, image_region):
        """截圖完成回調"""
        self.deiconify()
        
        if image_region is None:
            return
        
        try:
            x1, y1, x2, y2 = image_region
            
            # 截取螢幕區域
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # ✅ 使用 pic 命名系統（pic01, pic02...）
            pic_name = f"pic{self._pic_counter:02d}"  # 格式化為兩位數，例如 pic01
            image_filename = f"{pic_name}.png"
            image_path = os.path.join(self.images_dir, image_filename)
            
            # 儲存圖片
            screenshot.save(image_path)
            
            # 詢問圖片辨識名稱（預設使用 pic 編號）
            display_name = simpledialog.askstring(
                "圖片辨識名稱",
                f"請輸入圖片的辨識名稱：\n(檔案：{image_filename})",
                initialvalue=pic_name
            )
            
            if not display_name:
                display_name = pic_name
            
            # 更新計數器
            self._pic_counter += 1
            
            # 插入辨識指令到編輯器（✅ 簡化格式，只用pic名稱）
            current_time = self._get_next_available_time()
            command = f">辨識>{display_name}, T={current_time}\n"
            
            # 在游標位置插入
            self.text_editor.insert(tk.INSERT, command)
            
            # 顯示預覽
            self._show_image_preview(screenshot, display_name, image_filename)
            
            messagebox.showinfo(
                "完成",
                f"✅ 圖片已儲存並插入指令\n\n"
                f"名稱：{display_name}\n"
                f"檔案：{image_filename}\n"
                f"路徑：{image_path}\n\n"
                f"可以配合使用：\n"
                f">移動至>{display_name}, T=...\n"
                f">左鍵點擊>{display_name}, T=..."
            )
            
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存圖片失敗：{e}")
    
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
    
    def _show_image_preview(self, image, display_name, filename):
        """顯示圖片預覽"""
        preview_win = tk.Toplevel(self)
        preview_win.title(f"圖片預覽 - {display_name}")
        preview_win.geometry("400x400")
        
        # 調整圖片大小以適應視窗
        img_copy = image.copy()
        img_copy.thumbnail((380, 320), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img_copy)
        
        label = tk.Label(preview_win, image=photo)
        label.image = photo  # 保持引用
        label.pack(pady=10)
        
        info_frame = tk.Frame(preview_win)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text=f"辨識名稱：{display_name}\n檔案名稱：{filename}",
            font=("Microsoft JhengHei", 10),
            justify="left"
        ).pack()
        
        tk.Button(
            preview_win,
            text="關閉",
            command=preview_win.destroy,
            bg="#607D8B",
            fg="white",
            font=("Microsoft JhengHei", 10, "bold"),
            padx=20,
            pady=5
        ).pack(pady=10)
    
    # ==================== 自訂模組功能 ====================
    
    def _open_custom_module(self):
        """開啟自訂模組管理視窗"""
        CustomModuleManager(self, self.text_editor, self.modules_dir)
    
    # ==================== 圖片辨識指令解析 ====================
    
    def _parse_image_command(self, line: str) -> Dict[str, Any]:
        """解析圖片辨識相關指令
        
        支援格式：
        >辨識>pic01, T=時間（新格式）
        >辨識>pic01>img_001.png, T=時間（舊格式，相容性）
        >移動至>pic01, T=時間
        >左鍵點擊>pic01, T=時間
        >右鍵點擊>pic02, T=時間
        """
        # 辨識指令（✅ 新格式：只有pic名稱）
        match = re.match(r'>辨識>([^>,]+),\s*T=(\d+)s(\d+)', line)
        if match:
            display_name = match.group(1).strip()
            seconds = int(match.group(2))
            millis = int(match.group(3))
            
            # 自動查找pic對應的圖片檔案
            image_file = self._find_pic_image_file(display_name)
            
            return {
                "type": "image_recognize",
                "display_name": display_name,
                "image_file": image_file,
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
        self.rect_id = None
        self.result = None
        
        # 全螢幕置頂
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        
        # 畫布
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)
        
        # 說明文字
        self.canvas.create_text(
            self.winfo_screenwidth() // 2,
            50,
            text="拖曳滑鼠選取要辨識的區域 (ESC取消)",
            font=("Microsoft JhengHei", 20, "bold"),
            fill="yellow"
        )
        
        # 綁定事件
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Escape>", lambda e: self._cancel())
        
        self.focus_force()
    
    def _on_press(self, event):
        """滑鼠按下"""
        self.start_x = event.x
        self.start_y = event.y
        
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=3
        )
    
    def _on_drag(self, event):
        """滑鼠拖曳"""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id,
                self.start_x, self.start_y,
                event.x, event.y
            )
    
    def _on_release(self, event):
        """滑鼠放開"""
        end_x = event.x
        end_y = event.y
        
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


class CustomModuleManager(tk.Toplevel):
    """自訂模組管理器"""
    
    def __init__(self, parent, text_editor, modules_dir):
        super().__init__(parent)
        
        self.parent_editor = text_editor
        self.modules_dir = modules_dir
        
        self.title("自訂模組管理")
        self.geometry("600x500")
        
        self._create_ui()
        self._load_modules()
        
        self.transient(parent)
        self.grab_set()
    
    def _create_ui(self):
        """創建UI"""
        # 頂部說明
        info_frame = tk.Frame(self, bg="#e3f2fd", relief="ridge", borderwidth=2)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text="💡 自訂模組：儲存常用指令組合，方便重複使用",
            font=("Microsoft JhengHei", 11, "bold"),
            bg="#e3f2fd"
        ).pack(pady=10)
        
        # 按鈕列
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(
            btn_frame,
            text="💾 儲存新模組",
            command=self._save_new_module,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft JhengHei", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="📥 插入選取的模組",
            command=self._insert_selected_module,
            bg="#2196F3",
            fg="white",
            font=("Microsoft JhengHei", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="🗑️ 刪除模組",
            command=self._delete_module,
            bg="#F44336",
            fg="white",
            font=("Microsoft JhengHei", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side="left", padx=5)
        
        # 模組列表
        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tk.Label(
            list_frame,
            text="已儲存的模組 (雙擊插入):",
            font=("Microsoft JhengHei", 10, "bold")
        ).pack(anchor="w", pady=5)
        
        # Listbox + Scrollbar
        list_container = tk.Frame(list_frame)
        list_container.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side="right", fill="y")
        
        self.module_listbox = tk.Listbox(
            list_container,
            font=("Microsoft JhengHei", 10),
            yscrollcommand=scrollbar.set
        )
        self.module_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.module_listbox.yview)
        
        self.module_listbox.bind("<Double-Button-1>", lambda e: self._insert_selected_module())
        
        # 預覽區
        preview_frame = tk.Frame(self)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        tk.Label(
            preview_frame,
            text="模組內容預覽:",
            font=("Microsoft JhengHei", 10, "bold")
        ).pack(anchor="w", pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            font=("Consolas", 9),
            height=8,
            wrap="none",
            state="disabled"
        )
        self.preview_text.pack(fill="both", expand=True)
        
        self.module_listbox.bind("<<ListboxSelect>>", self._on_module_selected)
    
    def _load_modules(self):
        """載入模組列表"""
        self.module_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.modules_dir):
            return
        
        modules = [f for f in os.listdir(self.modules_dir) if f.endswith('.txt')]
        for module in sorted(modules):
            display_name = os.path.splitext(module)[0]
            self.module_listbox.insert(tk.END, display_name)
    
    def _on_module_selected(self, event):
        """模組選取事件"""
        selection = self.module_listbox.curselection()
        if not selection:
            return
        
        module_name = self.module_listbox.get(selection[0])
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", content)
            self.preview_text.config(state="disabled")
        except Exception as e:
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", f"讀取失敗: {e}")
            self.preview_text.config(state="disabled")
    
    def _save_new_module(self):
        """儲存新模組"""
        # 獲取編輯器中選取的文字
        try:
            selected_text = self.parent_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            messagebox.showwarning("提示", "請先在編輯器中選取(反白)要儲存的指令")
            return
        
        if not selected_text.strip():
            messagebox.showwarning("提示", "選取的內容為空")
            return
        
        # 詢問模組名稱
        module_name = simpledialog.askstring(
            "模組名稱",
            "請輸入自訂模組的名稱："
        )
        
        if not module_name:
            return
        
        # 儲存模組
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(selected_text)
            
            messagebox.showinfo("成功", f"模組已儲存：{module_name}")
            self._load_modules()
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗：{e}")
    
    def _insert_selected_module(self):
        """插入選取的模組到編輯器"""
        selection = self.module_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "請先選取一個模組")
            return
        
        module_name = self.module_listbox.get(selection[0])
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在游標位置插入
            self.parent_editor.insert(tk.INSERT, content + "\n")
            
            messagebox.showinfo("完成", f"已插入模組：{module_name}")
            self.destroy()
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取模組失敗：{e}")
    
    def _delete_module(self):
        """刪除模組"""
        selection = self.module_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "請先選取要刪除的模組")
            return
        
        module_name = self.module_listbox.get(selection[0])
        
        if not messagebox.askyesno("確認", f"確定要刪除模組「{module_name}」嗎？"):
            return
        
        module_path = os.path.join(self.modules_dir, f"{module_name}.txt")
        
        try:
            os.remove(module_path)
            messagebox.showinfo("完成", f"已刪除模組：{module_name}")
            self._load_modules()
            
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("錯誤", f"刪除失敗：{e}")


# 測試用
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # 測試用腳本路徑
    test_script = r"c:\Users\Lucien\Documents\GitHub\scripts\2025_1117_1540_20.json"
    
    editor = TextCommandEditor(root, test_script)
    root.mainloop()

