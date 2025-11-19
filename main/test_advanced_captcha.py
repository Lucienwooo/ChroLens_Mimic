"""
測試腳本 - 測試進階驗證碼識別系統
針對 76N8 級別的強噪點驗證碼
"""

import cv2
import os
import sys

# 導入進階識別器
try:
    from captcha_recognition_advanced import AdvancedCaptchaRecognizer
except ImportError:
    print("✗ 無法導入 captcha_recognition_advanced 模組")
    sys.exit(1)


def test_captcha_image(image_path: str):
    """
    測試驗證碼圖片識別
    :param image_path: 圖片路徑
    """
    print("="*80)
    print("🧪 進階驗證碼識別測試")
    print("="*80)
    
    # 檢查圖片是否存在
    if not os.path.exists(image_path):
        print(f"✗ 圖片不存在: {image_path}")
        return
    
    # 顯示圖片資訊
    img = cv2.imread(image_path)
    if img is None:
        print(f"✗ 無法讀取圖片: {image_path}")
        return
    
    print(f"📷 圖片資訊:")
    print(f"  - 路徑: {image_path}")
    print(f"  - 大小: {img.shape[1]} x {img.shape[0]} 像素")
    print(f"  - 色彩通道: {img.shape[2] if len(img.shape) == 3 else 1}")
    print()
    
    # 創建識別器
    recognizer = AdvancedCaptchaRecognizer()
    
    # 執行識別（保存調試圖片）
    result = recognizer.recognize_from_file(
        image_path, 
        char_type="alphanumeric",  # 數字 + 字母
        save_debug=True
    )
    
    # 顯示結果
    print("\n" + "="*80)
    if result:
        print(f"🎉 識別成功!")
        print(f"📝 識別結果: {result}")
        print(f"📏 長度: {len(result)} 字符")
        
        # 分析結果
        has_digit = any(c.isdigit() for c in result)
        has_alpha = any(c.isalpha() for c in result)
        
        print(f"🔍 字符分析:")
        print(f"  - 包含數字: {'✓' if has_digit else '✗'}")
        print(f"  - 包含字母: {'✓' if has_alpha else '✗'}")
        
        # 逐字符分析
        print(f"  - 字符詳情:")
        for i, char in enumerate(result):
            char_type = "數字" if char.isdigit() else "字母"
            print(f"    [{i+1}] '{char}' ({char_type})")
    else:
        print(f"❌ 識別失敗")
        print(f"💡 建議:")
        print(f"  1. 檢查調試圖片 (debug_*.png) 查看預處理效果")
        print(f"  2. 嘗試調整圖片品質或拍攝角度")
        print(f"  3. 確保 Tesseract-OCR 已正確安裝")
    
    print("="*80)
    
    # 列出生成的調試圖片
    print("\n📁 生成的調試圖片:")
    debug_files = [f for f in os.listdir('.') if f.startswith('debug_') and f.endswith('.png')]
    if debug_files:
        debug_files.sort()
        for i, f in enumerate(debug_files, 1):
            file_size = os.path.getsize(f) / 1024  # KB
            print(f"  [{i:2d}] {f} ({file_size:.1f} KB)")
    else:
        print("  (無調試圖片)")
    
    return result


def test_multiple_images(image_folder: str = "captcha_tests"):
    """
    測試多張驗證碼圖片
    :param image_folder: 圖片資料夾
    """
    if not os.path.exists(image_folder):
        print(f"✗ 資料夾不存在: {image_folder}")
        return
    
    # 尋找所有圖片
    image_files = []
    for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
        image_files.extend([f for f in os.listdir(image_folder) if f.lower().endswith(ext)])
    
    if not image_files:
        print(f"✗ 資料夾中沒有圖片: {image_folder}")
        return
    
    print(f"找到 {len(image_files)} 張圖片，開始測試...\n")
    
    results = []
    for i, image_file in enumerate(image_files, 1):
        image_path = os.path.join(image_folder, image_file)
        print(f"\n[{i}/{len(image_files)}] 測試: {image_file}")
        print("-" * 80)
        
        result = test_captcha_image(image_path)
        results.append((image_file, result))
        
        print()
    
    # 顯示總結
    print("\n" + "="*80)
    print("📊 測試總結")
    print("="*80)
    
    success_count = sum(1 for _, r in results if r)
    print(f"總測試: {len(results)} 張")
    print(f"成功: {success_count} 張 ({success_count/len(results)*100:.1f}%)")
    print(f"失敗: {len(results) - success_count} 張")
    print()
    
    print("詳細結果:")
    for image_file, result in results:
        status = "✓" if result else "✗"
        result_text = result if result else "失敗"
        print(f"  {status} {image_file:30s} -> {result_text}")


def main():
    """主函數"""
    print("\n🚀 進階驗證碼識別測試程式")
    print("專門針對 76N8 級別的強噪點、多色彩驗證碼\n")
    
    # 檢查命令列參數
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_captcha_image(image_path)
    else:
        # 預設測試圖片
        test_images = [
            "captcha_test.png",
            "captcha_76n8.png",
            "test_captcha.png",
        ]
        
        found = False
        for test_image in test_images:
            if os.path.exists(test_image):
                print(f"找到測試圖片: {test_image}\n")
                test_captcha_image(test_image)
                found = True
                break
        
        if not found:
            print("ℹ️  使用說明:")
            print(f"  python {os.path.basename(__file__)} <圖片路徑>")
            print()
            print("範例:")
            print(f"  python {os.path.basename(__file__)} captcha_76n8.png")
            print()
            print("或將驗證碼圖片保存為以下任一檔名:")
            for img in test_images:
                print(f"  - {img}")


if __name__ == "__main__":
    main()
