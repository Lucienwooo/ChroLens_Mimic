# -*- coding: utf-8 -*-
"""
測試圖片識別 - 中文路徑支援
快速測試腳本
"""

import os
import sys

# 添加主目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from image_recognition import ImageRecognition

def test_image_recognition():
    """測試圖片識別功能"""
    
    print("=" * 60)
    print("ChroLens 圖片識別測試")
    print("=" * 60)
    print()
    
    # 測試圖片路徑
    test_dir = os.path.join(os.path.dirname(__file__), "images", "templates")
    
    if not os.path.exists(test_dir):
        print(f"✗ 圖片目錄不存在: {test_dir}")
        print("請先創建 images/templates/ 目錄並放入測試圖片")
        return
    
    # 列出所有圖片
    print(f"📁 掃描圖片目錄: {test_dir}")
    print()
    
    image_files = []
    for file in os.listdir(test_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            image_files.append(file)
    
    if not image_files:
        print("✗ 沒有找到任何圖片檔案")
        print("請在 images/templates/ 目錄中放入測試圖片")
        return
    
    print(f"找到 {len(image_files)} 個圖片:")
    for i, file in enumerate(image_files, 1):
        print(f"  {i}. {file}")
    print()
    
    # 讓使用者選擇
    try:
        choice = input(f"請選擇要測試的圖片 (1-{len(image_files)}) 或按Enter測試全部: ").strip()
        
        if choice:
            idx = int(choice) - 1
            if 0 <= idx < len(image_files):
                test_files = [image_files[idx]]
            else:
                print("無效的選擇")
                return
        else:
            test_files = image_files
    except:
        print("輸入錯誤")
        return
    
    print()
    print("=" * 60)
    print("開始測試...")
    print("=" * 60)
    print()
    
    # 創建識別器
    ir = ImageRecognition(confidence=0.75)
    
    # 測試每個圖片
    for file in test_files:
        print(f"📋 測試: {file}")
        print("-" * 60)
        
        full_path = os.path.join(test_dir, file)
        
        # 1. 測試載入
        print("  ⏳ 載入圖片...")
        template = ir._load_template(full_path)
        
        if template is None:
            print("  ✗ 載入失敗")
            print()
            continue
        
        h, w = template.shape[:2]
        print(f"  ✓ 載入成功 ({w}x{h} px)")
        
        # 2. 測試識別
        print("  ⏳ 搜尋圖片 (可能需要幾秒)...")
        location = ir.find_image(full_path, multi_scale=True, grayscale=True)
        
        if location:
            x, y, w, h = location
            center = ir.get_image_center(location)
            print(f"  ✓ 找到圖片!")
            print(f"     位置: ({x}, {y})")
            print(f"     尺寸: {w}x{h} px")
            print(f"     中心: {center}")
        else:
            print("  ✗ 未找到圖片")
            print("     提示:")
            print("     - 確認圖片在螢幕上可見")
            print("     - 圖片不能被其他視窗遮擋")
            print("     - 嘗試使用更小或更清晰的圖片")
        
        print()
    
    print("=" * 60)
    print("測試完成!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_image_recognition()
    except KeyboardInterrupt:
        print("\n\n測試已取消")
    except Exception as e:
        print(f"\n\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按Enter鍵退出...")
