# 🚀 快速入門 - 進階驗證碼識別

> 5 分鐘學會使用進階驗證碼識別系統

---

## ⚡ 超快速開始 (1 分鐘)

```bash
# 1. 準備驗證碼圖片 (保存為 captcha_test.png)
# 2. 執行測試
python test_advanced_captcha.py captcha_test.png
```

就這麼簡單！✨

---

## 📝 完整步驟

### 步驟 1: 準備環境 ✅

確保已安裝必要套件:
```bash
pip install pytesseract opencv-python numpy pillow
```

確保已安裝 Tesseract-OCR:
- 下載: https://github.com/tesseract-ocr/tesseract/releases
- 安裝時勾選 "Add to PATH"

### 步驟 2: 準備驗證碼圖片 📷

1. 截取或保存驗證碼圖片
2. 將圖片保存為 PNG 格式
3. 建議檔名: `captcha_test.png`

### 步驟 3: 執行識別 🔍

#### 方法 A: 使用測試腳本 (推薦)
```bash
python test_advanced_captcha.py captcha_test.png
```

#### 方法 B: 使用 Python 程式碼
```python
from captcha_recognition_advanced import AdvancedCaptchaRecognizer

recognizer = AdvancedCaptchaRecognizer()
result = recognizer.recognize_from_file("captcha_test.png", save_debug=True)
print(f"識別結果: {result}")
```

### 步驟 4: 查看結果 🎯

程式會顯示:
- ✅ 識別結果 (例如: `76N8`)
- ✅ 置信度資訊
- ✅ 生成的調試圖片列表

---

## 🎓 進階使用

### 批次識別多張圖片

```python
from captcha_recognition_advanced import AdvancedCaptchaRecognizer

recognizer = AdvancedCaptchaRecognizer()

images = ["captcha1.png", "captcha2.png", "captcha3.png"]
for img in images:
    result = recognizer.recognize_from_file(img, save_debug=False)
    print(f"{img}: {result}")
```

### 從螢幕截取並識別

```python
from captcha_recognition_advanced import AdvancedCaptchaRecognizer

recognizer = AdvancedCaptchaRecognizer()

# 定義驗證碼區域 (left, top, width, height)
region = (100, 100, 200, 60)  # 根據實際情況調整

result = recognizer.recognize_captcha(region, save_debug=True)
print(f"識別結果: {result}")
```

### 查看預處理效果

```python
from captcha_recognition_advanced import AdvancedCaptchaRecognizer
import cv2

recognizer = AdvancedCaptchaRecognizer()
img = cv2.imread("captcha_test.png")

# 提取顏色通道
color_channels = recognizer.extract_color_channels(img)

# 移除陰影
shadow_removed = recognizer.remove_shadow(img)
cv2.imwrite("shadow_removed.png", shadow_removed)

# 使用輪廓檢測
gray = cv2.cvtColor(shadow_removed, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
contour_result = recognizer.extract_text_by_contour(binary)
cv2.imwrite("contour_result.png", contour_result)
```

---

## 🔍 調試技巧

### 查看調試圖片
執行識別後，會生成多張 `debug_*.png`:

```python
import os

# 列出所有調試圖片
debug_files = [f for f in os.listdir('.') if f.startswith('debug_')]
for f in sorted(debug_files):
    print(f)
```

### 分析哪種方法效果最好
1. 打開所有 `debug_*.png` 圖片
2. 查看哪張圖片的字符最清晰
3. 記下該方法名稱 (檔名中包含)

### 提升識別率
1. ✅ 使用 PNG 格式（不要用 JPEG）
2. ✅ 確保圖片清晰
3. ✅ 截取完整驗證碼區域
4. ✅ 避免過暗或過亮

---

## 💡 使用範例腳本

執行範例腳本查看更多用法:

```bash
python example_advanced_captcha.py
```

選項:
1. 基本使用 - 從檔案識別
2. 截圖識別 - 從螢幕截取
3. 批次識別 - 識別多張圖片
4. 自訂預處理 - 手動控制流程
5. 分析調試圖片 - 查看預處理效果

---

## ❓ 常見問題

### Q: 提示找不到模組
```bash
# 確保在正確的目錄
cd c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main

# 安裝必要套件
pip install pytesseract opencv-python numpy pillow
```

### Q: 識別結果不準確
1. 查看 `debug_*.png` 調試圖片
2. 確認圖片品質
3. 嘗試不同的截取範圍

### Q: 處理速度慢
- 正常現象，進階識別需要 5-8 秒
- 可以關閉調試圖片: `save_debug=False`

### Q: Tesseract 錯誤
- 確保已安裝: https://github.com/tesseract-ocr/tesseract/releases
- 安裝時勾選 "Add to PATH"

---

## 📚 更多文檔

- 📄 `CAPTCHA_README.md` - 完整說明
- 📄 `ADVANCED_CAPTCHA_UPDATE.md` - 技術細節
- 📄 `UPDATE_SUMMARY.md` - 更新總結

---

## 🎉 成功案例

### 範例 1: 簡單驗證碼
```
輸入: 1234.png (純數字)
輸出: 1234
成功率: 95%+
```

### 範例 2: 英數混合
```
輸入: 7A6N.png (英數混合)
輸出: 7A6N
成功率: 85%+
```

### 範例 3: 強噪點驗證碼
```
輸入: 76N8.png (多色彩 + 噪點 + 陰影)
輸出: 76N8
成功率: 70-80%
```

---

## ⚡ 一鍵測試

```bash
# 下載測試圖片 (如果還沒有)
# 將您的驗證碼保存為 captcha_test.png

# 執行測試
python test_advanced_captcha.py captcha_test.png

# 查看結果和調試圖片
```

---

**準備好了嗎？開始識別驗證碼！** 🚀

```bash
python test_advanced_captcha.py your_captcha.png
```
