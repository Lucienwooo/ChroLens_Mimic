"""
ChroLens_Mimic 自安裝更新器
類似 ExplorerPatcher 的 ep_setup.exe
這是一個獨立的安裝/更新程式
"""

import os
import sys
import time
import shutil
import zipfile
import subprocess
from pathlib import Path
import ctypes


def is_admin():
    """檢查是否有管理員權限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def elevate_if_needed():
    """如果沒有管理員權限則請求提升"""
    if not is_admin():
        # 請求提升權限重新執行
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)


def install_or_update():
    """安裝或更新 ChroLens_Mimic"""
    
    print("ChroLens_Mimic 安裝/更新程式")
    print("=" * 50)
    
    # 確定安裝目錄
    if len(sys.argv) > 1:
        install_dir = Path(sys.argv[1])
    else:
        # 預設安裝到 Program Files
        install_dir = Path(os.environ.get('ProgramFiles', 'C:\\Program Files')) / "ChroLens_Mimic"
    
    print(f"\n安裝目錄: {install_dir}")
    
    # 檢查是否為更新（安裝目錄已存在）
    is_update = install_dir.exists() and (install_dir / "ChroLens_Mimic.exe").exists()
    
    if is_update:
        print("\n檢測到現有安裝，執行更新...")
        
        # 1. 等待主程式關閉
        print("  [1/6] 等待主程式關閉...")
        time.sleep(3)
        
        # 2. 備份用戶數據
        print("  [2/6] 備份用戶數據...")
        backup_dir = install_dir / "backup_temp"
        backup_dir.mkdir(exist_ok=True)
        
        for item in ["scripts", "user_config.json", "last_script.txt"]:
            src = install_dir / item
            if src.exists():
                if src.is_dir():
                    shutil.copytree(src, backup_dir / item, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, backup_dir / item)
        
        # 3. 刪除舊檔案
        print("  [3/6] 刪除舊版本...")
        for item in install_dir.iterdir():
            if item.name in ["backup_temp", "scripts", "user_config.json", "last_script.txt"]:
                continue
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except Exception as e:
                print(f"    警告: 無法刪除 {item.name}: {e}")
    else:
        print("\n執行全新安裝...")
        install_dir.mkdir(parents=True, exist_ok=True)
        backup_dir = None
    
    # 4. 解壓新版本
    print(f"  [{'4' if is_update else '1'}/6] 解壓新版本...")
    
    # 找到內嵌的 ZIP 檔案（假設在安裝器末尾）
    # 或者從當前目錄查找
    setup_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    zip_file = None
    
    for f in setup_dir.iterdir():
        if f.name.endswith('.zip') and 'ChroLens_Mimic' in f.name:
            zip_file = f
            break
    
    if not zip_file or not zip_file.exists():
        print(f"\n錯誤: 找不到更新檔案！")
        print(f"搜尋目錄: {setup_dir}")
        input("\n按 Enter 鍵退出...")
        sys.exit(1)
    
    print(f"    解壓: {zip_file.name}")
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zf:
            # 提取所有檔案
            for member in zf.namelist():
                # 移除頂層目錄（如果有）
                parts = member.split('/')
                if len(parts) > 1 and parts[0] == 'ChroLens_Mimic':
                    # 跳過頂層目錄，直接提取內容
                    target_path = install_dir / '/'.join(parts[1:])
                else:
                    target_path = install_dir / member
                
                if member.endswith('/'):
                    # 目錄
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    # 檔案
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as source, open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                
                print(f"    ✓ {target_path.name}")
    except Exception as e:
        print(f"\n錯誤: 解壓失敗: {e}")
        input("\n按 Enter 鍵退出...")
        sys.exit(1)
    
    # 5. 還原用戶數據
    if is_update and backup_dir and backup_dir.exists():
        print(f"  [5/6] 還原用戶數據...")
        for item in backup_dir.iterdir():
            dst = install_dir / item.name
            try:
                if item.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dst)
                print(f"    ✓ {item.name}")
            except Exception as e:
                print(f"    警告: 無法還原 {item.name}: {e}")
        
        # 刪除備份
        try:
            shutil.rmtree(backup_dir)
        except:
            pass
    
    # 6. 啟動程式
    exe_path = install_dir / "ChroLens_Mimic.exe"
    if exe_path.exists():
        print(f"  [{'6' if is_update else '2'}/6] 啟動程式...")
        
        try:
            # 使用 subprocess.Popen 在背景啟動
            subprocess.Popen(
                [str(exe_path)],
                cwd=str(install_dir),
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
            print(f"\n{'更新' if is_update else '安裝'}完成！程式已啟動。")
        except Exception as e:
            print(f"\n{'更新' if is_update else '安裝'}完成！請手動啟動程式。")
            print(f"程式位置: {exe_path}")
    else:
        print(f"\n錯誤: 找不到主程式！")
        print(f"預期位置: {exe_path}")
    
    print("\n" + "=" * 50)
    print("3 秒後自動關閉...")
    time.sleep(3)


if __name__ == "__main__":
    try:
        # 檢查權限（可選，根據需求）
        # elevate_if_needed()
        
        install_or_update()
    except Exception as e:
        print(f"\n發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 鍵退出...")
        sys.exit(1)
