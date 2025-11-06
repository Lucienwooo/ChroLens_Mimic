"""
ChroLens_Mimic 簡化更新管理模組
使用外部更新器策略，完全避免檔案鎖定問題
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path


class UpdateManager:
    """更新管理器 - 使用外部更新器策略"""
    
    GITHUB_REPO = "Lucienwooo/ChroLens_Mimic"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __init__(self, current_version: str):
        self.current_version = current_version
        
        # 安裝目錄
        if getattr(sys, 'frozen', False):
            self.install_dir = Path(sys.executable).parent
            self.exe_path = Path(sys.executable)
        else:
            self.install_dir = Path(__file__).parent
            self.exe_path = self.install_dir / "ChroLens_Mimic.exe"
        
        # 臨時目錄
        self.temp_dir = Path(tempfile.gettempdir()) / f"ChroLens_Update_{int(time.time())}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def check_for_updates(self) -> dict:
        """檢查更新"""
        try:
            req = urllib.request.Request(self.API_URL)
            req.add_header('User-Agent', 'ChroLens-Mimic-UpdateChecker')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            latest_version = data.get('tag_name', '').lstrip('v')
            
            # 優先尋找安裝器 (類似 ExplorerPatcher)
            download_url = None
            asset_name = None
            file_size = 0
            use_installer = False
            
            for asset in data.get('assets', []):
                name = asset.get('name', '')
                # 優先使用安裝器
                if 'Setup' in name and name.endswith('.exe'):
                    download_url = asset.get('browser_download_url')
                    asset_name = name
                    file_size = asset.get('size', 0)
                    use_installer = True
                    break
            
            # 如果沒有安裝器，回退到 ZIP
            if not download_url:
                for asset in data.get('assets', []):
                    if asset.get('name', '').endswith('.zip'):
                        download_url = asset.get('browser_download_url')
                        asset_name = asset.get('name')
                        file_size = asset.get('size', 0)
                        use_installer = False
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
                "use_installer": use_installer
            }
        except Exception as e:
            return {"has_update": False, "error": str(e)}
    
    def _compare_versions(self, v1: str, v2: str) -> bool:
        """比較版本號"""
        try:
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            return parts1 > parts2
        except:
            return False
    
    def download_update(self, url: str, filename: str, progress_callback=None) -> Path:
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
    
    def apply_update(self, file_path: Path, use_installer: bool = False):
        """
        應用更新
        如果是安裝器：直接執行安裝器（類似 ExplorerPatcher）
        如果是 ZIP：使用 updater.bat
        """
        if use_installer:
            # 使用安裝器模式（推薦）
            print(f"使用安裝器模式更新: {file_path}")
            
            # 傳遞安裝目錄參數
            install_dir_str = str(self.install_dir.absolute())
            
            # 直接執行安裝器
            subprocess.Popen(
                [str(file_path), install_dir_str],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            # 主程式關閉，讓安裝器接手
            print("安裝器已啟動，主程式即將關閉...")
            
        else:
            # 使用 ZIP + updater.bat 模式（備用）
            print(f"使用 ZIP 模式更新: {file_path}")
            
            updater_bat = self.install_dir / "updater.bat"
            
            if not updater_bat.exists():
                raise Exception(f"找不到更新器: {updater_bat}")
            
            # 準備參數
            zip_path_str = str(file_path.absolute())
            install_dir_str = str(self.install_dir.absolute())
            exe_name = self.exe_path.name
            
            # 啟動 .bat 更新器
            cmd = [str(updater_bat), zip_path_str, install_dir_str, exe_name]
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.Popen(
                cmd,
                cwd=str(self.temp_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                shell=True
            )
            
            print("更新器已啟動，主程式即將關閉...")
    
    def cleanup(self):
        """清理臨時檔案"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except:
            pass


def format_size(bytes_size: int) -> str:
    """格式化檔案大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
