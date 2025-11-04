# ChroLens Mimic - MSI 安裝程式構建指南

## 前置需求

### 1. 安裝 WiX Toolset

**下載地址：** https://wixtoolset.org/releases/

選擇 WiX Toolset v3.11.2（穩定版）

**安裝步驟：**
```powershell
# 1. 下載 wix311.exe
# 2. 執行安裝程式
# 3. 安裝到預設路徑：C:\Program Files (x86)\WiX Toolset v3.11

# 4. 添加到 PATH（可選，方便命令列使用）
$env:Path += ";C:\Program Files (x86)\WiX Toolset v3.11\bin"
```

**驗證安裝：**
```powershell
candle.exe -?
# 應該顯示 WiX Toolset 說明
```

---

## 構建流程

### 步驟 1：使用 PyInstaller 構建程式

```powershell
cd C:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main
python build.py
```

這會產生：
```
dist/
  ChroLens_Mimic/
    ChroLens_Mimic.exe
    _internal/
      python313.dll
      (其他 .pyd, .dll 檔案)
```

### 步驟 2：使用 Heat 收集檔案清單

Heat 是 WiX 工具，用於自動掃描目錄並生成 WXS 片段。

```powershell
# 進入 installer 目錄
cd C:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\installer

# 掃描 _internal 目錄，生成元件清單
& "C:\Program Files (x86)\WiX Toolset v3.11\bin\heat.exe" dir `
    "..\main\dist\ChroLens_Mimic\_internal" `
    -cg InternalFiles `
    -dr INSTALLFOLDER `
    -var var.SourceDir `
    -gg `
    -sfrag `
    -srd `
    -template fragment `
    -out InternalFiles.wxs
```

**參數說明：**
- `-cg InternalFiles`：元件組名稱
- `-dr INSTALLFOLDER`：安裝到的目錄引用
- `-var var.SourceDir`：使用變數引用源目錄
- `-gg`：生成 GUID
- `-sfrag`：壓制片段封裝
- `-srd`：壓制根目錄
- `-out`：輸出檔案

### 步驟 3：編譯 WXS 為 WIXOBJ

```powershell
# 編譯主要的 Product.wxs
& "C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe" `
    Product.wxs `
    -dVersion="2.6.5" `
    -dSourceDir="..\main\dist\ChroLens_Mimic" `
    -arch x64 `
    -ext WixUIExtension

# 編譯 InternalFiles.wxs
& "C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe" `
    InternalFiles.wxs `
    -dSourceDir="..\main\dist\ChroLens_Mimic" `
    -arch x64
```

這會產生：
- `Product.wixobj`
- `InternalFiles.wixobj`

### 步驟 4：連結成 MSI

```powershell
& "C:\Program Files (x86)\WiX Toolset v3.11\bin\light.exe" `
    -out "ChroLens_Mimic_2.6.5.msi" `
    Product.wixobj `
    InternalFiles.wixobj `
    -ext WixUIExtension `
    -cultures:zh-TW `
    -loc Product_zh-TW.wxl
```

**參數說明：**
- `-out`：輸出的 MSI 檔案名
- `-ext WixUIExtension`：啟用 UI 擴展
- `-cultures:zh-TW`：本地化語言
- `-loc`：本地化字串檔案（可選）

---

## 自動化構建腳本

### build_msi.py

```python
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
```

### 使用方法

```powershell
# 在專案根目錄執行
cd C:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\installer
python build_msi.py
```

這會自動執行所有步驟，最終生成 MSI 安裝程式。

---

## 測試 MSI

### 安裝測試

```powershell
# 無聲安裝（用於測試）
msiexec /i ChroLens_Mimic_2.6.5.msi /qn

# 基本 UI 安裝
msiexec /i ChroLens_Mimic_2.6.5.msi /qb

# 完整 UI 安裝（正常用戶使用）
msiexec /i ChroLens_Mimic_2.6.5.msi
```

### 升級測試

```powershell
# 1. 安裝舊版本（例如 2.6.4）
msiexec /i ChroLens_Mimic_2.6.4.msi

# 2. 安裝新版本（例如 2.6.5）
msiexec /i ChroLens_Mimic_2.6.5.msi

# MSI 會自動：
# - 關閉舊版本程序
# - 替換所有檔案
# - 保留用戶設定（scripts/, user_config.json）
```

### 卸載測試

```powershell
# 透過 MSI 卸載
msiexec /x ChroLens_Mimic_2.6.5.msi

# 或在「設定 → 應用程式」中卸載
```

---

## 更新管理器整合

修改 `update_manager.py` 以支援 MSI：

```python
class UpdateManager:
    def download_installer(self, url: str, version: str) -> Path:
        """下載 MSI 安裝程式"""
        msi_name = f"ChroLens_Mimic_{version}.msi"
        msi_path = self.temp_dir / msi_name
        
        # 下載邏輯...
        return msi_path
    
    def install_update(self, msi_path: Path):
        """啟動 MSI 升級安裝"""
        print(f"啟動 MSI 安裝: {msi_path}")
        
        # 使用 msiexec 靜默升級
        subprocess.Popen([
            "msiexec.exe",
            "/i", str(msi_path),
            "/qb",  # 基本 UI（顯示進度條）
            "REINSTALLMODE=damus",  # 強制重新安裝所有檔案
            "REINSTALL=ALL"
        ])
        
        # 主程序可以立即退出，MSI 會自動處理一切
        print("MSI 安裝已啟動，程式即將退出")
        sys.exit(0)
```

---

## 常見問題

### Q1: 如何修改安裝路徑？

修改 `Product.wxs` 中的 `Directory` 結構：

```xml
<!-- 改為 Program Files -->
<Directory Id="ProgramFilesFolder">
    <Directory Id="INSTALLFOLDER" Name="ChroLens Mimic">
    </Directory>
</Directory>
```

### Q2: 如何添加圖示？

在 `Product.wxs` 中添加：

```xml
<Icon Id="icon.ico" SourceFile="$(var.SourceDir)\icon.ico"/>
<Property Id="ARPPRODUCTICON" Value="icon.ico" />
```

### Q3: 如何保留用戶設定？

WiX 會自動保留不在 MSI 中的檔案（如 `user_config.json`, `scripts/`）。

如果需要明確指定，使用 `NeverOverwrite="yes"`：

```xml
<Component>
    <File Source="user_config.json" NeverOverwrite="yes"/>
</Component>
```

### Q4: 如何支援 Per-Machine 安裝？

修改 `Package` 的 `InstallScope`：

```xml
<Package InstallScope="perMachine" />
```

並修改安裝目錄為 Program Files。

---

## 下一步

1. **測試 MSI 構建**
   - 安裝 WiX Toolset
   - 執行 `build_msi.py`
   - 測試安裝/升級/卸載

2. **整合到 CI/CD**
   - GitHub Actions 自動構建 MSI
   - 發布到 Releases

3. **更新文檔**
   - 更新 README.md
   - 提供 MSI 安裝說明

4. **廢棄舊系統**
   - 移除 `updater.exe`
   - 簡化 `update_manager.py`
