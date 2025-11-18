# -*- coding: utf-8 -*-
"""
ChroLens 圖片識別模組
提供螢幕圖片識別、比對、定位功能
"""

import pyautogui
import cv2
import numpy as np
from typing import Tuple, Optional, List
import time
import os


class ImageRecognition:
    """圖片識別核心類別 - 增強版"""
    
    def __init__(self, confidence: float = 0.75):
        """
        初始化
        :param confidence: 識別信心度閾值 (0.0-1.0), 降低預設值提高辨識成功率
        """
        self.confidence = confidence
        self.min_confidence = 0.6  # 最低可接受信心度
        pyautogui.FAILSAFE = True  # 移動滑鼠到角落停止
        pyautogui.PAUSE = 0.1  # 每次操作間隔
    
    def _load_template(self, template_path: str) -> Optional[np.ndarray]:
        """
        安全載入模板圖片 (支援中文路徑)
        :param template_path: 模板圖片路徑
        :return: OpenCV圖片陣列或None
        """
        try:
            # 方法1: 直接讀取 (可能在中文路徑失敗)
            img = cv2.imread(template_path)
            if img is not None:
                return img
            
            # 方法2: 使用imdecode繞過路徑編碼問題
            with open(template_path, 'rb') as f:
                img_data = f.read()
                img_array = np.frombuffer(img_data, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    return img
            
            print(f"✗ 無法讀取圖片: {template_path}")
            return None
            
        except Exception as e:
            print(f"✗ 載入圖片時出錯: {e}")
            return None
    
    def _match_template_cv2(self, screenshot: np.ndarray, template: np.ndarray, 
                            confidence: float, grayscale: bool = True) -> Optional[Tuple[int, int, int, int]]:
        """
        使用OpenCV進行模板匹配
        :param screenshot: 螢幕截圖
        :param template: 模板圖片
        :param confidence: 信心度閾值
        :param grayscale: 是否轉灰階
        :return: (x, y, width, height) 或 None
        """
        try:
            # 轉灰階
            if grayscale:
                screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                screenshot_gray = screenshot
                template_gray = template
            
            # 模板匹配
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 檢查信心度
            if max_val >= confidence:
                h, w = template.shape[:2]
                x, y = max_loc
                return (x, y, w, h)
            
            return None
            
        except Exception as e:
            print(f"✗ OpenCV匹配失敗: {e}")
            return None
    
    def find_image(self, 
                   template_path: str, 
                   region: Optional[Tuple[int, int, int, int]] = None,
                   grayscale: bool = True,
                   multi_scale: bool = True) -> Optional[Tuple[int, int, int, int]]:
        """
        在螢幕上尋找圖片 - 增強版 (支援中文路徑)
        :param template_path: 模板圖片路徑
        :param region: 搜尋區域 (left, top, width, height)
        :param grayscale: 是否使用灰階比對(更快)
        :param multi_scale: 是否嘗試多尺度匹配(提高辨識率)
        :return: (x, y, width, height) 或 None
        """
        # 1. 驗證檔案路徑
        print(f"[1/4] 驗證檔案路徑...")
        template_path = os.path.normpath(template_path)
        
        if not os.path.exists(template_path):
            print(f"  ✗ 圖片不存在: {template_path}")
            return None
        print(f"  ✓ 檔案存在")
        
        # 2. 載入模板圖片
        print(f"[2/4] 載入模板圖片 (支援中文路徑)...")
        template = self._load_template(template_path)
        if template is None:
            print(f"  ✗ 載入失敗")
            return None
        
        print(f"  ✓ 模板載入成功: {os.path.basename(template_path)} (尺寸: {template.shape[1]}x{template.shape[0]})")
        
        # 3. 截取螢幕
        print(f"[3/4] 截取螢幕畫面...")
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
                print(f"  ✓ 已截取區域: {region}")
            else:
                screenshot = pyautogui.screenshot()
                print(f"  ✓ 已截取全螢幕")
            
            # 轉換為OpenCV格式 (PIL -> numpy -> BGR)
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            print(f"  ✗ 截圖失敗: {e}")
            return None
        
        # 4. 開始圖片匹配
        print(f"[4/4] 開始圖片匹配...")
        
        # 策略1: 標準信心度 + 灰階
        print(f"  → 策略1: 標準識別 (信心度 {self.confidence}, 灰階={grayscale})")
        result = self._match_template_cv2(screenshot_bgr, template, self.confidence, grayscale)
        if result:
            print(f"  ✓ 標準識別成功! 位置: ({result[0]}, {result[1]})")
            return result
        
        # 策略2: 降低信心度 (多尺度)
        if multi_scale:
            for idx, conf in enumerate([self.confidence - 0.05, self.confidence - 0.1, self.confidence - 0.15, self.min_confidence], 2):
                if conf < self.min_confidence:
                    break
                print(f"  → 策略{idx}: 降低信心度 (信心度 {conf:.2f})")
                result = self._match_template_cv2(screenshot_bgr, template, conf, grayscale)
                if result:
                    print(f"  ✓ 降低信心度識別成功! 位置: ({result[0]}, {result[1]})")
                    return result
        
        # 策略3: 彩色模式 (如果原本用灰階)
        if grayscale:
            print(f"  → 策略3: 彩色模式")
            result = self._match_template_cv2(screenshot_bgr, template, self.min_confidence, False)
            if result:
                print(f"  ✓ 彩色模式識別成功! 位置: ({result[0]}, {result[1]})")
                return result
        
        print(f"  ✗ 所有策略均未找到圖片")
        return None
    
    def find_all_images(self,
                        template_path: str,
                        region: Optional[Tuple[int, int, int, int]] = None) -> List[Tuple[int, int, int, int]]:
        """
        找出所有符合的圖片位置
        :return: [(x, y, w, h), ...] 列表
        """
        if not os.path.exists(template_path):
            print(f"圖片不存在: {template_path}")
            return []
        
        try:
            locations = list(pyautogui.locateAllOnScreen(
                template_path,
                confidence=self.confidence,
                region=region
            ))
            return locations
        except Exception as e:
            print(f"批量圖片識別失敗: {e}")
            return []
    
    def get_image_center(self, location: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """
        取得圖片中心點座標
        :param location: (x, y, width, height)
        :return: (center_x, center_y)
        """
        x, y, w, h = location
        return (x + w // 2, y + h // 2)
    
    def wait_for_image(self,
                       template_path: str,
                       timeout: float = 30.0,
                       check_interval: float = 0.5,
                       region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Tuple[int, int]]:
        """
        等待圖片出現
        :param template_path: 模板圖片路徑
        :param timeout: 超時時間(秒)
        :param check_interval: 檢查間隔(秒)
        :param region: 搜尋區域
        :return: 圖片中心點座標或None(超時)
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            location = self.find_image(template_path, region)
            if location:
                return self.get_image_center(location)
            time.sleep(check_interval)
        
        return None  # 超時
    
    def move_to_image(self,
                      template_path: str,
                      region: Optional[Tuple[int, int, int, int]] = None,
                      duration: float = 0.3) -> Optional[Tuple[int, int]]:
        """
        找到圖片並移動滑鼠到圖片中心
        :param template_path: 模板圖片路徑
        :param region: 搜尋區域
        :param duration: 移動持續時間(秒), 0表示瞬間移動
        :return: 圖片中心座標或None
        """
        location = self.find_image(template_path, region)
        if location:
            center = self.get_image_center(location)
            pyautogui.moveTo(center[0], center[1], duration=duration)
            print(f"✓ 滑鼠已移動至圖片中心: {center}")
            return center
        print(f"✗ 未找到圖片,無法移動滑鼠")
        return None
    
    def click_image(self,
                    template_path: str,
                    clicks: int = 1,
                    button: str = 'left',
                    region: Optional[Tuple[int, int, int, int]] = None,
                    duration: float = 0.3,
                    move_first: bool = True) -> bool:
        """
        找到圖片並點擊 (增強版)
        :param template_path: 模板圖片路徑
        :param clicks: 點擊次數
        :param button: 'left', 'right', 'middle'
        :param region: 搜尋區域
        :param duration: 移動到圖片的持續時間(秒)
        :param move_first: 是否先移動滑鼠再點擊 (True=更像人類操作)
        :return: 是否成功
        """
        location = self.find_image(template_path, region)
        if location:
            center = self.get_image_center(location)
            
            if move_first and duration > 0:
                # 先移動滑鼠到目標位置
                pyautogui.moveTo(center[0], center[1], duration=duration)
                time.sleep(0.05)  # 短暫停頓
                # 然後點擊
                pyautogui.click(clicks=clicks, button=button)
            else:
                # 直接點擊 (pyautogui會自動移動)
                pyautogui.click(center[0], center[1], clicks=clicks, button=button, duration=duration)
            
            print(f"✓ 已點擊圖片中心: {center}")
            return True
        
        print(f"✗ 未找到圖片,無法點擊")
        return False
    
    def image_exists(self, 
                     template_path: str, 
                     region: Optional[Tuple[int, int, int, int]] = None) -> bool:
        """
        檢查圖片是否存在
        :param template_path: 模板圖片路徑
        :param region: 搜尋區域
        :return: True/False
        """
        return self.find_image(template_path, region) is not None
    
    def capture_screenshot(self, 
                          region: Optional[Tuple[int, int, int, int]] = None,
                          save_path: Optional[str] = None):
        """
        截取螢幕
        :param region: 截取區域 (left, top, width, height)，None表示全螢幕
        :param save_path: 儲存路徑，None表示不儲存
        :return: PIL Image 物件
        """
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            if save_path:
                screenshot.save(save_path)
            
            return screenshot
        except Exception as e:
            print(f"截圖失敗: {e}")
            return None


# 方便的快速方法
def find_and_click(image_path: str, confidence: float = 0.8, timeout: float = 0.0) -> bool:
    """
    快速找圖並點擊
    :param image_path: 圖片路徑
    :param confidence: 信心度
    :param timeout: 等待超時(0表示不等待)
    :return: 是否成功
    """
    ir = ImageRecognition(confidence)
    
    if timeout > 0:
        result = ir.wait_for_image(image_path, timeout)
        if result:
            pyautogui.click(result[0], result[1])
            return True
        return False
    else:
        return ir.click_image(image_path)


def wait_image(image_path: str, timeout: float = 30.0, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
    """
    快速等待圖片
    :param image_path: 圖片路徑
    :param timeout: 超時時間
    :param confidence: 信心度
    :return: 圖片中心座標或None
    """
    ir = ImageRecognition(confidence)
    return ir.wait_for_image(image_path, timeout)


def check_image_exists(image_path: str, confidence: float = 0.8) -> bool:
    """
    快速檢查圖片是否存在
    :param image_path: 圖片路徑
    :param confidence: 信心度
    :return: True/False
    """
    ir = ImageRecognition(confidence)
    return ir.image_exists(image_path)


# 測試用
if __name__ == "__main__":
    print("ChroLens 圖片識別模組測試")
    print("=" * 50)
    
    # 測試截圖
    print("測試1: 全螢幕截圖...")
    ir = ImageRecognition()
    screenshot = ir.capture_screenshot(save_path="test_screenshot.png")
    if screenshot:
        print("✓ 截圖成功，已儲存為 test_screenshot.png")
    else:
        print("✗ 截圖失敗")
    
    print("\n使用說明:")
    print("1. 準備要識別的圖片(PNG格式)")
    print("2. 使用 ImageRecognition 類別進行識別")
    print("3. 支援等待、點擊、檢查等功能")
    print("\n範例程式碼:")
    print("  ir = ImageRecognition(confidence=0.8)")
    print("  location = ir.find_image('button.png')")
    print("  if location:")
    print("      ir.click_image('button.png')")
