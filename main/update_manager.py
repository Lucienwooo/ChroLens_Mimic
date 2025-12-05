"""
自動更新管理器
基於 GitHub Releases 的自動更新系統

設計理念：
1. 從 GitHub Releases 獲取版本資訊
2. 下載更新包（zip 格式）
3. 解壓到臨時目錄
4. 使用批次腳本在程式關閉後替換檔案
5. 重新啟動程式

作者: Lucien
版本: 1.0.0
日期: 2025/11/12
"""

import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import tempfile
import shutil
import subprocess
import threading
import datetime
import ctypes
from pathlib import Path
from typing import Optional, Dict, Callable


class UpdateManager:
    """更新管理器"""
    
    # GitHub 資訊
    GITHUB_REPO = "Lucienwooo/ChroLens_Mimic"
    API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    
    def __init__(self, current_version: str, logger: Optional[Callable] = None):
        """
        初始化更新管理器
        
        Args:
            current_version: 當前版本號（如 "2.6.3"）
            logger: 日誌函數
        """
        self.current_version = current_version
        self._logger = logger or (lambda msg: print(f"[UpdateManager] {msg}"))
        
        # 更新狀態
        self._checking = False
        self._downloading = False
        self._progress = 0
        self._status_message = ""
        
        # 更新資訊
        self._latest_version = None
        self._release_notes = ""
        self._download_url = None
        self._asset_name = None
        self._update_script_path = None  # 批次腳本路徑
        
        # 回調函數
        self._on_progress = None  # 進度回調 (progress: float, message: str)
        self._on_complete = None  # 完成回調
        self._on_error = None     # 錯誤回調 (error: str)
        
        # 檢查環境權限
        self._check_environment()
    
    def _check_environment(self):
        """
        檢查執行環境與權限
        
        檢查項目：
        1. 是否在受保護的目錄（如 C:\\Program Files）
        2. 是否有管理員權限
        3. 目標目錄是否有寫入權限
        """
        try:
            if getattr(sys, 'frozen', False):
                # 打包環境
                current_dir = os.path.dirname(sys.executable)
            else:
                # 開發環境
                current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 檢查是否在受保護目錄
            protected_paths = [
                os.path.expandvars(r'%ProgramFiles%'),
                os.path.expandvars(r'%ProgramFiles(x86)%'),
                os.path.expandvars(r'%SystemRoot%'),
            ]
            
            is_protected = any(
                current_dir.lower().startswith(path.lower()) 
                for path in protected_paths if path
            )
            
            # 檢查管理員權限（僅 Windows）
            is_admin = False
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                pass
            
            # 檢查寫入權限
            test_file = os.path.join(current_dir, f".write_test_{os.getpid()}.tmp")
            has_write_permission = False
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                has_write_permission = True
            except:
                pass
            
            # 記錄環境資訊
            self._logger(f"環境檢查:")
            self._logger(f"  目錄: {current_dir}")
            self._logger(f"  受保護目錄: {'是' if is_protected else '否'}")
            self._logger(f"  管理員權限: {'是' if is_admin else '否'}")
            self._logger(f"  寫入權限: {'是' if has_write_permission else '否'}")
            
            # 警告：需要權限但沒有
            if is_protected and not is_admin:
                self._logger("⚠️  警告: 程式安裝在受保護目錄，但未以管理員身分執行")
                self._logger("   更新可能會失敗，請考慮以管理員身分執行")
            
            if not has_write_permission:
                self._logger("⚠️  警告: 目標目錄沒有寫入權限")
                self._logger("   更新將無法完成，請檢查權限設定")
                
        except Exception as e:
            self._logger(f"環境檢查失敗: {e}")
    
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """設定進度回調"""
        self._on_progress = callback
    
    def set_complete_callback(self, callback: Callable):
        """設定完成回調"""
        self._on_complete = callback
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """設定錯誤回調"""
        self._on_error = callback
    
    def _update_progress(self, progress: float, message: str):
        """
        更新進度
        
        ⚠️ 執行緒安全警告：
        此方法會從背景執行緒呼叫 _on_progress 回調函數。
        如果回調函數需要更新 GUI（如 Tkinter/PyQt），請確保使用適當的執行緒安全機制：
        - Tkinter: 使用 root.after() 或 queue
        - PyQt: 使用 QMetaObject.invokeMethod() 或 signals/slots
        - 否則可能導致程式崩潰
        """
        self._progress = progress
        self._status_message = message
        self._logger(f"[{progress:.1f}%] {message}")
        
        if self._on_progress:
            try:
                self._on_progress(progress, message)
            except Exception as e:
                self._logger(f"⚠️ 進度回調函數錯誤: {e}")
    
    def _report_error(self, error: str):
        """
        報告錯誤
        
        ⚠️ 執行緒安全警告：
        此方法會從背景執行緒呼叫 _on_error 回調函數。
        請參考 _update_progress 的警告。
        """
        self._logger(f"錯誤: {error}")
        
        if self._on_error:
            try:
                self._on_error(error)
            except Exception as e:
                self._logger(f"⚠️ 錯誤回調函數錯誤: {e}")
    
    def check_for_updates(self) -> Optional[Dict]:
        """
        檢查更新（同步）
        
        Returns:
            如果有更新，返回更新資訊字典；否則返回 None
            {
                'version': '2.6.4',
                'notes': '更新內容...',
                'download_url': 'https://...',
                'asset_name': 'ChroLens_Mimic_v2.6.4.zip',
                'has_update': True
            }
        """
        if self._checking:
            self._logger("已在檢查更新中...")
            return None
        
        self._checking = True
        try:
            self._update_progress(5, "正在連線到 GitHub...")
            
            # 發送 API 請求
            req = urllib.request.Request(self.API_URL)
            req.add_header('User-Agent', 'ChroLens_Mimic')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            self._update_progress(30, "正在解析版本資訊...")
            
            # 解析版本資訊
            latest_version = data.get('tag_name', '').lstrip('v').lstrip('V')
            release_notes = data.get('body', '無更新說明')
            
            # 尋找 zip 檔案（更強健的匹配邏輯）
            assets = data.get('assets', [])
            download_url = None
            asset_name = None
            
            # 優先順序匹配策略
            # 1. 精確匹配：ChroLens_Mimic_{version}.zip
            # 2. 模糊匹配：包含 ChroLens_Mimic 和版本號
            # 3. 寬鬆匹配：任何包含 ChroLens_Mimic 的 zip
            
            matching_assets = []
            for asset in assets:
                name = asset.get('name', '')
                if name.endswith('.zip') and 'ChroLens_Mimic' in name:
                    # 計算匹配優先級
                    priority = 0
                    
                    # 精確匹配版本號
                    expected_name = f"ChroLens_Mimic_{latest_version}.zip"
                    if name == expected_name:
                        priority = 100
                    # 包含版本號
                    elif latest_version in name:
                        priority = 50
                    # 基本匹配
                    else:
                        priority = 10
                    
                    matching_assets.append({
                        'name': name,
                        'url': asset.get('browser_download_url'),
                        'priority': priority
                    })
            
            # 按優先級排序，選擇最佳匹配
            if matching_assets:
                matching_assets.sort(key=lambda x: x['priority'], reverse=True)
                best_match = matching_assets[0]
                download_url = best_match['url']
                asset_name = best_match['name']
                self._logger(f"找到更新包: {asset_name} (優先級: {best_match['priority']})")
            else:
                self._logger("警告: 找不到更新包（.zip 檔案）")
                self._logger(f"可用的資產檔案: {[a.get('name') for a in assets]}")
            
            self._update_progress(50, "正在比較版本...")
            
            # 比較版本
            has_update = self._compare_versions(self.current_version, latest_version)
            
            self._update_progress(100, "檢查完成")
            
            # 儲存資訊
            self._latest_version = latest_version
            self._release_notes = release_notes
            self._download_url = download_url
            self._asset_name = asset_name
            
            result = {
                'version': latest_version,
                'notes': release_notes,
                'download_url': download_url,
                'asset_name': asset_name,
                'has_update': has_update
            }
            
            return result if has_update else None
            
        except urllib.error.URLError as e:
            error = f"無法連線到 GitHub: {str(e)}\n請檢查網路連線"
            self._report_error(error)
            return None
        except Exception as e:
            error = f"檢查更新失敗: {str(e)}"
            self._report_error(error)
            return None
        finally:
            self._checking = False
    
    def _compare_versions(self, current: str, latest: str) -> bool:
        """
        比較版本號（支援語意化版本）
        
        Args:
            current: 當前版本（如 "2.6.3" 或 "2.7.0-beta"）
            latest: 最新版本（如 "2.6.4" 或 "2.7.0"）
        
        Returns:
            如果 latest > current 返回 True
        
        支援格式：
        - 標準版本: "2.6.3"
        - 預發布版本: "2.7.0-beta", "3.0.0-rc.1"
        - 非數字部分會被視為 0
        """
        def parse_version(version_str: str) -> list:
            """解析版本字串為可比較的列表"""
            # 移除 'v' 前綴（如果有）
            version_str = version_str.lstrip('vV')
            
            # 分離主版本號和預發布標籤
            if '-' in version_str:
                main_version, prerelease = version_str.split('-', 1)
            else:
                main_version, prerelease = version_str, ''
            
            # 解析主版本號
            parts = []
            for part in main_version.split('.'):
                try:
                    parts.append(int(part))
                except ValueError:
                    # 非數字部分視為 0
                    parts.append(0)
            
            # 預發布版本比正式版本低
            # 例如: 2.7.0-beta < 2.7.0
            has_prerelease = 1 if prerelease else 0
            
            return parts + [has_prerelease]
        
        try:
            current_parts = parse_version(current)
            latest_parts = parse_version(latest)
            
            # 補齊長度（不包含預發布標記）
            max_len = max(len(current_parts) - 1, len(latest_parts) - 1)
            
            # 補齊主版本號部分
            while len(current_parts) - 1 < max_len:
                current_parts.insert(-1, 0)
            while len(latest_parts) - 1 < max_len:
                latest_parts.insert(-1, 0)
            
            # 比較版本
            # 先比較主版本號（不包含預發布標記）
            for i in range(max_len):
                if latest_parts[i] > current_parts[i]:
                    return True
                elif latest_parts[i] < current_parts[i]:
                    return False
            
            # 主版本號相同，比較預發布標記
            # has_prerelease=0 表示正式版，has_prerelease=1 表示預發布版
            # 正式版（0）> 預發布版（1）
            current_prerelease = current_parts[-1]
            latest_prerelease = latest_parts[-1]
            
            return latest_prerelease < current_prerelease
            
        except Exception as e:
            self._logger(f"版本比較錯誤: {e}")
            # 發生錯誤時，保守地返回 False（不更新）
            return False
    
    def download_and_install(self):
        """下載並安裝更新（在背景執行緒中運行）"""
        if self._downloading:
            self._logger("已在下載中...")
            return
        
        if not self._download_url:
            self._report_error("沒有可用的更新包下載連結")
            return
        
        # 在背景執行緒中執行
        thread = threading.Thread(target=self._download_and_install_thread, daemon=True)
        thread.start()
    
    def _download_and_install_thread(self):
        """下載與安裝的執行緒函數"""
        self._downloading = True
        temp_zip = None
        temp_extract_dir = None
        
        # === 步驟 0: 先寫入初始日誌 ===
        self._logger("開始更新流程...")
        
        # 確定當前執行檔路徑
        if getattr(sys, 'frozen', False):
            # 打包後的執行檔
            current_exe = sys.executable
            current_dir = os.path.dirname(current_exe)
            env_type = "打包環境"
        else:
            # 開發環境
            current_exe = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_exe)
            env_type = "開發環境"
        
        self._logger(f"環境類型: {env_type}")
        self._logger(f"當前目錄: {current_dir}")
        self._logger(f"執行檔: {current_exe}")
        
        # 嘗試寫入初始日誌
        log_written = False
        initial_log_path = None
        
        # 嘗試 1: 主程式目錄
        try:
            initial_log_path = os.path.join(current_dir, "update_log.txt")
            self._logger(f"嘗試寫入主目錄日誌: {initial_log_path}")
            
            with open(initial_log_path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("ChroLens_Mimic 更新程式 - 初始日誌\n")
                f.write(f"更新時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*60 + "\n")
                f.write(f"當前版本: {self.current_version}\n")
                f.write(f"目標版本: {self._latest_version}\n")
                f.write(f"環境類型: {env_type}\n")
                f.write(f"主程式目錄: {current_dir}\n")
                f.write(f"執行檔: {current_exe}\n")
                f.write("\n開始下載更新...\n\n")
            
            log_written = True
            self._logger(f"✅ 初始日誌已寫入: {initial_log_path}")
            
        except Exception as e:
            self._logger(f"❌ 無法寫入主目錄日誌: {e}")
        
        # 嘗試 2: 臨時目錄
        if not log_written:
            try:
                initial_log_path = os.path.join(tempfile.gettempdir(), "ChroLens_update_log.txt")
                self._logger(f"嘗試寫入臨時目錄日誌: {initial_log_path}")
                
                with open(initial_log_path, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write("ChroLens_Mimic 更新程式 - 初始日誌 (臨時目錄)\n")
                    f.write(f"更新時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n")
                    f.write(f"當前版本: {self.current_version}\n")
                    f.write(f"目標版本: {self._latest_version}\n")
                    f.write(f"環境類型: {env_type}\n")
                    f.write(f"主程式目錄: {current_dir}\n")
                    f.write(f"執行檔: {current_exe}\n")
                    f.write("\n注意: 無法寫入主目錄，使用臨時目錄\n")
                    f.write("開始下載更新...\n\n")
                
                log_written = True
                self._logger(f"✅ 初始日誌已寫入臨時目錄: {initial_log_path}")
                
            except Exception as e:
                self._logger(f"❌ 無法寫入臨時目錄日誌: {e}")
        
        # 嘗試 3: 桌面 (最後的備用方案)
        if not log_written:
            try:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                initial_log_path = os.path.join(desktop, "ChroLens_update_log.txt")
                self._logger(f"嘗試寫入桌面日誌: {initial_log_path}")
                
                with open(initial_log_path, 'w', encoding='utf-8') as f:
                    f.write("="*60 + "\n")
                    f.write("ChroLens_Mimic 更新程式 - 初始日誌 (桌面)\n")
                    f.write(f"更新時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n")
                    f.write(f"當前版本: {self.current_version}\n")
                    f.write(f"目標版本: {self._latest_version}\n")
                    f.write(f"環境類型: {env_type}\n")
                    f.write(f"主程式目錄: {current_dir}\n")
                    f.write(f"執行檔: {current_exe}\n")
                    f.write("\n注意: 無法寫入主目錄和臨時目錄，使用桌面\n")
                    f.write("開始下載更新...\n\n")
                
                log_written = True
                self._logger(f"✅ 初始日誌已寫入桌面: {initial_log_path}")
                
            except Exception as e:
                self._logger(f"❌ 無法寫入桌面日誌: {e}")
        
        if not log_written:
            self._logger("⚠️  警告: 所有位置都無法寫入日誌！")
        else:
            self._logger(f"✅ 日誌檔案位置: {initial_log_path}")
        
        try:
            # === 步驟 1: 下載更新包 ===
            self._update_progress(0, "準備下載更新包...")
            
            # 建立臨時檔案
            temp_dir = tempfile.gettempdir()
            temp_zip = os.path.join(temp_dir, self._asset_name or "update.zip")
            
            self._update_progress(5, f"開始下載: {self._asset_name}")
            
            # 下載檔案（帶進度）
            self._download_file_with_progress(self._download_url, temp_zip, 5, 40)
            
            # === 步驟 2: 解壓更新包 ===
            self._update_progress(45, "正在解壓更新包...")
            
            temp_extract_dir = os.path.join(temp_dir, f"ChroLens_Update_{self._latest_version}")
            if os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)
            os.makedirs(temp_extract_dir)
            
            # 🔒 Zip Slip 安全防護：防止目錄遍歷攻擊
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    # 解析目標路徑
                    member_path = os.path.join(temp_extract_dir, member)
                    # 正規化路徑並檢查是否在目標目錄內
                    normalized_path = os.path.normpath(member_path)
                    if not normalized_path.startswith(os.path.normpath(temp_extract_dir)):
                        raise Exception(f"安全警告：檢測到潛在的 Zip Slip 攻擊 - {member}")
                    # 安全解壓
                    zip_ref.extract(member, temp_extract_dir)
            
            self._update_progress(60, "解壓完成")
            self._logger(f"✅ ZIP 解壓完成：{len(os.listdir(temp_extract_dir))} 個檔案/資料夾")
            
            # === 步驟 3: 準備安裝腳本 ===
            self._update_progress(65, "準備安裝...")
            
            # 確定當前執行檔路徑
            if getattr(sys, 'frozen', False):
                # 打包後的執行檔
                current_exe = sys.executable
                current_dir = os.path.dirname(current_exe)
            else:
                # 開發環境
                current_exe = os.path.abspath(__file__)
                current_dir = os.path.dirname(current_exe)
            
            # 尋找更新檔案目錄（可能在 zip 根目錄或子目錄）
            update_source = self._find_update_source(temp_extract_dir)
            if not update_source:
                raise Exception("更新包結構錯誤：找不到可執行檔")
            
            self._logger(f"✅ 找到更新來源：{update_source}")
            self._update_progress(70, "正在生成安裝腳本...")
            
            # 建立更新腳本
            update_script = self._create_update_script(
                update_source, 
                current_dir,
                current_exe
            )
            
            self._logger(f"✅ 批次腳本已生成：{update_script}")
            self._update_progress(90, "安裝腳本已準備")
            
            # === 步驟 4: 準備安裝（不啟動批次腳本） ===
            self._update_progress(95, "更新已準備完成")
            
            # 更新日誌：添加批次腳本信息
            if log_written and initial_log_path:
                try:
                    with open(initial_log_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n下載完成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"批次腳本路徑: {update_script}\n")
                        f.write(f"更新來源: {update_source}\n")
                        f.write("\n批次腳本已準備，等待使用者確認...\n\n")
                    self._logger(f"已更新日誌: {initial_log_path}")
                except Exception as e:
                    self._logger(f"無法更新日誌: {e}")
            
            # 儲存批次腳本路徑，供後續使用
            self._update_script_path = update_script
            
            self._update_progress(100, "更新準備完成")
            self._logger("=" * 60)
            self._logger("✅ 更新已準備完成，等待使用者確認執行")
            self._logger(f"   批次腳本：{update_script}")
            self._logger(f"   更新來源：{update_source}")
            self._logger(f"   目標目錄：{current_dir}")
            self._logger("=" * 60)
            
            # 通知完成（但不啟動批次腳本）
            if self._on_complete:
                self._on_complete()
            
        except Exception as e:
            error = f"更新失敗: {str(e)}"
            self._report_error(error)
            
            # 清理失敗的下載資源
            try:
                if temp_zip and os.path.exists(temp_zip):
                    os.remove(temp_zip)
                    self._logger(f"已清理臨時檔案: {temp_zip}")
            except Exception as cleanup_error:
                self._logger(f"清理臨時檔案失敗: {cleanup_error}")
            
            try:
                if temp_extract_dir and os.path.exists(temp_extract_dir):
                    shutil.rmtree(temp_extract_dir)
                    self._logger(f"已清理解壓目錄: {temp_extract_dir}")
            except Exception as cleanup_error:
                self._logger(f"清理解壓目錄失敗: {cleanup_error}")
                
        finally:
            self._downloading = False
    
    def _download_file_with_progress(self, url: str, dest: str, start_progress: float, end_progress: float):
        """
        下載檔案並更新進度
        
        Args:
            url: 下載連結
            dest: 目標檔案路徑
            start_progress: 起始進度（0-100）
            end_progress: 結束進度（0-100）
        """
        response = None
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'ChroLens_Mimic')
            
            response = urllib.request.urlopen(req, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 計算進度
                    if total_size > 0:
                        download_percent = downloaded / total_size
                        current_progress = start_progress + (end_progress - start_progress) * download_percent
                        
                        # 格式化大小
                        size_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        
                        self._update_progress(
                            current_progress,
                            f"下載中: {size_mb:.1f} MB / {total_mb:.1f} MB"
                        )
        finally:
            # 確保資源正確關閉
            if response:
                try:
                    response.close()
                except:
                    pass
    
    def _find_update_source(self, extract_dir: str) -> Optional[str]:
        """
        尋找更新檔案來源目錄
        
        Args:
            extract_dir: 解壓目錄
        
        Returns:
            包含可執行檔的目錄路徑，或 None
        """
        # 檢查根目錄
        if self._is_valid_update_source(extract_dir):
            return extract_dir
        
        # 檢查子目錄（一層）
        for item in os.listdir(extract_dir):
            item_path = os.path.join(extract_dir, item)
            if os.path.isdir(item_path) and self._is_valid_update_source(item_path):
                return item_path
        
        return None
    
    def _is_valid_update_source(self, path: str) -> bool:
        """檢查目錄是否包含有效的更新檔案"""
        if getattr(sys, 'frozen', False):
            # 打包後：檢查是否有 .exe
            exe_files = [f for f in os.listdir(path) if f.endswith('.exe')]
            return len(exe_files) > 0
        else:
            # 開發環境：檢查是否有 .py
            return os.path.exists(os.path.join(path, 'ChroLens_Mimic.py'))
    
    def _create_update_script(self, source_dir: str, target_dir: str, exe_path: str) -> str:
        """
        建立更新批次腳本
        
        Args:
            source_dir: 更新檔案來源目錄
            target_dir: 目標安裝目錄
            exe_path: 可執行檔路徑
        
        Returns:
            批次腳本的路徑
        """
        script_path = os.path.join(tempfile.gettempdir(), "ChroLens_Update.bat")
        
        # ✅ 2.7.1 成功邏輯：使用 _latest_version（新版本）生成連結檔案
        # 備份檔案使用當前版本，連結檔案使用新版本
        backup_version_txt = f"version{self.current_version}.txt"
        github_link_txt = f"{self._latest_version}.txt"  # 關鍵：必須用新版本
        github_url = f"https://github.com/{self.GITHUB_REPO}/releases/tag/v{self._latest_version}"
        
        # 生成日誌檔案路徑
        log_file = os.path.join(target_dir, "update_log.txt")
        
        # ✅ 採用 2.7.1 簡化版批次腳本 + 增強檔案鎖定處理
        script_content = f"""@echo off
chcp 65001 >nul

REM 建立日誌檔案
set LOG_FILE="{log_file}"
echo ======================================== > %LOG_FILE%
echo ChroLens_Mimic 更新程式 >> %LOG_FILE%
echo 更新時間: %date% %time% >> %LOG_FILE%
echo ======================================== >> %LOG_FILE%
echo. >> %LOG_FILE%

echo ========================================
echo ChroLens_Mimic 更新程式
echo ========================================
echo.

REM 等待主程式關閉（最多 30 秒）
echo 正在等待程式關閉...
echo 正在等待程式關閉... >> %LOG_FILE%
set /a count=0
:wait_loop
tasklist /FI "IMAGENAME eq ChroLens_Mimic.exe" 2>NUL | find /I /N "ChroLens_Mimic.exe">NUL
if "%ERRORLEVEL%"=="0" (
    if %count% LSS 30 (
        timeout /t 1 /nobreak >nul
        set /a count+=1
        goto wait_loop
    ) else (
        echo 警告: 程式仍在運行，嘗試強制結束... >> %LOG_FILE%
        taskkill /F /IM ChroLens_Mimic.exe 2>NUL
        timeout /t 2 /nobreak >nul
    )
) else (
    echo 程式已關閉 >> %LOG_FILE%
)

REM ✅ 關鍵修復：額外等待 5 秒確保檔案鎖定完全釋放
echo 等待檔案鎖定釋放... >> %LOG_FILE%
timeout /t 5 /nobreak >nul

echo 開始更新檔案...
echo 開始更新檔案... >> %LOG_FILE%

REM 建立 backup 資料夾
if not exist "{target_dir}\\backup" (
    mkdir "{target_dir}\\backup" >nul 2>&1
    echo 建立 backup 資料夾 >> %LOG_FILE%
)

REM 備份舊版本的 version.txt 到 backup 資料夾
if exist "{target_dir}\\{backup_version_txt}" (
    echo 備份舊版本檔案...
    echo 備份 {backup_version_txt} >> %LOG_FILE%
    move /Y "{target_dir}\\{backup_version_txt}" "{target_dir}\\backup\\{backup_version_txt}" >nul 2>&1
)

REM 在 backup 資料夾生成 GitHub 下載連結檔案
echo 生成版本資訊...
echo 生成版本資訊: {github_link_txt} >> %LOG_FILE%
echo {github_url} > "{target_dir}\\backup\\{github_link_txt}"

REM 刪除舊版 exe（使用重命名+重試機制）
echo 移除舊版本檔案...
echo 處理舊版 exe... >> %LOG_FILE%

REM 先刪除可能存在的 .old 檔案
if exist "{target_dir}\\ChroLens_Mimic.exe.old" (
    echo 刪除 .exe.old 檔案 >> %LOG_FILE%
    del /F /Q "{target_dir}\\ChroLens_Mimic.exe.old" >nul 2>&1
)

REM 將舊的 exe 重命名為 .old，然後嘗試刪除
if exist "{target_dir}\\ChroLens_Mimic.exe" (
    echo 重命名舊版 exe... >> %LOG_FILE%
    ren "{target_dir}\\ChroLens_Mimic.exe" "ChroLens_Mimic.exe.old" >nul 2>&1
    if exist "{target_dir}\\ChroLens_Mimic.exe.old" (
        REM 重試刪除 3 次
        set /a retry=0
        :delete_retry
        del /F /Q "{target_dir}\\ChroLens_Mimic.exe.old" >nul 2>&1
        if exist "{target_dir}\\ChroLens_Mimic.exe.old" (
            if %retry% LSS 3 (
                timeout /t 1 /nobreak >nul
                set /a retry+=1
                goto delete_retry
            ) else (
                echo 警告: 無法刪除舊版 exe，但會繼續更新 >> %LOG_FILE%
            )
        ) else (
            echo 舊版 exe 已刪除 >> %LOG_FILE%
        )
    )
)

REM 複製新檔案（覆蓋所有檔案）
echo 正在安裝更新...
echo 複製新檔案... >> %LOG_FILE%
echo 來源目錄: {source_dir} >> %LOG_FILE%
echo 目標目錄: {target_dir} >> %LOG_FILE%

xcopy /E /I /Y /Q "{source_dir}\\*" "{target_dir}\\" >> %LOG_FILE% 2>&1

if errorlevel 1 (
    echo 更新失敗！錯誤碼: %errorlevel% >> %LOG_FILE%
    echo 更新失敗！請查看 update_log.txt
    pause
    exit /b 1
) else (
    echo 檔案複製成功 >> %LOG_FILE%
)

echo 更新完成！
echo 更新完成！ >> %LOG_FILE%

REM 清理臨時檔案
echo 清理臨時檔案...
echo 清理臨時檔案: {os.path.dirname(source_dir)} >> %LOG_FILE%
rd /S /Q "{os.path.dirname(source_dir)}" >nul 2>&1

REM 重新啟動程式
echo 正在重新啟動程式...
echo 重新啟動程式: {exe_path} >> %LOG_FILE%
timeout /t 2 /nobreak >nul
start "" "{exe_path}"

echo 腳本執行完成 >> %LOG_FILE%

REM 刪除自己
(goto) 2>nul & del "%~f0"
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_path
    
    def get_current_progress(self) -> tuple:
        """獲取當前進度"""
        return (self._progress, self._status_message)
    
    def execute_update_script(self) -> bool:
        """
        執行更新腳本
        
        Returns:
            是否成功啟動腳本
        """
        if not self._update_script_path or not os.path.exists(self._update_script_path):
            self._logger("錯誤: 找不到更新腳本")
            return False
        
        try:
            # 確定當前目錄
            if getattr(sys, 'frozen', False):
                current_dir = os.path.dirname(sys.executable)
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # 啟動批次腳本
            process = subprocess.Popen(
                self._update_script_path,
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=current_dir
            )
            self._logger(f"✅ 批次腳本已啟動，PID: {process.pid}")
            self._logger(f"   腳本路徑: {self._update_script_path}")
            return True
            
        except Exception as e:
            self._logger(f"❌ 啟動批次腳本失敗: {e}")
            return False


# ============================================
# 使用示例
# ============================================
if __name__ == "__main__":
    def on_progress(progress, message):
        print(f"[{progress:.1f}%] {message}")
    
    def on_complete():
        print("更新完成！")
    
    def on_error(error):
        print(f"錯誤: {error}")
    
    # 建立更新管理器
    updater = UpdateManager("2.6.3")
    updater.set_progress_callback(on_progress)
    updater.set_complete_callback(on_complete)
    updater.set_error_callback(on_error)
    
    # 檢查更新
    print("檢查更新中...")
    update_info = updater.check_for_updates()
    
    if update_info:
        print(f"\n發現新版本: {update_info['version']}")
        print(f"更新內容:\n{update_info['notes'][:200]}...")
        
        # 模擬下載（實際使用時需要用戶確認）
        # updater.download_and_install()
    else:
        print("已是最新版本")
