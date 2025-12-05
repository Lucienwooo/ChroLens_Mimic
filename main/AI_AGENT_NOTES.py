"""
AI_AGENT_NOTES.py
═══════════════════════════════════════════════════════════════════════════
【重要】每次 AI Agent 工作時必讀此檔案
═══════════════════════════════════════════════════════════════════════════

本檔案包含所有開發規範、流程說明和重要備註。
在對 ChroLens_Mimic 專案進行任何修改前，請先閱讀此檔案。

作者: Lucien
更新日期: 2025-12-05
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【🔄 版本更新完整檢查清單】- AI Agent 必讀！
# ═══════════════════════════════════════════════════════════════════════════

VERSION_UPDATE_CHECKLIST = """
⚠️ 每次更新版本號時，必須檢查並更新以下所有位置：

1. 【核心程式檔案】
   ✅ main/ChroLens_Mimic.py
      - VERSION = "X.X.X" (第 18 行附近)
      - 版本更新紀錄註解 (第 12 行附近)

2. 【打包相關檔案】
   ✅ main/version_info.txt
      - filevers=(X, X, X, 0)
      - prodvers=(X, X, X, 0)
      - FileVersion="X.X.X.0"
      - ProductVersion="X.X.X.0"
   ✅ main/pack_safe.py
      - fallback 版本號 (第 45 行: return "X.X.X")
   ✅ main/打包.bat
      - 標題註解 (第 2 行: REM ChroLens_Mimic vX.X.X)

3. 【文檔相關檔案】
   ✅ docs/index.html
      - versionData 陣列第一項 (版本號和更新日期)
   ✅ main/AI_AGENT_NOTES.py
      - VERSION_HISTORY 最新版本
   ✅ 發布檢查清單.md
      - 範例版本號 (多處)

4. 【測試檔案】（選擇性更新）
   ⚠️ test_version_compare.py
      - 如需測試新版本，加入測試案例
   ⚠️ validate_release.py
      - 範例檔名中的版本號

5. 【版本更新機制檢查】⭐ 重要！
   ✅ main/update_manager.py
      - 確認 github_link_txt 使用 self._latest_version (第 547 行)
      - 確認 github_url 使用 self._latest_version (第 548 行)
      - 這是關鍵！確保更新後生成正確版本的 txt 檔

【版本更新流程】
1. 使用搜尋功能找出所有舊版本號 (例如搜尋 "2.7.1")
2. 逐一檢查上述檔案，確保版本號一致
3. 特別注意 update_manager.py 中的版本資訊生成邏輯
4. 打包前測試：檢查 ChroLens_Mimic.exe 右鍵→內容→詳細資料，確認版本號正確
5. 上傳 GitHub Release 時，Tag 使用 vX.X.X 格式 (例如 v2.7.2)
6. 測試更新機制：從舊版本更新到新版本，檢查 backup 資料夾中是否生成正確版本的 txt 檔

【常見錯誤】
❌ 忘記更新 version_info.txt → exe 顯示舊版本號
❌ 忘記更新 pack_safe.py fallback → 讀取失敗時顯示舊版本
❌ update_manager.py 使用 current_version → 更新後生成舊版本 txt 檔 ⚠️ 重要！
❌ 只更新主程式，忘記更新文檔 → 使用者看到版本號不一致

【自動化建議】
未來可考慮建立 update_version.py 腳本，自動更新所有檔案中的版本號
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【🎯 版本更新成功模式】- 基於 2.7.1 成功經驗 (2025-12-05)
# ═══════════════════════════════════════════════════════════════════════════

UPDATE_SUCCESS_PATTERN = """
✅ 2.7.1 版本成功更新模式分析 (2.6.x → 2.7.1 可正常更新)

【核心成功要素】
1. 批次腳本結構：採用簡化但穩定的結構
   - 等待時間：30 秒 (足夠但不過長)
   - 額外檔案鎖定等待：5 秒 (關鍵！確保 Python 進程完全釋放)
   - 重試機制：簡單的 3 次重試刪除舊 exe
   - 自刪除：使用 (goto) 2>nul & del "%~f0" (簡單有效)

2. 版本資訊生成邏輯 (⭐ 最重要！)：
   ```python
   # update_manager.py 的 _create_update_script 方法中：
   backup_version_txt = f"version{self.current_version}.txt"  # 備份舊版
   github_link_txt = f"{self._latest_version}.txt"            # ✅ 使用新版本！
   github_url = f"https://github.com/.../v{self._latest_version}"
   ```
   
   理由：
   - backup 資料夾中應該存放「新版本」的下載連結
   - 例如：從 2.7.1 更新到 2.7.2 時，應生成「2.7.2.txt」
   - 這樣使用者可以在 backup 資料夾查看每個版本的來源

3. 批次腳本關鍵步驟順序：
   ```batch
   1. 等待主程式關閉 (30 秒超時)
   2. 強制結束 + 額外等待 5 秒 ⭐
   3. 建立 backup 資料夾
   4. 備份舊版 version.txt
   5. 生成新版本連結 txt ⭐
   6. 重命名舊 exe 為 .old
   7. 重試刪除 .old (3 次)
   8. xcopy 複製新檔案 (/E /I /Y /Q)
   9. 清理臨時檔案
   10. 重新啟動程式
   11. 自刪除批次檔
   ```

【為何 2.7.2 (複雜版) 失敗】
❌ 過度複雜的錯誤處理：
   - 10 次重試迴圈 (太複雜，容易卡死)
   - 權限檢查 (在批次腳本中執行，增加失敗點)
   - VBS 自刪除 (增加依賴，可能失敗)
   - 桌面錯誤檔案 (執行環境可能不同)

❌ 等待時間過長：
   - 60 秒超時 + 3 秒等待 = 太長
   - 使用者體驗差，容易以為程式當掉

【成功公式】⭐
```
簡單穩定 > 複雜完美
關鍵等待 (5秒) > 無限重試
正確版本號 > 額外功能
```

【AI Agent 更新時必須遵循】
1. 保持批次腳本簡單：
   - 總行數 < 100 行
   - 迴圈 < 2 層
   - 錯誤處理簡潔明瞭

2. 關鍵等待時間：
   - taskkill 後等待：5 秒 (不可省略！)
   - 程式重啟前等待：2 秒
   - 刪除重試間隔：1 秒

3. 版本資訊生成：
   - 永遠使用 self._latest_version (新版本)
   - 在每次修改 update_manager.py 後，檢查此行
   - 使用測試腳本驗證 (test_update_version_logic.py)

4. 測試驗證：
   - 打包後立即測試更新流程
   - 檢查 backup 資料夾生成的 txt 檔名
   - 從舊版本實際更新，而非假設

【錯誤排查流程】
如果更新失敗：
1. 檢查日誌中「生成版本資訊」後的 txt 檔名
   - 正確：應為「新版本.txt」(如 2.7.3.txt)
   - 錯誤：如果是「舊版本.txt」(如 2.7.2.txt) → 版本邏輯錯誤

2. 檢查日誌卡在哪一步：
   - 「處理舊版 exe」→ 檔案鎖定問題，增加等待時間
   - 「複製新檔案」→ 權限問題或磁碟空間不足
   - 無任何輸出 → 批次腳本語法錯誤

3. 檢查 exe 內部的 update_manager.py：
   - 當前運行的 exe 包含的是打包時的代碼
   - 源碼修復不等於 exe 修復
   - 必須重新打包才能生效

【防呆機制】
- 打包前自動檢查版本號：pack_safe.py 已實作
- 更新前自動檢查 exe 版本：update_dialog.py 顯示版本號
- 失敗後日誌保留：update_log.txt 永久保存
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【版本更新規範】
# ═══════════════════════════════════════════════════════════════════════════

VERSION_UPDATE_RULES = """
當程式版本更新時，必須執行以下步驟：

1. 更新 ChroLens_Mimic.py 中的 VERSION 變數
   例如: VERSION = "2.7.2"

2. 更新 docs/index.html 的更新日誌
   位置: 在 versionData 陣列的最前面添加新版本
   格式:
   {
       version: "v2.7.2",
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
- text_script_editor.py (文字指令編輯器 - 主編輯器)
- about.py (關於視窗)
- update_dialog.py (更新對話框)
- 所有自訂 Dialog 和 Toplevel 視窗

注意：visual_script_editor.py 已移除，現統一使用 text_script_editor.py
```

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
# 【打包說明】⚠️ 重要：優先保證功能完整性
# ═══════════════════════════════════════════════════════════════════════════

PACKAGING_NOTES = """
【主要打包工具】
1. 執行 打包.bat（推薦）
2. 或直接執行 python pack_safe.py

⚠️ 重要規範：
- pack_safe.py 是主要打包腳本（標準打包，不排除任何模組）
- pack.py 是保守優化版本（僅排除確定不使用的大型模組）
- 打包.bat 會調用 pack_safe.py 確保功能完整
- 優先原則：功能完整 > 檔案大小

【打包策略】
pack_safe.py (推薦):
- 標準 PyInstaller 打包
- 不排除任何模組
- 確保所有功能（錄製、播放、圖片辨識、OCR）正常
- 檔案較大但穩定

pack.py (進階):
- 保守優化打包
- 僅排除確定不使用的模組（torch, tensorflow, pandas 等）
- 保留可能被間接使用的依賴
- 檔案較小但需測試驗證

【打包流程】(標準版 - 5 步驟)
1. 清理舊檔案：刪除 build/、dist/、*.spec
2. 標準打包：使用 PyInstaller 標準設定
3. 計算大小：統計解壓縮後的檔案大小
4. 創建 ZIP：使用最高壓縮等級 (compresslevel=9)
5. 清理建置檔案：刪除 build/ 和 *.spec

【打包參數】(標準版)
pyinstaller \
  --noconsole \           # 無控制台視窗
  --onedir \              # 單資料夾模式
  --clean \               # 清理暫存
  --noconfirm \           # 不詢問覆蓋
  --icon=../pic/umi_奶茶色.ico \
  --add-data=../pic/umi_奶茶色.ico;. \
  --version-file=version_info.txt \
  ChroLens_Mimic.py

【打包後目錄結構】
dist/
  ChroLens_Mimic/
    ChroLens_Mimic.exe  ← 主程式
    _internal/          ← Python 執行環境（完整）
    TTF/                ← 字型資源
    images/             ← 圖片資源 (如果有)

【驗證清單】
打包完成後必須測試：
✓ 錄製功能（滑鼠、鍵盤）
✓ 播放功能（執行腳本）
✓ 圖片辨識功能
✓ OCR 文字辨識功能
✓ 編輯器開啟和儲存
✓ 設定功能
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
[2.7.2] - 2025-12-05
  - 🖼️ 強化圖片命名辨識系統，支援任意 pic 開頭的命名
  - 📝 支援中文、英文、數字組合命名（如 pic血條、pic王01、pic確定按鈕）
  - 🔧 修復版本更新流程，優化批次腳本執行時機
  - 📚 更新 HTML 文檔示範內容，統一圖片命名規則

[2.7.1] - 2025-12-04
  - ✨ 邏輯增強：變數/循環/多條件/隨機/計數器/計時器
  - 🔧 修復轉換問題

[2.7.0] - 2025-12-03
  - 🎨 全新編輯器系統：真正的軌跡摺疊、效能優化、輸入體驗改善

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
# 【UI 響應式設計規範】
# ═══════════════════════════════════════════════════════════════════════════

UI_RESPONSIVE_DESIGN_RULES = """
所有視窗和對話框必須使用響應式/自適應框架設計，防止內容超出視窗範圍。

【基本原則】
1. 使用 grid 或 pack 的 expand=True, fill="both" 實現自適應
2. 設定合理的 minsize() 確保最小可用尺寸
3. 使用 Scrollbar 處理超長內容
4. 按鈕使用 Frame 容器包裝，避免超出邊界
5. 測試不同螢幕解析度下的顯示效果

【標準視窗設定】
```python
# 設定最小尺寸（防止視窗太小）
window.minsize(800, 600)

# 主容器使用 grid
main_frame = tk.Frame(window)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# 可滾動內容
canvas = tk.Canvas(main_frame)
scrollbar = tk.Scrollbar(main_frame, command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
```

【按鈕群組佈局】
```python
# 使用 Frame 包裝按鈕，自動換行
button_container = tk.Frame(parent)
button_container.pack(fill="both", expand=True)

# 多行按鈕佈局
for row_idx, button_row in enumerate(button_rows):
    row_frame = tk.Frame(button_container)
    row_frame.pack(fill="x", pady=2)
    for btn_text, btn_color, btn_cmd in button_row:
        btn = tk.Button(row_frame, text=btn_text, bg=btn_color, command=btn_cmd)
        btn.pack(side="left", padx=2)
```

【視窗隱藏標準流程】（用於截圖等場景）
```python
def hide_windows_for_capture(self):
    # 儲存原始狀態
    self.editor_geometry = self.geometry()
    if self.parent:
        self.parent_geometry = self.parent.geometry()
    
    screen_width = self.winfo_screenwidth()
    screen_height = self.winfo_screenheight()
    
    # 步驟1: 縮小至 1x1 像素
    self.geometry("1x1")
    if self.parent:
        self.parent.geometry("1x1")
    self.update_idletasks()
    
    # 步驟2: 移到螢幕外
    self.geometry(f"1x1+{screen_width + 100}+{screen_height + 100}")
    if self.parent:
        self.parent.geometry(f"1x1+{screen_width + 200}+{screen_height + 200}")
    self.update_idletasks()
    
    # 步驟3: 隱藏視窗
    self.withdraw()
    if self.parent:
        self.parent.withdraw()
    self.update_idletasks()
    
    # 步驟4: 延遲足夠時間（600ms）
    self.after(600, callback_function)
```
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【字型使用規範】
# ═══════════════════════════════════════════════════════════════════════════

FONT_USAGE_RULES = """
所有介面文字必須優先使用 LINESeedTW_TTF_Rg.ttf 字型。

【字型設定方法】
```python
import os
from tkinter import font as tkfont

# 載入字型
font_path = os.path.join(os.path.dirname(__file__), "TTF", "LINESeedTW_TTF_Rg.ttf")
if os.path.exists(font_path):
    try:
        import tkinter as tk
        # 註冊字型（僅需一次）
        tk.Tk().withdraw()  # 臨時視窗
        from tkinter.font import Font
        # 使用 pyglet 或 PIL 載入字型（打包後仍可用）
    except Exception as e:
        print(f"字型載入失敗: {e}")

# 使用字型的標準方法
def font_tuple(size=10, weight="normal", monospace=False):
    if monospace:
        return ("Consolas", size, weight)
    return ("LINESeedTW_TTF_Rg", size, weight)
```

【適用範圍】
- 所有 Label、Button、Entry、Text 元件
- 訊息對話框
- 提示文字
- 日誌輸出（除了需要等寬字型的程式碼區域）

【例外情況】
- 程式碼編輯器：使用 Consolas 等寬字型
- 座標顯示：使用 Consolas 等寬字型
- 時間顯示：使用 Consolas 等寬字型
"""

# ═══════════════════════════════════════════════════════════════════════════
# 【Emoji 使用規範】
# ═══════════════════════════════════════════════════════════════════════════

EMOJI_USAGE_RULES = """
僅在特定文件中使用 Emoji，其他地方一律禁用。

【允許使用 Emoji 的文件】
1. AI_AGENT_NOTES.py（本文件）- 用於分類和標記
2. docs/index.html - 用於增加可讀性
3. README.md - 用於 GitHub 展示

【禁止使用 Emoji 的地方】
1. 所有 Python 程式碼中的 print() 輸出
2. 日誌系統（logger）的任何輸出
3. 使用者介面的按鈕文字
4. 對話框訊息
5. 狀態列顯示
6. 錯誤訊息
7. 提示訊息

【正確示範】
❌ 錯誤：self.log("圖片辨識成功")
✅ 正確：self.log("圖片辨識成功")

❌ 錯誤：messagebox.showinfo("完成", "操作完成")
✅ 正確：messagebox.showinfo("完成", "操作完成")

❌ 錯誤：btn = Button(text="開啟")
✅ 正確：btn = Button(text="開啟")
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
7. 禁止在動態日誌和介面中使用任何 emoji（僅限文檔中用於分類標記）
8. 只有在版本更新時才產生 .md 文件來比對版本差異，其他情況一律不產生 .md 文件
9. 所有視窗必須使用響應式設計，確保內容不會超出邊界
10. 優先使用 LINESeedTW_TTF_Rg.ttf 字型（程式碼區域除外）
11. 視窗隱藏時必須先縮小至 1x1，再移至螢幕外，最後 withdraw
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
    print("  - UI 響應式設計規範 (NEW)")
    print("  - 字型使用規範 (NEW)")
    print("  - Emoji 使用規範 (NEW)")
    print("  - 版本歷史記錄")
    print("  - 常見問題和解決方案")
    print("  - 開發注意事項")
    print("\n" + "="*70)
