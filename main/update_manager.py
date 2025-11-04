"""
ChroLens_Mimic 更新管理模組
參考 PowerToys 的更新機制

功能:
1. 檢查 GitHub Releases 新版本
2. 下載更新包
3. 智能備份當前版本
4. 安裝新版本
5. 版本回退功能
"""

import os
import sys
import json
import time
import shutil
import hashlib
import tempfile
import zipfile
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


class UpdateManager:
    """更新管理器"""
    
    # GitHub Repository 資訊
    GITHUB_REPO = "Lucienwooo/ChroLens_Mimic"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    # 使用者資料檔案 (不會被更新覆蓋)
    USER_DATA_FILES = ["scripts", "user_config.json", "last_script.txt"]
    
    def __init__(self, current_version: str, install_dir: str = None):
        """
        初始化更新管理器
        
        Args:
            current_version: 當前版本號 (例如: "2.6.4")
            install_dir: 安裝目錄 (預設為程式所在目錄)
        """
        self.current_version = current_version
        
        # 確定安裝目錄
        if install_dir:
            self.install_dir = Path(install_dir)
        elif getattr(sys, 'frozen', False):
            # 打包後的執行檔
            self.install_dir = Path(sys.executable).parent
        else:
            # 開發環境
            self.install_dir = Path(__file__).parent
        
        # 備份目錄
        self.backup_dir = self.install_dir / "backup"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 臨時目錄
        self.temp_dir = Path(tempfile.gettempdir()) / f"ChroLens_Update_{int(time.time())}"
    
    def check_for_updates(self) -> dict:
        """
        檢查是否有新版本
        
        Returns:
            dict: {
                "has_update": bool,
                "latest_version": str,
                "current_version": str,
                "release_notes": str,
                "download_url": str,
                "asset_name": str,
                "published_at": str,
                "size": int  # 檔案大小 (bytes)
            }
        """
        try:
            # 發送 API 請求
            req = urllib.request.Request(self.API_URL)
            req.add_header('User-Agent', 'ChroLens-Mimic-UpdateChecker')
            req.add_header('Accept', 'application/vnd.github.v3+json')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            # 解析版本資訊
            latest_version = data.get('tag_name', '').lstrip('v')
            release_notes = data.get('body', '無發行說明')
            published_at = data.get('published_at', '')
            
            # 找到 .zip 下載連結
            download_url = None
            asset_name = None
            file_size = 0
            
            for asset in data.get('assets', []):
                name = asset.get('name', '')
                if name.endswith('.zip') and 'ChroLens_Mimic' in name:
                    download_url = asset.get('browser_download_url', '')
                    asset_name = name
                    file_size = asset.get('size', 0)
                    break
            
            # 比較版本號
            has_update = self._compare_versions(latest_version, self.current_version)
            
            return {
                "has_update": has_update,
                "latest_version": latest_version,
                "current_version": self.current_version,
                "release_notes": release_notes,
                "download_url": download_url,
                "asset_name": asset_name,
                "published_at": published_at,
                "size": file_size
            }
        
        except urllib.error.URLError as e:
            raise Exception(f"網路連線失敗: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"無法解析 GitHub API 回應: {e}")
        except Exception as e:
            raise Exception(f"檢查更新時發生錯誤: {e}")
    
    def download_update(self, download_url: str, asset_name: str, progress_callback=None) -> Path:
        """
        下載更新檔案
        
        Args:
            download_url: 下載連結
            asset_name: 檔案名稱
            progress_callback: 進度回調函數 (downloaded_bytes, total_bytes)
        
        Returns:
            Path: 下載的檔案路徑
        """
        try:
            # 建立臨時目錄
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            download_path = self.temp_dir / asset_name
            
            # 下載檔案
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if progress_callback:
                    progress_callback(downloaded, total_size)
            
            urllib.request.urlretrieve(download_url, str(download_path), report_progress)
            
            return download_path
        
        except Exception as e:
            # 清理臨時檔案
            self._cleanup_temp()
            raise Exception(f"下載更新失敗: {e}")
    
    def extract_update(self, zip_path: Path, progress_callback=None) -> Path:
        """
        解壓縮更新檔案
        
        Args:
            zip_path: ZIP 檔案路徑
            progress_callback: 進度回調函數 (current_file, total_files)
        
        Returns:
            Path: 解壓縮後的目錄 (ChroLens_Mimic 資料夾)
        """
        try:
            extract_dir = self.temp_dir / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                members = zip_ref.namelist()
                total_files = len(members)
                
                for idx, member in enumerate(members):
                    zip_ref.extract(member, extract_dir)
                    if progress_callback:
                        progress_callback(idx + 1, total_files)
            
            # 找到 ChroLens_Mimic 資料夾
            update_dir = None
            for root, dirs, files in os.walk(extract_dir):
                if 'ChroLens_Mimic' in dirs:
                    update_dir = Path(root) / 'ChroLens_Mimic'
                    break
                # 如果根目錄就是 ChroLens_Mimic 內容
                if any(f.endswith('.exe') and 'ChroLens' in f for f in files):
                    update_dir = Path(root)
                    break
            
            if not update_dir or not update_dir.exists():
                raise Exception("無法在壓縮檔中找到更新檔案")
            
            return update_dir
        
        except Exception as e:
            raise Exception(f"解壓縮失敗: {e}")
    
    def backup_current_version(self) -> Path:
        """
        備份當前版本
        
        Returns:
            Path: 備份目錄路徑
        """
        try:
            backup_path = self.backup_dir / self.current_version
            
            # 如果備份已存在,先刪除
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 備份所有檔案 (除了使用者資料)
            for item in self.install_dir.iterdir():
                # 跳過備份目錄本身和使用者資料
                if item.name == "backup" or item.name in self.USER_DATA_FILES:
                    continue
                
                # 跳過其他備份目錄
                if item.name.startswith("backup_"):
                    continue
                
                dest = backup_path / item.name
                
                if item.is_dir():
                    shutil.copytree(item, dest, ignore_dangling_symlinks=True)
                else:
                    shutil.copy2(item, dest)
            
            return backup_path
        
        except Exception as e:
            raise Exception(f"備份失敗: {e}")
    
    def install_update(self, update_dir: Path, progress_callback=None):
        """
        安裝更新
        
        Args:
            update_dir: 更新檔案目錄
            progress_callback: 進度回調函數 (current_file, total_files)
        """
        try:
            # 取得所有需要更新的檔案
            files_to_copy = []
            for root, dirs, files in os.walk(update_dir):
                # 跳過使用者資料目錄
                dirs[:] = [d for d in dirs if d not in self.USER_DATA_FILES]
                
                for file in files:
                    src_path = Path(root) / file
                    rel_path = src_path.relative_to(update_dir)
                    
                    # 跳過使用者資料檔案
                    if any(str(rel_path).startswith(user_file) for user_file in self.USER_DATA_FILES):
                        continue
                    
                    files_to_copy.append(rel_path)
            
            total_files = len(files_to_copy)
            
            # 複製檔案
            for idx, rel_path in enumerate(files_to_copy):
                src = update_dir / rel_path
                dst = self.install_dir / rel_path
                
                # 建立目標目錄
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # 特殊處理 EXE 檔案
                if dst.suffix == '.exe' and dst.exists():
                    # 重新命名舊檔案
                    old_exe = dst.with_suffix('.exe.old')
                    if old_exe.exists():
                        old_exe.unlink()
                    dst.rename(old_exe)
                
                # 複製新檔案
                shutil.copy2(src, dst)
                
                if progress_callback:
                    progress_callback(idx + 1, total_files)
            
            # 刪除舊的 .exe.old 檔案 (如果存在)
            for old_exe in self.install_dir.glob("*.exe.old"):
                try:
                    old_exe.unlink()
                except:
                    pass
        
        except Exception as e:
            raise Exception(f"安裝更新失敗: {e}")
    
    def create_version_file(self, version: str):
        """
        創建版本資訊檔
        
        Args:
            version: 版本號
        """
        version_file = self.install_dir / f"version{version}.txt"
        
        # 刪除舊的版本檔
        for old_version_file in self.install_dir.glob("version*.txt"):
            try:
                old_version_file.unlink()
            except:
                pass
        
        # 建立新版本檔
        content = f"""ChroLens_Mimic

當前版本: {version}
更新日期: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}

========================================
版本更新紀錄
========================================

[2.6.5] - 2025/11/04
  - 重新設計更新系統 (參考 PowerToys)
  - 新增：智能差異備份
  - 新增：版本回退功能
  - 移除：build.bat 打包腳本
  - 改進：更新流程更加穩定和安全

[2.6.4] - 2025/11/03
  - 重新設計打包架構，簡化流程
  - 修正：版本資訊檔改為 version版本號.txt
  - 改進：使用者資料自動保留

========================================
版本還原說明
========================================

如需還原舊版本:
1. 進入 backup\\{self.current_version}\\ 資料夾
2. 將所有檔案複製並覆蓋到程式目錄
3. 重新啟動程式即可還原
"""
        
        version_file.write_text(content, encoding='utf-8')
    
    def rollback_version(self, target_version: str = None) -> bool:
        """
        回退到指定版本
        
        Args:
            target_version: 目標版本號 (None 則回退到最新備份)
        
        Returns:
            bool: 是否成功回退
        """
        try:
            # 找到目標備份
            if target_version:
                backup_path = self.backup_dir / target_version
                if not backup_path.exists():
                    raise Exception(f"找不到版本 {target_version} 的備份")
            else:
                # 找最新的備份
                backups = sorted(self.backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
                if not backups:
                    raise Exception("沒有可用的備份")
                backup_path = backups[0]
                target_version = backup_path.name
            
            # 備份當前版本
            current_backup = self.backup_dir / f"{self.current_version}_before_rollback"
            if current_backup.exists():
                shutil.rmtree(current_backup)
            self.backup_current_version()
            
            # 還原備份
            for item in backup_path.iterdir():
                # 跳過使用者資料
                if item.name in self.USER_DATA_FILES:
                    continue
                
                dest = self.install_dir / item.name
                
                # 刪除現有檔案
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                
                # 複製備份
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            
            # 更新版本檔
            self.create_version_file(target_version)
            
            return True
        
        except Exception as e:
            raise Exception(f"版本回退失敗: {e}")
    
    def cleanup(self):
        """清理臨時檔案"""
        self._cleanup_temp()
    
    def _cleanup_temp(self):
        """清理臨時目錄"""
        if self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def _compare_versions(self, version1: str, version2: str) -> bool:
        """
        比較兩個版本號
        
        Args:
            version1: 版本號 1
            version2: 版本號 2
        
        Returns:
            bool: version1 是否大於 version2
        """
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # 補齊長度
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))
            
            # 逐位比較
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 > v2:
                    return True
                elif v1 < v2:
                    return False
            
            return False
        except:
            return False


def calculate_file_hash(file_path: Path) -> str:
    """計算檔案 MD5 雜湊值"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_size(bytes_size: int) -> str:
    """格式化檔案大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
