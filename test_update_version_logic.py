"""
測試更新管理器的版本資訊生成邏輯
用於驗證 update_manager.py 是否正確使用 _latest_version
"""

import sys
import os
import tempfile

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'main'))

from update_manager import UpdateManager

def test_version_info_generation():
    """測試版本資訊生成邏輯"""
    
    print("="*70)
    print("ChroLens_Mimic 更新機制版本資訊測試")
    print("="*70)
    print()
    
    # 創建更新管理器實例
    print("初始化更新管理器...")
    manager = UpdateManager("2.7.2", logger=print)
    print(f"✓ 當前版本: {manager.current_version}")
    print()
    
    # 模擬發現新版本
    print("模擬檢測到新版本...")
    manager._latest_version = "2.7.3"
    print(f"✓ 最新版本: {manager._latest_version}")
    print()
    
    # 創建臨時目錄用於測試
    temp_dir = tempfile.mkdtemp()
    fake_source = os.path.join(temp_dir, "source")
    fake_target = os.path.join(temp_dir, "target")
    fake_exe = os.path.join(fake_target, "ChroLens_Mimic.exe")
    
    os.makedirs(fake_source)
    os.makedirs(fake_target)
    
    print("生成更新批次腳本...")
    try:
        # 生成批次腳本
        script_path = manager._create_update_script(
            source_dir=fake_source,
            target_dir=fake_target,
            exe_path=fake_exe
        )
        
        print(f"✓ 腳本已生成: {script_path}")
        print()
        
        # 讀取腳本內容
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查版本資訊
        print("檢查版本資訊生成...")
        print("-"*70)
        
        # 檢查是否使用了正確的版本號
        if "2.7.3.txt" in content:
            print("✅ 測試通過：使用了最新版本號 (2.7.3)")
            print("   → 批次腳本中包含: 2.7.3.txt")
        else:
            print("❌ 測試失敗：未使用最新版本號")
            if "2.7.2.txt" in content:
                print("   → 錯誤：批次腳本中包含當前版本號 (2.7.2)")
            
        # 檢查 GitHub 連結
        if "v2.7.3" in content:
            print("✅ 測試通過：GitHub 連結使用正確版本 (v2.7.3)")
        else:
            print("❌ 測試失敗：GitHub 連結版本錯誤")
            if "v2.7.2" in content:
                print("   → 錯誤：使用了當前版本 (v2.7.2)")
        
        print("-"*70)
        print()
        
        # 顯示相關腳本片段
        print("批次腳本關鍵片段:")
        print("-"*70)
        for line in content.split('\n'):
            if '生成版本資訊' in line or '.txt' in line or 'github.com' in line:
                print(line)
        print("-"*70)
        
        # 清理
        os.remove(script_path)
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理臨時目錄
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print()
    print("="*70)
    print("測試完成")
    print("="*70)

if __name__ == "__main__":
    test_version_info_generation()
