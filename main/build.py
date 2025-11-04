"""
ChroLens_Mimic 打包工具
使用 PyInstaller 打包程式

使用方式:
    python build.py [選項]

選項:
    --clean     清理舊檔案後重新打包
    --no-backup 不備份舊版本
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


class Builder:
    """打包工具"""
    
    def __init__(self, clean=False, no_backup=False):
        self.clean = clean
        self.no_backup = no_backup
        
        # 專案目錄
        self.project_dir = Path(__file__).parent
        self.main_file = self.project_dir / "ChroLens_Mimic.py"
        self.icon_file = self.project_dir.parent / "umi_奶茶色.ico"
        
        # 輸出目錄
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.output_dir = self.dist_dir / "ChroLens_Mimic"
        
        # 讀取版本號
        self.version = self._read_version()
        
        print(f"\n{'='*50}")
        print(f"ChroLens_Mimic 打包工具")
        print(f"版本: {self.version}")
        print(f"{'='*50}\n")
    
    def _read_version(self) -> str:
        """從主程式讀取版本號"""
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('VERSION ='):
                        version = line.split('=')[1].strip().strip('"\'')
                        return version
        except Exception as e:
            print(f"⚠️ 無法讀取版本號: {e}")
            return "unknown"
    
    def cleanup(self):
        """清理舊檔案"""
        print("[1/6] 清理舊檔案...")
        
        dirs_to_clean = [self.build_dir]
        if self.clean:
            dirs_to_clean.append(self.dist_dir)
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                print(f"  刪除: {dir_path.name}")
                shutil.rmtree(dir_path)
        
        # 刪除 spec 檔案
        spec_file = self.project_dir / "ChroLens_Mimic.spec"
        if spec_file.exists():
            spec_file.unlink()
        
        print("✓ 清理完成\n")
    
    def backup_user_data(self) -> dict:
        """備份使用者資料"""
        if self.no_backup or not self.output_dir.exists():
            print("[2/6] 跳過使用者資料備份\n")
            return {}
        
        print("[2/6] 備份使用者資料...")
        
        backup = {}
        user_files = ["scripts", "user_config.json", "last_script.txt"]
        
        for file_name in user_files:
            src = self.output_dir / file_name
            if src.exists():
                print(f"  備份: {file_name}")
                if src.is_dir():
                    backup[file_name] = ('dir', src)
                else:
                    backup[file_name] = ('file', src.read_bytes())
        
        print("✓ 備份完成\n")
        return backup
    
    def build(self):
        """執行打包"""
        print("[3/6] 開始打包...")
        
        # PyInstaller 參數
        args = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconsole",
            "--onedir",
            "-y",
            f"--icon={self.icon_file}",
            f"--add-data={self.icon_file};.",
            "--add-data=TTF;TTF",
            "--name=ChroLens_Mimic",
        ]
        
        # 添加所有模組
        modules = [
            "recorder.py", "lang.py", "script_io.py", "about.py", "mini.py",
            "window_selector.py", "script_parser.py", "config_manager.py",
            "hotkey_manager.py", "script_editor_methods.py", "script_manager.py",
            "ui_components.py", "visual_script_editor.py", "update_manager.py"
        ]
        
        for module in modules:
            args.append(f"--add-data={module};.")
        
        # 隱藏導入
        hidden_imports = [
            "ttkbootstrap", "tkinter", "tkinter.ttk", "PIL", "PIL.Image",
            "PIL.ImageTk", "pynput", "pynput.keyboard", "pynput.mouse",
            "psutil", "win32gui", "win32con", "win32api", "pywintypes"
        ]
        
        for imp in hidden_imports:
            args.append(f"--hidden-import={imp}")
        
        # 收集所有 ttkbootstrap 資料
        args.append("--collect-all=ttkbootstrap")
        
        # 主程式
        args.append(str(self.main_file))
        
        # 執行 PyInstaller
        print(f"\n執行命令:")
        print(f"  {' '.join(args)}\n")
        
        result = subprocess.run(args, cwd=self.project_dir)
        
        if result.returncode != 0:
            print("\n❌ 打包失敗！")
            sys.exit(1)
        
        print("\n✓ 打包完成\n")
    
    def restore_user_data(self, backup: dict):
        """恢復使用者資料"""
        if not backup:
            print("[4/6] 無需恢復使用者資料\n")
            return
        
        print("[4/6] 恢復使用者資料...")
        
        for file_name, (file_type, data) in backup.items():
            dst = self.output_dir / file_name
            print(f"  恢復: {file_name}")
            
            if file_type == 'dir':
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(data, dst)
            else:
                dst.write_bytes(data)
        
        print("✓ 恢復完成\n")
    
    def create_version_file(self):
        """建立版本資訊檔"""
        print("[5/6] 建立版本資訊...")
        
        # 刪除舊版本檔
        for old_file in self.output_dir.glob("version*.txt"):
            old_file.unlink()
        
        version_file = self.output_dir / f"version{self.version}.txt"
        
        content = f"""ChroLens_Mimic

當前版本: {self.version}
打包日期: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}

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

[2.6.3] - 2025/11/03
  - 修復：腳本寫入錯誤處理
  - 改進：統一檔名為 ChroLens_Mimic

========================================
使用說明
========================================

1. 程式會自動檢查 GitHub 上的新版本
2. 更新時會自動備份當前版本到 backup\\版本號\\ 目錄
3. 使用者資料 (scripts、設定檔等) 會自動保留
4. 如需回退版本，請使用程式內建的版本管理功能

========================================
目錄結構
========================================

ChroLens_Mimic\\
├── ChroLens_Mimic.exe     主程式
├── version{self.version}.txt        版本資訊
├── _internal\\             程式核心
├── scripts\\               使用者腳本
├── user_config.json       使用者設定
├── last_script.txt        最後執行的腳本
└── backup\\                版本備份
    └── 舊版本號\\
        └── ... (舊版本檔案)
"""
        
        version_file.write_text(content, encoding='utf-8')
        print(f"  ✓ {version_file.name} 已建立\n")
    
    def cleanup_build_files(self):
        """清理打包產生的暫存檔"""
        print("[6/6] 清理打包暫存檔...")
        
        # 刪除 build 目錄
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        
        # 刪除 spec 檔案
        spec_file = self.project_dir / "ChroLens_Mimic.spec"
        if spec_file.exists():
            spec_file.unlink()
        
        # 刪除錯誤產物
        for old_exe in self.output_dir.glob("*.exe.old"):
            old_exe.unlink()
        
        print("✓ 清理完成\n")
    
    def show_summary(self):
        """顯示打包摘要"""
        print(f"\n{'='*50}")
        print("打包完成！")
        print(f"{'='*50}\n")
        
        print("📦 輸出檔案:")
        print(f"  主程式: {self.output_dir}\\ChroLens_Mimic.exe")
        print(f"  版本檔: {self.output_dir}\\version{self.version}.txt")
        
        # 計算檔案大小
        exe_file = self.output_dir / "ChroLens_Mimic.exe"
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"  大小: {size_mb:.1f} MB")
        
        print(f"\n📂 目錄結構:")
        print(f"  {self.output_dir}\\")
        print(f"  ├── ChroLens_Mimic.exe")
        print(f"  ├── version{self.version}.txt")
        print(f"  ├── _internal\\")
        
        # 檢查使用者資料
        if (self.output_dir / "scripts").exists():
            print(f"  ├── scripts\\ (已保留)")
        if (self.output_dir / "user_config.json").exists():
            print(f"  ├── user_config.json (已保留)")
        if (self.output_dir / "last_script.txt").exists():
            print(f"  └── last_script.txt (已保留)")
        
        print(f"\n{'='*50}\n")
    
    def run(self):
        """執行完整打包流程"""
        try:
            # 1. 清理
            self.cleanup()
            
            # 2. 備份使用者資料
            backup = self.backup_user_data()
            
            # 3. 打包
            self.build()
            
            # 4. 恢復使用者資料
            self.restore_user_data(backup)
            
            # 5. 建立版本檔
            self.create_version_file()
            
            # 6. 清理暫存檔
            self.cleanup_build_files()
            
            # 7. 顯示摘要
            self.show_summary()
            
            return True
        
        except KeyboardInterrupt:
            print("\n\n⚠️ 使用者中斷打包")
            return False
        except Exception as e:
            print(f"\n\n❌ 打包過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(description='ChroLens_Mimic 打包工具')
    parser.add_argument('--clean', action='store_true', help='清理所有舊檔案')
    parser.add_argument('--no-backup', action='store_true', help='不備份使用者資料')
    
    args = parser.parse_args()
    
    builder = Builder(clean=args.clean, no_backup=args.no_backup)
    success = builder.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
