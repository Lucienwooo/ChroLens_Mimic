# -*- coding: utf-8 -*-
"""
測試文字指令編輯器的所有功能
"""
import tkinter as tk
from text_script_editor import TextCommandEditor
import os
import json
import time

def test_editor_functions():
    """測試編輯器的所有功能"""
    print("=" * 60)
    print("開始測試文字指令編輯器")
    print("=" * 60)
    
    root = tk.Tk()
    root.withdraw()
    
    # 測試1: 創建編輯器
    print("\n[測試1] 創建編輯器...")
    try:
        editor = TextCommandEditor(root)
        print("✅ 編輯器創建成功")
        time.sleep(0.5)
    except Exception as e:
        print(f"❌ 編輯器創建失敗: {e}")
        return
    
    # 測試2: 檢查下拉選單是否有內容
    print("\n[測試2] 檢查腳本下拉選單...")
    try:
        scripts = editor.script_combo['values']
        print(f"✅ 找到 {len(scripts)} 個腳本: {scripts[:3] if len(scripts) > 3 else scripts}")
    except Exception as e:
        print(f"❌ 下拉選單檢查失敗: {e}")
    
    # 測試3: 測試自訂腳本功能
    print("\n[測試3] 測試自訂腳本功能...")
    test_script_name = f"test_{int(time.time())}"
    try:
        # 模擬選擇"自訂腳本"
        editor.script_var.set("自訂腳本")
        editor._on_script_selected(None)
        print("  - 觸發自訂腳本選擇")
        
        # 檢查輸入框是否顯示
        if editor.custom_name_entry.winfo_ismapped():
            print("  ✅ 輸入框正確顯示")
            
            # 輸入名稱並建立
            editor.custom_name_var.set(test_script_name)
            editor._create_custom_script()
            
            # 檢查下拉選單是否恢復
            if editor.script_combo.winfo_ismapped():
                print("  ✅ 下拉選單成功恢復")
            else:
                print("  ❌ 下拉選單未恢復")
            
            # 檢查腳本是否建立
            script_path = os.path.join(os.getcwd(), "scripts", test_script_name + ".json")
            if os.path.exists(script_path):
                print(f"  ✅ 腳本檔案已建立: {test_script_name}")
                # 清理測試檔案
                os.remove(script_path)
                print(f"  🗑️ 測試檔案已清理")
            else:
                print(f"  ❌ 腳本檔案未建立")
        else:
            print("  ❌ 輸入框未顯示")
    except Exception as e:
        print(f"  ❌ 自訂腳本測試失敗: {e}")
    
    # 測試4: 測試文字到JSON轉換
    print("\n[測試4] 測試文字指令轉換...")
    try:
        test_text = """>按Y, 延遲50ms, T=0s100
>移動至(100,200), T=0s200
>左鍵點擊(100,200), T=0s300"""
        
        json_data = editor._text_to_json(test_text)
        event_count = len(json_data.get("events", []))
        print(f"  ✅ 轉換成功，產生 {event_count} 個事件")
        
        # 驗證事件類型
        events = json_data.get("events", [])
        if events:
            print(f"  - 第1個事件: {events[0]['type']} - {events[0].get('event', 'N/A')}")
            print(f"  - 最後事件: {events[-1]['type']} - {events[-1].get('event', 'N/A')}")
    except Exception as e:
        print(f"  ❌ 文字轉換失敗: {e}")
    
    # 測試5: 測試JSON到文字轉換
    print("\n[測試5] 測試JSON到文字轉換...")
    try:
        test_json = {
            "events": [
                {"type": "keyboard", "event": "down", "name": "A", "time": 1000.0},
                {"type": "keyboard", "event": "up", "name": "A", "time": 1000.05}
            ],
            "settings": {}
        }
        
        text_output = editor._json_to_text(test_json)
        if ">按A" in text_output:
            print("  ✅ JSON轉文字成功")
            print(f"  - 生成內容預覽: {text_output.split(chr(10))[4] if len(text_output.split(chr(10))) > 4 else '(無)'}")
        else:
            print("  ❌ 轉換結果不包含預期指令")
    except Exception as e:
        print(f"  ❌ JSON轉換失敗: {e}")
    
    # 測試6: 檢查執行方法是否存在
    print("\n[測試6] 檢查執行方法...")
    try:
        if hasattr(editor, '_execute_script'):
            print("  ✅ _execute_script 方法存在")
        if hasattr(editor, '_save_script'):
            print("  ✅ _save_script 方法存在")
        if hasattr(editor, '_load_script'):
            print("  ✅ _load_script 方法存在")
    except Exception as e:
        print(f"  ❌ 方法檢查失敗: {e}")
    
    # 測試7: 檢查圖片辨識指令解析
    print("\n[測試7] 測試圖片辨識指令解析...")
    try:
        # 新格式
        result1 = editor._parse_image_command(">辨識>pic01, T=0s100")
        if result1 and result1['type'] == 'image_recognize':
            print("  ✅ 新格式解析成功 (>辨識>pic01)")
        else:
            print("  ❌ 新格式解析失敗")
        
        # 舊格式相容性
        result2 = editor._parse_image_command(">辨識>pic01>img_001.png, T=0s100")
        if result2 and result2['type'] == 'image_recognize':
            print("  ✅ 舊格式解析成功 (相容性)")
        else:
            print("  ❌ 舊格式解析失敗")
    except Exception as e:
        print(f"  ❌ 圖片指令解析失敗: {e}")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
    
    # 關閉編輯器
    editor.destroy()
    root.destroy()

if __name__ == "__main__":
    test_editor_functions()
