# ScriptEditorWindow 的所有方法（供參考和整合使用）
# 這個檔案包含了所有需要添加到 ScriptEditorWindow 類別的方法

# 將這些方法複製到 test2.6.py 中的 ScriptEditorWindow 類別中

def on_tree_select(self, event=None):
    """處理列表選擇事件"""
    selected = self.tree.selection()
    if selected:
        item = selected[0]
        values = self.tree.item(item, "values")
        self.selected_index = int(values[0]) - 1
        self.update_info_tab()
    else:
        self.selected_index = None

def show_context_menu(self, event):
    """顯示右鍵選單"""
    # 選擇點擊的項目
    item = self.tree.identify_row(event.y)
    if item:
        self.tree.selection_set(item)
        
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏️ 編輯", command=self.edit_selected)
        menu.add_command(label="📋 複製", command=self.copy_selected)
        menu.add_separator()
        menu.add_command(label="🗑 刪除", command=self.delete_selected)
        menu.add_separator()
        menu.add_command(label="⬆️ 上移", command=self.move_up)
        menu.add_command(label="⬇️ 下移", command=self.move_down)
        
        menu.post(event.x_root, event.y_root)

def update_tree(self):
    """更新 Treeview（帶圖示）"""
    self.tree.delete(*self.tree.get_children())
    
    # 指令圖示映射
    icon_map = {
        "move_to": "🖱️",
        "click": "👆",
        "double_click": "👆👆",
        "right_click": "👉",
        "type_text": "⌨️",
        "press_key": "🔘",
        "delay": "⏱️",
        "log": "📝",
        "": "❓"
    }
    
    for idx, act in enumerate(self.actions, 1):
        command = act.get("command", "")
        icon = icon_map.get(command, "❓")
        
        self.tree.insert("", "end", values=(
            idx,
            icon,
            command or "(空白)",
            act.get("params", ""),
            act.get("delay", "0")
        ))
    
    # 更新標題計數
    if hasattr(self, 'status_label'):
        self.status_label.config(text=f"共 {len(self.actions)} 個動作")

def update_preview(self):
    """更新腳本預覽"""
    if not hasattr(self, 'preview_text'):
        return
    
    script = self._actions_to_script()
    
    self.preview_text.config(state="normal")
    self.preview_text.delete("1.0", "end")
    
    # 添加標頭註解
    header = "# ChroLens 腳本預覽\n# 自動生成於動作列表\n\n"
    self.preview_text.insert("1.0", header)
    self.preview_text.insert("end", script)
    
    self.preview_text.config(state="disabled")

def update_info_tab(self):
    """更新詳細資訊標籤"""
    if not hasattr(self, 'info_text'):
        return
    
    self.info_text.config(state="normal")
    self.info_text.delete("1.0", "end")
    
    if self.selected_index is not None and 0 <= self.selected_index < len(self.actions):
        act = self.actions[self.selected_index]
        
        info = f"""選中的動作詳細資訊
{'=' * 40}

序號：{self.selected_index + 1}
指令：{act.get('command', '(空白)')}
參數：{act.get('params', '(無)')}
延遲：{act.get('delay', '0')} 毫秒

說明：
{self._get_command_description(act.get('command', ''))}

{'=' * 40}
"""
        self.info_text.insert("1.0", info)
    else:
        self.info_text.insert("1.0", "請選擇一個動作以查看詳細資訊")
    
    self.info_text.config(state="disabled")

def _get_command_description(self, command):
    """取得指令說明"""
    descriptions = {
        "move_to": "移動滑鼠游標到指定的螢幕座標位置。\n參數格式: x, y\n範例: 100, 200",
        "click": "執行滑鼠左鍵點擊。\n可選參數: x, y（點擊前先移動到該位置）",
        "double_click": "執行滑鼠左鍵雙擊。\n可選參數: x, y",
        "right_click": "執行滑鼠右鍵點擊。\n可選參數: x, y",
        "type_text": "輸入文字內容。\n參數: 要輸入的文字\n範例: Hello World",
        "press_key": "按下指定的按鍵。\n參數: 按鍵名稱\n範例: enter, tab, ctrl",
        "delay": "暫停執行指定的時間。\n參數: 毫秒數\n範例: 1000（等待1秒）",
        "log": "在輸出區顯示訊息。\n參數: 訊息內容\n範例: 開始執行",
        "": "空白動作，不執行任何操作"
    }
    return descriptions.get(command, "未知指令")

def add_action(self):
    """新增動作（開啟編輯對話框）"""
    self.edit_action_dialog(-1, {
        "command": "",
        "params": "",
        "delay": "0"
    })

def edit_selected(self):
    """編輯選中的動作"""
    if self.selected_index is not None and 0 <= self.selected_index < len(self.actions):
        self.edit_action_dialog(self.selected_index, self.actions[self.selected_index].copy())

def delete_selected(self):
    """刪除選中的動作"""
    selected = self.tree.selection()
    if not selected:
        return
    
    # 從後往前刪除以保持索引正確
    indices = [int(self.tree.item(item, "values")[0]) - 1 for item in selected]
    
    # 確認刪除
    if len(indices) > 1:
        result = tk.messagebox.askyesno("確認刪除", f"確定要刪除選中的 {len(indices)} 個動作嗎？")
        if not result:
            return
    
    for idx in sorted(indices, reverse=True):
        if 0 <= idx < len(self.actions):
            self.actions.pop(idx)
    
    self.update_tree()
    self.update_preview()
    self.status_label.config(text=f"已刪除 {len(indices)} 個動作")

def copy_selected(self):
    """複製選中的動作"""
    if self.selected_index is not None and 0 <= self.selected_index < len(self.actions):
        act_copy = self.actions[self.selected_index].copy()
        self.actions.insert(self.selected_index + 1, act_copy)
        self.update_tree()
        self.update_preview()
        self.status_label.config(text="已複製動作")

def move_up(self):
    """將選中的動作上移"""
    if self.selected_index is not None and self.selected_index > 0:
        # 交換位置
        self.actions[self.selected_index], self.actions[self.selected_index - 1] = \
            self.actions[self.selected_index - 1], self.actions[self.selected_index]
        
        self.selected_index -= 1
        self.update_tree()
        self.update_preview()
        
        # 重新選中
        children = self.tree.get_children()
        if self.selected_index < len(children):
            self.tree.selection_set(children[self.selected_index])

def move_down(self):
    """將選中的動作下移"""
    if self.selected_index is not None and self.selected_index < len(self.actions) - 1:
        # 交換位置
        self.actions[self.selected_index], self.actions[self.selected_index + 1] = \
            self.actions[self.selected_index + 1], self.actions[self.selected_index]
        
        self.selected_index += 1
        self.update_tree()
        self.update_preview()
        
        # 重新選中
        children = self.tree.get_children()
        if self.selected_index < len(children):
            self.tree.selection_set(children[self.selected_index])

def edit_action_dialog(self, index, action):
    """開啟動作編輯對話框（全新設計）"""
    win = tk.Toplevel(self)
    win.title("編輯動作" if index >= 0 else "新增動作")
    win.geometry("600x650")
    win.resizable(True, True)
    win.minsize(550, 600)
    win.grab_set()
    win.transient(self)
    
    # 主框架
    main_frame = tb.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # === 指令選擇區 ===
    tb.Label(main_frame, text="📋 選擇指令", font=("Microsoft JhengHei", 12, "bold")).pack(anchor="w", pady=(0, 15))
    
    command_var = tk.StringVar(value=action.get("command", ""))
    
    commands = [
        ("move_to", "🖱️ 移動滑鼠", "移動到指定座標"),
        ("click", "👆 左鍵點擊", "執行滑鼠左鍵點擊"),
        ("double_click", "👆👆 雙擊", "執行滑鼠雙擊"),
        ("right_click", "👉 右鍵點擊", "執行滑鼠右鍵點擊"),
        ("type_text", "⌨️ 輸入文字", "輸入文字內容"),
        ("press_key", "🔘 按鍵", "按下指定按鍵"),
        ("delay", "⏱️ 延遲", "暫停指定時間"),
        ("log", "📝 日誌", "輸出日誌訊息"),
    ]
    
    # 使用 Frame + Scrollbar 以支援更多指令
    cmd_canvas = tk.Canvas(main_frame, height=200, bd=0, highlightthickness=0)
    cmd_scrollbar = tb.Scrollbar(main_frame, orient="vertical", command=cmd_canvas.yview)
    cmd_frame = tb.Frame(cmd_canvas)
    
    cmd_frame.bind(
        "<Configure>",
        lambda e: cmd_canvas.configure(scrollregion=cmd_canvas.bbox("all"))
    )
    
    cmd_canvas.create_window((0, 0), window=cmd_frame, anchor="nw")
    cmd_canvas.configure(yscrollcommand=cmd_scrollbar.set)
    
    cmd_canvas.pack(side="left", fill="both", expand=True)
    cmd_scrollbar.pack(side="right", fill="y")
    
    for cmd, label, desc in commands:
        frame = tb.Frame(cmd_frame)
        frame.pack(fill="x", padx=5, pady=2)
        
        rb = tb.Radiobutton(frame, text=label, variable=command_var, value=cmd, width=20)
        rb.pack(side="left")
        
        desc_label = tb.Label(frame, text=desc, font=("Microsoft JhengHei", 8), foreground="#666")
        desc_label.pack(side="left", padx=10)
    
    tb.Separator(main_frame, orient="horizontal").pack(fill="x", pady=15)
    
    # === 參數輸入區 ===
    tb.Label(main_frame, text="⚙️ 參數設定", font=("Microsoft JhengHei", 12, "bold")).pack(anchor="w", pady=(0, 10))
    
    param_frame = tb.Frame(main_frame)
    param_frame.pack(fill="x", pady=5)
    
    tb.Label(param_frame, text="參數：", font=("Microsoft JhengHei", 10)).grid(row=0, column=0, sticky="w", pady=5)
    params_var = tk.StringVar(value=action.get("params", ""))
    params_entry = tb.Entry(param_frame, textvariable=params_var, font=("Consolas", 10), width=40)
    params_entry.grid(row=0, column=1, sticky="ew", padx=(10, 0))
    param_frame.columnconfigure(1, weight=1)
    
    # 參數說明
    param_hint = tb.Label(param_frame, text="", font=("Microsoft JhengHei", 8), foreground="#888", wraplength=400, justify="left")
    param_hint.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(2, 0))
    
    def update_param_hint(*args):
        hints = {
            "move_to": "格式: x, y\n範例: 100, 200",
            "click": "可選: x, y（點擊前先移動）",
            "double_click": "可選: x, y",
            "right_click": "可選: x, y",
            "type_text": "要輸入的文字\n範例: Hello World",
            "press_key": "按鍵名稱\n範例: enter, tab, esc",
            "delay": "毫秒數\n範例: 1000（= 1秒）",
            "log": "訊息內容\n範例: 開始執行",
        }
        param_hint.config(text=hints.get(command_var.get(), ""))
    
    command_var.trace_add("write", update_param_hint)
    update_param_hint()
    
    tb.Separator(main_frame, orient="horizontal").pack(fill="x", pady=15)
    
    # === 延遲設定 ===
    tb.Label(main_frame, text="⏱️ 延遲設定", font=("Microsoft JhengHei", 12, "bold")).pack(anchor="w", pady=(0, 10))
    
    delay_frame = tb.Frame(main_frame)
    delay_frame.pack(fill="x", pady=5)
    
    tb.Label(delay_frame, text="執行前延遲：", font=("Microsoft JhengHei", 10)).grid(row=0, column=0, sticky="w")
    delay_var = tk.StringVar(value=action.get("delay", "0"))
    tb.Entry(delay_frame, textvariable=delay_var, font=("Consolas", 10), width=15).grid(row=0, column=1, sticky="w", padx=(10, 5))
    tb.Label(delay_frame, text="毫秒（1000 = 1秒）", font=("Microsoft JhengHei", 8), foreground="#666").grid(row=0, column=2, sticky="w")
    
    # === 按鈕區 ===
    btn_frame = tb.Frame(main_frame)
    btn_frame.pack(fill="x", pady=(20, 0))
    
    def confirm():
        new_action = {
            "command": command_var.get(),
            "params": params_var.get().strip(),
            "delay": delay_var.get().strip()
        }
        
        if index >= 0:
            # 編輯現有動作
            self.actions[index] = new_action
        else:
            # 新增動作
            self.actions.append(new_action)
        
        self.update_tree()
        self.update_preview()
        self.status_label.config(text="已儲存動作")
        win.destroy()
    
    tb.Button(btn_frame, text="✔️ 確定", bootstyle=SUCCESS, command=confirm, width=15).pack(side="left", padx=5)
    tb.Button(btn_frame, text="❌ 取消", bootstyle=SECONDARY, command=win.destroy, width=15).pack(side="left", padx=5)
    
    # 聚焦到參數輸入框
    params_entry.focus()

# 以下是原有方法的保留/更新版本...

def run_script(self):
    """執行腳本"""
    if not self.actions:
        self.log_output("[提示] 動作列表為空，請先新增動作")
        return
    
    if self.is_executing:
        self.log_output("[提示] 腳本正在執行中...")
        return
    
    self.output_text.config(state="normal")
    self.output_text.delete("1.0", "end")
    self.output_text.config(state="disabled")
    
    self.log_output("[資訊] ========== 開始執行腳本 ==========")
    self.log_output(f"[資訊] 共 {len(self.actions)} 個動作")
    self.log_output("")
    
    script_code = self._actions_to_script()
    self.is_executing = True
    self.status_label.config(text="執行中...")
    
    def execute_in_thread():
        try:
            self.executor.execute(script_code)
            self.is_executing = False
            self.status_label.config(text="執行完成")
            self.log_output("")
            self.log_output("[資訊] ========== 執行完成 ==========")
        except Exception as e:
            self.log_output(f"[錯誤] 執行時發生異常：{e}")
            self.is_executing = False
            self.status_label.config(text="執行失敗")
    
    import threading
    thread = threading.Thread(target=execute_in_thread, daemon=True)
    thread.start()

def stop_script(self):
    """停止腳本執行"""
    if hasattr(self, 'executor'):
        self.executor.stop()
        self.is_executing = False
        self.log_output("")
        self.log_output("[資訊] ========== 已停止執行 ==========")
        self.status_label.config(text="已停止")

def save_script(self):
    """儲存腳本"""
    from tkinter import filedialog
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("ChroLens Script", "*.json"), ("All Files", "*.*")],
        initialdir=self.parent.script_dir if hasattr(self.parent, 'script_dir') else "scripts"
    )
    
    # 重新聚焦
    self.lift()
    self.focus_force()
    
    if filepath:
        try:
            script_data = {
                "events": [],
                "settings": {
                    "script_actions": self.actions,
                    "script_code": self._actions_to_script(),
                    "speed": 100,
                    "repeat": 1
                }
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(script_data, f, ensure_ascii=False, indent=2)
            
            self.log_output(f"[成功] 已儲存至：{filepath}")
            self.status_label.config(text=f"已儲存：{os.path.basename(filepath)}")
            
            # 同步回主程式並刷新列表
            self.apply_to_parent()
            if hasattr(self.parent, 'refresh_script_list'):
                self.parent.refresh_script_list()
            if hasattr(self.parent, 'refresh_script_listbox'):
                self.parent.refresh_script_listbox()
        except Exception as e:
            self.log_output(f"[錯誤] 儲存失敗：{e}")
            tk.messagebox.showerror("儲存失敗", f"無法儲存檔案：{e}")

def load_script(self):
    """載入腳本"""
    from tkinter import filedialog
    filepath = filedialog.askopenfilename(
        filetypes=[("ChroLens Script", "*.json"), ("All Files", "*.*")],
        initialdir=self.parent.script_dir if hasattr(self.parent, 'script_dir') else "scripts"
    )
    
    self.lift()
    self.focus_force()
    
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.log_output(f"[資訊] 正在載入：{os.path.basename(filepath)}")
            
            # 優先檢查動作列表格式
            if "settings" in data and "script_actions" in data["settings"]:
                self.actions = data["settings"]["script_actions"]
                self.log_output(f"[成功] 已載入 {len(self.actions)} 個動作")
            elif "settings" in data and "script_code" in data["settings"]:
                code = data["settings"]["script_code"]
                self.actions = self._script_to_actions(code)
                self.log_output(f"[成功] 已從腳本程式碼轉換 {len(self.actions)} 個動作")
            elif "events" in data:
                self.actions = self._events_to_actions(data["events"])
                self.log_output(f"[成功] 已從錄製事件轉換 {len(self.actions)} 個動作")
            else:
                raise ValueError("無法識別的檔案格式")
            
            self.update_tree()
            self.update_preview()
            self.status_label.config(text=f"已載入：{os.path.basename(filepath)}")
            
        except Exception as e:
            self.log_output(f"[錯誤] 載入失敗：{e}")
            tk.messagebox.showerror("載入失敗", f"無法載入檔案：{e}")

def show_syntax_help(self):
    """顯示語法說明"""
    help_window = tk.Toplevel(self)
    help_window.title("ChroLens 腳本語法說明")
    help_window.geometry("800x700")
    help_window.resizable(True, True)
    help_window.minsize(700, 600)
    help_window.transient(self)
    
    # 分頁控制
    notebook = tb.Notebook(help_window)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Tab 1: 基本語法
    basic_tab = tb.Frame(notebook)
    notebook.add(basic_tab, text="📚 基本語法")
    
    basic_text = tk.Text(basic_tab, font=("Consolas", 10), wrap="word", padx=10, pady=10)
    basic_text.pack(fill="both", expand=True)
    
    basic_content = """ChroLens 腳本語法說明
=====================

支援的指令：
-----------

🖱️ move_to(x, y)
   移動滑鼠到座標 (x, y)
   範例: move_to(100, 200)

👆 click()
   執行滑鼠左鍵點擊
   範例: click()

👆👆 double_click()
   執行滑鼠雙擊
   範例: double_click()

👉 right_click()
   執行滑鼠右鍵點擊
   範例: right_click()

⌨️ type_text("文字")
   輸入文字
   範例: type_text("Hello World")

🔘 press_key("按鍵")
   按下指定按鍵
   範例: press_key("enter")
   常用按鍵: enter, tab, esc, space, ctrl, alt, shift

⏱️ delay(毫秒)
   暫停執行
   範例: delay(1000)  # 暫停1秒

📝 log("訊息")
   輸出日誌
   範例: log("開始執行")

多語言支援：
-----------
大部分指令都支援中文、日文、英文：
- move_to / 移動 / 移動する
- click / 點擊 / クリック
- delay / 延遲 / 待機
"""
    
    basic_text.insert("1.0", basic_content)
    basic_text.config(state="disabled")
    
    # Tab 2: 範例腳本
    example_tab = tb.Frame(notebook)
    notebook.add(example_tab, text="💡 範例腳本")
    
    example_text = tk.Text(example_tab, font=("Consolas", 10), wrap="word", padx=10, pady=10)
    example_text.pack(fill="both", expand=True)
    
    example_content = """範例腳本集
=========

=== 範例 1: 開啟記事本並輸入文字 ===

# 點擊開始按鈕
move_to(50, 1050)
click()
delay(500)

# 輸入 notepad 並按 Enter
type_text("notepad")
delay(300)
press_key("enter")
delay(2000)

# 在記事本中輸入
type_text("Hello from ChroLens!")
press_key("enter")
type_text("這是自動化腳本測試")


=== 範例 2: 遊戲自動點擊 ===

log("開始執行遊戲腳本")

# 點擊遊戲開始按鈕
move_to(500, 300)
click()
delay(3000)

# 連續點擊10次
move_to(600, 400)
click()
delay(100)
click()
delay(100)
click()

log("腳本執行完成")


=== 範例 3: 使用中文指令 ===

日誌("開始執行中文腳本")
延遲(1000)

移動(100, 200)
點擊()
延遲(500)

輸入("測試文字")
按鍵("enter")

日誌("執行完成")
"""
    
    example_text.insert("1.0", example_content)
    example_text.config(state="disabled")
    
    # 關閉按鈕
    tb.Button(help_window, text="關閉", bootstyle=SECONDARY, command=help_window.destroy, width=15).pack(pady=10)

def log_output(self, message):
    """輸出日誌"""
    self.output_text.config(state="normal")
    self.output_text.insert("end", message + "\n")
    self.output_text.see("end")
    self.output_text.config(state="disabled")

def load_from_events(self, events):
    """從事件載入"""
    self.actions = self._events_to_actions(events)
    self.update_tree()
    self.update_preview()

# ... 其餘輔助方法保持不變 ...
