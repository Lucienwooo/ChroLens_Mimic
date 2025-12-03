"""
測試更新日誌生成功能
用於診斷為什麼 update_log.txt 沒有生成
"""

import os
import sys
import datetime
import tempfile

def test_log_writing():
    """測試日誌寫入功能"""
    print("="*60)
    print("更新日誌寫入測試")
    print("="*60)
    print()
    
    # 測試 1: 當前目錄
    test_locations = [
        ("當前目錄", os.getcwd()),
        ("腳本目錄", os.path.dirname(os.path.abspath(__file__))),
        ("臨時目錄", tempfile.gettempdir()),
        ("桌面", os.path.join(os.path.expanduser("~"), "Desktop")),
    ]
    
    results = []
    
    for name, location in test_locations:
        log_path = os.path.join(location, "update_log_test.txt")
        print(f"測試 {name}: {location}")
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("ChroLens_Mimic 更新程式 - 測試\n")
                f.write(f"測試時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n")
                f.write(f"測試位置: {location}\n")
                f.write(f"日誌路徑: {log_path}\n")
                f.write("\n這是一個測試檔案。\n")
                f.write("如果您看到這個檔案，表示日誌寫入功能正常。\n")
            
            # 驗證檔案存在
            if os.path.exists(log_path):
                file_size = os.path.getsize(log_path)
                print(f"  ✅ 成功！檔案大小: {file_size} bytes")
                print(f"  📁 完整路徑: {log_path}")
                results.append((name, True, log_path))
            else:
                print(f"  ❌ 失敗：檔案不存在")
                results.append((name, False, log_path))
                
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            results.append((name, False, str(e)))
        
        print()
    
    # 總結
    print("="*60)
    print("測試總結")
    print("="*60)
    
    success_count = sum(1 for _, success, _ in results if success)
    print(f"成功: {success_count}/{len(results)}")
    print()
    
    for name, success, info in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}: {info if not success else '成功'}")
    
    print()
    print("="*60)
    
    # 如果有成功的，顯示第一個成功的檔案路徑
    for name, success, path in results:
        if success:
            print(f"✅ 至少一個位置可以寫入日誌！")
            print(f"範例檔案: {path}")
            print(f"\n請開啟此檔案查看內容。")
            break
    else:
        print("❌ 所有位置都無法寫入日誌！")
        print("這可能是權限問題。")

def generate_sample_log():
    """生成完整的範例日誌檔案"""
    sample_log_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "update_log_SAMPLE.txt"
    )
    
    print(f"\n正在生成範例日誌: {sample_log_path}")
    
    try:
        with open(sample_log_path, 'w', encoding='utf-8') as f:
            f.write("""========================================
ChroLens_Mimic 更新程式
更新時間: 2025-12-03 14:30:45
========================================
當前版本: 2.6.6
目標版本: 2.6.7
批次腳本: C:\\Users\\Lucien\\AppData\\Local\\Temp\\ChroLens_Update.bat
主程式目錄: C:\\Program Files\\ChroLens_Mimic
批次腳本已啟動，等待程式關閉...

[以下是批次腳本執行時添加的內容]
========================================
ChroLens_Mimic 更新程式
========================================

正在等待程式關閉...
程式已關閉
開始更新檔案...
建立 backup 資料夾
生成版本資訊: 2.6.6.txt
處理舊版 exe...
重命名舊版 exe...
舊版 exe 已刪除
複製新檔案...
來源目錄: C:\\Users\\Lucien\\AppData\\Local\\Temp\\ChroLens_Update_2.6.7
目標目錄: C:\\Program Files\\ChroLens_Mimic
檔案複製成功
更新完成！
清理臨時檔案: C:\\Users\\Lucien\\AppData\\Local\\Temp\\ChroLens_Update_2.6.7
重新啟動程式: C:\\Program Files\\ChroLens_Mimic\\ChroLens_Mimic.exe
腳本執行完成
""")
        
        print(f"✅ 範例日誌已生成: {sample_log_path}")
        print(f"\n這是一個完整的更新日誌範例。")
        print(f"實際的更新日誌應該包含類似的內容。")
        
        return sample_log_path
        
    except Exception as e:
        print(f"❌ 生成範例日誌失敗: {e}")
        return None

def test_update_manager_import():
    """測試 update_manager 模組是否能正確載入"""
    print("\n" + "="*60)
    print("測試 update_manager 模組")
    print("="*60)
    
    try:
        from update_manager import UpdateManager
        print("✅ update_manager 模組載入成功")
        
        # 創建實例
        updater = UpdateManager("2.6.6", logger=print)
        print("✅ UpdateManager 實例創建成功")
        
        # 測試日誌寫入路徑
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
            current_dir = os.path.dirname(current_exe)
            print(f"📦 打包環境")
        else:
            current_exe = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_exe)
            print(f"🐍 開發環境")
        
        print(f"當前目錄: {current_dir}")
        test_log = os.path.join(current_dir, "update_log.txt")
        print(f"日誌路徑: {test_log}")
        
        # 測試寫入
        try:
            with open(test_log, 'w', encoding='utf-8') as f:
                f.write("測試寫入\n")
            print(f"✅ 可以在此位置寫入日誌")
            
            # 刪除測試檔案
            if os.path.exists(test_log):
                os.remove(test_log)
                
        except Exception as e:
            print(f"❌ 無法在此位置寫入: {e}")
        
    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ChroLens_Mimic 更新日誌診斷工具")
    print("="*60)
    print()
    
    # 1. 測試日誌寫入
    test_log_writing()
    
    # 2. 生成範例日誌
    sample_path = generate_sample_log()
    
    # 3. 測試 update_manager 模組
    test_update_manager_import()
    
    print("\n" + "="*60)
    print("測試完成！")
    print("="*60)
    
    if sample_path:
        print(f"\n📄 請查看範例日誌: {sample_path}")
    
    input("\n按 Enter 鍵退出...")
