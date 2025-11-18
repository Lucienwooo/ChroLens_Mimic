# 驗證碼識別 - 完整安裝教學

## ❌ 錯誤訊息解說

如果你看到這個錯誤：
```
無法找到 Tesseract 執行檔

建議：
1. 已安裝 Tesseract-OCR
2. 已將安裝路徑加入環境變數
   或在程式中設定:
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

這表示需要安裝兩個東西：
1. Python 套件 (`pytesseract`, `opencv-python`)
2. Tesseract-OCR 程式

---

## 📦 完整安裝步驟

### 步驟 1: 安裝 Python 套件 ✅

```powershell
pip install pytesseract opencv-python pillow numpy
```

等待安裝完成，應該看到類似：
```
Successfully installed pytesseract-0.3.10 opencv-python-4.8.1.78 ...
```

---

### 步驟 2: 下載 Tesseract-OCR 程式 📥

#### 方法 A: 使用安裝程式（推薦）

1. **開啟下載頁面**  
   https://github.com/UB-Mannheim/tesseract/wiki

2. **選擇適合的版本**  
   - 64 位元 Windows: `tesseract-ocr-w64-setup-5.3.3.20231005.exe`
   - 32 位元 Windows: `tesseract-ocr-w32-setup-5.3.3.20231005.exe`

3. **下載檔案**  
   點擊連結下載（約 50-60 MB）

---

### 步驟 3: 安裝 Tesseract-OCR 🔧

1. **執行安裝程式**  
   雙擊下載的 `.exe` 檔案

2. **選擇安裝路徑**  
   預設路徑：`C:\Program Files\Tesseract-OCR`  
   ⚠️ 記住這個路徑！

3. **選擇語言包**（可選）  
   - 如果只識別英文/數字，預設即可
   - 如果需要其他語言，勾選對應語言包

4. **⭐ 重要：勾選「Add to PATH」**  
   在安裝過程中，確保勾選「Add to PATH」或「Add to system PATH」選項

5. **完成安裝**  
   點擊「Install」並等待完成

---

### 步驟 4: 驗證安裝 ✅

開啟 PowerShell 或命令提示字元，輸入：

```powershell
tesseract --version
```

如果顯示版本資訊，表示安裝成功：
```
tesseract 5.3.3
 leptonica-1.83.1
  libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.1.5.1) : libpng 1.6.40 : libtiff 4.5.1 : zlib 1.2.13 : libwebp 1.3.2 : libopenjp2 2.5.0
```

如果顯示錯誤「'tesseract' 不是內部或外部命令...」，繼續下一步。

---

## 🔧 進階設定（如果步驟 4 失敗）

### 方法 1: 手動加入環境變數

1. **複製 Tesseract 安裝路徑**  
   預設是：`C:\Program Files\Tesseract-OCR`

2. **開啟環境變數設定**
   - 按 `Win + Pause` 或右鍵「本機」→「內容」
   - 點擊「進階系統設定」
   - 點擊「環境變數」

3. **編輯 PATH**
   - 在「系統變數」區域找到 `Path`
   - 點擊「編輯」
   - 點擊「新增」
   - 貼上：`C:\Program Files\Tesseract-OCR`
   - 點擊「確定」全部關閉

4. **重新啟動**  
   重新開啟 PowerShell 和 ChroLens Mimic

### 方法 2: 程式已自動處理（推薦）

最新版的 `image_manager.py` 已經包含自動路徑偵測功能，會自動尋找以下位置：

```
✅ C:\Program Files\Tesseract-OCR\tesseract.exe
✅ C:\Program Files (x86)\Tesseract-OCR\tesseract.exe
✅ C:\Tesseract-OCR\tesseract.exe
✅ %LOCALAPPDATA%\Tesseract-OCR\tesseract.exe
✅ %LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe
✅ 系統 PATH 環境變數
```

**只要你安裝在上述任一位置，程式會自動找到！**

---

## 🧪 測試安裝

### 測試 1: 命令列測試

```powershell
# 測試 Python 套件
python -c "import pytesseract; import cv2; print('Python 套件 OK')"

# 測試 Tesseract
tesseract --version
```

### 測試 2: 使用測試腳本

```powershell
python test_captcha_recognition.py
```

### 測試 3: 在程式中測試

1. 開啟 ChroLens Mimic
2. 點擊「圖片管理器」
3. 匯入一張驗證碼圖片
4. 點擊「🔍 識別驗證碼」

如果看到結果，表示成功！✅

---

## 📋 快速安裝指令（一鍵執行）

### PowerShell 一鍵安裝腳本

複製並執行以下指令：

```powershell
# 1. 安裝 Python 套件
Write-Host "安裝 Python 套件..." -ForegroundColor Yellow
pip install pytesseract opencv-python pillow numpy

# 2. 檢查 Tesseract
Write-Host "檢查 Tesseract..." -ForegroundColor Yellow
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tesseractPath) {
    Write-Host "✓ Tesseract 已安裝" -ForegroundColor Green
    & $tesseractPath --version
} else {
    Write-Host "✗ 未找到 Tesseract" -ForegroundColor Red
    Write-Host "請下載: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    Start-Process "https://github.com/UB-Mannheim/tesseract/wiki"
}

# 3. 測試安裝
Write-Host "測試 Python 套件..." -ForegroundColor Yellow
python -c "import pytesseract; import cv2; print('✓ Python 套件安裝成功')"
```

或直接執行現成的腳本：

```powershell
.\install_captcha_recognition.ps1
```

---

## 🎯 常見問題

### Q1: pip install 很慢或失敗

**解決方法：使用國內鏡像**

```powershell
pip install pytesseract opencv-python pillow numpy -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 下載 Tesseract 很慢

**解決方法：使用備用下載點**

- GitHub Release: https://github.com/tesseract-ocr/tesseract/releases
- 備用鏡像: https://digi.bib.uni-mannheim.de/tesseract/

### Q3: 安裝後仍然找不到 tesseract

**檢查清單：**

1. ✅ 確認安裝路徑是否正確
   ```powershell
   dir "C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

2. ✅ 確認環境變數
   ```powershell
   $env:Path -split ';' | Select-String "Tesseract"
   ```

3. ✅ 重新啟動程式
   - 關閉 ChroLens Mimic
   - 重新開啟

4. ✅ 手動設定路徑（最後手段）
   在 `image_manager.py` 的第 561 行附近加入：
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Q4: 識別結果不準確

**提高識別率的方法：**

1. 使用更清晰的圖片（至少 100x40 px）
2. 轉換為 PNG 格式
3. 調整圖片對比度
4. 手動清理背景雜訊
5. 參考 `CAPTCHA_RECOGNITION_GUIDE.md` 的進階技巧

### Q5: 需要識別中文驗證碼

**Tesseract 預設不支援中文，需要額外設定：**

1. 下載中文語言包
2. 放到 Tesseract 的 `tessdata` 資料夾
3. 修改識別配置

詳細步驟較複雜，建議參考 Tesseract 官方文檔。

---

## 📥 下載連結整理

### Python 套件（PyPI）
```
pytesseract: https://pypi.org/project/pytesseract/
opencv-python: https://pypi.org/project/opencv-python/
```

### Tesseract-OCR

**主要下載點：**
- Windows 安裝程式: https://github.com/UB-Mannheim/tesseract/wiki
- GitHub Releases: https://github.com/tesseract-ocr/tesseract/releases

**推薦版本：**
- tesseract-ocr-w64-setup-5.3.3.20231005.exe (64位元)
- tesseract-ocr-w32-setup-5.3.3.20231005.exe (32位元)

---

## ✅ 安裝確認清單

安裝完成後，確認以下項目：

- [ ] Python 套件已安裝（pytesseract, opencv-python）
- [ ] Tesseract-OCR 已安裝
- [ ] tesseract --version 可以執行
- [ ] 程式已重新啟動
- [ ] 圖片管理器中有「驗證碼識別」區域
- [ ] 點擊「識別驗證碼」可以執行（不報錯）
- [ ] 可以成功識別簡單的驗證碼

全部打勾 ✅ = 安裝成功！

---

## 🎓 延伸閱讀

- Tesseract 官方文檔: https://tesseract-ocr.github.io/
- pytesseract 使用教學: https://github.com/madmaze/pytesseract
- OpenCV 官方教學: https://docs.opencv.org/
- ChroLens 驗證碼識別完整手冊: `CAPTCHA_RECOGNITION_GUIDE.md`

---

## 📞 還有問題？

1. 檢查 `CAPTCHA_QUICK_REF.md` 的故障排除章節
2. 執行 `test_captcha_recognition.py` 診斷問題
3. 重新執行 `install_captcha_recognition.ps1`

---

**安裝完成後，記得重新啟動 ChroLens Mimic！** 🔄

**祝安裝順利！** 🎉
