"""
ChroLens_Mimic 簡化打包工具
只打包主程式，不生成 updater.exe
updater 改用 updater.bat
"""

import os
import sys
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
        """清理舊檔案"""
        print("\n[1/5] 清理舊檔案...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                print(f"  - 刪除 {dir_path.name}/")
                shutil.rmtree(dir_path)
        
        print("  清理完成\n")
    
    def build_main(self):
        """打包主程式"""
        print("\n[2/5] 打包主程式...")
        
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
        
        # 隱藏控制台模組
        hidden_imports = [
            'pyautogui', 'pynput', 'keyboard',
            'PIL', 'win32gui', 'win32con', 'win32api'
        ]
        for module in hidden_imports:
            cmd.append(f'--hidden-import={module}')
        
        # 主文件
        cmd.append(str(self.main_file))
        
        # 執行打包
        print(f"  執行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=str(self.project_dir))
        
        if result.returncode != 0:
            raise Exception("主程式打包失敗")
        
        print("  主程式打包完成\n")
    
    def copy_updater_bat(self):
        """複製 updater.bat 到輸出目錄"""
        print("\n[3/5] 複製更新器...")
        
        updater_src = self.project_dir / "updater.bat"
        updater_dst = self.output_dir / "updater.bat"
        
        if updater_src.exists():
            shutil.copy2(updater_src, updater_dst)
            print(f"  - 複製 updater.bat")
        else:
            print(f"  警告: 找不到 updater.bat")
        
        print("  更新器複製完成\n")
    
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
            print(f"輸出目錄: {self.output_dir}")
            print(f"ZIP 檔案: {self.dist_dir / 'ChroLens_Mimic.zip'}")
            print(f"{'='*50}\n")
            
        except Exception as e:
            print(f"\n錯誤: {e}")
            sys.exit(1)


if __name__ == "__main__":
    builder = SimpleBuilder()
    builder.build()
