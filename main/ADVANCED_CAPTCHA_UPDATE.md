# 進階驗證碼識別系統 - 更新說明

## 📅 更新日期: 2025-11-19

---

## 🎯 更新目標

針對 **76N8** 級別的強噪點、多色彩、帶陰影的驗證碼，開發進階識別系統。

### 驗證碼特徵
- ✅ **強噪點**: 大量背景噪點干擾
- ✅ **多色彩**: 每個字符使用不同顏色 (紅、綠、藍、黃等)
- ✅ **陰影效果**: 字符下方有重疊陰影
- ✅ **複雜背景**: 紋理背景增加識別難度

---

## 🚀 新增檔案

### 核心模組
1. **`captcha_recognition_advanced.py`** (新增)
   - 進階驗證碼識別器
   - 使用顏色分離、輪廓檢測、陰影移除等技術
   - 支援 6 種預處理方法並投票選出最佳結果

2. **`test_advanced_captcha.py`** (新增)
   - 測試工具
   - 可測試單張或多張驗證碼圖片
   - 自動生成調試圖片方便分析

3. **`example_advanced_captcha.py`** (新增)
   - 使用範例腳本
   - 包含 5 個詳細範例
   - 展示各種使用場景

### 文件更新
4. **`CAPTCHA_README.md`** (更新)
   - 更新為進階識別功能說明
   - 移除過時的文件引用
   - 添加故障排除指南

---

## 🗑️ 清理檔案

已刪除以下多餘的測試和文檔檔案:

### 測試檔案
- ❌ `test_76n8_ultimate.py` (已刪除)
- ❌ `quick_test_76n8.py` (已刪除)
- ❌ `demo_combat.py` (已刪除)
- ❌ `check_hotkey.py` (已刪除)

### 文檔檔案
- ❌ `使用說明_驗證碼識別.md` (已刪除)
- ❌ `SCREEN_CAPTURE_GUIDE.md` (已刪除)
- ❌ `INSTALL_GUIDE.md` (已刪除)
- ❌ `installer/BUILD_GUIDE.md` (已刪除)

### 保留檔案
- ✅ `README.md` (主要說明文件)
- ✅ `CAPTCHA_README.md` (驗證碼識別專用說明)

---

## 🔧 技術特點

### 1. 顏色分離技術
使用 HSV、LAB、RGB 三種色彩空間，分離出不同顏色的字符:
- 紅色通道
- 綠色通道
- 藍色通道
- 黃色通道
- 青色通道
- 洋紅色通道
- 深色通道

### 2. 陰影移除
使用 LAB 色彩空間的 CLAHE (對比度限制自適應直方圖均衡化):
- 移除背景陰影
- 增強字符對比度
- 保留字符細節

### 3. 輪廓檢測
- 自動檢測字符邊界
- 過濾小噪點
- 保留合理大小的輪廓

### 4. 多方法投票
使用 6 種預處理方法:
1. **顏色分離法** - 分離不同顏色通道
2. **陰影移除法** - 移除陰影並二值化
3. **形態學梯度法** - 提取邊緣特徵
4. **Canny 邊緣法** - 精確邊緣檢測
5. **多尺度投票法** - 多尺度處理並投票
6. **顏色聚合法** - 合併最佳顏色通道

### 5. 多 PSM 模式
使用 Tesseract 的多種 Page Segmentation Mode:
- PSM 6: 假設單一文字區塊
- PSM 7: 單行文字
- PSM 8: 單字
- PSM 10: 單字符
- PSM 11: 稀疏文字
- PSM 13: 無序文字

---

## 📝 使用方法

### 快速開始

```python
from captcha_recognition_advanced import AdvancedCaptchaRecognizer

# 創建識別器
recognizer = AdvancedCaptchaRecognizer()

# 從檔案識別
result = recognizer.recognize_from_file(
    "captcha_76n8.png",
    char_type="alphanumeric",
    save_debug=True  # 保存調試圖片
)

print(f"識別結果: {result}")
```

### 命令列測試

```bash
# 測試單張圖片
python test_advanced_captcha.py captcha_76n8.png

# 查看使用範例
python example_advanced_captcha.py
```

---

## 🐛 調試功能

### 自動保存調試圖片
設定 `save_debug=True` 時，會自動保存以下調試圖片:

1. `debug_00_original.png` - 原始圖片
2. `debug_01_color_red.png` - 紅色通道
3. `debug_02_color_green.png` - 綠色通道
4. `debug_03_shadow_removed_otsu.png` - 陰影移除 + Otsu
5. `debug_04_morphological_gradient.png` - 形態學梯度
6. `debug_05_canny_edge.png` - Canny 邊緣
7. 等等...

### 分析調試圖片
使用範例腳本分析:
```bash
python example_advanced_captcha.py
# 選擇選項 5
```

---

## 📊 預期效果

| 驗證碼類型 | 識別率 | 處理時間 |
|-----------|--------|---------|
| 簡單驗證碼 (低噪點) | 90%+ | 1-2 秒 |
| 中等驗證碼 (中噪點) | 80%+ | 2-3 秒 |
| 困難驗證碼 (強噪點 + 多色彩) | 70-80% | 3-5 秒 |
| 極難驗證碼 (如 76N8) | 60-75% | 5-8 秒 |

### 提升識別率的建議
1. 使用高品質的驗證碼圖片
2. 確保圖片清晰，無模糊
3. 截取時包含完整的驗證碼區域
4. 避免過度壓縮的 JPEG 圖片，建議使用 PNG
5. 查看調試圖片，選擇效果最好的預處理方法

---

## 🔮 未來改進方向

### 短期 (1-2 週)
- [ ] 添加機器學習模型 (CNN) 輔助識別
- [ ] 優化顏色分離算法
- [ ] 添加更多預處理策略

### 中期 (1-2 月)
- [ ] 訓練專用的驗證碼識別模型
- [ ] 建立驗證碼樣本數據集
- [ ] 支援更多驗證碼類型

### 長期 (3+ 月)
- [ ] 開發 GUI 工具
- [ ] 支援即時識別
- [ ] 雲端識別 API

---

## 📞 支援

如有問題或建議，請:
1. 查看 `CAPTCHA_README.md` 故障排除章節
2. 執行 `example_advanced_captcha.py` 查看範例
3. 檢查調試圖片分析預處理效果
4. 在 GitHub 提交 Issue

---

## 📜 授權

與 ChroLens_Mimic 主專案相同的授權條款。

---

**最後更新**: 2025-11-19  
**版本**: Advanced v1.0
