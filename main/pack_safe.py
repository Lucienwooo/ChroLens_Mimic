"""
ChroLens_Mimic 安全打包工具
不排除任何模組，確保功能完整性

使用方法：python pack_safe.py
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path

class SafePacker:
    """安全打包工具 - 不排除任何模組"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.main_file = self.project_dir / "ChroLens_Mimic.py"
        self.icon_file = self.project_dir.parent / "pic" / "umi_奶茶色.ico"
        
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.output_dir = self.dist_dir / "ChroLens_Mimic"
        
        self.version = self._read_version()
        
        print(f"\n{'='*60}")
        print(f"ChroLens_Mimic 安全打包工具")
        print(f"版本: {self.version}")
        print(f"策略: 保留所有依賴，確保功能完整")
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
            print(f"無法讀取版本號: {e}")
            return "2.7.2"
    
    def clean_old_files(self):
        """清理舊的打包檔案"""
        print("步驟 1/5: 清理舊檔案...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                print(f"  - 刪除: {dir_path.name}/")
                shutil.rmtree(dir_path, ignore_errors=True)
        
        for spec_file in self.project_dir.glob("*.spec"):
            print(f"  - 刪除: {spec_file.name}")
            spec_file.unlink()
        
        print("清理完成\n")
    
    def build(self):
        """使用標準 PyInstaller 設定打包（不排除任何模組）"""
        print("步驟 2/5: 標準打包...")
        print("  保留所有依賴，確保功能完整\n")
        
        # 檢查圖標
        icon_arg = f"--icon={self.icon_file}" if self.icon_file.exists() else ""
        add_icon_arg = f"--add-data={self.icon_file};." if self.icon_file.exists() else ""
        
        # 檢查版本資訊
        version_info_file = self.project_dir / "version_info.txt"
        version_arg = f"--version-file={version_info_file}" if version_info_file.exists() else ""
        
        # 構建命令（標準打包，不排除任何模組）
        cmd = [
            'pyinstaller',
            '--noconsole',
            '--onedir',
            '--clean',
            '--noconfirm',
        ]
        
        if icon_arg:
            cmd.append(icon_arg)
        if add_icon_arg:
            cmd.append(add_icon_arg)
        if version_arg:
            cmd.append(version_arg)
        
        cmd.append(str(self.main_file))
        
        print(f"  執行: {' '.join(cmd[:5])} ...")
        
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
                print(f"打包失敗！")
                print(f"錯誤訊息: {result.stderr}")
                sys.exit(1)
            
            exe_file = self.output_dir / "ChroLens_Mimic.exe"
            if not exe_file.exists():
                print(f"找不到 exe: {exe_file}")
                sys.exit(1)
            
            print(f"打包完成: {exe_file}\n")
            
        except Exception as e:
            print(f"打包失敗: {e}")
            sys.exit(1)
    
    def calculate_size(self):
        """計算輸出目錄大小"""
        print("步驟 3/5: 計算大小...")
        
        if not self.output_dir.exists():
            print("  輸出目錄不存在")
            return 0
        
        total_size = 0
        file_count = 0
        
        for item in self.output_dir.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1
        
        size_mb = total_size / (1024 * 1024)
        print(f"  檔案數量: {file_count}")
        print(f"  總大小: {size_mb:.2f} MB")
        print(f"計算完成\n")
        
        return size_mb
    
    def create_zip(self):
        """創建 ZIP 壓縮檔"""
        print("步驟 4/5: 創建 ZIP...")
        
        if not self.output_dir.exists():
            print(f"找不到輸出目錄: {self.output_dir}")
            sys.exit(1)
        
        zip_name = f"ChroLens_Mimic_{self.version}.zip"
        zip_path = self.dist_dir / zip_name
        
        print(f"  壓縮為: {zip_name}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.output_dir.parent)
                    zipf.write(file_path, arcname)
        
        file_size = zip_path.stat().st_size
        print(f"ZIP 建立完成")
        print(f"  檔案: {zip_path}")
        print(f"  大小: {file_size / (1024*1024):.2f} MB\n")
        
        return zip_path, file_size / (1024*1024)
    
    def clean_build_files(self):
        """清理建置檔案"""
        print("步驟 5/5: 清理建置檔案...")
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir, ignore_errors=True)
        
        for spec_file in self.project_dir.glob("*.spec"):
            spec_file.unlink()
        
        print("清理完成\n")
    
    def run(self):
        """執行完整流程"""
        try:
            # 1. 清理舊檔案
            self.clean_old_files()
            
            # 2. 標準打包
            self.build()
            
            # 3. 計算大小
            uncompressed_size = self.calculate_size()
            
            # 4. 創建 ZIP
            zip_path, compressed_size = self.create_zip()
            
            # 5. 清理建置檔案
            self.clean_build_files()
            
            # 完成
            print(f"{'='*60}")
            print(f"安全打包完成！")
            print(f"{'='*60}")
            print(f"版本: {self.version}")
            print(f"解壓縮大小: {uncompressed_size:.2f} MB")
            print(f"壓縮檔大小: {compressed_size:.2f} MB")
            print(f"壓縮率: {(1 - compressed_size/uncompressed_size)*100:.1f}%")
            print(f"ZIP: {zip_path}")
            print(f"{'='*60}")
            print(f"提示：使用標準打包，所有功能應正常運作")
            print(f"{'='*60}\n")
            
        except KeyboardInterrupt:
            print("\n\n使用者中斷操作")
            sys.exit(1)
        except Exception as e:
            print(f"\n發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    packer = SafePacker()
    packer.run()
