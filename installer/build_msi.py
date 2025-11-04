"""
ChroLens Mimic MSI 構建腳本
自動化整個構建流程
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


class MSIBuilder:
    """MSI 安裝程式構建器"""
    
    def __init__(self, version: str):
        self.version = version
        self.root_dir = Path(__file__).parent.parent
        self.main_dir = self.root_dir / "main"
        self.installer_dir = self.root_dir / "installer"
        self.dist_dir = self.main_dir / "dist" / "ChroLens_Mimic"
        
        # WiX 工具路徑
        self.wix_bin = Path(r"C:\Program Files (x86)\WiX Toolset v3.11\bin")
        self.candle = self.wix_bin / "candle.exe"
        self.light = self.wix_bin / "light.exe"
        self.heat = self.wix_bin / "heat.exe"
        
        # 檢查 WiX 是否安裝
        if not self.candle.exists():
            raise FileNotFoundError(
                "找不到 WiX Toolset！\n"
                "請從 https://wixtoolset.org/releases/ 下載並安裝"
            )
    
    def build_exe(self):
        """步驟 1：使用 PyInstaller 構建程式"""
        print("\n=== 步驟 1：構建 PyInstaller 程式 ===")
        os.chdir(self.main_dir)
        
        result = subprocess.run([sys.executable, "build.py"], capture_output=True)
        
        if result.returncode != 0:
            print("❌ PyInstaller 構建失敗")
            print(result.stderr.decode('utf-8', errors='ignore'))
            return False
        
        print("✅ PyInstaller 構建完成")
        return True
    
    def harvest_files(self):
        """步驟 2：使用 Heat 收集檔案清單"""
        print("\n=== 步驟 2：使用 Heat 收集 _internal 檔案 ===")
        os.chdir(self.installer_dir)
        
        internal_dir = self.dist_dir / "_internal"
        if not internal_dir.exists():
            print(f"❌ 找不到 _internal 目錄: {internal_dir}")
            return False
        
        cmd = [
            str(self.heat), "dir",
            str(internal_dir),
            "-cg", "InternalFiles",
            "-dr", "INSTALLFOLDER",
            "-var", "var.SourceDir",
            "-gg",
            "-sfrag",
            "-srd",
            "-template", "fragment",
            "-out", "InternalFiles.wxs"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Heat 執行失敗")
            print(result.stderr)
            return False
        
        print("✅ InternalFiles.wxs 生成完成")
        
        # 修正 InternalFiles.wxs 中的路徑
        self._fix_internal_files_wxs()
        return True
    
    def _fix_internal_files_wxs(self):
        """修正 Heat 生成的 WXS 中的路徑"""
        wxs_path = self.installer_dir / "InternalFiles.wxs"
        content = wxs_path.read_text(encoding='utf-8')
        
        # Heat 會生成 SourceDir\_internal，需要改成 SourceDir
        content = content.replace(
            'Source="$(var.SourceDir)\\_internal\\',
            'Source="$(var.SourceDir)\\_internal\\'
        )
        
        wxs_path.write_text(content, encoding='utf-8')
    
    def compile_wxs(self):
        """步驟 3：編譯 WXS 為 WIXOBJ"""
        print("\n=== 步驟 3：編譯 WXS 檔案 ===")
        os.chdir(self.installer_dir)
        
        # 編譯 Product.wxs
        print("編譯 Product.wxs...")
        cmd_product = [
            str(self.candle),
            "Product.wxs",
            f"-dVersion={self.version}",
            f"-dSourceDir={self.dist_dir}",
            "-arch", "x64",
            "-ext", "WixUIExtension"
        ]
        
        result = subprocess.run(cmd_product, capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Product.wxs 編譯失敗")
            print(result.stderr)
            return False
        
        # 編譯 InternalFiles.wxs
        print("編譯 InternalFiles.wxs...")
        cmd_internal = [
            str(self.candle),
            "InternalFiles.wxs",
            f"-dSourceDir={self.dist_dir}",
            "-arch", "x64"
        ]
        
        result = subprocess.run(cmd_internal, capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ InternalFiles.wxs 編譯失敗")
            print(result.stderr)
            return False
        
        print("✅ 編譯完成")
        return True
    
    def link_msi(self):
        """步驟 4：連結成 MSI"""
        print("\n=== 步驟 4：連結 MSI 安裝程式 ===")
        os.chdir(self.installer_dir)
        
        msi_name = f"ChroLens_Mimic_{self.version}.msi"
        
        cmd = [
            str(self.light),
            "-out", msi_name,
            "Product.wixobj",
            "InternalFiles.wixobj",
            "-ext", "WixUIExtension",
            "-spdb"  # 壓制 PDB 生成
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ MSI 連結失敗")
            print(result.stderr)
            return False
        
        print(f"✅ MSI 構建完成: {msi_name}")
        
        # 顯示檔案資訊
        msi_path = self.installer_dir / msi_name
        size_mb = msi_path.stat().st_size / (1024 * 1024)
        print(f"   檔案大小: {size_mb:.2f} MB")
        print(f"   檔案路徑: {msi_path}")
        
        return True
    
    def clean_temp_files(self):
        """清理臨時檔案"""
        print("\n=== 清理臨時檔案 ===")
        os.chdir(self.installer_dir)
        
        patterns = ["*.wixobj", "*.wixpdb", "InternalFiles.wxs"]
        for pattern in patterns:
            for file in self.installer_dir.glob(pattern):
                file.unlink()
                print(f"刪除: {file.name}")
    
    def build(self):
        """完整構建流程"""
        print("=" * 60)
        print("ChroLens Mimic MSI 構建器")
        print(f"版本: {self.version}")
        print("=" * 60)
        
        steps = [
            ("構建 PyInstaller 程式", self.build_exe),
            ("收集檔案清單", self.harvest_files),
            ("編譯 WXS", self.compile_wxs),
            ("連結 MSI", self.link_msi),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ 構建失敗於: {step_name}")
                return False
        
        self.clean_temp_files()
        
        print("\n" + "=" * 60)
        print("✅ MSI 構建成功！")
        print("=" * 60)
        return True


def main():
    """主函數"""
    # 從 ChroLens_Mimic.py 讀取版本號
    main_file = Path(__file__).parent.parent / "main" / "ChroLens_Mimic.py"
    
    with open(main_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('VERSION = '):
                version = line.split('=')[1].strip().strip('"\'')
                break
        else:
            print("❌ 無法讀取版本號")
            return
    
    builder = MSIBuilder(version)
    success = builder.build()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
