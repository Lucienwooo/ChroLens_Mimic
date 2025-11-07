# ChroLens Mimic v2.6.4 Release Notes

## 📦 版本資訊
- **版本號**: 2.6.4
- **發布日期**: 2025年11月7日
- **下載**: [ChroLens_Mimic_2.6.4_Update.zip](ChroLens_Mimic_2.6.4_Update.zip)
- **檔案校驗**: SHA256 `257C2E414A534BCA09498E889F243D65FFAB2778203E10B62657636ADFC7A081`

---

## 🐛 修復問題

### 1. 快捷鍵無法觸發停止功能 ✅
**問題描述**: 使用者更改快捷鍵後，無論設定為何按鍵都無法觸發停止功能。

**修復內容**:
- 修復 lambda 閉包問題（所有快捷鍵都引用同一個變數）
- 實作 `make_callback()` 函數為每個快捷鍵創建獨立回調
- 所有快捷鍵改用 `trigger_on_release=True` 模式，提升穩定性

**技術細節**:
```python
# 修復前（有 BUG）
func_map = {
    "start": lambda: self.start_record(),
    "stop": lambda: self.stop_all(),  # ❌ 所有 lambda 都指向最後一個 key
    ...
}

# 修復後（正確）
def make_callback(action_key):
    if action_key == "start": return lambda: self.start_record()
    elif action_key == "stop": return lambda: self.stop_all()
    ...
callback = make_callback(key)  # ✓ 每個快捷鍵都有獨立回調
```

---

### 2. 腳本編輯器載入腳本顯示「載入0動作」✅
**問題描述**: 開啟視覺化腳本編輯器載入 scripts 資料夾中的腳本時，總是顯示「載入0動作」。

**修復內容**:
- 修正事件轉動作的邏輯（第一個移動事件被錯誤忽略）
- 降低過濾門檻：從 50 像素調整為 30 像素
- 改進延遲計算，確保第一個事件也能正確記錄
- 增加 DEBUG 訊息，便於追蹤轉換過程

**修復前後對比**:
```python
# 修復前
if delay > 0:  # ❌ 第一個事件 delay=0 被跳過
    actions.append(...)

# 修復後
if last_mouse_pos is None:
    # ✓ 第一個移動事件一定記錄
    actions.append(...)
    last_mouse_pos = (x, y)
elif abs(x - last_mouse_pos[0]) > 30:  # ✓ 降低門檻
    actions.append(...)
```

**測試結果**:
- 輸入: 1324 個錄製事件
- 輸出: 預期會有合理數量的動作（不再是 0）

---

## ⚡ 效能優化

### 容量大幅縮減
- 刪除 build 和 dist 資料夾（包含重複的 OpenCV 檔案）
- **專案容量**: 417.95 MB → **7.66 MB** （縮減 98%！）

### 檔案清單
清理的大型檔案:
- `cv2.pyd` (67.5 MB × 2)
- `opencv_videoio_ffmpeg4120_64.dll` (27 MB × 2)
- `libscipy_openblas64_*.dll` (19.45 MB × 2)

---

## 🔧 技術改進

### 快捷鍵系統
- 所有快捷鍵使用 `trigger_on_release=True`
- 不再使用 `suppress=True`，避免按鍵失效
- 改進錯誤處理和日誌記錄

### 腳本編輯器
- 優化滑鼠移動事件記錄（30 像素門檻）
- 改進雙擊偵測邏輯
- 增強空值檢查（鍵盤事件）
- 新增詳細的 DEBUG 訊息

---

## 📥 安裝方式

### 更新現有版本
1. 下載 `ChroLens_Mimic_2.6.4_Update.zip`
2. 解壓縮到程式安裝目錄（覆蓋舊檔案）
3. 確認 `version2.6.4.txt` 存在

### 從原始碼執行
```bash
cd ChroLens_Mimic/main
python ChroLens_Mimic.py
```

---

## ✅ 測試驗證

所有修復項目已通過自動化測試：

```
【測試 1】檢查版本號...
✓ 版本號已更新為 2.6.4

【測試 2】檢查快捷鍵修復...
✓ 快捷鍵 lambda 閉包問題已修復
✓ 所有快捷鍵使用 trigger_on_release 模式

【測試 3】檢查腳本編輯器修復...
✓ 腳本編輯器事件轉換邏輯已修復
✓ 滑鼠移動門檻設定為 30 像素

【測試 4】檢查容量優化...
✓ build 和 dist 資料夾已清理

【測試 5】檢查更新包...
✓ ChroLens_Mimic_2.6.4_Update.zip 已建立 (53.54 KB)
```

---

## 🎯 使用建議

### 測試快捷鍵修復
1. 啟動 ChroLens Mimic
2. 前往「快捷鍵設定」更改停止快捷鍵
3. 測試新快捷鍵是否能正常觸發停止功能
4. 確認所有快捷鍵（開始/暫停/停止/回放/MiniMode）都能正常運作

### 測試腳本編輯器修復
1. 錄製一個簡單腳本（移動滑鼠、點擊、輸入文字）
2. 儲存腳本到 scripts 資料夾
3. 開啟視覺化腳本編輯器
4. 載入剛才錄製的腳本
5. 確認顯示正確的動作數量（不再是「載入0動作」）

---

## 📋 已知問題

目前無已知問題。

---

## 🔗 相關連結

- [GitHub Repository](https://github.com/YOUR_USERNAME/ChroLens_Mimic)
- [問題回報](https://github.com/YOUR_USERNAME/ChroLens_Mimic/issues)
- [使用說明](../使用說明.md)

---

## 📄 授權

本軟體依據 MIT 授權條款發布。

---

**感謝您使用 ChroLens Mimic！**

如有任何問題或建議，歡迎在 GitHub Issues 中回報。
