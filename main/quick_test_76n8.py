"""
快速測試工具 - 使用附圖測試 76N8 驗證碼識別
"""

import cv2
import numpy as np
from PIL import Image
import os

# 將附圖 Base64 或從剪貼簿讀取
def save_captcha_from_clipboard():
    """從剪貼簿保存驗證碼圖片"""
    try:
        from PIL import ImageGrab
        
        # 從剪貼簿獲取圖片
        img = ImageGrab.grabclipboard()
        
        if img is None:
            print("❌ 剪貼簿中沒有圖片")
            print("\n請先:")
            print("  1. 右鍵點擊驗證碼圖片")
            print("  2. 選擇'複製圖片'")
            print("  3. 再次執行此腳本")
            return None
        
        # 保存圖片
        filename = "76n8_captcha.png"
        img.save(filename)
        print(f"✓ 已從剪貼簿保存圖片: {filename}")
        return filename
    
    except Exception as e:
        print(f"❌ 從剪貼簿讀取失敗: {e}")
        return None


def quick_test():
    """快速測試流程"""
    print("\n" + "="*60)
    print("🚀 76N8 驗證碼快速測試工具")
    print("="*60 + "\n")
    
    # 檢查是否已有測試圖片
    test_files = ['76n8_captcha.png', 'captcha.png', 'test_captcha.png']
    
    captcha_file = None
    for filename in test_files:
        if os.path.exists(filename):
            captcha_file = filename
            print(f"✓ 找到測試圖片: {filename}")
            break
    
    # 如果沒有，嘗試從剪貼簿讀取
    if not captcha_file:
        print("📋 未找到測試圖片，嘗試從剪貼簿讀取...")
        captcha_file = save_captcha_from_clipboard()
    
    if not captcha_file:
        print("\n" + "="*60)
        print("⚠️  使用說明")
        print("="*60)
        print("\n方法 1: 從剪貼簿")
        print("  1. 右鍵點擊驗證碼圖片 → 複製圖片")
        print("  2. 執行: python quick_test_76n8.py")
        print("\n方法 2: 手動保存")
        print("  1. 將驗證碼圖片另存為 '76n8_captcha.png'")
        print("  2. 執行: python test_76n8_ultimate.py 76n8_captcha.png")
        return
    
    # 執行測試
    print(f"\n開始識別驗證碼...")
    print("-"*60 + "\n")
    
    # 導入測試模組
    import test_76n8_ultimate
    test_76n8_ultimate.test_captcha_image(captcha_file)


if __name__ == "__main__":
    quick_test()
