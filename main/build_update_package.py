"""
ChroLens_Mimic 更新包打包工具
只打包與主程式不同的檔案，用於覆蓋更新
"""

import os
import sys
import json
import shutil
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime

class UpdatePackageBuilder:
    """更新包打包工具"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.main_file = self.project_dir / "ChroLens_Mimic.py"
        
        # 讀取當前版本（代碼中的版本）
        self.current_version = self._read_version()
        
        # 主程式目錄（假設已經打包過）
        self.main_program_dir = self.project_dir / "dist" / "ChroLens_Mimic"
        
        # 更新包輸出目錄
        self.update_dir = self.project_dir / "updates"
        self.update_dir.mkdir(exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"ChroLens_Mimic 更新包打包工具")
        print(f"當前版本: {self.current_version}")
        print(f"{'='*60}\n")
    
    def _read_version(self) -> str:
        """從主程式讀取版本號"""
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('VERSION ='):
                        version = line.split('=')[1].strip().strip('"\'')
                        return version
        except Exception as e:
            print(f"錯誤: 無法讀取版本號: {e}")
            sys.exit(1)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """計算檔案的 SHA256 雜湊值"""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            print(f"警告: 無法計算 {file_path} 的雜湊值: {e}")
            return ""
    
    def _compare_files(self, source: Path, target: Path) -> bool:
        """比較兩個檔案是否相同（使用雜湊值）"""
        if not target.exists():
            return False  # 目標檔案不存在，需要更新
        
        # 比較檔案大小（快速檢查）
        if source.stat().st_size != target.stat().st_size:
            return False
        
        # 比較雜湊值（精確檢查）
        source_hash = self._get_file_hash(source)
        target_hash = self._get_file_hash(target)
        
        return source_hash == target_hash
    
    def find_changed_files(self) -> list:
        """找出需要更新的檔案"""
        print("\n[1/4] 分析檔案差異...")
        
        if not self.main_program_dir.exists():
            print(f"錯誤: 找不到主程式目錄: {self.main_program_dir}")
            print("請先執行「完整打包.bat」生成主程式")
            sys.exit(1)
        
        changed_files = []
        
        # 需要檢查的 Python 檔案（源代碼）
        source_files = [
            "ChroLens_Mimic.py",
            "visual_script_editor.py",
            "recorder.py",
            "script_parser.py",
            "script_io.py",
            "script_manager.py",
            "script_editor_methods.py",
            "config_manager.py",
            "hotkey_manager.py",
            "update_manager_v2.py",
            "update_system.py",
            "ui_components.py",
            "window_selector.py",
            "mini.py",
            "about.py",
            "lang.py",
            "multi_monitor.py",
            "performance_optimizer.py",
            "schedule_manager.py",
        ]
        
        print("\n  檢查 Python 源代碼:")
        for filename in source_files:
            source_file = self.project_dir / filename
            target_file = self.main_program_dir / filename
            
            if source_file.exists():
                if not target_file.exists():
                    print(f"    + {filename} (新檔案)")
                    changed_files.append(source_file)
                elif not self._compare_files(source_file, target_file):
                    print(f"    * {filename} (已修改)")
                    changed_files.append(source_file)
                else:
                    print(f"    - {filename} (無變化)")
        
        # 檢查版本文件
        version_file = self.project_dir / f"version{self.current_version}.txt"
        if version_file.exists():
            print(f"\n  版本文件:")
            print(f"    + version{self.current_version}.txt")
            changed_files.append(version_file)
        
        # 檢查 updater.bat
        updater_file = self.project_dir / "updater.bat"
        if updater_file.exists():
            target_updater = self.main_program_dir / "updater.bat"
            if not target_updater.exists() or not self._compare_files(updater_file, target_updater):
                print(f"\n  更新器:")
                print(f"    * updater.bat (已修改)")
                changed_files.append(updater_file)
        
        print(f"\n  ✓ 找到 {len(changed_files)} 個需要更新的檔案")
        return changed_files
    
    def create_update_package(self, changed_files: list):
        """創建更新包"""
        print(f"\n[2/4] 創建更新包...")
        
        if not changed_files:
            print("  沒有需要更新的檔案")
            return None
        
        # 更新包檔名
        zip_filename = f"ChroLens_Mimic_{self.current_version}_Update.zip"
        zip_path = self.update_dir / zip_filename
        
        # 刪除舊的更新包
        if zip_path.exists():
            zip_path.unlink()
            print(f"  - 刪除舊的更新包")
        
        # 創建 ZIP
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in changed_files:
                # 使用相對於專案目錄的路徑作為壓縮包內的路徑
                arcname = file_path.name
                zipf.write(file_path, arcname)
                print(f"    + {arcname}")
        
        zip_size = zip_path.stat().st_size / 1024
        print(f"\n  ✓ 更新包已創建: {zip_filename} ({zip_size:.2f} KB)")
        
        return zip_path
    
    def create_update_info(self, changed_files: list, zip_path: Path):
        """創建更新資訊檔案"""
        print(f"\n[3/4] 創建更新資訊...")
        
        # 讀取版本歷史（從最新的版本更新記錄）
        changelog = self._extract_latest_changelog()
        
        # 計算檔案雜湊值
        file_checksums = {}
        for file_path in changed_files:
            file_hash = self._get_file_hash(file_path)
            file_checksums[file_path.name] = file_hash
        
        # 計算 ZIP 的雜湊值
        zip_hash = self._get_file_hash(zip_path)
        
        # 更新資訊
        update_info = {
            "version": self.current_version,
            "release_date": datetime.now().strftime("%Y-%m-%d"),
            "changelog": changelog,
            "files_to_update": [f.name for f in changed_files],
            "download_url": f"https://github.com/Lucienwooo/ChroLens_Mimic/releases/download/v{self.current_version}/{zip_path.name}",
            "file_checksums": file_checksums,
            "package_checksum": {
                "algorithm": "SHA256",
                "value": zip_hash
            },
            "package_size": zip_path.stat().st_size,
            "update_instructions": [
                "1. 關閉正在運行的 ChroLens Mimic",
                "2. 解壓更新包到程式安裝目錄",
                "3. 覆蓋同名檔案",
                "4. 重新啟動程式"
            ]
        }
        
        # 儲存 JSON
        json_filename = f"UPDATE_PACKAGE_{self.current_version}.json"
        json_path = self.update_dir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(update_info, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ 更新資訊已創建: {json_filename}")
        print(f"  ✓ SHA256: {zip_hash}")
        
        return json_path
    
    def _extract_latest_changelog(self) -> dict:
        """從主程式中提取最新版本的更新日誌"""
        changelog = {
            "fixes": [],
            "improvements": [],
            "technical": []
        }
        
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 找到版本區段
                lines = content.split('\n')
                in_version_section = False
                current_version_found = False
                
                for line in lines:
                    # 檢查是否進入版本更新記錄區段
                    if '=== 版本更新紀錄 ===' in line:
                        in_version_section = True
                        continue
                    
                    # 檢查是否離開版本區段
                    if in_version_section and ('=== 未來功能規劃 ===' in line or 'pyinstaller' in line.lower()):
                        break
                    
                    # 在版本區段中
                    if in_version_section:
                        # 找到當前版本
                        if f'[{self.current_version}]' in line:
                            current_version_found = True
                            continue
                        
                        # 如果找到下一個版本標記，停止
                        if current_version_found and line.strip().startswith('# ['):
                            break
                        
                        # 提取更新內容
                        if current_version_found:
                            clean_line = line.strip().lstrip('#').strip()
                            if clean_line and clean_line.startswith('-'):
                                clean_line = clean_line.lstrip('-').strip()
                                
                                # 分類
                                if '修復' in clean_line or '修正' in clean_line or '🐛' in clean_line:
                                    changelog['fixes'].append(clean_line)
                                elif '新增' in clean_line or '改進' in clean_line or '優化' in clean_line or '⚡' in clean_line or '🚀' in clean_line:
                                    changelog['improvements'].append(clean_line)
                                elif '技術' in clean_line or '架構' in clean_line or '🔧' in clean_line:
                                    changelog['technical'].append(clean_line)
                                else:
                                    changelog['improvements'].append(clean_line)
        
        except Exception as e:
            print(f"  警告: 無法提取更新日誌: {e}")
        
        return changelog
    
    def create_readme(self, zip_path: Path):
        """創建更新包使用說明"""
        print(f"\n[4/4] 創建使用說明...")
        
        readme_path = self.update_dir / f"更新說明_{self.current_version}.txt"
        
        content = f"""ChroLens Mimic v{self.current_version} 更新包
{'='*60}

此更新包包含從舊版本更新到 v{self.current_version} 所需的檔案。

【使用方法】
1. 方式一：自動更新（推薦）
   - 在程式中點擊「檢查更新」
   - 程式會自動下載並安裝更新

2. 方式二：手動更新
   - 關閉正在運行的 ChroLens Mimic
   - 解壓 {zip_path.name} 到程式安裝目錄
   - 選擇「覆蓋同名檔案」
   - 重新啟動程式

【注意事項】
⚠ 更新前請先關閉程式
⚠ 您的腳本和設定檔案會被保留
⚠ 建議更新前備份重要資料

【檔案說明】
- ChroLens_Mimic.py: 主程式邏輯
- visual_script_editor.py: 視覺化腳本編輯器
- version{self.current_version}.txt: 版本資訊
- 其他 .py 檔案: 各功能模組

【更新內容】
請查看 version{self.current_version}.txt 或更新資訊檔案

【技術資訊】
- 更新包大小: {zip_path.stat().st_size / 1024:.2f} KB
- 校驗碼 (SHA256): {self._get_file_hash(zip_path)}
- 建立時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
ChroLens Studio
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ 使用說明已創建: {readme_path.name}")
    
    def build(self):
        """執行更新包打包流程"""
        try:
            # 1. 找出變更的檔案
            changed_files = self.find_changed_files()
            
            if not changed_files:
                print("\n沒有需要更新的檔案，取消打包")
                return
            
            # 2. 創建更新包
            zip_path = self.create_update_package(changed_files)
            
            if not zip_path:
                return
            
            # 3. 創建更新資訊
            json_path = self.create_update_info(changed_files, zip_path)
            
            # 4. 創建使用說明
            self.create_readme(zip_path)
            
            # 完成
            print(f"\n{'='*60}")
            print(f"✅ 更新包打包完成！")
            print(f"{'='*60}")
            print(f"\n輸出位置:")
            print(f"  📦 更新包: {zip_path}")
            print(f"  📄 更新資訊: {json_path}")
            print(f"  📝 使用說明: updates/更新說明_{self.current_version}.txt")
            print(f"\n下一步:")
            print(f"  1. 測試更新包（手動解壓到主程式目錄）")
            print(f"  2. 上傳到 GitHub Release:")
            print(f"     https://github.com/Lucienwooo/ChroLens_Mimic/releases/new")
            print(f"  3. Tag: v{self.current_version}")
            print(f"  4. 上傳 {zip_path.name}")
            print()
            
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    builder = UpdatePackageBuilder()
    builder.build()
