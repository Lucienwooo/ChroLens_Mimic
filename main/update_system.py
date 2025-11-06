"""
ChroLens_Mimic 完整更新系統
參考 VSCode、Discord 等軟體的更新方式
"""

import os
import sys
import json
import time
import shutil
import zipfile
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Callable


class UpdateSystem:
    """完整的更新系統"""
    
    GITHUB_REPO = "Lucienwooo/ChroLens_Mimic"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    # 需要保留的用戶數據
    USER_FILES = [
        "scripts",           # 用戶腳本目錄
        "user_config.json",  # 用戶設定
        "last_script.txt",   # 最後腳本
        "hotkeys.json",      # 快捷鍵設定
    ]
    
    # 需要備份的舊版本文件
    BACKUP_FILES = [
        "ChroLens_Mimic.exe",
        "version*.txt",
    ]
    
    def __init__(self, current_version: str):
        self.current_version = current_version
        self.last_error = None  # 用於存儲最後一次錯誤信息
        
        # 確定安裝目錄
        if getattr(sys, 'frozen', False):
            # 打包後執行
            self.install_dir = Path(sys.executable).parent
            self.exe_path = Path(sys.executable)
        else:
            # 開發環境
            self.install_dir = Path(__file__).parent
            self.exe_path = self.install_dir / "ChroLens_Mimic.exe"
        
        # 用戶數據目錄
        self.scripts_dir = self.install_dir / "scripts"
        self.backup_dir = self.install_dir / "backup"
        
        # 臨時目錄
        self.temp_dir = Path(tempfile.gettempdir()) / f"ChroLens_Update_{int(time.time())}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def check_for_updates(self) -> dict:
        """檢查 GitHub 上的新版本"""
        try:
            req = urllib.request.Request(self.API_URL)
            req.add_header('User-Agent', 'ChroLens-Mimic-UpdateChecker')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            latest_version = data.get('tag_name', '').lstrip('v')
            
            # 尋找 ZIP 更新包
            download_url = None
            asset_name = None
            file_size = 0
            
            for asset in data.get('assets', []):
                name = asset.get('name', '')
                if name.endswith('.zip') and 'ChroLens_Mimic' in name:
                    download_url = asset.get('browser_download_url')
                    asset_name = name
                    file_size = asset.get('size', 0)
                    break
            
            if not download_url:
                return {"has_update": False, "error": "找不到更新檔案"}
            
            # 比較版本
            has_update = self._compare_versions(latest_version, self.current_version)
            
            return {
                "has_update": has_update,
                "latest_version": latest_version,
                "current_version": self.current_version,
                "release_notes": data.get('body', ''),
                "download_url": download_url,
                "asset_name": asset_name,
                "size": file_size,
            }
        except Exception as e:
            return {"has_update": False, "error": str(e)}
    
    def _compare_versions(self, v1: str, v2: str) -> bool:
        """比較版本號 v1 > v2"""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            return parts1 > parts2
        except:
            return False
    
    def download_update(self, url: str, filename: str, 
                       progress_callback: Optional[Callable] = None) -> Path:
        """下載更新檔案"""
        download_path = self.temp_dir / filename
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'ChroLens-Mimic-Updater')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        
        return download_path
    
    def backup_current_version(self, new_version: str) -> Path:
        """備份當前版本"""
        # 創建備份目錄
        backup_version_dir = self.backup_dir / self.current_version
        backup_version_dir.mkdir(parents=True, exist_ok=True)
        
        # 備份 exe 和版本文件
        if self.exe_path.exists():
            shutil.copy2(self.exe_path, backup_version_dir / "ChroLens_Mimic.exe")
        
        # 備份版本資訊檔
        version_file = self.install_dir / f"version{self.current_version}.txt"
        if version_file.exists():
            shutil.copy2(version_file, backup_version_dir / version_file.name)
        
        # 創建下載連結文件
        download_link = backup_version_dir / "下載點.txt"
        with open(download_link, 'w', encoding='utf-8') as f:
            f.write(f"ChroLens_Mimic v{self.current_version}\n")
            f.write(f"GitHub: https://github.com/{self.GITHUB_REPO}/releases/tag/v{self.current_version}\n")
            f.write(f"\n備份時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"更新至版本: {new_version}\n")
        
        return backup_version_dir
    
    def backup_user_data(self) -> Path:
        """備份用戶數據到臨時目錄"""
        user_backup = self.temp_dir / "user_data_backup"
        user_backup.mkdir(parents=True, exist_ok=True)
        
        for item in self.USER_FILES:
            src = self.install_dir / item
            if src.exists():
                dst = user_backup / item
                if src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        
        return user_backup
    
    def apply_update(self, zip_path: Path, new_version: str,
                    progress_callback: Optional[Callable] = None) -> bool:
        """
        應用更新
        1. 備份當前版本
        2. 備份用戶數據
        3. 解壓新版本
        4. 恢復用戶數據
        5. 清理臨時文件
        """
        try:
            # 1. 備份當前版本
            if progress_callback:
                progress_callback("備份當前版本...", 10)
            self.backup_current_version(new_version)
            
            # 2. 備份用戶數據
            if progress_callback:
                progress_callback("備份用戶數據...", 20)
            user_backup = self.backup_user_data()
            
            # 3. 解壓新版本到臨時目錄
            if progress_callback:
                progress_callback("解壓更新檔案...", 30)
            
            extract_dir = self.temp_dir / "new_version"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 尋找實際的程式目錄（可能在 ChroLens_Mimic 子目錄中）
            program_dir = extract_dir / "ChroLens_Mimic"
            if not program_dir.exists():
                # 直接在根目錄
                program_dir = extract_dir
            
            # 4. 刪除舊的程式檔案（保留用戶數據）
            if progress_callback:
                progress_callback("移除舊版本檔案...", 50)
            
            # ！！！注意：正在運行的 exe 無法刪除，需要使用外部更新器
            # 檢查 exe 是否正在運行
            if self.exe_path.exists() and getattr(sys, 'frozen', False):
                # 程式正在運行，無法直接刪除 exe
                # 需要使用批次檔更新器
                raise Exception("無法在程式運行時更新主程式，請使用外部更新器（updater.bat）")
            
            # 刪除舊的 exe（僅在開發環境或程式未運行時）
            if self.exe_path.exists():
                try:
                    self.exe_path.unlink()
                except PermissionError:
                    raise Exception("無法刪除舊版本檔案（文件被鎖定），請關閉所有 ChroLens_Mimic 程序後重試")
            
            internal_dir = self.install_dir / "_internal"
            if internal_dir.exists():
                shutil.rmtree(internal_dir)
            
            # 刪除舊的版本文件
            for f in self.install_dir.glob("version*.txt"):
                f.unlink()
            
            # 5. 複製新版本檔案
            if progress_callback:
                progress_callback("安裝新版本...", 70)
            
            # 複製 exe
            new_exe = program_dir / "ChroLens_Mimic.exe"
            if new_exe.exists():
                shutil.copy2(new_exe, self.exe_path)
            
            # 複製 _internal
            new_internal = program_dir / "_internal"
            if new_internal.exists():
                shutil.copytree(new_internal, internal_dir, dirs_exist_ok=True)
            
            # 複製版本文件和其他必要檔案
            for item in program_dir.iterdir():
                if item.name in ["ChroLens_Mimic.exe", "_internal", "scripts", 
                               "user_config.json", "last_script.txt", "hotkeys.json"]:
                    continue
                
                dst = self.install_dir / item.name
                if item.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)
            
            # 6. 恢復用戶數據
            if progress_callback:
                progress_callback("恢復用戶數據...", 90)
            
            for item in user_backup.iterdir():
                dst = self.install_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dst)
            
            # 7. 清理臨時文件
            if progress_callback:
                progress_callback("清理臨時文件...", 95)
            
            return True
            
        except Exception as e:
            # 更新失敗，嘗試恢復
            import traceback
            error_msg = f"更新失敗: {e}\n{traceback.format_exc()}"
            print(error_msg)
            
            # 將錯誤信息保存到文件以便調試
            try:
                error_log = self.install_dir / "update_error.log"
                with open(error_log, 'w', encoding='utf-8') as f:
                    f.write(error_msg)
            except:
                pass
            
            # 將詳細錯誤信息存儲，以便上層調用者可以獲取
            self.last_error = str(e)
            return False
    
    def prepare_external_update(self, zip_path: Path, new_version: str) -> Path:
        """
        準備外部更新（使用批次檔）
        返回批次檔路徑
        """
        # 備份用戶數據
        user_backup = self.backup_user_data()
        
        # 解壓新版本到臨時目錄
        extract_dir = self.temp_dir / "new_version"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 尋找實際的程式目錄
        program_dir = extract_dir / "ChroLens_Mimic"
        if not program_dir.exists():
            program_dir = extract_dir
        
        # 創建更新批次檔
        bat_content = f"""@echo off
chcp 65001 > nul
title ChroLens_Mimic 更新程式
echo.
echo ====================================
echo   ChroLens_Mimic 自動更新
echo   版本: {new_version}
echo ====================================
echo.

REM 等待主程式關閉
echo [1/5] 等待主程式關閉...
timeout /t 2 /nobreak > nul

REM 備份當前版本
echo [2/5] 備份當前版本...
if exist "backup\\v{self.current_version}" rmdir /s /q "backup\\v{self.current_version}"
mkdir "backup\\v{self.current_version}" 2>nul
if exist "ChroLens_Mimic.exe" copy /y "ChroLens_Mimic.exe" "backup\\v{self.current_version}\\" > nul
if exist "version*.txt" copy /y "version*.txt" "backup\\v{self.current_version}\\" > nul

REM 刪除舊版本（保留用戶數據）
echo [3/5] 移除舊版本...
if exist "ChroLens_Mimic.exe" del /f /q "ChroLens_Mimic.exe"
if exist "_internal" rmdir /s /q "_internal"
if exist "version*.txt" del /f /q "version*.txt"

REM 安裝新版本
echo [4/5] 安裝新版本...
xcopy /e /i /y "{program_dir}\\*.*" "." > nul

REM 恢復用戶數據
echo [5/5] 恢復用戶數據...
xcopy /e /i /y "{user_backup}\\*.*" "." > nul

REM 清理臨時文件
rmdir /s /q "{self.temp_dir}" 2>nul

echo.
echo ====================================
echo   更新完成！正在啟動程式...
echo ====================================
timeout /t 2 /nobreak > nul

REM 啟動新版本
start "" "ChroLens_Mimic.exe"

REM 刪除自己
del "%~f0"
"""
        
        bat_path = self.install_dir / "updater_auto.bat"
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        return bat_path
    
    def restart_application(self):
        """重啟應用程式"""
        if self.exe_path.exists():
            subprocess.Popen([str(self.exe_path)], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS)
    
    def cleanup(self):
        """清理臨時檔案"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass


def format_size(bytes_size: int) -> str:
    """格式化檔案大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
