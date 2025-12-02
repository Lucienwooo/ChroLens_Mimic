"""
AI_AGENT_NOTES.py
═══════════════════════════════════════════════════════════════════════════
【重要】每次 AI Agent 工作時必讀此檔案
═══════════════════════════════════════════════════════════════════════════

本檔案包含所有開發規範、流程說明和重要備註。
在對 ChroLens_Mimic 專案進行任何修改前，請先閱讀此檔案。

作者: Lucien
更新日期: 2025-12-02
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【版本更新規範】
# ═══════════════════════════════════════════════════════════════════════════

VERSION_UPDATE_RULES = """
當程式版本更新時，必須執行以下步驟：

1. 更新 ChroLens_Mimic.py 中的 VERSION 變數
   例如: VERSION = "2.6.7"

2. 更新 docs/index.html 的更新日誌
   位置: 在 versionData 陣列的最前面添加新版本
   格式:
   {
       version: "v2.6.7",
       date: "YYYY-MM-DD",  # 使用當天日期
       changes: [
           "🎨 新功能1的描述",
           "🔧 修復問題2的描述",
           "⚡ 優化功能3的描述"
       ]
   }

3. 更新 HTML 中的「最新消息」段落
   位置: <p><strong>🎉 最新消息：</strong>v2.6.x 版本已發布...</p>
   
4. 確保更新內容清晰、簡潔，使用表情符號增加可讀性

常用表情符號：
  🎉 重大更新
  ✨ 新功能
  🔧 修復
  ⚡ 性能優化
  💾 儲存/資料相關
  🖼️ 圖片/UI相關
  🎨 介面優化
  🐛 Bug修復
  📝 文件更新
  🔒 安全性
  🧹 代碼清理
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【視窗圖標統一規範】
# ═══════════════════════════════════════════════════════════════════════════

WINDOW_ICON_RULES = """
所有 Toplevel、Tk、Dialog 等響應式框架視窗的圖標（.ico）必須與主程式相同

設定方法:
```python
from ChroLens_Mimic import get_icon_path
icon_path = get_icon_path()
if os.path.exists(icon_path):
    window.iconbitmap(icon_path)  # 或 window.wm_iconbitmap(icon_path)
```

適用於:
- text_script_editor.py (文字編輯器)
- visual_script_editor.py (視覺編輯器)
- about.py (關於視窗)
- update_dialog.py (更新對話框)
- 所有自訂 Dialog 和 Toplevel 視窗
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【自動發布流程說明】
# ═══════════════════════════════════════════════════════════════════════════

RELEASE_WORKFLOW = """
🚀 快速發布指令：
   1. 更新版本號（ChroLens_Mimic.py 的 VERSION 變數）
   2. 執行: python pack.py（打包）
   3. 執行: 打包.bat（一鍵打包，如果存在）

📋 完整發布流程：

1. 清理多餘檔案
   - 刪除 build/、dist/、__pycache__/ 目錄
   - 刪除所有 *.spec 檔案
   - 刪除測試檔案（test_*.py, quick_*.py, *_test.py）

2. 讀取版本資訊
   - 從 ChroLens_Mimic.py 讀取 VERSION 變數

3. PyInstaller 打包
   參數：
     --name=ChroLens_Mimic
     --onedir
     --noconsole  # 或 --windowed
     --icon=../pic/umi_奶茶色.ico
     --add-data=TTF;TTF
     --add-data=images;images
     --hidden-import=pynput.keyboard._win32
     --hidden-import=pynput.mouse._win32
     --hidden-import=PIL._tkinter_finder

4. 創建 ZIP 壓縮檔
   - 檔名格式：ChroLens_Mimic_{版本號}.zip
   - 包含整個 dist/ChroLens_Mimic/ 目錄

5. 清理建置檔案
   - 刪除 build/ 目錄
   - 刪除所有 *.spec 檔案
   - 保留 dist/ 目錄和 ZIP 檔案

6. 發布到 GitHub Release（可選）
   使用 GitHub CLI (gh)：
     gh release create v{版本號} \
       ChroLens_Mimic_{版本號}.zip \
       --title "ChroLens_Mimic v{版本號}" \
       --notes "{更新說明}" \
       --repo Lucienwooo/ChroLens_Mimic

⚙️ 前置需求：
- PyInstaller: pip install pyinstaller
- GitHub CLI (可選): https://cli.github.com/
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【專案文件清理規則】
# ═══════════════════════════════════════════════════════════════════════════

FILE_CLEANUP_RULES = """
重要：本專案應該保持精簡，避免累積測試檔案

【應保留的檔案】
- README.md (專案根目錄，主要說明文件)
- docs/index.html (線上使用手冊)
- AI_AGENT_NOTES.py (本檔案，AI Agent 必讀)

【應刪除的檔案】（每次修復後清理）
- main/*_test.py, main/test_*.py (測試檔案)
- main/validate_*.py, main/verify_*.py (驗證腳本)
- main/*_GUIDE.md, main/*_FIXES.md (臨時文檔)
- main/TEST_*.txt, main/*_CHECKLIST.txt (測試清單)

【清理命令】PowerShell:
Remove-Item main\*_test.py -Force -ErrorAction SilentlyContinue
Remove-Item main\test_*.py -Force -ErrorAction SilentlyContinue
Remove-Item main\validate_*.py -Force -ErrorAction SilentlyContinue
Remove-Item main\verify_*.py -Force -ErrorAction SilentlyContinue
Remove-Item main\*_GUIDE.md -Force -ErrorAction SilentlyContinue
Remove-Item main\TEST_*.txt -Force -ErrorAction SilentlyContinue
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【打包說明】
# ═══════════════════════════════════════════════════════════════════════════

PACKAGING_NOTES = """
1. 執行 python pack.py 進行打包
2. 或執行 打包.bat（如果存在）
3. 打包後檔名統一為 "ChroLens_Mimic.exe"
4. 版本號顯示於視窗標題

打包後目錄結構:
dist/
  ChroLens_Mimic/
    ChroLens_Mimic.exe  ← 主程式
    _internal/          ← Python 執行環境
    TTF/                ← 字型資源
    images/             ← 圖片資源（如果有）
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【圖片辨識功能擴展規範】(v2.6.7+)
# ═══════════════════════════════════════════════════════════════════════════

IMAGE_RECOGNITION_FEATURES = """
v2.6.7 新增功能：

1. 辨識時顯示邊框
   - 語法: >辨識>pic01, 邊框, T=0s000
   - 功能: 在辨識到圖片時顯示綠色半透明邊框（1.5秒）
   - 用途: 視覺化確認辨識位置

2. 範圍辨識
   - 語法: >辨識>pic01, 範圍(x1,y1,x2,y2), T=0s000
   - 功能: 限定在指定範圍內搜尋圖片
   - 用途: 提高辨識速度和準確性，避免誤判

3. 組合使用
   - 語法: >辨識>pic01, 邊框, 範圍(100,200,500,600), T=0s000
   - 同時啟用邊框和範圍限定

支援的指令類型:
- >辨識>pic01, [邊框], [範圍(x1,y1,x2,y2)], T=時間
- >移動至>pic01, [邊框], [範圍(x1,y1,x2,y2)], T=時間
- >左鍵點擊>pic01, [邊框], [範圍(x1,y1,x2,y2)], T=時間
- >右鍵點擊>pic01, [邊框], [範圍(x1,y1,x2,y2)], T=時間
- >if>pic01, [邊框], [範圍(x1,y1,x2,y2)], T=時間

編輯器新增按鈕:
- 「範圍辨識」按鈕：位於第一行第二個位置
- 點擊後出現全螢幕藍色遮罩，拖曳選擇範圍
- 自動插入帶範圍座標的指令模板
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【版本歷史記錄】
# ═══════════════════════════════════════════════════════════════════════════

VERSION_HISTORY = """
[2.6.7] - 2025-12-02
  - 🎨 新增辨識時顯示邊框功能，視覺化確認辨識位置
  - 🔍 新增範圍辨識功能，可指定辨識區域提高準確性
  - 🖼️ 編輯器新增「範圍辨識」按鈕，快速設定辨識範圍
  - 📝 支援組合使用邊框和範圍參數
  - 🧹 整理專案結構，建立 AI_AGENT_NOTES.py 統一管理規範

[2.6.6] - 2025-11-30
  - 🔧 修復標籤顯示問題
  - 💾 優化腳本編輯器儲存機制
  - 🖼️ 強化圖片辨識功能
  - 🎨 新增語法高亮功能

[2.6.5] - 2025-11-25
  - ✨ 新增自訂模組功能
  - 🐛 修復滑鼠拖曳座標記錄錯誤
  - ⚡ 提升腳本執行效能

[2.6.4] - 快捷鍵系統優化、打包系統完善
[2.6.3] - UI 改進、備份機制優化
[2.6.0] - 重大更新：文字指令編輯器、圖片辨識、條件判斷
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【常見問題和解決方案】
# ═══════════════════════════════════════════════════════════════════════════

FAQ_AND_SOLUTIONS = """
Q1: 打包後無法啟動
A: 檢查 hidden imports 是否完整，特別是:
   - pynput.keyboard._win32
   - pynput.mouse._win32
   - PIL._tkinter_finder

Q2: 圖標未正確顯示
A: 確認所有視窗都使用 get_icon_path() 設定圖標

Q3: 圖片辨識失敗
A: 確認 images/ 目錄是否正確打包到 _internal/

Q4: 字型無法載入
A: 確認 TTF/ 目錄使用 --add-data=TTF;TTF 打包

Q5: 視窗被遮住或顯示不完整
A: 檢查 minsize() 和 geometry() 設定，確保足夠大
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【開發注意事項】
# ═══════════════════════════════════════════════════════════════════════════

DEVELOPMENT_NOTES = """
1. 所有 print() 輸出應該透過 logger 系統
2. 避免硬編碼路徑，使用 Path 物件
3. 錯誤處理要完整，使用 try-except 包裝
4. 新增功能後更新本檔案和 docs/index.html
5. 測試完成後清理臨時檔案
6. 提交前確認版本號已更新
"""

# ═══════════════════════════════════════════════════════════════════════════
# 結束
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*70)
    print("AI_AGENT_NOTES.py - ChroLens_Mimic 開發規範")
    print("="*70)
    print("\n本檔案包含所有開發規範和流程說明。")
    print("每次 AI Agent 工作時請先閱讀此檔案。\n")
    print("主要章節:")
    print("  - 版本更新規範")
    print("  - 視窗圖標統一規範")
    print("  - 自動發布流程說明")
    print("  - 專案文件清理規則")
    print("  - 打包說明")
    print("  - 圖片辨識功能擴展規範 (v2.6.7+)")
    print("  - 版本歷史記錄")
    print("  - 常見問題和解決方案")
    print("  - 開發注意事項")
    print("\n" + "="*70)
