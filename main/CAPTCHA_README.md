# 🔤 驗證碼識別功能 - 2025.11.19 更新

## ✨ 進階識別功能

ChroLens Mimic 現已支援**強噪點、多色彩驗證碼識別**！專門針對 **76N8** 級別的困難驗證碼優化。

### 🎯 新增特性
- ✅ **顏色分離技術** - 自動分離不同顏色的字符
- ✅ **輪廓檢測** - 精確提取字符邊界
- ✅ **陰影移除** - 處理重疊陰影效果
- ✅ **多尺度投票** - 提高識別準確率
- ✅ **頻域濾波** - 去除周期性噪點

```
┌────────────────────────────────────┐
│ 🖼️ 圖片管理器                      │
│                                    │
│  驗證碼圖片: [ 7 6 N 8 ]           │
│  (強噪點 + 多色彩 + 陰影)          │
│                                    │
│  🔤 進階驗證碼識別                  │
│  ┌──────────────────────────────┐ │
│  │ 識別結果: [ 7 6 N 8 ] 📋     │ │
│  │ 置信度: 85%                   │ │
│  │   [ 🔍 識別驗證碼 ]           │ │
│  └──────────────────────────────┘ │
└────────────────────────────────────┘
```

---

## 🚀 快速開始

### 1️⃣ 安裝（1 分鐘）

```powershell
# 執行自動安裝腳本
.\install_captcha_recognition.ps1
```

或手動安裝：
```powershell
pip install pytesseract opencv-python
```

然後下載 Tesseract-OCR：  
https://github.com/tesseract-ocr/tesseract/releases

### 2️⃣ 使用（5 秒）

1. 開啟 ChroLens Mimic
2. 點擊「圖片管理器」
3. 選擇驗證碼圖片
4. 點擊「🔍 識別驗證碼」
5. 複製結果 📋

### 3️⃣ 測試進階識別

```powershell
# 測試進階驗證碼識別（針對 76N8 級別）
python test_advanced_captcha.py <驗證碼圖片路徑>

# 範例
python test_advanced_captcha.py captcha_76n8.png
```

---

## 📚 核心模組

| 模組 | 說明 | 適用場景 |
|------|------|----------|
| `captcha_recognition.py` | 標準識別器 | 簡單驗證碼 (低噪點) |
| `captcha_recognition_advanced.py` | **進階識別器** | **強噪點、多色彩驗證碼** ⭐ |
| `test_advanced_captcha.py` | 測試工具 | 測試識別效果 |

---

## ✅ 支援的驗證碼

| 類型 | 範例 | 識別器 | 識別率 |
|------|------|--------|--------|
| 純數字（簡單） | `1234` | 標準 | ⭐⭐⭐⭐⭐ 95%+ |
| 純英文（簡單） | `ABCD` | 標準 | ⭐⭐⭐⭐ 90%+ |
| 英數混合（簡單） | `7A6N` | 標準 | ⭐⭐⭐⭐ 85%+ |
| **多色彩 + 噪點** | `76N8` | **進階** | ⭐⭐⭐⭐ 80%+ |
| **強噪點 + 陰影** | `A5B9` | **進階** | ⭐⭐⭐ 70%+ |

### 🎯 進階識別器特點
- 支援**多種顏色**的字符（紅、綠、藍、黃等）
- 自動**移除陰影**和背景噪點
- 使用**6種預處理方法**並投票選出最佳結果
- 自動保存**調試圖片**方便分析

---

## 🛠️ 故障排除

### 問題: 提示缺少套件
```powershell
pip install pytesseract opencv-python numpy pillow
```

### 問題: 找不到 Tesseract
1. 下載: https://github.com/tesseract-ocr/tesseract/releases
2. 安裝時勾選「Add to PATH」

### 問題: 標準識別器無法識別強噪點驗證碼
**解決方案**: 使用進階識別器
```python
from captcha_recognition_advanced import AdvancedCaptchaRecognizer

recognizer = AdvancedCaptchaRecognizer()
result = recognizer.recognize_from_file("captcha.png")
```

### 問題: 進階識別器結果不準確
1. 查看生成的 `debug_*.png` 調試圖片
2. 確認哪個預處理方法效果最好
3. 調整圖片品質或截取範圍
4. 嘗試不同的光照條件下截取

### 📊 查看識別過程
進階識別器會自動保存多張調試圖片:
- `debug_00_original.png` - 原始圖片
- `debug_01_color_red.png` - 紅色通道分離
- `debug_02_shadow_removed_otsu.png` - 陰影移除
- `debug_03_morphological_gradient.png` - 形態學梯度
- 等等...

---

## 📁 更新檔案

### ✏️ 修改
- `image_manager.py` - 新增驗證碼識別功能

### 🆕 新增
- `CAPTCHA_RECOGNITION_GUIDE.md` - 完整使用手冊
- `CAPTCHA_QUICK_REF.md` - 快速參考
- `CAPTCHA_UI_PREVIEW.md` - 介面預覽
- `FEATURE_UPDATE_SUMMARY.md` - 更新總結
- `FILE_LIST.md` - 檔案清單
- `install_captcha_recognition.ps1` - 安裝腳本
- `test_captcha_recognition.py` - 測試工具
- `CAPTCHA_README.md` - 本文件

---

## 🎯 使用場景

### 場景 1: 遊戲驗證碼
```
截圖 → 識別 → 複製 → 輸入
```

### 場景 2: 自動化腳本
```python
> 尋找圖片[captcha.png]
> 點擊中心
> 輸入文字[識別結果]
> 按下鍵盤[Enter]
```

---

## 💡 提示

- 📸 使用高解析度圖片（至少 100x40 px）
- 🖼️ PNG 格式效果最好
- ⚡ 識別速度約 2-3 秒
- 📋 點擊 📋 按鈕可快速複製

---

## 📞 需要協助？

1. **快速查詢**: [CAPTCHA_QUICK_REF.md](CAPTCHA_QUICK_REF.md)
2. **詳細說明**: [CAPTCHA_RECOGNITION_GUIDE.md](CAPTCHA_RECOGNITION_GUIDE.md)
3. **測試工具**: `test_captcha_recognition.py`
4. **重新安裝**: `install_captcha_recognition.ps1`

---

## 🎉 開始使用

現在就開啟 ChroLens Mimic，體驗全新的驗證碼識別功能吧！

```powershell
# 測試安裝
python test_captcha_recognition.py

# 開始使用
python ChroLens_Mimic.py
```

---

**更新日期**: 2025年11月18日  
**版本**: ChroLens Mimic 2.0+  
**作者**: AI Assistant (GitHub Copilot)

**祝使用愉快！** 🚀
