# -*- coding: utf-8 -*-
"""
手動測試編輯器功能 - 互動式測試
"""
import tkinter as tk
from tkinter import messagebox
from text_script_editor import TextCommandEditor
import os
import time

def manual_test():
    """互動式測試"""
    print("\n" + "=" * 60)
    print("文字指令編輯器 - 互動式測試")
    print("=" * 60)
    print("\n此測試將開啟編輯器視窗，請依照提示操作：\n")
    
    print("測試項目：")
    print("1. ✅ 編輯器開啟")
    print("2. 📝 腳本下拉選單功能")
    print("3. ➕ 自訂腳本建立")
    print("4. 💾 儲存腳本")
    print("5. 📂 載入腳本")
    print("6. ▶️ 執行腳本")
    print("7. 📷 圖片辨識功能")
    print("\n按Enter開始測試...")
    input()
    
    root = tk.Tk()
    root.title("測試主視窗")
    root.geometry("300x200")
    
    # 創建一個簡單的模擬主程式
    class MockParent:
        def __init__(self):
            self.events = []
            self.metadata = {}
            self.speed_var = tk.StringVar(value="100")
            self.repeat_var = tk.StringVar(value="1")
            self.repeat_time_var = tk.StringVar(value="00:00:00")
            self.repeat_interval_var = tk.StringVar(value="00:00:00")
            self.target_hwnd = None
            
        def play_script(self):
            print("  ⚠️ 模擬執行腳本（實際應用需要完整主程式）")
            print(f"  - 事件數量: {len(self.events)}")
            
        def log(self, message):
            print(f"  [LOG] {message}")
    
    mock_parent = MockParent()
    
    # 開啟編輯器
    print("\n✅ 正在開啟編輯器...")
    editor = TextCommandEditor(mock_parent)
    
    # 添加測試指令
    print("\n📝 自動插入測試指令...")
    test_commands = """# 測試腳本
>按Y, 延遲50ms, T=0s000
>移動至(100,200), T=0s100
>左鍵點擊(100,200), T=0s200
>按Enter, 延遲50ms, T=0s300
"""
    editor.text_editor.delete("1.0", "end")
    editor.text_editor.insert("1.0", test_commands)
    print("  ✅ 測試指令已插入")
    
    # 創建測試指南視窗
    guide_window = tk.Toplevel(root)
    guide_window.title("測試指南")
    guide_window.geometry("400x500")
    guide_window.attributes('-topmost', True)
    
    guide_text = tk.Text(guide_window, wrap=tk.WORD, font=("Microsoft JhengHei", 10))
    guide_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    guide_content = """
📋 測試步驟指南

1️⃣ 檢查腳本下拉選單
   - 點擊「腳本:」右側的下拉選單
   - 應該看到「自訂腳本」選項
   ✅ 選單正常顯示

2️⃣ 測試自訂腳本功能
   - 選擇「自訂腳本」
   - 應該出現輸入框和✓按鈕
   - 輸入名稱「測試腳本001」
   - 點擊✓確認
   - 下拉選單應該恢復並顯示新腳本
   ✅ 自訂腳本功能正常

3️⃣ 測試編輯功能
   - 修改編輯器中的測試指令
   - 嘗試添加新的指令行
   ✅ 編輯功能正常

4️⃣ 測試儲存功能
   - 點擊「💾 儲存」按鈕
   - 檢查狀態列是否顯示儲存成功
   ✅ 儲存功能正常

5️⃣ 測試重新載入功能
   - 點擊「🔄 重新載入」按鈕
   - 內容應該重新載入
   ✅ 重新載入功能正常

6️⃣ 測試執行功能
   - 點擊「▶️ 執行」按鈕
   - 檢查控制台輸出
   - 不應該有錯誤訊息
   ✅ 執行功能正常

7️⃣ 測試圖片辨識（可選）
   - 點擊「📷 圖片辨識」
   - 截圖一個區域
   - 檢查是否插入指令
   ✅ 圖片辨識功能正常

---
完成所有測試後關閉編輯器視窗
    """
    
    guide_text.insert("1.0", guide_content)
    guide_text.config(state=tk.DISABLED)
    
    # 添加關閉按鈕
    def on_test_complete():
        print("\n" + "=" * 60)
        print("測試結果：")
        print("=" * 60)
        
        # 檢查編輯器狀態
        try:
            if editor.winfo_exists():
                print("✅ 編輯器視窗正常")
                if editor.script_combo.winfo_ismapped():
                    print("✅ 腳本下拉選單正常顯示")
                else:
                    print("❌ 腳本下拉選單未顯示")
                
                # 檢查測試腳本
                scripts_dir = os.path.join(os.getcwd(), "scripts")
                test_files = [f for f in os.listdir(scripts_dir) if f.startswith("測試腳本")]
                if test_files:
                    print(f"✅ 找到測試腳本: {test_files}")
                else:
                    print("⚠️ 未找到測試腳本（可能未執行建立步驟）")
        except:
            pass
        
        print("\n感謝測試！")
        print("=" * 60 + "\n")
        
        root.quit()
        root.destroy()
    
    btn_frame = tk.Frame(guide_window)
    btn_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Button(
        btn_frame,
        text="✅ 測試完成，關閉",
        command=on_test_complete,
        bg="#4CAF50",
        fg="white",
        font=("Microsoft JhengHei", 11, "bold"),
        padx=20,
        pady=10
    ).pack(fill=tk.X)
    
    print("\n⚠️ 請查看測試指南視窗並依照步驟測試")
    print("   測試完成後點擊「測試完成」按鈕\n")
    
    root.mainloop()

if __name__ == "__main__":
    manual_test()
