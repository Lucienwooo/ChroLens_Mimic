# ChroLens_Mimic 更新系統修復 (2.6.7) - 第二次修復

## 問題回顧
從 2.6.6 更新到 2.6.7 時失敗，且主程式目錄沒有生成 `update_log.txt`。

## 根本原因重新分析

經過深入分析，發現第一次修復過於複雜，反而引入了新問題：

1. **subprocess.Popen 命令過於複雜**
   - 使用 `['cmd', '/c', 'start', '/min', ...]` 可能導致命令解析失敗
   - 路徑中的引號和特殊字元處理不當

2. **初始日誌寫入位置問題**
   - 可能因為權限問題無法寫入主程式目錄
   - 沒有備用方案

3. **程式退出時機過於激進**
   - 使用 `os._exit(0)` 強制終止可能導致資源未釋放
   - 批次腳本可能還沒完全啟動就被終止

## 第二次修復方案

### ✅ 修復 1: 簡化批次腳本啟動 (`update_manager.py`)

**修改前：**
```python
subprocess.Popen(
    ['cmd', '/c', 'start', '/min', '"ChroLens Update"', update_script],
    shell=False,
    cwd=current_dir
)
```

**修改後：**
```python
process = subprocess.Popen(
    update_script,
    shell=True,
    creationflags=subprocess.CREATE_NEW_CONSOLE,
    cwd=current_dir
)
self._logger(f"批次腳本已啟動，PID: {process.pid}")
```

**改變說明：**
- 直接執行批次腳本，不通過 `start` 命令
- 使用 `CREATE_NEW_CONSOLE` 在新視窗中執行
- 記錄進程 PID 以便追蹤

### ✅ 修復 2: 雙重日誌寫入機制 (`update_manager.py`)

```python
# 嘗試 1: 主程式目錄
try:
    initial_log_path = os.path.join(current_dir, "update_log.txt")
    with open(initial_log_path, 'w', encoding='utf-8') as f:
        # 寫入初始日誌
    log_written = True
except Exception as e:
    self._logger(f"無法寫入主程式目錄日誌: {e}")

# 嘗試 2: 臨時目錄（備用方案）
if not log_written:
    try:
        initial_log_path = os.path.join(tempfile.gettempdir(), "ChroLens_update_log.txt")
        # 寫入初始日誌到臨時目錄
        log_written = True
    except Exception as e:
        self._logger(f"無法寫入臨時目錄日誌: {e}")
```

**改變說明：**
- 優先嘗試寫入主程式目錄
- 如果失敗（權限問題），寫入臨時目錄作為備用
- 確保至少有一份日誌可供查看

### ✅ 修復 3: 恢復溫和的程式退出方式 (`update_dialog.py`)

**修改前：**
```python
def delayed_exit():
    time.sleep(0.5)
    os._exit(0)

threading.Thread(target=delayed_exit, daemon=True).start()
```

**修改後：**
```python
# 關閉對話框
self.dialog.destroy()

# 延遲0.5秒確保批次腳本已啟動
time.sleep(0.5)

# 關閉主視窗
self.parent.quit()
self.parent.destroy()
```

**改變說明：**
- 移除強制終止 (`os._exit`)
- 恢復使用標準的 `quit()` + `destroy()`
- 保留 0.5 秒延遲確保批次腳本已啟動
- 這與 2.6.5 → 2.6.6 成功更新的方式一致

### ✅ 修復 4: 增強日誌記錄

新增記錄內容：
- 批次腳本的 PID
- 主程式目錄路徑
- 每次嘗試的成功/失敗狀態

## 修復對比表

| 項目 | 第一次修復 | 第二次修復 | 理由 |
|------|----------|----------|------|
| subprocess 命令 | `['cmd', '/c', 'start', ...]` | `update_script, shell=True` | 簡單可靠 |
| 進程創建 | `shell=False` | `CREATE_NEW_CONSOLE` | 確保獨立運行 |
| 初始日誌位置 | 僅主程式目錄 | 主目錄 + 臨時目錄 | 雙重保險 |
| 程式退出 | `os._exit(0)` | `quit() + destroy()` | 符合 2.6.6 經驗 |
| 延遲機制 | 後台線程延遲 | 直接延遲 | 更簡單直接 |

## 測試步驟

### 1. 確認初始日誌
更新開始後立即檢查：
- 主程式目錄：`update_log.txt`
- 或臨時目錄：`%TEMP%\ChroLens_update_log.txt`

應該看到：
```
========================================
ChroLens_Mimic 更新程式
更新時間: 2025-12-03 XX:XX:XX
========================================
當前版本: 2.6.6
目標版本: 2.6.7
批次腳本: C:\...\ChroLens_Update.bat
主程式目錄: C:\...
批次腳本已啟動，等待程式關閉...
```

### 2. 觀察批次腳本視窗
- 批次腳本會在新視窗中執行（不是最小化）
- 可以看到更新進度
- 所有輸出都會寫入 `update_log.txt`

### 3. 確認版本更新
- 程式自動重啟
- 檢查版本號是否變為 2.6.7

### 4. 查看完整日誌
- 主程式目錄的 `update_log.txt`
- 包含完整的更新過程記錄

## 打包說明

`pack.py` 會自動包含所有被 `import` 的模組，包括：
- `update_manager.py`
- `update_dialog.py`

主程式中的動態 import 語句：
```python
from update_manager import UpdateManager
from update_dialog import UpdateDialog, NoUpdateDialog
```

PyInstaller 會自動檢測並包含這些模組。

### 手動打包步驟

1. **開啟 PowerShell 或 CMD**
2. **切換到 main 目錄：**
   ```powershell
   cd "c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main"
   ```

3. **執行打包腳本：**
   ```powershell
   python pack.py
   ```

4. **等待完成：**
   - 會生成 `dist\ChroLens_Mimic\` 目錄
   - 會創建 `ChroLens_Mimic_2.6.7.zip`

## 關鍵差異：為什麼這次應該成功

### 對比 2.6.5 → 2.6.6 成功經驗

| 項目 | 2.6.5→2.6.6 (成功) | 第一次修復 (失敗) | 第二次修復 |
|------|-------------------|-----------------|----------|
| subprocess 方式 | 簡單直接 | 過於複雜 | **回歸簡單** ✅ |
| 程式退出 | quit/destroy | os._exit(0) | **quit/destroy** ✅ |
| 批次腳本視窗 | 可見 | 隱藏/最小化 | **可見** ✅ |
| 日誌機制 | 基本 | 主目錄單一 | **雙重備份** ✅ |

### 為什麼第一次修復失敗

1. **過度優化**：使用 `start /min` 等複雜命令
2. **強制終止**：`os._exit(0)` 可能導致批次腳本未完全啟動
3. **單點失敗**：日誌只嘗試寫入主目錄

### 為什麼第二次修復應該成功

1. **回歸簡單**：參考 2.6.6 的成功經驗
2. **溫和退出**：使用標準方法，確保資源正確釋放
3. **雙重保險**：日誌寫入有備用方案
4. **可追蹤性**：記錄 PID 和詳細路徑

## 檔案修改清單

1. ✅ `update_manager.py` - 簡化 subprocess 調用，雙重日誌機制
2. ✅ `update_dialog.py` - 恢復標準退出方式
3. ✅ `UPDATE_FIX_2.6.7.md` - 本說明文件（更新）

## 如果仍然失敗

請提供：
1. 主程式目錄的 `update_log.txt`（如果存在）
2. 臨時目錄的 `ChroLens_update_log.txt`（`%TEMP%` 目錄下）
3. 批次腳本視窗中顯示的任何錯誤訊息

---
**修復日期**: 2025-12-03  
**修復版本**: 2.6.7  
**修復次數**: 第二次  
**參考經驗**: 2.6.5 → 2.6.6 成功更新  
**測試狀態**: 待手動測試
