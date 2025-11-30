# ChroLens_Mimic 自動發布使用說明

## 📦 快速開始

### 1. 安裝前置需求

```bash
# 安裝 PyInstaller
pip install pyinstaller

# 安裝 GitHub CLI (Windows)
# 下載安裝程式：https://cli.github.com/
# 或使用 winget
winget install --id GitHub.cli

# 登入 GitHub CLI
gh auth login
```

### 2. 執行自動發布

```bash
cd main
python auto_release.py
```

## 🔄 發布流程說明

### 執行步驟

1. **清理檔案** - 刪除 build、dist、spec、測試檔案
2. **讀取版本** - 從 ChroLens_Mimic.py 讀取 VERSION
3. **打包程式** - 使用 PyInstaller 打包
4. **創建 ZIP** - 壓縮打包結果
5. **清理建置** - 刪除 build 和 spec 檔案
6. **發布 Release** - 上傳到 GitHub

### 輸出檔案

- `dist/ChroLens_Mimic/` - 打包後的程式目錄
- `dist/ChroLens_Mimic_{版本號}.zip` - 發布用壓縮檔

## 📝 Release Notes 格式

檔案位置：`更新說明_v{版本號}.md`

建議格式（簡短版）：
```markdown
# ChroLens_Mimic v2.6.6 更新說明

## 更新內容

- 🔧 修復標籤顯示問題，確保標籤不再重疊或錯位
- 💾 優化腳本編輯器儲存機制，提升儲存穩定性
- 🖼️ 強化圖片辨識功能，提高匹配準確度
- 🎨 新增語法高亮功能，指令符號以橘色/青綠色顯示
- 🧹 清理專案檔案，移除冗餘代碼
- 📝 統一編輯器命名為「腳本編輯器」
```

## ⚙️ 手動操作

### 僅打包（不發布）

```bash
python build_simple.py
```

### 手動上傳到 GitHub

如果 GitHub CLI 無法使用：

1. 前往 https://github.com/Lucienwooo/ChroLens_Mimic/releases/new
2. 填寫 Tag: `v2.6.6`
3. 填寫標題: `ChroLens_Mimic v2.6.6`
4. 貼上 Release Notes
5. 上傳 `dist/ChroLens_Mimic_2.6.6.zip`
6. 點擊 "Publish release"

## 🧹 清理命令

手動清理多餘檔案：

```powershell
# 刪除建置檔案
Remove-Item -Recurse -Force main\build, main\dist, main\__pycache__

# 刪除 spec 檔案
Remove-Item main\*.spec

# 刪除測試檔案
Remove-Item main\test_*.py, main\*_test.py, main\quick_*.py
```

## ❓ 常見問題

### Q: GitHub CLI 認證失敗

```bash
# 重新登入
gh auth logout
gh auth login

# 檢查狀態
gh auth status
```

### Q: PyInstaller 打包失敗

檢查是否缺少依賴：
```bash
pip install pynput pillow opencv-python numpy ttkbootstrap
```

### Q: 找不到圖標檔案

確認 `pic/umi_奶茶色.ico` 存在於專案根目錄。

## 📋 檢查清單

發布前確認：

- [ ] 版本號已更新（ChroLens_Mimic.py 第 96 行）
- [ ] 創建對應的更新說明檔案（更新說明_v{版本號}.md）
- [ ] 測試主程式功能正常
- [ ] 清理測試檔案和臨時檔案
- [ ] GitHub CLI 已登入並有權限

## 🔗 相關連結

- GitHub 專案：https://github.com/Lucienwooo/ChroLens_Mimic
- GitHub CLI 文檔：https://cli.github.com/manual/
- PyInstaller 文檔：https://pyinstaller.org/
