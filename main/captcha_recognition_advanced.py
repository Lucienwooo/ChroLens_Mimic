"""
進階驗證碼識別模組 - 專門針對 76N8 級別的強噪點、多色彩驗證碼
使用顏色分離 + 輪廓檢測 + 深度學習方法
"""

import cv2
import numpy as np
from PIL import Image
import pyautogui
from typing import Optional, Tuple, List, Dict
import os
from collections import Counter

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("警告: pytesseract 未安裝，部分功能將受限")


class AdvancedCaptchaRecognizer:
    """進階驗證碼識別器 - 針對強噪點、多色彩驗證碼優化"""
    
    def __init__(self):
        """初始化驗證碼識別器"""
        self.tesseract_available = TESSERACT_AVAILABLE
        
        # 設定 Tesseract 路徑 (Windows)
        if TESSERACT_AVAILABLE:
            possible_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'D:\Program Files\Tesseract-OCR\tesseract.exe',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"✓ 找到 Tesseract: {path}")
                    break
    
    def capture_captcha(self, region: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        截取驗證碼區域
        :param region: (left, top, width, height)
        :return: OpenCV 圖片陣列
        """
        try:
            screenshot = pyautogui.screenshot(region=region)
            img_np = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            return img_bgr
        except Exception as e:
            print(f"✗ 截取驗證碼失敗: {e}")
            return None
    
    def extract_color_channels(self, img: np.ndarray) -> Dict[str, np.ndarray]:
        """
        提取不同顏色通道 - 針對多色彩驗證碼
        :param img: OpenCV 圖片 (BGR)
        :return: 各顏色通道的二值化圖片字典
        """
        print("    🎨 分析顏色通道...")
        
        # 轉換到不同色彩空間
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        
        results = {}
        
        # === 1. HSV 色彩分離 ===
        # 紅色範圍 (0-10 和 170-180)
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        results['red'] = cv2.bitwise_or(mask_red1, mask_red2)
        
        # 綠色範圍
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        results['green'] = cv2.inRange(hsv, lower_green, upper_green)
        
        # 藍色範圍
        lower_blue = np.array([100, 40, 40])
        upper_blue = np.array([130, 255, 255])
        results['blue'] = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # 黃色範圍
        lower_yellow = np.array([20, 50, 50])
        upper_yellow = np.array([40, 255, 255])
        results['yellow'] = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # 青色範圍
        lower_cyan = np.array([80, 40, 40])
        upper_cyan = np.array([100, 255, 255])
        results['cyan'] = cv2.inRange(hsv, lower_cyan, upper_cyan)
        
        # 洋紅色範圍
        lower_magenta = np.array([130, 40, 40])
        upper_magenta = np.array([170, 255, 255])
        results['magenta'] = cv2.inRange(hsv, lower_magenta, upper_magenta)
        
        # 深色文字（低飽和度、低亮度）
        lower_dark = np.array([0, 0, 0])
        upper_dark = np.array([180, 255, 100])
        results['dark'] = cv2.inRange(hsv, lower_dark, upper_dark)
        
        # === 2. LAB 色彩分離（更精確的顏色分離）===
        # L通道 - 亮度
        l_channel = lab[:,:,0]
        # 提取深色區域（字符可能在這裡）
        _, dark_mask = cv2.threshold(l_channel, 100, 255, cv2.THRESH_BINARY_INV)
        results['lab_dark'] = dark_mask
        
        # A通道 - 紅綠軸
        a_channel = lab[:,:,1]
        # 提取偏紅色區域
        _, red_a = cv2.threshold(a_channel, 135, 255, cv2.THRESH_BINARY)
        results['lab_red'] = red_a
        
        # 提取偏綠色區域
        _, green_a = cv2.threshold(a_channel, 0, 255, cv2.THRESH_BINARY_INV)
        results['lab_green'] = cv2.threshold(green_a, 120, 255, cv2.THRESH_BINARY_INV)[1]
        
        # === 3. RGB 通道分離 ===
        b, g, r = cv2.split(img)
        
        # 強化紅色通道
        _, r_thresh = cv2.threshold(r, 100, 255, cv2.THRESH_BINARY)
        results['rgb_red'] = r_thresh
        
        # 強化綠色通道
        _, g_thresh = cv2.threshold(g, 100, 255, cv2.THRESH_BINARY)
        results['rgb_green'] = g_thresh
        
        # 強化藍色通道
        _, b_thresh = cv2.threshold(b, 100, 255, cv2.THRESH_BINARY)
        results['rgb_blue'] = b_thresh
        
        # 統計每個通道的有效像素數量
        stats = {}
        for name, mask in results.items():
            count = cv2.countNonZero(mask)
            stats[name] = count
        
        # 顯示統計
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        print(f"      顏色通道統計 (前5):")
        for name, count in sorted_stats[:5]:
            if count > 0:
                print(f"        {name}: {count} 像素")
        
        return results
    
    def remove_shadow(self, img: np.ndarray) -> np.ndarray:
        """
        移除陰影效果
        :param img: OpenCV 圖片
        :return: 移除陰影後的圖片
        """
        print("    🌟 移除陰影...")
        
        # 轉換為 LAB 色彩空間
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # 對 L 通道進行 CLAHE (對比度限制自適應直方圖均衡化)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l)
        
        # 合併回 LAB
        lab_clahe = cv2.merge([l_clahe, a, b])
        
        # 轉回 BGR
        result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
        
        return result
    
    def extract_text_by_contour(self, img: np.ndarray, min_area: int = 50) -> np.ndarray:
        """
        使用輪廓檢測提取文字區域
        :param img: 二值化圖片
        :param min_area: 最小輪廓面積
        :return: 提取文字後的圖片
        """
        print("    📐 使用輪廓檢測提取文字...")
        
        # 尋找輪廓
        contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return img
        
        # 計算輪廓統計資訊
        areas = [cv2.contourArea(c) for c in contours]
        if not areas:
            return img
        
        median_area = np.median(areas)
        mean_area = np.mean(areas)
        std_area = np.std(areas)
        
        print(f"      輪廓統計: 總數={len(contours)}, 中位數面積={median_area:.1f}, 平均面積={mean_area:.1f}")
        
        # 創建遮罩
        mask = np.zeros_like(img)
        
        # 篩選輪廓：保留接近中位數大小的輪廓（可能是字符）
        kept_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # 條件1: 面積在合理範圍內（中位數的 0.2 倍到 5 倍）
            if median_area * 0.2 <= area <= median_area * 5:
                # 條件2: 長寬比合理（字符不會太扁或太高）
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0
                
                if 0.2 <= aspect_ratio <= 3.0:
                    # 繪製輪廓
                    cv2.drawContours(mask, [contour], -1, 255, -1)
                    kept_count += 1
        
        print(f"      保留輪廓: {kept_count}/{len(contours)}")
        
        return mask
    
    def ultimate_preprocess(self, img: np.ndarray, save_debug: bool = False) -> List[Tuple[np.ndarray, str]]:
        """
        終極預處理 - 使用多種方法組合
        :param img: 原始圖片
        :param save_debug: 是否保存調試圖片
        :return: 處理後的圖片列表 [(圖片, 方法名稱), ...]
        """
        print("\n  🚀 === 啟動終極預處理流程 === 🚀")
        results = []
        
        # 放大圖片 (10倍，提供更多細節)
        h, w = img.shape[:2]
        enlarged = cv2.resize(img, (w * 10, h * 10), interpolation=cv2.INTER_LANCZOS4)
        
        # === 方法 1: 顏色分離法 ===
        print("\n  [方法 1] 顏色分離法")
        color_channels = self.extract_color_channels(enlarged)
        
        # 對每個有效的顏色通道進行處理
        for color_name, color_mask in color_channels.items():
            if cv2.countNonZero(color_mask) > 100:  # 至少要有一些像素
                # 降噪
                denoised = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                denoised = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
                
                # 輪廓提取
                contour_result = self.extract_text_by_contour(denoised, min_area=100)
                
                if cv2.countNonZero(contour_result) > 0:
                    # 膨脹以連接斷裂
                    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    dilated = cv2.dilate(contour_result, kernel_dilate, iterations=2)
                    
                    results.append((dilated, f"color_{color_name}"))
        
        # === 方法 2: 移除陰影 + 灰階處理 ===
        print("\n  [方法 2] 陰影移除法")
        shadow_removed = self.remove_shadow(enlarged)
        
        # 轉灰階
        gray = cv2.cvtColor(shadow_removed, cv2.COLOR_BGR2GRAY)
        
        # 多階段降噪
        # 1. 中值濾波
        median = cv2.medianBlur(gray, 7)
        
        # 2. 非局部均值降噪
        nlm = cv2.fastNlMeansDenoising(median, None, h=30, templateWindowSize=7, searchWindowSize=21)
        
        # 3. 雙邊濾波
        bilateral = cv2.bilateralFilter(nlm, 11, 90, 90)
        
        # 4. 高斯模糊
        gaussian = cv2.GaussianBlur(bilateral, (5, 5), 1.5)
        
        # 多種二值化方法
        # Otsu
        _, binary_otsu = cv2.threshold(gaussian, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        results.append((binary_otsu, "shadow_removed_otsu"))
        
        # 自適應閾值
        binary_adaptive = cv2.adaptiveThreshold(
            gaussian, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, blockSize=31, C=10
        )
        results.append((binary_adaptive, "shadow_removed_adaptive"))
        
        # === 方法 3: 形態學梯度邊緣檢測 ===
        print("\n  [方法 3] 形態學梯度法")
        kernel_grad = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gradient = cv2.morphologyEx(gaussian, cv2.MORPH_GRADIENT, kernel_grad)
        
        # 二值化
        _, binary_grad = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 閉運算連接邊緣
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed_grad = cv2.morphologyEx(binary_grad, cv2.MORPH_CLOSE, kernel_close, iterations=3)
        
        results.append((closed_grad, "morphological_gradient"))
        
        # === 方法 4: Canny邊緣 + 膨脹 ===
        print("\n  [方法 4] Canny 邊緣法")
        edges = cv2.Canny(gaussian, 50, 150)
        
        # 膨脹連接邊緣
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        dilated_edges = cv2.dilate(edges, kernel_dilate, iterations=2)
        
        # 閉運算填充
        closed_edges = cv2.morphologyEx(dilated_edges, cv2.MORPH_CLOSE, kernel_close, iterations=3)
        
        results.append((closed_edges, "canny_edge"))
        
        # === 方法 5: 多尺度多閾值投票法 ===
        print("\n  [方法 5] 多尺度投票法")
        vote_result = np.zeros_like(gray, dtype=np.float32)
        
        for scale in [8, 10, 12]:
            scaled = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
            gray_scaled = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
            
            # 降噪
            denoised_scaled = cv2.fastNlMeansDenoising(gray_scaled, None, h=25, templateWindowSize=7, searchWindowSize=21)
            
            # 多閾值
            _, b1 = cv2.threshold(denoised_scaled, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            b2 = cv2.adaptiveThreshold(denoised_scaled, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 25, 8)
            
            # 合併
            combined = cv2.bitwise_and(b1, b2)
            
            # 調整到目標大小
            resized = cv2.resize(combined, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_AREA)
            
            # 累加投票
            vote_result += resized.astype(np.float32) / 255.0
        
        # 取平均，超過50%投票則為前景
        final_vote = ((vote_result / 3.0) > 0.5).astype(np.uint8) * 255
        results.append((final_vote, "multiscale_voting"))
        
        # === 方法 6: 顏色聚合法 ===
        print("\n  [方法 6] 顏色聚合法")
        # 合併最佳的幾個顏色通道
        best_channels = []
        channel_stats = [(name, cv2.countNonZero(mask)) for name, mask in color_channels.items()]
        channel_stats.sort(key=lambda x: x[1], reverse=True)
        
        for name, count in channel_stats[:3]:  # 取前3個
            if count > 500:  # 至少有500個像素
                best_channels.append(color_channels[name])
        
        if best_channels:
            # 合併通道
            aggregated = np.zeros_like(best_channels[0])
            for channel in best_channels:
                aggregated = cv2.bitwise_or(aggregated, channel)
            
            # 輪廓提取
            contour_agg = self.extract_text_by_contour(aggregated, min_area=100)
            
            # 形態學處理
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            cleaned_agg = cv2.morphologyEx(contour_agg, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            results.append((cleaned_agg, "color_aggregation"))
        
        # 對所有結果進行後處理
        print("\n  🔧 後處理所有結果...")
        final_results = []
        for idx, (img_processed, method_name) in enumerate(results):
            # 連通組件分析去除小噪點
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(img_processed, connectivity=8)
            
            if num_labels > 1:
                areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
                if areas:
                    median_area = np.median(areas)
                    
                    # 創建遮罩，只保留合理大小的組件
                    mask = np.zeros_like(img_processed)
                    for i in range(1, num_labels):
                        area = stats[i, cv2.CC_STAT_AREA]
                        if area > median_area * 0.15:  # 保留面積 > 中位數的15%
                            mask[labels == i] = 255
                    
                    img_processed = mask
            
            # 最終銳化
            kernel_sharp = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(img_processed, -1, kernel_sharp)
            
            final_results.append((sharpened, method_name))
            
            # 保存調試圖片
            if save_debug:
                debug_path = f"debug_{idx}_{method_name}.png"
                cv2.imwrite(debug_path, sharpened)
                print(f"      保存調試圖片: {debug_path}")
        
        print(f"\n  ✅ 完成預處理，產生 {len(final_results)} 個候選圖片")
        return final_results
    
    def recognize_with_tesseract(self, img: np.ndarray, 
                                 char_type: str = "alphanumeric",
                                 psm: int = 7) -> Optional[str]:
        """
        使用 Tesseract OCR 識別
        :param img: OpenCV 圖片
        :param char_type: 字符類型
        :param psm: Page Segmentation Mode
        :return: 識別結果
        """
        if not self.tesseract_available:
            return None
        
        try:
            # 字符白名單
            if char_type == "digits":
                whitelist = '0123456789'
            elif char_type == "alpha":
                whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            else:  # alphanumeric
                whitelist = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            
            # 配置
            config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist={whitelist}'
            
            # 轉換為 PIL Image
            if len(img.shape) == 2:  # 灰階圖
                img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            else:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            pil_img = Image.fromarray(img_rgb)
            
            # OCR
            text = pytesseract.image_to_string(pil_img, config=config)
            text = ''.join(filter(str.isalnum, text)).strip()
            
            return text if text else None
            
        except Exception as e:
            return None
    
    def recognize_captcha(self, 
                         region: Tuple[int, int, int, int],
                         char_type: str = "alphanumeric",
                         save_debug: bool = True) -> Optional[str]:
        """
        完整驗證碼識別流程
        :param region: 驗證碼區域 (left, top, width, height)
        :param char_type: 字符類型
        :param save_debug: 是否保存調試圖片
        :return: 識別結果
        """
        print("\n" + "="*70)
        print("🔍 === 進階驗證碼識別系統啟動 (76N8 專用) === 🔍")
        print("="*70)
        
        # 1. 截取驗證碼
        print(f"\n[1/4] 📸 截取驗證碼區域: {region}")
        img = self.capture_captcha(region)
        if img is None:
            return None
        print("  ✓ 截取成功")
        
        # 保存原始圖片
        if save_debug:
            cv2.imwrite("debug_00_original.png", img)
            print("  ✓ 保存原始圖片: debug_00_original.png")
        
        # 2. 終極預處理
        print(f"\n[2/4] 🔧 圖片預處理中...")
        processed_images = self.ultimate_preprocess(img, save_debug=save_debug)
        
        # 3. OCR 識別
        print(f"\n[3/4] 🤖 OCR 識別中...")
        all_results = []
        
        # PSM 模式列表
        psm_modes = [6, 7, 8, 10, 11, 13]
        
        for img_processed, method_name in processed_images:
            for psm in psm_modes:
                result = self.recognize_with_tesseract(img_processed, char_type, psm)
                
                if result and len(result) >= 3:  # 過濾太短的結果
                    all_results.append((result, f"{method_name}_PSM{psm}"))
                    print(f"  [{method_name}] PSM{psm}: '{result}'")
        
        # 4. 統計和選擇最佳結果
        print(f"\n[4/4] 📊 分析結果...")
        if all_results:
            # 統計出現次數
            result_counts = Counter([r for r, _ in all_results])
            
            # 顯示統計
            print(f"  共獲得 {len(all_results)} 個識別結果:")
            for result, count in result_counts.most_common(10):
                sources = [s for r, s in all_results if r == result]
                print(f"    '{result}' - 出現 {count} 次")
                if count > 1:
                    print(f"      來源: {', '.join(sources[:3])}{' ...' if len(sources) > 3 else ''}")
            
            # 選擇策略：優先選擇出現次數多的，如果次數相同則選擇4個字符的
            candidates = []
            for result, count in result_counts.most_common():
                if len(result) == 4:  # 76N8 是4個字符
                    candidates.append((result, count))
            
            # 如果沒有4個字符的，就選出現最多的
            if not candidates:
                candidates = result_counts.most_common()
            
            best_result = candidates[0][0] if candidates else result_counts.most_common(1)[0][0]
            best_count = candidates[0][1] if candidates else result_counts.most_common(1)[0][1]
            
            print(f"\n✅ === 識別完成 ===")
            print(f"  最佳結果: '{best_result}' (長度: {len(best_result)}, 置信度: {best_count}/{len(processed_images)} 方法投票)")
            print("="*70 + "\n")
            
            return best_result
        else:
            print(f"\n❌ === 識別失敗 ===")
            print(f"  所有方法均無法識別驗證碼")
            print(f"  建議: 檢查圖片品質或調整識別參數")
            print("="*70 + "\n")
            return None
    
    def recognize_from_file(self, filepath: str, 
                           char_type: str = "alphanumeric",
                           save_debug: bool = True) -> Optional[str]:
        """
        從檔案識別驗證碼
        :param filepath: 圖片檔案路徑
        :param char_type: 字符類型
        :param save_debug: 是否保存調試圖片
        :return: 識別結果
        """
        print("\n" + "="*70)
        print(f"🔍 === 從檔案識別驗證碼: {filepath} === 🔍")
        print("="*70)
        
        # 讀取圖片
        img = cv2.imread(filepath)
        if img is None:
            print(f"✗ 無法讀取圖片: {filepath}")
            return None
        
        print(f"  ✓ 讀取成功，圖片大小: {img.shape[1]}x{img.shape[0]}")
        
        # 保存原始圖片
        if save_debug:
            cv2.imwrite("debug_00_original.png", img)
            print("  ✓ 保存原始圖片: debug_00_original.png")
        
        # 終極預處理
        print(f"\n🔧 圖片預處理中...")
        processed_images = self.ultimate_preprocess(img, save_debug=save_debug)
        
        # OCR 識別
        print(f"\n🤖 OCR 識別中...")
        all_results = []
        
        psm_modes = [6, 7, 8, 10, 11, 13]
        
        for img_processed, method_name in processed_images:
            for psm in psm_modes:
                result = self.recognize_with_tesseract(img_processed, char_type, psm)
                
                if result and len(result) >= 3:
                    all_results.append((result, f"{method_name}_PSM{psm}"))
                    print(f"  [{method_name}] PSM{psm}: '{result}'")
        
        # 統計和選擇最佳結果
        print(f"\n📊 分析結果...")
        if all_results:
            result_counts = Counter([r for r, _ in all_results])
            
            print(f"  共獲得 {len(all_results)} 個識別結果:")
            for result, count in result_counts.most_common(10):
                print(f"    '{result}' - 出現 {count} 次")
            
            # 優先選擇4個字符的結果
            candidates = []
            for result, count in result_counts.most_common():
                if len(result) == 4:
                    candidates.append((result, count))
            
            if not candidates:
                candidates = result_counts.most_common()
            
            best_result = candidates[0][0] if candidates else result_counts.most_common(1)[0][0]
            best_count = candidates[0][1] if candidates else result_counts.most_common(1)[0][1]
            
            print(f"\n✅ === 識別完成 ===")
            print(f"  最佳結果: '{best_result}' (長度: {len(best_result)}, 置信度: {best_count}/{len(processed_images)} 方法投票)")
            print("="*70 + "\n")
            
            return best_result
        else:
            print(f"\n❌ === 識別失敗 ===")
            print("="*70 + "\n")
            return None


# 使用範例
if __name__ == "__main__":
    print("進階驗證碼識別模組")
    print("專門針對 76N8 級別的強噪點、多色彩驗證碼\n")
    
    recognizer = AdvancedCaptchaRecognizer()
    
    # 測試從檔案識別
    test_file = "captcha_test.png"  # 您的驗證碼圖片
    if os.path.exists(test_file):
        result = recognizer.recognize_from_file(test_file, char_type="alphanumeric", save_debug=True)
        print(f"\n最終識別結果: {result}")
    else:
        print(f"請將驗證碼圖片保存為 {test_file} 後執行測試")
