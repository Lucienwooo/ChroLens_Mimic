"""
ChroLens_Mimic 快捷鍵診斷工具
用於診斷和測試快捷鍵功能是否正常

使用方法：
1. 直接執行此腳本
2. 按下提示的快捷鍵測試
3. 查看診斷結果
"""

import sys
import os
import traceback

def check_keyboard_module():
    """檢查 keyboard 模組"""
    print("\n" + "="*60)
    print("1. 檢查 keyboard 模組")
    print("="*60)
    
    try:
        import keyboard
        print("✓ keyboard 模組載入成功")
        print(f"  版本: {keyboard.__version__ if hasattr(keyboard, '__version__') else '未知'}")
        print(f"  路徑: {keyboard.__file__}")
        
        # 測試基本功能
        try:
            # 測試按鍵檢測
            print("\n測試按鍵檢測功能...")
            print("請按下 'space' 鍵（5秒內）...")
            
            import time
            start_time = time.time()
            detected = False
            
            def on_space():
                nonlocal detected
                detected = True
                print("✓ 檢測到 space 鍵按下！")
            
            keyboard.on_press_key('space', lambda _: on_space())
            
            while time.time() - start_time < 5:
                if detected:
                    break
                time.sleep(0.1)
            
            keyboard.unhook_all()
            
            if detected:
                print("✓ keyboard 模組功能正常")
                return True
            else:
                print("⚠ 5秒內未檢測到按鍵，可能需要管理員權限")
                return False
                
        except Exception as e:
            print(f"✗ keyboard 模組功能測試失敗: {e}")
            print(f"  詳細錯誤: {traceback.format_exc()}")
            return False
            
    except ImportError as e:
        print(f"✗ keyboard 模組未安裝: {e}")
        print("  解決方法: pip install keyboard")
        return False
    except Exception as e:
        print(f"✗ keyboard 模組載入失敗: {e}")
        print(f"  詳細錯誤: {traceback.format_exc()}")
        return False

def check_pynput_module():
    """檢查 pynput 模組"""
    print("\n" + "="*60)
    print("2. 檢查 pynput 模組")
    print("="*60)
    
    try:
        from pynput import keyboard as pynput_keyboard
        from pynput.keyboard import Key, KeyCode
        print("✓ pynput 模組載入成功")
        print(f"  路徑: {pynput_keyboard.__file__}")
        
        # 測試監聽器
        try:
            print("\n測試 pynput 監聽器...")
            print("請按下 'ESC' 鍵（5秒內）...")
            
            detected = False
            
            def on_press(key):
                nonlocal detected
                if key == Key.esc:
                    detected = True
                    print("✓ 檢測到 ESC 鍵按下！")
                    return False  # 停止監聽
            
            with pynput_keyboard.Listener(on_press=on_press) as listener:
                listener.join(timeout=5)
            
            if detected:
                print("✓ pynput 模組功能正常")
                return True
            else:
                print("⚠ 5秒內未檢測到按鍵")
                return False
                
        except Exception as e:
            print(f"✗ pynput 模組功能測試失敗: {e}")
            print(f"  詳細錯誤: {traceback.format_exc()}")
            return False
            
    except ImportError as e:
        print(f"✗ pynput 模組未安裝: {e}")
        print("  解決方法: pip install pynput")
        return False
    except Exception as e:
        print(f"✗ pynput 模組載入失敗: {e}")
        print(f"  詳細錯誤: {traceback.format_exc()}")
        return False

def check_admin_privileges():
    """檢查管理員權限"""
    print("\n" + "="*60)
    print("3. 檢查管理員權限")
    print("="*60)
    
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        
        if is_admin:
            print("✓ 程式以管理員權限運行")
            return True
        else:
            print("✗ 程式未以管理員權限運行")
            print("  某些快捷鍵功能可能無法正常工作")
            print("  解決方法: 右鍵 → 以系統管理員身分執行")
            return False
            
    except Exception as e:
        print(f"⚠ 無法檢測管理員權限: {e}")
        return None

def check_system_info():
    """檢查系統資訊"""
    print("\n" + "="*60)
    print("4. 系統資訊")
    print("="*60)
    
    print(f"Python 版本: {sys.version}")
    print(f"執行模式: {'打包後 (PyInstaller)' if getattr(sys, 'frozen', False) else '開發模式 (Python)'}")
    print(f"作業系統: {os.name}")
    print(f"當前目錄: {os.getcwd()}")

def check_hotkey_config():
    """檢查快捷鍵配置"""
    print("\n" + "="*60)
    print("5. 檢查快捷鍵配置")
    print("="*60)
    
    config_file = "user_config.json"
    if os.path.exists(config_file):
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            hotkey_map = config.get("hotkey_map", {})
            if hotkey_map:
                print("✓ 找到快捷鍵配置:")
                for action, key in hotkey_map.items():
                    print(f"  {action}: {key}")
            else:
                print("⚠ 配置檔案中沒有快捷鍵設定")
                
        except Exception as e:
            print(f"✗ 讀取配置檔案失敗: {e}")
    else:
        print("⚠ 找不到 user_config.json")

def test_hotkey_registration():
    """測試快捷鍵註冊"""
    print("\n" + "="*60)
    print("6. 測試快捷鍵註冊")
    print("="*60)
    
    try:
        import keyboard
        
        print("正在註冊測試快捷鍵 'ctrl+shift+t'...")
        
        triggered = False
        
        def test_callback():
            nonlocal triggered
            triggered = True
            print("✓ 快捷鍵 'ctrl+shift+t' 被觸發！")
        
        handler = keyboard.add_hotkey('ctrl+shift+t', test_callback)
        print("✓ 快捷鍵註冊成功")
        print("請按下 'Ctrl+Shift+T' 測試（5秒內）...")
        
        import time
        start_time = time.time()
        while time.time() - start_time < 5:
            if triggered:
                break
            time.sleep(0.1)
        
        keyboard.remove_hotkey(handler)
        
        if triggered:
            print("✓ 快捷鍵功能完全正常")
            return True
        else:
            print("⚠ 5秒內未觸發快捷鍵")
            return False
            
    except Exception as e:
        print(f"✗ 快捷鍵註冊失敗: {e}")
        print(f"  詳細錯誤: {traceback.format_exc()}")
        return False

def main():
    """主函數"""
    print("\n" + "="*60)
    print("ChroLens_Mimic 快捷鍵診斷工具")
    print("="*60)
    
    results = {}
    
    # 1. 檢查 keyboard 模組
    results['keyboard'] = check_keyboard_module()
    
    # 2. 檢查 pynput 模組
    results['pynput'] = check_pynput_module()
    
    # 3. 檢查管理員權限
    results['admin'] = check_admin_privileges()
    
    # 4. 系統資訊
    check_system_info()
    
    # 5. 檢查配置
    check_hotkey_config()
    
    # 6. 測試快捷鍵註冊
    if results.get('keyboard'):
        results['hotkey_test'] = test_hotkey_registration()
    
    # 總結
    print("\n" + "="*60)
    print("診斷總結")
    print("="*60)
    
    all_ok = all([v for v in results.values() if v is not None])
    
    if all_ok:
        print("✓ 所有檢查通過！快捷鍵應該可以正常使用")
    else:
        print("⚠ 發現以下問題：")
        if not results.get('keyboard'):
            print("  • keyboard 模組有問題")
        if not results.get('pynput'):
            print("  • pynput 模組有問題")
        if results.get('admin') == False:
            print("  • 未以管理員權限運行")
        if results.get('hotkey_test') == False:
            print("  • 快捷鍵註冊測試失敗")
        
        print("\n建議解決方法：")
        print("1. 確保已安裝所有依賴: pip install keyboard pynput")
        print("2. 以管理員權限運行程式")
        print("3. 檢查防毒軟體是否阻擋")
        print("4. 重新安裝 keyboard 模組: pip uninstall keyboard & pip install keyboard")
    
    print("\n按 Enter 鍵結束...")
    input()

if __name__ == "__main__":
    main()
