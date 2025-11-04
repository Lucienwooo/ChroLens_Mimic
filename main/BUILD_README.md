# ChroLens_Mimic 打包與更新系統

## 📦 打包方式 (v2.6.5+)

### 方式 1: 使用 Python 腳本 (推薦)

```powershell
# 基本打包
python build.py

# 清理所有舊檔案後重新打包
python build.py --clean

# 不備份使用者資料 (首次打包)
python build.py --no-backup
```

### 方式 2: 使用 PowerShell (快速)

```powershell
# 執行快速打包
.\build.ps1
```

## 📋 打包流程

1. **清理舊檔案** (build 目錄、spec 檔案)
2. **備份使用者資料** (scripts、user_config.json、last_script.txt)
3. **執行 PyInstaller** 打包主程式和所有模組
4. **恢復使用者資料** 到新版本
5. **建立版本資訊檔** (version{版本號}.txt)
6. **清理暫存檔** (刪除 build 目錄和 .exe.old)

## 📁 輸出結構

```
dist\ChroLens_Mimic\
├── ChroLens_Mimic.exe       ✅ 主程式
├── version2.6.5.txt          ✅ 版本資訊
├── _internal\                ✅ 程式核心
├── scripts\                  ✅ 使用者腳本 (自動保留)
├── user_config.json          ✅ 使用者設定 (自動保留)
├── last_script.txt           ✅ 最後腳本 (自動保留)
└── backup\                   ✅ 舊版本備份
    └── 2.6.4\                    (舊版本號)
        ├── ChroLens_Mimic.exe
        └── _internal\
```

## 🔄 更新系統 (參考 PowerToys)

### 更新管理器 (UpdateManager)

新版本使用 `update_manager.py` 模組處理所有更新相關功能:

#### 功能特點

1. **自動檢查更新**
   - 從 GitHub Releases 檢查最新版本
   - 比較版本號並顯示更新內容
   - 自動下載更新檔案 (.zip)

2. **智能備份**
   - 自動備份當前版本到 `backup\版本號\`
   - 僅備份程式檔案,不備份使用者資料
   - 支援版本回退功能

3. **安全更新**
   - 下載失敗自動清理臨時檔案
   - 安裝失敗自動還原備份
   - 使用者可隨時取消更新

4. **使用者資料保護**
   - 更新時自動保留 scripts 目錄
   - 自動保留 user_config.json
   - 自動保留 last_script.txt

### 使用方式

#### 在程式中檢查更新

```python
from update_manager import UpdateManager

# 初始化
update_mgr = UpdateManager(current_version="2.6.5")

# 檢查更新
update_info = update_mgr.check_for_updates()

if update_info["has_update"]:
    print(f"發現新版本: {update_info['latest_version']}")
    
    # 下載更新
    download_path = update_mgr.download_update(
        update_info["download_url"],
        update_info["asset_name"],
        progress_callback=lambda downloaded, total: print(f"{downloaded}/{total}")
    )
    
    # 解壓縮
    update_dir = update_mgr.extract_update(download_path)
    
    # 備份當前版本
    backup_path = update_mgr.backup_current_version()
    
    # 安裝更新
    update_mgr.install_update(update_dir)
    
    # 建立版本檔
    update_mgr.create_version_file(update_info["latest_version"])
    
    # 清理
    update_mgr.cleanup()
```

#### 版本回退

```python
from update_manager import UpdateManager

update_mgr = UpdateManager(current_version="2.6.5")

# 回退到指定版本
update_mgr.rollback_version("2.6.4")

# 或回退到最新備份
update_mgr.rollback_version()
```

## ⚠️ 注意事項

### 打包前

1. **更新版本號**: 修改 `ChroLens_Mimic.py` 中的 `VERSION` 常數
2. **更新版本紀錄**: 在註解中添加新版本的更新內容
3. **測試功能**: 確保所有功能正常運作

### 打包時

1. **不要手動刪除 dist 目錄**: build.py 會自動處理
2. **確保模組完整**: 所有 `.py` 模組都要加入 `--add-data`
3. **檢查字型檔**: TTF 資料夾要正確打包

### 發布時

1. **建立 GitHub Release**: 標籤格式為 `v2.6.5`
2. **上傳 ZIP 檔案**: 壓縮整個 `dist\ChroLens_Mimic` 目錄
3. **填寫更新說明**: 參考版本更新紀錄

## 🔧 故障排除

### 打包失敗

```powershell
# 清理所有檔案後重試
python build.py --clean

# 手動清理
Remove-Item -Recurse -Force build, dist
Remove-Item ChroLens_Mimic.spec
```

### 更新失敗

1. **檢查網路連線**: 確保可以連線到 GitHub
2. **檢查 Releases**: 確認 GitHub 上有最新版本
3. **檢查 ZIP 檔案**: 確認 ZIP 中包含 ChroLens_Mimic 資料夾
4. **手動回退**: 從 `backup\版本號\` 目錄手動還原

### 版本檔案錯誤

```powershell
# 刪除舊的版本檔
Remove-Item dist\ChroLens_Mimic\version*.txt

# 重新建立
python -c "from update_manager import UpdateManager; UpdateManager('2.6.5').create_version_file('2.6.5')"
```

## 📚 相關檔案

- `build.py` - 打包腳本
- `update_manager.py` - 更新管理模組
- `ChroLens_Mimic.py` - 主程式 (包含更新 UI)
- `version{版本號}.txt` - 版本資訊檔

## 🎯 與 PowerToys 的相似之處

1. **模組化設計**: UpdateManager 獨立處理所有更新邏輯
2. **智能備份**: 僅備份變更的檔案,節省空間
3. **使用者友善**: 詳細的進度提示和錯誤處理
4. **安全機制**: 失敗自動回退,確保程式可用
5. **版本管理**: 完整的版本歷史和回退功能

## 📝 版本紀錄格式

在 `ChroLens_Mimic.py` 和 `version{版本號}.txt` 中保持一致的格式:

```
[版本號] - 日期
  - 類別：說明
  - 類別：說明
  ...
```

類別:
- 🚀 新增
- 改進
- 修正
- 移除
- ⚠️ 警告
