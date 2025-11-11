"""
ChroLens_Mimic 簡化打包工具
只打包主程式，不生成 updater.exe
updater 改用 updater.bat
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

class SimpleBuilder:
    """簡化打包工具"""
    
    def __init__(self):
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
        print(f"ChroLens_Mimic 簡化打包工具")
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
            print(f"警告: 無法讀取版本號: {e}")
            return "unknown"
    
    def clean(self):
        """清理舊檔案（如果失敗則跳過）"""
        print("\n[1/5] 清理舊檔案...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                print(f"  - 嘗試刪除 {dir_path.name}/")
                try:
                    shutil.rmtree(dir_path, ignore_errors=False)
                    print(f"  ✓ 已刪除 {dir_path.name}/")
                except Exception as e:
                    print(f"  ⚠ 無法完全刪除 {dir_path.name}/ - 將使用現有目錄")
                    print(f"    原因: 某些檔案可能正在使用中")
                    # 不中斷流程，繼續打包
        
        print("  清理完成\n")
    
    def build_main(self):
        """打包主程式"""
        print("\n[2/5] 打包主程式...")
        
        # 檢查並終止可能佔用檔案的程序
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if 'ChroLens_Mimic.exe' in proc.info['name']:
                    print(f"  - 發現運行中的程序，正在關閉...")
                    proc.kill()
                    import time
                    time.sleep(2)
        except ImportError:
            print("  - 提示：安裝 psutil 可以自動關閉佔用程序")
            print("    pip install psutil")
        except Exception as e:
            print(f"  - 無法自動關閉程序: {e}")
        
        # PyInstaller 命令
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            '--onedir',
            '--windowed',
            '--name=ChroLens_Mimic',
        ]
        
        # 添加圖示
        if self.icon_file.exists():
            cmd.append(f'--icon={self.icon_file}')
        
        # 添加數據文件
        ttf_dir = self.project_dir / "TTF"
        if ttf_dir.exists():
            cmd.append(f'--add-data={ttf_dir};TTF')
        
        # 添加更新系統模組
        update_system_file = self.project_dir / "update_system.py"
        if update_system_file.exists():
            cmd.append(f'--add-data={update_system_file};.')
        
        # 隱藏控制台模組（特別注意 pynput 相關）
        hidden_imports = [
            # 快捷鍵與輸入控制（打包後必需）
            'pynput', 'pynput.keyboard', 'pynput.mouse', 
            'pynput.keyboard._win32', 'pynput.mouse._win32',
            'keyboard', 'mouse', 'pyautogui',
            # Windows API
            'win32gui', 'win32con', 'win32api', 'pywintypes',
            # GUI 與圖像
            'PIL', 'ttkbootstrap',
            # 其他模組
            'update_system'
        ]
        for module in hidden_imports:
            cmd.append(f'--hidden-import={module}')
        
        # 主文件
        cmd.append(str(self.main_file))
        
        # 執行打包
        print(f"  執行 PyInstaller...")
        try:
            result = subprocess.run(cmd, cwd=str(self.project_dir), 
                                   capture_output=False, text=True)
            
            if result.returncode != 0:
                raise Exception("主程式打包失敗")
        except Exception as e:
            print(f"\n錯誤: {e}")
            print("\n可能的原因：")
            print("  1. dist 目錄中的檔案被其他程序佔用")
            print("  2. 請執行 '清理並重啟.bat' 後重試")
            raise
        
        print("  主程式打包完成\n")
    
    def copy_updater_bat(self):
        """複製必要文件到輸出目錄"""
        print("\n[3/5] 複製必要文件...")
        
        # 創建必要的目錄
        scripts_dir = self.output_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        
        backup_dir = self.output_dir / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        # 複製 updater.bat (如果存在)
        updater_src = self.project_dir / "updater.bat"
        updater_dst = self.output_dir / "updater.bat"
        if updater_src.exists():
            shutil.copy2(updater_src, updater_dst)
            print(f"  - 複製 updater.bat")
        
        # 創建空的配置文件（如果不存在）
        config_file = self.output_dir / "user_config.json"
        if not config_file.exists():
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            print(f"  - 創建 user_config.json")
        
        # 創建示例腳本說明
        readme_file = scripts_dir / "README.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write("此目錄用於存放您的腳本文件\n")
            f.write("所有錄製的腳本都會自動儲存在這裡\n")
            f.write("\n更新程式時，此目錄的內容會被保留\n")
        print(f"  - 創建 scripts/README.txt")
        
        print("  必要文件複製完成\n")
    
    def create_version_file(self):
        """創建版本文件"""
        print("\n[4/5] 創建版本文件...")
        
        version_file = self.output_dir / f"version{self.version}.txt"
        
        # 讀取版本歷史 (從頂部註釋中提取)
        version_history = []
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                in_history = False
                for line in f:
                    if '=== 版本更新紀錄 ===' in line:
                        in_history = True
                        continue
                    elif in_history:
                        if '=== 未來功能規劃 ===' in line or 'pyinstaller' in line.lower():
                            break
                        if line.strip().startswith('#'):
                            # 移除開頭的 # 符號
                            clean_line = line.lstrip('#').rstrip()
                            if clean_line:  # 不添加空行
                                version_history.append(clean_line)
        except Exception as e:
            print(f"  警告: 無法讀取版本歷史: {e}")
        
        # 寫入版本文件
        content = f"""ChroLens_Mimic v{self.version}
{'='*50}

版本更新紀錄:
{chr(10).join(version_history)}

打包時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  - 創建 {version_file.name}")
        print("  版本文件創建完成\n")
    
    def create_zip(self):
        """創建 ZIP 包"""
        print("\n[5/5] 創建 ZIP 包...")
        
        zip_path = self.dist_dir / f"ChroLens_Mimic.zip"
        
        if zip_path.exists():
            zip_path.unlink()
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.output_dir.parent)
                    zipf.write(file_path, arcname)
                    print(f"  - 添加: {arcname}")
        
        zip_size = zip_path.stat().st_size / (1024 * 1024)
        print(f"\n  ZIP 包創建完成: {zip_path.name} ({zip_size:.2f} MB)\n")
    
    def build_setup_installer(self):
        """打包安裝器程式"""
        print("\n[6/7] 打包安裝器...")
        
        setup_script = self.project_dir / "setup_installer.py"
        
        if not setup_script.exists():
            print(f"  警告: 找不到 setup_installer.py，跳過")
            return
        
        # PyInstaller 命令
        cmd = [
            'pyinstaller',
            '--clean',
            '--noconfirm',
            '--onefile',  # 單一 exe
            '--console',  # 顯示控制台
            '--name=ChroLens_Mimic_Setup',
        ]
        
        # 添加圖示
        if self.icon_file.exists():
            cmd.append(f'--icon={self.icon_file}')
        
        # 主文件
        cmd.append(str(setup_script))
        
        # 執行打包
        print(f"  執行命令: {' '.join(cmd[:5])}...")
        result = subprocess.run(cmd, cwd=str(self.project_dir), 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
        
        if result.returncode != 0:
            print(f"  警告: 安裝器打包失敗")
            return
        
        # 複製安裝器到 dist 目錄
        setup_exe_src = self.dist_dir / "ChroLens_Mimic_Setup.exe"
        setup_exe_dst = self.dist_dir / "ChroLens_Mimic_Setup.exe"
        
        if setup_exe_src.exists():
            print(f"  - 創建 ChroLens_Mimic_Setup.exe")
        else:
            print(f"  警告: 找不到生成的安裝器")
        
        print("  安裝器打包完成\n")
    
    def create_release_package(self):
        """創建發布包（安裝器 + ZIP）"""
        print("\n[7/7] 創建發布包...")
        
        # 複製 ZIP 到安裝器旁邊
        setup_dir = self.dist_dir / "setup"
        setup_dir.mkdir(exist_ok=True)
        
        # 複製安裝器
        setup_exe = self.dist_dir / "ChroLens_Mimic_Setup.exe"
        if setup_exe.exists():
            shutil.copy2(setup_exe, setup_dir / f"ChroLens_Mimic_Setup_{self.version}.exe")
            print(f"  - 複製安裝器")
        
        # 複製 ZIP
        zip_file = self.dist_dir / "ChroLens_Mimic.zip"
        if zip_file.exists():
            shutil.copy2(zip_file, setup_dir / f"ChroLens_Mimic.zip")
            print(f"  - 複製 ZIP 檔案")
        
        # 創建使用說明
        readme = setup_dir / "README.txt"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(f"""ChroLens_Mimic v{self.version} 安裝包
{'='*50}

安裝方式 1: 使用安裝器（推薦）
  1. 執行 ChroLens_Mimic_Setup_{self.version}.exe
  2. 安裝器會自動解壓並安裝到指定目錄
  3. 完成後自動啟動程式

安裝方式 2: 手動解壓
  1. 解壓 ChroLens_Mimic.zip
  2. 執行 ChroLens_Mimic.exe

更新方式:
  - 程式內建自動更新功能
  - 或下載新版安裝器直接執行即可

{'='*50}
ChroLens Studio - {datetime.now().strftime('%Y-%m-%d')}
""")
        
        print(f"\n  發布包創建完成: {setup_dir}\n")
    
    def build(self):
        """執行完整打包流程"""
        try:
            self.clean()
            self.build_main()
            self.copy_updater_bat()
            self.create_version_file()
            self.create_zip()
            
            print(f"\n{'='*50}")
            print(f"打包完成!")
            print(f"程式目錄: {self.output_dir}")
            print(f"ZIP 檔案: {self.dist_dir / 'ChroLens_Mimic.zip'}")
            print(f"{'='*50}\n")
            
        except Exception as e:
            print(f"\n錯誤: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    builder = SimpleBuilder()
    builder.build()
