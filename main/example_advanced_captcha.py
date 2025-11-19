"""
使用範例 - 進階驗證碼識別器
展示如何使用顏色分離和輪廓檢測來識別強噪點驗證碼
"""

import cv2
import os
from captcha_recognition_advanced import AdvancedCaptchaRecognizer


def example_1_basic_recognition():
    """範例 1: 基本使用 - 從檔案識別"""
    print("\n" + "="*80)
    print("範例 1: 基本使用 - 從檔案識別")
    print("="*80)
    
    # 創建識別器
    recognizer = AdvancedCaptchaRecognizer()
    
    # 從檔案識別
    result = recognizer.recognize_from_file(
        "captcha_test.png",
        char_type="alphanumeric",  # 支援數字和字母
        save_debug=True  # 保存調試圖片
    )
    
    if result:
        print(f"\n✅ 識別成功: {result}")
    else:
        print(f"\n❌ 識別失敗")


def example_2_screenshot_recognition():
    """範例 2: 截圖識別 - 從螢幕截取驗證碼區域"""
    print("\n" + "="*80)
    print("範例 2: 截圖識別")
    print("="*80)
    
    # 創建識別器
    recognizer = AdvancedCaptchaRecognizer()
    
    # 定義驗證碼區域 (left, top, width, height)
    # 這些數值需要根據實際情況調整
    region = (100, 100, 200, 60)
    
    print(f"請確保驗證碼顯示在螢幕座標 {region}")
    input("按 Enter 開始截取並識別...")
    
    # 執行識別
    result = recognizer.recognize_captcha(
        region,
        char_type="alphanumeric",
        save_debug=True
    )
    
    if result:
        print(f"\n✅ 識別成功: {result}")
    else:
        print(f"\n❌ 識別失敗")


def example_3_batch_recognition():
    """範例 3: 批次識別 - 識別多張驗證碼"""
    print("\n" + "="*80)
    print("範例 3: 批次識別")
    print("="*80)
    
    # 創建識別器
    recognizer = AdvancedCaptchaRecognizer()
    
    # 準備測試圖片列表
    test_images = [
        "captcha_1.png",
        "captcha_2.png",
        "captcha_3.png",
    ]
    
    results = []
    for i, image_path in enumerate(test_images, 1):
        if not os.path.exists(image_path):
            print(f"\n[{i}/{len(test_images)}] ⚠️ 檔案不存在: {image_path}")
            continue
        
        print(f"\n[{i}/{len(test_images)}] 處理: {image_path}")
        result = recognizer.recognize_from_file(
            image_path,
            char_type="alphanumeric",
            save_debug=False  # 批次處理時不保存調試圖
        )
        
        results.append((image_path, result))
        print(f"結果: {result if result else '失敗'}")
    
    # 顯示總結
    print("\n" + "-"*80)
    print("批次識別總結:")
    print("-"*80)
    success = sum(1 for _, r in results if r)
    print(f"總數: {len(results)}")
    print(f"成功: {success}")
    print(f"失敗: {len(results) - success}")
    print(f"成功率: {success/len(results)*100:.1f}%" if results else "N/A")


def example_4_custom_preprocessing():
    """範例 4: 自訂預處理 - 手動控制預處理流程"""
    print("\n" + "="*80)
    print("範例 4: 自訂預處理")
    print("="*80)
    
    # 讀取圖片
    image_path = "captcha_test.png"
    if not os.path.exists(image_path):
        print(f"⚠️ 檔案不存在: {image_path}")
        return
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 無法讀取圖片")
        return
    
    # 創建識別器
    recognizer = AdvancedCaptchaRecognizer()
    
    # 手動執行預處理
    print("\n步驟 1: 提取顏色通道...")
    color_channels = recognizer.extract_color_channels(img)
    
    print(f"  找到 {len(color_channels)} 個顏色通道")
    for name, mask in color_channels.items():
        count = cv2.countNonZero(mask)
        if count > 0:
            print(f"    {name}: {count} 個像素")
            # 保存通道圖片
            cv2.imwrite(f"channel_{name}.png", mask)
    
    print("\n步驟 2: 移除陰影...")
    shadow_removed = recognizer.remove_shadow(img)
    cv2.imwrite("shadow_removed.png", shadow_removed)
    print("  ✓ 已保存: shadow_removed.png")
    
    print("\n步驟 3: 提取文字輪廓...")
    gray = cv2.cvtColor(shadow_removed, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contour_result = recognizer.extract_text_by_contour(binary)
    cv2.imwrite("contour_result.png", contour_result)
    print("  ✓ 已保存: contour_result.png")
    
    print("\n✅ 自訂預處理完成")


def example_5_analyze_debug_images():
    """範例 5: 分析調試圖片 - 查看預處理效果"""
    print("\n" + "="*80)
    print("範例 5: 分析調試圖片")
    print("="*80)
    
    # 列出所有調試圖片
    debug_files = [f for f in os.listdir('.') if f.startswith('debug_') and f.endswith('.png')]
    
    if not debug_files:
        print("⚠️ 沒有找到調試圖片")
        print("請先執行識別並設定 save_debug=True")
        return
    
    debug_files.sort()
    
    print(f"找到 {len(debug_files)} 張調試圖片:")
    print()
    
    for i, filename in enumerate(debug_files, 1):
        # 讀取圖片
        img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        
        # 統計資訊
        white_pixels = cv2.countNonZero(img)
        total_pixels = img.shape[0] * img.shape[1]
        white_ratio = white_pixels / total_pixels * 100
        
        print(f"[{i:2d}] {filename}")
        print(f"     大小: {img.shape[1]}x{img.shape[0]}")
        print(f"     白色像素: {white_pixels} ({white_ratio:.1f}%)")
        print()


def main():
    """主函數"""
    print("\n" + "="*80)
    print("🎯 進階驗證碼識別器 - 使用範例")
    print("="*80)
    
    print("\n請選擇要執行的範例:")
    print("  1. 基本使用 - 從檔案識別")
    print("  2. 截圖識別 - 從螢幕截取")
    print("  3. 批次識別 - 識別多張圖片")
    print("  4. 自訂預處理 - 手動控制流程")
    print("  5. 分析調試圖片 - 查看預處理效果")
    print("  0. 執行所有範例")
    
    choice = input("\n請輸入選項 (0-5): ").strip()
    
    if choice == "1":
        example_1_basic_recognition()
    elif choice == "2":
        example_2_screenshot_recognition()
    elif choice == "3":
        example_3_batch_recognition()
    elif choice == "4":
        example_4_custom_preprocessing()
    elif choice == "5":
        example_5_analyze_debug_images()
    elif choice == "0":
        example_1_basic_recognition()
        example_3_batch_recognition()
        example_4_custom_preprocessing()
        example_5_analyze_debug_images()
    else:
        print("❌ 無效的選項")


if __name__ == "__main__":
    main()
