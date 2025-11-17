# -*- coding: utf-8 -*-
"""
ChroLens 文字指令式腳本編輯器
將JSON事件轉換為簡單的文字指令格式
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import re
from typing import List, Dict, Any, Tuple


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
        
        self._create_ui()
        self._load_script()
        
        # 置頂顯示
        self.lift()
        self.focus_force()
    
    def _create_ui(self):
        """創建UI"""
        # 頂部工具列
        toolbar = tk.Frame(self, bg="#f0f0f0", height=50)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        tk.Label(
            toolbar, 
            text="💡 格式說明: >動作, 延遲時間(ms), T=絕對時間",
            font=("Microsoft JhengHei", 10),
            bg="#f0f0f0"
        ).pack(side="left", padx=10)
        
        tk.Button(
            toolbar,
            text="💾 儲存",
            command=self._save_script,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft JhengHei", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side="right", padx=5)
        
        tk.Button(
            toolbar,
            text="🔄 重新載入",
            command=self._load_script,
            bg="#2196F3",
            fg="white",
            font=("Microsoft JhengHei", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side="right", padx=5)
        
        tk.Button(
            toolbar,
            text="📂 載入",
            command=self._show_script_list,
            bg="#FF9800",
            fg="white",
            font=("Microsoft JhengHei", 10, "bold"),
            padx=15,
            pady=5
        ).pack(side="right", padx=5)
        
        # 設定區
        settings_frame = tk.Frame(self)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            settings_frame,
            text="預設按鍵持續時間(ms):",
            font=("Microsoft JhengHei", 9)
        ).pack(side="left", padx=5)
        
        self.duration_var = tk.StringVar(value="50")
        duration_entry = tk.Entry(
            settings_frame,
            textvariable=self.duration_var,
            width=8,
            font=("Consolas", 10)
        )
        duration_entry.pack(side="left", padx=5)
        
        tk.Label(
            settings_frame,
            text="(建議: 快速點擊30-50ms, 正常輸入50-100ms, 長按100ms+)",
            font=("Microsoft JhengHei", 8),
            fg="#666"
        ).pack(side="left", padx=5)
        
        # 主編輯區
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
        
        # 右側: 預覽和說明 (自動擴展填滿剩餘空間)
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            right_frame,
            text="📖 指令格式說明",
            font=("Microsoft JhengHei", 11, "bold")
        ).pack(anchor="w", pady=5)
        
        help_text = """
格式範例:
━━━━━━━━━━━━━━━━━━━
>按Y, 延遲50ms, T=17s500
>按4, 延遲50ms, T=17s600
>按Enter, 延遲50ms, T=17s800

滑鼠操作:
>移動至(1586,1034), T=15s140
>左鍵點擊(1586,1034), T=15s672

組合鍵:
>按下Ctrl, 延遲0ms, T=5s000
>按下C, 延遲100ms, T=5s000
>放開C, 延遲0ms, T=5s100
>放開Ctrl, 延遲0ms, T=5s100

🖼️ 圖片識別指令:
>等待圖片[按鈕.png], 超時30s
  成功→跳到 #標籤A
  失敗→跳到 #標籤B

>點擊圖片[圖示.png], 信心度0.8
  成功→繼續
  失敗→重試3次, 間隔1s

>如果存在[錯誤圖.png]
  執行→跳到 #錯誤處理

#標籤A
>按Y, 延遲50ms

━━━━━━━━━━━━━━━━━━━
⚡ 快速技巧:
• 複製貼上重複動作
• 直接修改按鍵名稱
• 調整延遲時間
• 修改絕對時間

⏱️ 時間格式:
• T=17s500 = 17.5秒
• T=1m30s = 1分30秒
• 延遲50ms = 0.05秒

⌨️ 按鍵持續建議:
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
    
    def _show_script_list(self):
        """顯示腳本列表對話框"""
        # 獲取腳本目錄
        if hasattr(self.parent, 'script_dir'):
            script_dir = self.parent.script_dir
        else:
            script_dir = os.path.join(os.path.dirname(__file__), "scripts")
        
        if not os.path.exists(script_dir):
            messagebox.showwarning("警告", f"腳本目錄不存在:\n{script_dir}")
            return
        
        # 創建對話框
        dialog = tk.Toplevel(self)
        dialog.title("選擇腳本")
        dialog.geometry("400x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # 居中顯示
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # 標題
        tk.Label(
            dialog,
            text="📂 腳本列表 (雙擊載入)",
            font=("Microsoft JhengHei", 12, "bold"),
            bg="#f5f5f5",
            pady=10
        ).pack(fill="x")
        
        # 列表框架
        list_frame = tk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 捲軸
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # 列表框
        listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Microsoft JhengHei", 10),
            selectmode=tk.SINGLE,
            activestyle="none"
        )
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        # 載入腳本列表
        script_files = []
        try:
            for file in os.listdir(script_dir):
                if file.endswith('.json'):
                    script_name = file[:-5]  # 移除 .json
                    listbox.insert(tk.END, script_name)
                    script_files.append(os.path.join(script_dir, file))
        except Exception as e:
            messagebox.showerror("錯誤", f"讀取腳本目錄失敗:\n{e}")
            dialog.destroy()
            return
        
        if not script_files:
            tk.Label(
                dialog,
                text="沒有找到任何腳本",
                font=("Microsoft JhengHei", 9),
                fg="#999"
            ).pack(pady=20)
        
        # 雙擊事件處理
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                self.script_path = script_files[index]
                self._load_script()
                dialog.destroy()
        
        listbox.bind("<Double-Button-1>", on_double_click)
        
        # 提示
        tk.Label(
            dialog,
            text="💡 雙擊腳本名稱即可載入",
            font=("Microsoft JhengHei", 9),
            fg="#666",
            bg="#f9f9f9",
            pady=8
        ).pack(fill="x", side="bottom")
    
    def _load_script(self):
        """載入腳本並轉換為文字指令"""
        if not self.script_path or not os.path.exists(self.script_path):
            self.text_editor.delete("1.0", "end")
            self.text_editor.insert("1.0", "# 請使用「📂 載入」按鈕選擇一個腳本來編輯\n")
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
                        if action.startswith("按"):
                            # 按鍵操作
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
                        
                        elif "移動至" in action:
                            # 滑鼠移動
                            coords = re.search(r'\((\d+),(\d+)\)', action)
                            if coords:
                                x, y = int(coords.group(1)), int(coords.group(2))
                                events.append({
                                    "type": "mouse",
                                    "event": "move",
                                    "x": x,
                                    "y": y,
                                    "time": abs_time,
                                    "in_target": True
                                })
                        
                        elif "點擊" in action or "按下" in action or "放開" in action:
                            # 滑鼠點擊
                            coords = re.search(r'\((\d+),(\d+)\)', action)
                            button = "left"
                            if "右" in action:
                                button = "right"
                            elif "中" in action:
                                button = "middle"
                            
                            if coords:
                                x, y = int(coords.group(1)), int(coords.group(2))
                                
                                if "按下" in action:
                                    event_type = "down"
                                elif "放開" in action:
                                    event_type = "up"
                                else:  # 點擊 = 按下 + 放開
                                    events.append({
                                        "type": "mouse",
                                        "event": "down",
                                        "button": button,
                                        "x": x,
                                        "y": y,
                                        "time": abs_time,
                                        "in_target": True
                                    })
                                    event_type = "up"
                                    abs_time += 0.05  # 點擊持續50ms
                                
                                events.append({
                                    "type": "mouse",
                                    "event": event_type,
                                    "button": button,
                                    "x": x,
                                    "y": y,
                                    "time": abs_time,
                                    "in_target": True
                                })
                
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
            
            messagebox.showinfo("成功", "腳本已儲存!")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存腳本失敗:\n{e}")
            self.status_label.config(
                text=f"❌ 儲存失敗: {e}",
                bg="#ffebee",
                fg="#c62828"
            )


# 測試用
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    # 測試用腳本路徑
    test_script = r"c:\Users\Lucien\Documents\GitHub\scripts\2025_1117_1540_20.json"
    
    editor = TextCommandEditor(root, test_script)
    root.mainloop()
