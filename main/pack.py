"""
ChroLens_Mimic 簡易打包工具
基於原始打包方式，自動清理並生成 ZIP

使用方法：
    python pack.py

功能：
1. 清理舊的 build/、dist/ 目錄和 .spec 檔案
2. 使用 PyInstaller 打包
3. 自動清理 build/ 和 .spec 檔案
4. 生成 ZIP 壓縮檔

作者: Lucien
日期: 2025-12-01
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

class SimplePacker:
    """簡易打包工具"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.main_file = self.project_dir / "ChroLens_Mimic.py"
        self.icon_file = self.project_dir.parent / "pic" / "umi_奶茶色.ico"
        
        # 建置目錄
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.output_dir = self.dist_dir / "ChroLens_Mimic"
        
        # 版本資訊
        self.version = self._read_version()
        
        print(f"\n{'='*60}")
        print(f"ChroLens_Mimic 簡易打包工具")
        print(f"版本: {self.version}")
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
            print(f"⚠️  無法讀取版本號: {e}")
            return "2.6.6"
    
    def clean_old_files(self):
        """清理舊的打包檔案"""
        print("🧹 步驟 1/4: 清理舊檔案...")
        
        # 清理 build 和 dist
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                print(f"  - 刪除: {dir_path.name}/")
                shutil.rmtree(dir_path, ignore_errors=True)
        
        # 清理 spec 檔案
        for spec_file in self.project_dir.glob("*.spec"):
            print(f"  - 刪除: {spec_file.name}")
            spec_file.unlink()
        
        print("✅ 清理完成\n")
    
    def build(self):
        """使用 PyInstaller 打包"""
        print("📦 步驟 2/4: 打包程式...")
        
        # 檢查圖標
        if not self.icon_file.exists():
            print(f"  ⚠️  找不到圖標: {self.icon_file}")
            print(f"  將不使用圖標")
            icon_arg = ""
            add_icon_arg = ""
        else:
            print(f"  ✓ 找到圖標: {self.icon_file}")
            icon_arg = f"--icon={self.icon_file}"
            add_icon_arg = f"--add-data={self.icon_file};."
        
        # 檢查版本資訊檔案
        version_info_file = self.project_dir / "version_info.txt"
        if version_info_file.exists():
            print(f"  ✓ 找到版本資訊: {version_info_file.name}")
            version_arg = f"--version-file={version_info_file}"
        else:
            print(f"  ⚠️  找不到版本資訊檔案，圖標可能無法正確顯示")
            version_arg = ""
        
        # 構建命令（基於原始打包方式）
        cmd = [
            'pyinstaller',
            '--noconsole',
            '--onedir',
        ]
        
        if icon_arg:
            cmd.append(icon_arg)
        if add_icon_arg:
            cmd.append(add_icon_arg)
        if version_arg:
            cmd.append(version_arg)
        
        cmd.append(str(self.main_file))
        
        print(f"  執行: pyinstaller --noconsole --onedir ...")
        
        # 執行打包
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                print(f"❌ 打包失敗！")
                print(f"錯誤訊息: {result.stderr}")
                sys.exit(1)
            
            # 檢查輸出
            exe_file = self.output_dir / "ChroLens_Mimic.exe"
            if not exe_file.exists():
                print(f"❌ 找不到 exe: {exe_file}")
                sys.exit(1)
            
            print(f"✅ 打包完成: {exe_file}\n")
            
        except Exception as e:
            print(f"❌ 打包失敗: {e}")
            sys.exit(1)
    
    def create_zip(self):
        """創建 ZIP 壓縮檔"""
        print("🗜️  步驟 3/4: 創建 ZIP...")
        
        if not self.output_dir.exists():
            print(f"❌ 找不到輸出目錄: {self.output_dir}")
            sys.exit(1)
        
        zip_name = f"ChroLens_Mimic_{self.version}.zip"
        zip_path = self.dist_dir / zip_name
        
        print(f"  壓縮為: {zip_name}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.output_dir.parent)
                    zipf.write(file_path, arcname)
        
        file_size = zip_path.stat().st_size
        print(f"✅ ZIP 建立完成")
        print(f"  檔案: {zip_path}")
        print(f"  大小: {file_size / (1024*1024):.2f} MB\n")
        
        return zip_path
    
    def clean_build_files(self):
        """清理建置檔案"""
        print("🧹 步驟 4/4: 清理建置檔案...")
        
        # 刪除 build
        if self.build_dir.exists():
            print(f"  - 刪除: {self.build_dir.name}/")
            shutil.rmtree(self.build_dir, ignore_errors=True)
        
        # 刪除 spec
        for spec_file in self.project_dir.glob("*.spec"):
            print(f"  - 刪除: {spec_file.name}")
            spec_file.unlink()
        
        print("✅ 清理完成\n")
    
    def run(self):
        """執行完整流程"""
        try:
            # 1. 清理舊檔案
            self.clean_old_files()
            
            # 2. 打包
            self.build()
            
            # 3. 創建 ZIP
            zip_path = self.create_zip()
            
            # 4. 清理建置檔案
            self.clean_build_files()
            
            # 完成
            print(f"{'='*60}")
            print(f"🎉 打包完成！")
            print(f"{'='*60}")
            print(f"版本: {self.version}")
            print(f"ZIP: {zip_path}")
            print(f"{'='*60}\n")
            
        except KeyboardInterrupt:
            print("\n\n⚠️  使用者中斷操作")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    packer = SimplePacker()
    packer.run()
