"""
驗證碼識別模組 - 使用OCR技術識別驗證碼
支援多種驗證碼類型：數字、字母、混合
✨ 針對 76N8 強噪點驗證碼特別優化
"""

import cv2
import numpy as np
from PIL import Image
import pyautogui
from typing import Optional, Tuple, List
import os
import math
from collections import Counter

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("警告: pytesseract 未安裝，驗證碼識別功能將受限")
    print("請執行: pip install pytesseract")
    print("並下載安裝 Tesseract-OCR: https://github.com/tesseract-ocr/tesseract")


class CaptchaRecognizer:
    """驗證碼識別器"""
    
    def __init__(self):
        """初始化驗證碼識別器"""
        self.tesseract_available = TESSERACT_AVAILABLE
        
        # 嘗試設定 Tesseract 路徑 (Windows)
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
            # 轉換為 OpenCV 格式
            img_np = np.array(screenshot)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            return img_bgr
        except Exception as e:
            print(f"✗ 截取驗證碼失敗: {e}")
            return None
    
    def preprocess_image(self, img: np.ndarray, method: str = "adaptive") -> np.ndarray:
        """
        圖片預處理 - 提高 OCR 識別率
        :param img: OpenCV 圖片
        :param method: 預處理方法 ("adaptive", "otsu", "simple", "denoise", "strategy1-5")
        :return: 處理後的圖片
        """
        # 1. 轉灰階
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()
        
        # 使用強化策略處理 76N8 級別驗證碼
        if method == "strategy1":
            return self._strategy1_process(gray)
        elif method == "strategy2":
            return self._strategy2_process(gray)
        elif method == "strategy3":
            return self._strategy3_process(gray)
        elif method == "strategy4":
            return self._strategy4_process(gray)
        elif method == "strategy5":
            return self._strategy5_process(gray)
        elif method == "strategy6":
            return self._strategy6_process(gray)
        elif method == "strategy7":
            return self._strategy7_process(gray)
        elif method == "strategy8":
            return self._strategy8_process(gray)
        elif method == "strategy9" or method == "ultimate":
            return self._strategy9_ultimate_denoiser(gray)
        elif method == "strategy10" or method == "frequency":
            return self._strategy10_frequency_domain_killer(gray)
        
        # 2. 放大圖片 (提高識別率)
        scale_factor = 3
        height, width = gray.shape
        enlarged = cv2.resize(gray, (width * scale_factor, height * scale_factor), 
                             interpolation=cv2.INTER_CUBIC)
        
        # 3. 根據方法進行二值化
        if method == "adaptive":
            # 自適應閾值 (適合不均勻光照)
            binary = cv2.adaptiveThreshold(
                enlarged, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
        elif method == "otsu":
            # Otsu 自動閾值
            _, binary = cv2.threshold(enlarged, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == "denoise":
            # 降噪 + 閾值
            denoised = cv2.fastNlMeansDenoising(enlarged, None, 10, 7, 21)
            _, binary = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY)
        else:  # simple
            # 簡單閾值
            _, binary = cv2.threshold(enlarged, 127, 255, cv2.THRESH_BINARY)
        
        # 4. 形態學操作 - 去除噪點
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def _strategy1_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 1: 超強放大 + 多次降噪"""
        # 超強放大 6 倍
        enlarged = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
        
        # 多重降噪
        denoised = cv2.fastNlMeansDenoising(enlarged, None, h=15, templateWindowSize=7, searchWindowSize=21)
        
        # 形態學梯度
        kernel_edge = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gradient = cv2.morphologyEx(denoised, cv2.MORPH_GRADIENT, kernel_edge)
        
        # Otsu 二值化
        blurred = cv2.GaussianBlur(denoised, (5, 5), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 開閉運算
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # 智能反色
        if cv2.mean(closed)[0] > 127:
            cleaned = cv2.bitwise_not(closed)
        else:
            cleaned = closed
        
        # 銳化
        kernel_sharp = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]])
        sharpened = cv2.filter2D(cleaned, -1, kernel_sharp)
        
        return sharpened
    
    def _strategy2_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 2: 雙邊濾波 + CLAHE"""
        enlarged = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
        
        # 雙邊濾波
        bilateral = cv2.bilateralFilter(enlarged, 9, 75, 75)
        
        # CLAHE 對比度增強
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(bilateral)
        
        # 自適應閾值
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        adaptive = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY, 15, 3)
        
        # 形態學
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        closed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel, iterations=1)
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # 反色
        if cv2.mean(opened)[0] > 127:
            final = cv2.bitwise_not(opened)
        else:
            final = opened
        
        return final
    
    def _strategy3_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 3: 頂帽變換去背景"""
        enlarged = cv2.resize(gray, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
        
        # 頂帽變換
        kernel_tophat = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        tophat = cv2.morphologyEx(enlarged, cv2.MORPH_TOPHAT, kernel_tophat)
        blackhat = cv2.morphologyEx(enlarged, cv2.MORPH_BLACKHAT, kernel_tophat)
        
        processed = cv2.add(enlarged, tophat)
        processed = cv2.subtract(processed, blackhat)
        
        # 固定閾值
        _, fixed_binary = cv2.threshold(processed, 127, 255, cv2.THRESH_BINARY)
        denoised = cv2.fastNlMeansDenoising(fixed_binary, None, 15, 7, 21)
        
        # 反色
        if cv2.mean(denoised)[0] > 127:
            denoised = cv2.bitwise_not(denoised)
        
        return denoised
    
    def _strategy4_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 4: Canny 邊緣檢測"""
        enlarged = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
        
        # 降噪
        denoised = cv2.fastNlMeansDenoising(enlarged, None, 20, 7, 21)
        
        # Canny 邊緣
        blurred = cv2.GaussianBlur(denoised, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # 膨脹
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated = cv2.dilate(edges, kernel_dilate, iterations=1)
        
        # 銳化
        kernel_sharpen = np.array([[-1,-1,-1,-1,-1],
                                   [-1, 2, 2, 2,-1],
                                   [-1, 2, 9, 2,-1],
                                   [-1, 2, 2, 2,-1],
                                   [-1,-1,-1,-1,-1]]) / 8.0
        sharpened = cv2.filter2D(dilated, -1, kernel_sharpen)
        
        # 二值化
        _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if cv2.mean(binary)[0] > 127:
            binary = cv2.bitwise_not(binary)
        
        return binary
    
    def _strategy5_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 5: 形態學重建 + 距離變換 (76N8 專用)"""
        # 超大放大 8 倍
        enlarged = cv2.resize(gray, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
        
        # 三次降噪
        temp = cv2.fastNlMeansDenoising(enlarged, None, h=25, templateWindowSize=7, searchWindowSize=21)
        temp = cv2.fastNlMeansDenoising(temp, None, h=20, templateWindowSize=7, searchWindowSize=21)
        temp = cv2.fastNlMeansDenoising(temp, None, h=15, templateWindowSize=7, searchWindowSize=21)
        
        # 形態學梯度
        kernel_grad = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gradient = cv2.morphologyEx(temp, cv2.MORPH_GRADIENT, kernel_grad)
        
        # 組合
        combined = cv2.addWeighted(temp, 0.7, gradient, 0.3, 0)
        
        # Otsu 二值化
        _, markers = cv2.threshold(combined, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 開閉運算
        kernel_final = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(markers, cv2.MORPH_OPEN, kernel_final, iterations=2)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_final, iterations=1)
        
        # 銳化
        kernel_sharp5 = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
        final = cv2.filter2D(closed, -1, kernel_sharp5)
        
        # 反色
        if cv2.mean(final)[0] > 127:
            final = cv2.bitwise_not(final)
        
        return final
    
    def _strategy6_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 6: 極致降噪 + 連通組件分析 (強噪點專用)"""
        # 10 倍超大放大
        enlarged = cv2.resize(gray, None, fx=10, fy=10, interpolation=cv2.INTER_LANCZOS4)
        
        # 多階段降噪
        # 第一階段：中值濾波去除椒鹽噪點
        median = cv2.medianBlur(enlarged, 5)
        
        # 第二階段：非局部均值降噪
        denoised1 = cv2.fastNlMeansDenoising(median, None, h=30, templateWindowSize=7, searchWindowSize=21)
        
        # 第三階段：高斯雙邊濾波（保邊去噪）
        bilateral = cv2.bilateralFilter(denoised1, 11, 90, 90)
        
        # 第四階段：再次非局部均值
        denoised2 = cv2.fastNlMeansDenoising(bilateral, None, h=25, templateWindowSize=7, searchWindowSize=21)
        
        # CLAHE 極致對比度增強
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))
        enhanced = clahe.apply(denoised2)
        
        # 使用多種閾值方法組合
        # 方法1: Otsu
        _, binary1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 方法2: Triangle (適合噪點多的圖片)
        _, binary2 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
        
        # 組合兩種閾值結果
        combined = cv2.bitwise_and(binary1, binary2)
        
        # 連通組件分析去除小噪點
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(combined, connectivity=8)
        
        # 計算平均面積
        if num_labels > 1:
            areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
            avg_area = np.mean(areas) if areas else 0
            
            # 創建遮罩，只保留面積大於平均值20%的組件
            mask = np.zeros_like(combined)
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] > avg_area * 0.2:
                    mask[labels == i] = 255
        else:
            mask = combined
        
        # 形態學重建
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=3)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 超強銳化
        kernel_sharp = np.array([
            [0, -1, -1, -1, 0],
            [-1, 2, 2, 2, -1],
            [-1, 2, 13, 2, -1],
            [-1, 2, 2, 2, -1],
            [0, -1, -1, -1, 0]
        ]) / 5.0
        sharpened = cv2.filter2D(closed, -1, kernel_sharp)
        
        # 反色
        if cv2.mean(sharpened)[0] > 127:
            final = cv2.bitwise_not(sharpened)
        else:
            final = sharpened
        
        return final
    
    def _strategy7_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 7: 頻域濾波 + 自適應局部閾值 (噪點克星)"""
        # 8 倍放大
        enlarged = cv2.resize(gray, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
        
        # 頻域濾波去除周期性噪點
        # 轉換到頻域
        dft = cv2.dft(np.float32(enlarged), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # 創建帶通濾波器（去除高頻噪點和低頻背景）
        rows, cols = enlarged.shape
        crow, ccol = rows // 2, cols // 2
        mask = np.ones((rows, cols, 2), np.uint8)
        
        # 去除低頻（背景）
        r_low = 30
        center = [crow, ccol]
        x, y = np.ogrid[:rows, :cols]
        mask_area = (x - center[0]) ** 2 + (y - center[1]) ** 2 <= r_low*r_low
        mask[mask_area] = 0
        
        # 去除過高頻（噪點）
        r_high = min(rows, cols) // 4
        mask_area = (x - center[0]) ** 2 + (y - center[1]) ** 2 >= r_high*r_high
        mask[mask_area] = 0
        
        # 應用濾波器
        fshift = dft_shift * mask
        
        # 逆變換回空域
        f_ishift = np.fft.ifftshift(fshift)
        img_back = cv2.idft(f_ishift)
        img_back = cv2.magnitude(img_back[:,:,0], img_back[:,:,1])
        
        # 歸一化
        img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        
        # 非局部均值降噪
        denoised = cv2.fastNlMeansDenoising(img_back, None, h=20, templateWindowSize=7, searchWindowSize=21)
        
        # 自適應局部閾值（針對不均勻光照）
        # 使用較大的 block size 來適應字符大小
        adaptive = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, blockSize=25, C=8
        )
        
        # 形態學閉運算連接斷裂筆畫
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        closed = cv2.morphologyEx(adaptive, cv2.MORPH_CLOSE, kernel_close, iterations=2)
        
        # 開運算去除小噪點
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open, iterations=1)
        
        # 反色
        if cv2.mean(opened)[0] > 127:
            final = cv2.bitwise_not(opened)
        else:
            final = opened
        
        return final
    
    def _strategy8_process(self, gray: np.ndarray) -> np.ndarray:
        """策略 8: 多尺度處理 + 投票機制 (終極穩定版)"""
        results = []
        
        # 多尺度處理（5x, 7x, 9x）
        for scale in [5, 7, 9]:
            enlarged = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
            # 降噪
            denoised = cv2.fastNlMeansDenoising(enlarged, None, h=20, templateWindowSize=7, searchWindowSize=21)
            
            # 使用多種二值化方法
            # Otsu
            _, binary1 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 自適應
            binary2 = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, blockSize=21, C=5
            )
            
            # Triangle
            _, binary3 = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
            
            # 投票機制：至少2種方法認為是前景才算前景
            vote = (binary1.astype(np.float32) + binary2.astype(np.float32) + binary3.astype(np.float32)) / 3.0
            voted = (vote > 127).astype(np.uint8) * 255
            
            results.append(voted)
        
        # 將三個尺度的結果調整為相同大小（使用中間尺度）
        target_size = results[1].shape[::-1]
        results[0] = cv2.resize(results[0], target_size, interpolation=cv2.INTER_AREA)
        results[2] = cv2.resize(results[2], target_size, interpolation=cv2.INTER_AREA)
        
        # 多尺度投票
        final_vote = (results[0].astype(np.float32) + results[1].astype(np.float32) + results[2].astype(np.float32)) / 3.0
        final = (final_vote > 127).astype(np.uint8) * 255
        
        # 形態學精煉
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        final = cv2.morphologyEx(final, cv2.MORPH_CLOSE, kernel, iterations=1)
        final = cv2.morphologyEx(final, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # 反色
        if cv2.mean(final)[0] > 127:
            final = cv2.bitwise_not(final)
        
        return final
    
    def _strategy9_ultimate_denoiser(self, gray: np.ndarray) -> np.ndarray:
        """
        策略 9: 終極噪點殺手 - 專門針對 76N8 級別的強噪點 🔥
        採用多階段漸進式處理：預處理 → 極致降噪 → 智能增強 → 精準二值化 → 後處理優化
        """
        print("    🔥 啟動終極噪點殺手模式...")
        
        # ===== 第一階段：預處理 - 建立良好基礎 =====
        # 超大放大 12 倍（提供更多細節用於降噪）
        h, w = gray.shape
        enlarged = cv2.resize(gray, (w * 12, h * 12), interpolation=cv2.INTER_LANCZOS4)
        
        # ===== 第二階段：極致降噪 - 多層過濾 =====
        # 階段 2.1: 形態學閉運算預填充（減少噪點孔洞）
        kernel_pre = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        morphed = cv2.morphologyEx(enlarged, cv2.MORPH_CLOSE, kernel_pre, iterations=2)
        
        # 階段 2.2: 中值濾波（消除椒鹽噪點）
        median1 = cv2.medianBlur(morphed, 7)
        
        # 階段 2.3: 非局部均值降噪（第一次，h=35 強力去噪）
        nlm1 = cv2.fastNlMeansDenoising(median1, None, h=35, templateWindowSize=9, searchWindowSize=25)
        
        # 階段 2.4: 雙邊濾波（保邊強化）
        bilateral = cv2.bilateralFilter(nlm1, 15, 100, 100)
        
        # 階段 2.5: 高斯濾波（平滑過渡）
        gaussian = cv2.GaussianBlur(bilateral, (7, 7), 1.5)
        
        # 階段 2.6: 非局部均值降噪（第二次，h=25 精細調整）
        nlm2 = cv2.fastNlMeansDenoising(gaussian, None, h=25, templateWindowSize=9, searchWindowSize=21)
        
        # ===== 第三階段：智能增強 - 凸顯字符特徵 =====
        # 階段 3.1: 超強 CLAHE 對比度增強
        clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(3, 3))
        enhanced = clahe.apply(nlm2)
        
        # 階段 3.2: 銳化濾波（增強邊緣）
        kernel_sharpen = np.array([
            [-1, -1, -1, -1, -1],
            [-1,  2,  2,  2, -1],
            [-1,  2, 16,  2, -1],
            [-1,  2,  2,  2, -1],
            [-1, -1, -1, -1, -1]
        ]) / 8.0
        sharpened = cv2.filter2D(enhanced, -1, kernel_sharpen)
        
        # 階段 3.3: 形態學梯度（突出邊界）
        kernel_grad = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        gradient = cv2.morphologyEx(sharpened, cv2.MORPH_GRADIENT, kernel_grad)
        
        # 階段 3.4: 混合增強（70% 銳化 + 30% 梯度）
        mixed = cv2.addWeighted(sharpened, 0.7, gradient, 0.3, 0)
        
        # ===== 第四階段：精準二值化 - 多方法投票 =====
        # 再次降噪後進行二值化
        final_denoise = cv2.fastNlMeansDenoising(mixed, None, h=20, templateWindowSize=7, searchWindowSize=21)
        
        # 方法 1: Otsu 全局閾值
        _, binary_otsu = cv2.threshold(final_denoise, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 方法 2: Triangle 閾值（適合偏態分佈）
        _, binary_triangle = cv2.threshold(final_denoise, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
        
        # 方法 3: 自適應閾值（局部調整）
        binary_adaptive = cv2.adaptiveThreshold(
            final_denoise, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, blockSize=31, C=10
        )
        
        # 方法 4: 基於均值的閾值
        mean_val = cv2.mean(final_denoise)[0]
        _, binary_mean = cv2.threshold(final_denoise, mean_val * 0.9, 255, cv2.THRESH_BINARY)
        
        # 四方法加權投票（Otsu 權重最高）
        vote = (
            binary_otsu.astype(np.float32) * 0.35 +
            binary_triangle.astype(np.float32) * 0.25 +
            binary_adaptive.astype(np.float32) * 0.25 +
            binary_mean.astype(np.float32) * 0.15
        ) / 255.0
        
        # 超過 50% 投票才認為是前景
        voted = (vote > 0.5).astype(np.uint8) * 255
        
        # ===== 第五階段：後處理優化 - 移除殘留噪點 =====
        # 階段 5.1: 連通組件分析（移除小噪點）
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(voted, connectivity=8)
        
        cleaned = np.zeros_like(voted)
        if num_labels > 1:
            # 計算面積統計
            areas = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)]
            if areas:
                median_area = np.median(areas)
                # 只保留面積 > 中位數的 15% 的組件
                for i in range(1, num_labels):
                    area = stats[i, cv2.CC_STAT_AREA]
                    if area > median_area * 0.15:
                        cleaned[labels == i] = 255
        else:
            cleaned = voted
        
        # 階段 5.2: 形態學閉運算（連接斷裂筆畫）
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
        closed = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel_close, iterations=3)
        
        # 階段 5.3: 形態學開運算（去除細小毛刺）
        kernel_open = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_open, iterations=2)
        
        # 階段 5.4: 再次銳化（提升清晰度）
        kernel_final_sharp = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        final_sharpened = cv2.filter2D(opened, -1, kernel_final_sharp)
        
        # 階段 5.5: 智能反色判斷
        mean_brightness = cv2.mean(final_sharpened)[0]
        if mean_brightness > 127:
            result = cv2.bitwise_not(final_sharpened)
        else:
            result = final_sharpened
        
        print("    ✅ 終極降噪完成")
        return result
    
    def _strategy10_frequency_domain_killer(self, gray: np.ndarray) -> np.ndarray:
        """
        策略 10: 頻域噪點殺手 - 使用傅立葉變換在頻域精準去除周期性噪點
        """
        print("    ⚡ 啟動頻域噪點殺手...")
        
        # 放大 10 倍
        enlarged = cv2.resize(gray, None, fx=10, fy=10, interpolation=cv2.INTER_LANCZOS4)
        
        # 預降噪
        denoised = cv2.fastNlMeansDenoising(enlarged, None, h=25, templateWindowSize=7, searchWindowSize=21)
        
        # 轉換到頻域
        dft = cv2.dft(np.float32(denoised), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # 創建精細帶通濾波器
        rows, cols = denoised.shape
        crow, ccol = rows // 2, cols // 2
        
        # 創建遮罩
        mask = np.ones((rows, cols, 2), np.float32)
        
        # 計算距離矩陣
        y, x = np.ogrid[:rows, :cols]
        dist = np.sqrt((x - ccol)**2 + (y - crow)**2)
        
        # 移除低頻（背景）- 半徑 40
        mask[dist < 40] = 0
        
        # 移除高頻（噪點）- 保留中頻（字符邊緣）
        r_high = min(rows, cols) // 5
        mask[dist > r_high] = 0.3  # 不完全移除，保留 30%
        
        # 對特定頻率加強衰減（針對周期性噪點）
        # 檢測並抑制能量峰值
        magnitude = np.sqrt(dft_shift[:,:,0]**2 + dft_shift[:,:,1]**2)
        threshold = np.percentile(magnitude, 98)  # 前 2% 的能量
        high_energy_mask = magnitude > threshold
        mask[high_energy_mask] *= 0.1  # 強烈抑制高能量點
        
        # 應用濾波器
        fshift = dft_shift * mask
        
        # 逆變換回空域
        f_ishift = np.fft.ifftshift(fshift)
        img_back = cv2.idft(f_ishift)
        img_back = cv2.magnitude(img_back[:,:,0], img_back[:,:,1])
        
        # 歸一化
        img_back = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        
        # 後處理
        # 雙邊濾波
        bilateral = cv2.bilateralFilter(img_back, 11, 80, 80)
        
        # CLAHE
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(bilateral)
        
        # 多閾值投票
        _, b1 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        b2 = cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 27, 8)
        
        # 投票
        voted = ((b1.astype(np.float32) + b2.astype(np.float32)) / 2.0 > 127).astype(np.uint8) * 255
        
        # 形態學
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        result = cv2.morphologyEx(voted, cv2.MORPH_CLOSE, kernel, iterations=2)
        result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # 反色
        if cv2.mean(result)[0] > 127:
            result = cv2.bitwise_not(result)
        
        print("    ✅ 頻域處理完成")
        return result
    
    def recognize_with_tesseract(self, img: np.ndarray, 
                                 char_type: str = "alphanumeric") -> Optional[str]:
        """
        使用 Tesseract OCR 識別驗證碼
        :param img: OpenCV 圖片
        :param char_type: 字符類型 ("digits", "alpha", "alphanumeric")
        :return: 識別出的文字
        """
        if not self.tesseract_available:
            print("✗ Tesseract 不可用，請安裝 pytesseract 和 Tesseract-OCR")
            return None
        
        try:
            # 設定 Tesseract 配置
            if char_type == "digits":
                config = '--psm 7 -c tessedit_char_whitelist=0123456789'
            elif char_type == "alpha":
                config = '--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            else:  # alphanumeric
                config = '--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            
            # 轉換為 PIL Image
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            # 執行 OCR
            text = pytesseract.image_to_string(pil_img, config=config)
            text = text.strip()
            
            return text if text else None
            
        except Exception as e:
            print(f"✗ Tesseract 識別失敗: {e}")
            return None
    
    def recognize_captcha(self, 
                         region: Tuple[int, int, int, int],
                         char_type: str = "alphanumeric",
                         try_all_methods: bool = True,
                         use_enhanced_strategies: bool = True) -> Optional[str]:
        """
        完整驗證碼識別流程
        :param region: 驗證碼區域 (left, top, width, height)
        :param char_type: 字符類型 ("digits", "alpha", "alphanumeric")
        :param try_all_methods: 是否嘗試所有預處理方法
        :param use_enhanced_strategies: 是否使用增強策略 (76N8 級別)
        :return: 識別出的驗證碼
        """
        print("\n" + "="*50)
        print("🔍 開始驗證碼識別流程")
        if use_enhanced_strategies:
            print("🚀 已啟用增強策略 (76N8 級別)")
        print("="*50)
        
        # 1. 截取驗證碼
        print(f"[1/4] 截取驗證碼區域: {region}")
        img = self.capture_captcha(region)
        if img is None:
            return None
        print("  ✓ 截取成功")
        
        # 2. 嘗試不同的預處理方法
        print(f"[2/4] 圖片預處理...")
        
        # 根據是否啟用增強策略選擇方法
        if use_enhanced_strategies:
            # 🔥 新增兩個終極策略，優先使用
            methods = [
                "strategy9",    # 終極噪點殺手（最強）
                "strategy10",   # 頻域噪點殺手
                "strategy6",    # 極致降噪 + 連通組件
                "strategy7",    # 頻域濾波 + 自適應
                "strategy8",    # 多尺度投票
                "strategy5",    # 形態學重建
                "strategy1",    # 超強放大降噪
                "strategy2",    # 雙邊濾波 CLAHE
            ]
            psm_modes = [6, 7, 8, 10, 11, 13]  # 使用更多 PSM 模式
        elif try_all_methods:
            methods = ["adaptive", "otsu", "denoise", "simple"]
            psm_modes = [7]  # 預設單行文字
        else:
            methods = ["adaptive"]
            psm_modes = [7]
        
        all_results = []
        
        for method in methods:
            print(f"  → 嘗試方法: {method}")
            processed = self.preprocess_image(img, method)
            
            # 3. OCR 識別 - 嘗試多個 PSM 模式
            for psm in psm_modes:
                result = self.recognize_with_tesseract_psm(processed, char_type, psm)
                
                if result and len(result) >= 3:  # 過濾太短的結果
                    all_results.append((result, f"{method}-PSM{psm}"))
                    print(f"    PSM {psm}: '{result}'")
        
        # 4. 統計和選擇最佳結果
        print(f"[3/4] 分析結果...")
        if all_results:
            from collections import Counter
            
            # 統計出現次數
            result_counts = Counter([r for r, _ in all_results])
            
            # 顯示所有結果
            print(f"  有效結果共 {len(all_results)} 個:")
            for result, count in result_counts.most_common(5):
                sources = [s for r, s in all_results if r == result]
                print(f"    '{result}' 出現 {count} 次")
            
            # 選擇最佳結果
            most_common = result_counts.most_common(1)[0]
            if most_common[1] > 1:  # 如果有結果出現多次
                best_result = most_common[0]
            else:
                # 選擇最長的結果
                best_result = max(all_results, key=lambda x: len(x[0]))[0]
            
            print(f"[4/4] 完成")
            print(f"✓ 最終結果: '{best_result}' (長度: {len(best_result)})")
            print("="*50 + "\n")
            return best_result
        else:
            print(f"[4/4] 完成")
            print(f"✗ 所有方法均無法識別驗證碼")
            print("="*50 + "\n")
            return None
    
    def recognize_with_tesseract_psm(self, img: np.ndarray, 
                                    char_type: str = "alphanumeric",
                                    psm: int = 7) -> Optional[str]:
        """
        使用指定 PSM 模式的 Tesseract OCR 識別
        :param img: OpenCV 圖片
        :param char_type: 字符類型 ("digits", "alpha", "alphanumeric")
        :param psm: Page Segmentation Mode (0-13)
        :return: 識別出的文字
        """
        if not self.tesseract_available:
            return None
        
        try:
            # 設定 Tesseract 配置
            if char_type == "digits":
                whitelist = '0123456789'
            elif char_type == "alpha":
                whitelist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            else:  # alphanumeric
                whitelist = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            
            config = f'--psm {psm} --oem 3 -c tessedit_char_whitelist={whitelist}'
            
            # 轉換為 PIL Image
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            # 執行 OCR
            text = pytesseract.image_to_string(pil_img, config=config)
            # 只保留字母和數字
            text = ''.join(filter(str.isalnum, text)).strip()
            
            return text if text else None
            
        except Exception as e:
            return None
    
    def save_debug_image(self, img: np.ndarray, filename: str = "captcha_debug.png"):
        """
        儲存除錯圖片
        :param img: OpenCV 圖片
        :param filename: 檔案名稱
        """
        try:
            cv2.imwrite(filename, img)
            print(f"✓ 除錯圖片已儲存: {filename}")
        except Exception as e:
            print(f"✗ 儲存除錯圖片失敗: {e}")


class SimpleCaptchaRecognizer:
    """
    簡單驗證碼識別器 - 不需要 Tesseract
    適用於簡單的數字或字母驗證碼
    使用模板匹配方法
    """
    
    def __init__(self, template_dir: str = "captcha_templates"):
        """
        初始化
        :param template_dir: 字符模板資料夾
        """
        self.template_dir = template_dir
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """載入字符模板"""
        if not os.path.exists(self.template_dir):
            print(f"警告: 模板資料夾不存在: {self.template_dir}")
            return
        
        for filename in os.listdir(self.template_dir):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                # 檔名應為字符本身 (例: 0.png, A.png)
                char = os.path.splitext(filename)[0]
                template_path = os.path.join(self.template_dir, filename)
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    self.templates[char] = template
        
        print(f"✓ 已載入 {len(self.templates)} 個字符模板")
    
    def segment_characters(self, img: np.ndarray) -> List[np.ndarray]:
        """
        切割字符
        :param img: 二值化圖片
        :return: 字符圖片列表
        """
        # 尋找輪廓
        contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 根據 x 座標排序
        bounding_boxes = [cv2.boundingRect(c) for c in contours]
        bounding_boxes = sorted(bounding_boxes, key=lambda x: x[0])
        
        # 提取字符
        characters = []
        for x, y, w, h in bounding_boxes:
            # 過濾太小的區域 (可能是噪點)
            if w > 5 and h > 5:
                char_img = img[y:y+h, x:x+w]
                characters.append(char_img)
        
        return characters
    
    def match_character(self, char_img: np.ndarray, threshold: float = 0.7) -> Optional[str]:
        """
        匹配單一字符
        :param char_img: 字符圖片
        :param threshold: 匹配閾值
        :return: 識別出的字符
        """
        best_match = None
        best_score = 0
        
        for char, template in self.templates.items():
            # 調整大小以匹配模板
            resized = cv2.resize(char_img, (template.shape[1], template.shape[0]))
            
            # 模板匹配
            result = cv2.matchTemplate(resized, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            if max_val > best_score:
                best_score = max_val
                best_match = char
        
        if best_score >= threshold:
            return best_match
        return None
    
    def recognize_captcha(self, img: np.ndarray) -> Optional[str]:
        """
        識別驗證碼
        :param img: OpenCV 圖片
        :return: 識別結果
        """
        # 預處理
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        # 切割字符
        characters = self.segment_characters(binary)
        
        if not characters:
            return None
        
        # 識別每個字符
        result = ""
        for char_img in characters:
            char = self.match_character(char_img)
            if char:
                result += char
        
        return result if result else None


# 使用範例
if __name__ == "__main__":
    print("驗證碼識別模組測試")
    print("="*50)
    
    # 測試 1: 使用 Tesseract
    if TESSERACT_AVAILABLE:
        print("\n測試 Tesseract OCR:")
        recognizer = CaptchaRecognizer()
        
        # 請提供驗證碼區域座標
        # region = (x, y, width, height)
        # result = recognizer.recognize_captcha(region, char_type="digits")
        # print(f"識別結果: {result}")
    
    # 測試 2: 簡單模板匹配
    print("\n測試模板匹配:")
    simple_recognizer = SimpleCaptchaRecognizer()
    print(f"已載入 {len(simple_recognizer.templates)} 個模板")
