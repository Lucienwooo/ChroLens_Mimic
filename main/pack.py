"""
ChroLens_Mimic 優化打包工具
採用保守優化策略，確保所有功能正常運作

【重要】此為主要打包工具，所有打包相關修改都應在此檔案進行！

優化原則：
1. 只排除確定不使用的大型模組（torch, tensorflow, pandas 等）
2. 保留所有可能被間接使用的依賴（如 scipy 的部分模組）
3. 不刪除任何 OpenCV、PIL、keyboard、mouse 相關檔案
4. 優先保證功能完整性，其次才是檔案大小

使用方法：
    python pack.py
    或執行 打包.bat

功能：
1. 清理舊的 build/、dist/ 目錄和 .spec 檔案
2. 使用 PyInstaller 保守優化打包
3. 移除確定不需要的檔案（torch, onnx 等）
4. 計算檔案大小並生成報告
5. 創建 ZIP 壓縮檔
6. 自動清理 build/ 和 .spec 檔案

預期效果：
- 在保證功能完整的前提下適度減少檔案大小
- 所有錄製、播放、圖片辨識、OCR 功能正常

作者: Lucien + AI Assistant
日期: 2025-12-04
"""

import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime

class SimplePacker:
    """優化打包工具 - 排除不必要的大型依賴"""
    
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
        print(f"ChroLens_Mimic 保守優化打包工具")
        print(f"版本: {self.version}")
        print(f"策略: 保證功能完整性優先")
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
        print("步驟 1/6: 清理舊檔案...")
        
        # 清理 build 和 dist
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                print(f"  - 刪除: {dir_path.name}/")
                shutil.rmtree(dir_path, ignore_errors=True)
        
        # 清理 spec 檔案
        for spec_file in self.project_dir.glob("*.spec"):
            print(f"  - 刪除: {spec_file.name}")
            spec_file.unlink()
        
        print("清理完成\n")
    
    def build(self):
        """使用保守優化的 PyInstaller 設定打包"""
        print("步驟 2/6: 保守優化打包...")
        print("  只排除確定不使用的模組...")
        
        # 檢查圖標
        if not self.icon_file.exists():
            print(f"  找不到圖標: {self.icon_file}")
            print(f"  將不使用圖標")
            icon_arg = ""
            add_icon_arg = ""
        else:
            print(f"  找到圖標: {self.icon_file}")
            icon_arg = f"--icon={self.icon_file}"
            add_icon_arg = f"--add-data={self.icon_file};."
        
        # 檢查版本資訊檔案
        version_info_file = self.project_dir / "version_info.txt"
        if version_info_file.exists():
            print(f"  找到版本資訊: {version_info_file.name}")
            version_arg = f"--version-file={version_info_file}"
        else:
            print(f"  找不到版本資訊檔案，圖標可能無法正確顯示")
            version_arg = ""
        
        # ⚠️ 保守優化：只排除確定不使用的大型模組
        # 注意：過度排除會導致功能損壞！
        excluded_modules = [
            # 深度學習框架（確定不使用）
            'torch',
            'torchvision', 
            'torchaudio',
            'tensorflow',
            'tensorboard',
            
            # 科學計算（可能被 OpenCV 間接引入，但我們不直接使用）
            'scipy.optimize',
            'scipy.sparse',
            'scipy.linalg',
            
            # ONNX（確定不使用）
            'onnxruntime',
            'onnx',
            
            # 數據分析（確定不使用）
            'pandas',
            'matplotlib',
            'sklearn',
            
            # 開發工具（確定不使用）
            'IPython',
            'jupyter',
            'notebook',
            'sphinx',
            'pytest',
            
            # 測試模組（確定不使用）
            'unittest',
            'tkinter.test',
        ]
        
        # 構建命令
        cmd = [
            'pyinstaller',
            '--noconsole',
            '--onedir',
            '--clean',
            '--noconfirm',
        ]
        
        # 添加排除項
        for module in excluded_modules:
            cmd.append(f'--exclude-module={module}')
        
        if icon_arg:
            cmd.append(icon_arg)
        if add_icon_arg:
            cmd.append(add_icon_arg)
        if version_arg:
            cmd.append(version_arg)
        
        cmd.append(str(self.main_file))
        
        print(f"  排除 {len(excluded_modules)} 個不必要的模組")
        print(f"  執行優化打包...")
        
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
                print(f"打包失敗！")
                print(f"錯誤訊息: {result.stderr}")
                sys.exit(1)
            
            # 檢查輸出
            exe_file = self.output_dir / "ChroLens_Mimic.exe"
            if not exe_file.exists():
                print(f"找不到 exe: {exe_file}")
                sys.exit(1)
            
            print(f"打包完成: {exe_file}\n")
            
        except Exception as e:
            print(f"打包失敗: {e}")
            sys.exit(1)
    
    def remove_unnecessary_files(self):
        """從輸出目錄中移除確定不需要的檔案（保守策略）"""
        print("步驟 3/6: 移除不必要的檔案...")
        
        if not self.output_dir.exists():
            print("  輸出目錄不存在，跳過清理")
            return
        
        # ⚠️ 只刪除確定不會影響功能的檔案
        remove_patterns = [
            # 編譯快取（安全刪除）
            '**/*.pyc',
            '**/__pycache__',
            
            # 測試目錄（安全刪除）
            '**/test',
            '**/tests',
            '**/Test',
            '**/Tests',
            
            # 深度學習框架檔案（確定不使用）
            '**/torch*.dll',
            '**/torch*.pyd',
            '**/onnx*.dll',
            '**/onnx*.pyd',
            
            # 特定大型 DLL（確定不使用）
            '**/fbgemm.dll',
        ]
        
        removed_count = 0
        saved_space = 0
        
        for pattern in remove_patterns:
            for item in self.output_dir.rglob(pattern.replace('**/', '')):
                try:
                    size = item.stat().st_size if item.is_file() else 0
                    if item.is_file():
                        item.unlink()
                        removed_count += 1
                        saved_space += size
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        removed_count += 1
                except Exception:
                    pass
        
        if removed_count > 0:
            print(f"已移除 {removed_count} 個項目，節省 {saved_space/1024/1024:.2f} MB\n")
        else:
            print(f"沒有找到需要移除的檔案\n")
    
    def calculate_size(self):
        """計算輸出目錄大小"""
        print("步驟 4/6: 計算大小...")
        
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
        print("步驟 5/6: 創建 ZIP...")
        
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
        print("步驟 6/6: 清理建置檔案...")
        
        # 刪除 build
        if self.build_dir.exists():
            print(f"  - 刪除: {self.build_dir.name}/")
            shutil.rmtree(self.build_dir, ignore_errors=True)
        
        # 刪除 spec
        for spec_file in self.project_dir.glob("*.spec"):
            print(f"  - 刪除: {spec_file.name}")
            spec_file.unlink()
        
        print("清理完成\n")
    
    def run(self):
        """執行完整流程"""
        try:
            # 1. 清理舊檔案
            self.clean_old_files()
            
            # 2. 優化打包
            self.build()
            
            # 3. 移除不必要的檔案
            self.remove_unnecessary_files()
            
            # 4. 計算大小
            uncompressed_size = self.calculate_size()
            
            # 5. 創建 ZIP
            zip_path, compressed_size = self.create_zip()
            
            # 6. 清理建置檔案
            self.clean_build_files()
            
            # 完成
            print(f"{'='*60}")
            print(f"保守優化打包完成！")
            print(f"{'='*60}")
            print(f"版本: {self.version}")
            print(f"解壓縮大小: {uncompressed_size:.2f} MB")
            print(f"壓縮檔大小: {compressed_size:.2f} MB")
            print(f"壓縮率: {(1 - compressed_size/uncompressed_size)*100:.1f}%")
            print(f"ZIP: {zip_path}")
            print(f"{'='*60}")
            print(f"提示：已保守優化，確保所有功能正常運作")
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
    packer = SimplePacker()
    packer.run()
