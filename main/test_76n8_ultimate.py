"""
76N8 強噪點驗證碼測試工具
測試新的終極策略對強噪點的處理能力
"""

import cv2
import numpy as np
import sys
import os

# 添加 main 目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from captcha_recognition import CaptchaRecognizer


def test_captcha_image(image_path: str):
    """
    測試驗證碼圖片
    :param image_path: 圖片路徑
    """
    print("\n" + "="*70)
    print("🔬 76N8 強噪點驗證碼測試工具")
    print("="*70)
    
    # 檢查圖片是否存在
    if not os.path.exists(image_path):
        print(f"❌ 找不到圖片: {image_path}")
        print("\n使用方法:")
        print("  1. 將驗證碼圖片保存為 '76n8_captcha.png'")
        print("  2. 執行: python test_76n8_ultimate.py 76n8_captcha.png")
        return
    
    # 讀取圖片
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ 無法讀取圖片: {image_path}")
        return
    
    print(f"✓ 成功讀取圖片: {image_path}")
    print(f"  圖片尺寸: {img.shape[1]} x {img.shape[0]}")
    
    # 轉灰階
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    
    # 初始化識別器
    recognizer = CaptchaRecognizer()
    
    if not recognizer.tesseract_available:
        print("\n❌ Tesseract OCR 未安裝或無法使用")
        print("請確保已安裝:")
        print("  1. pip install pytesseract")
        print("  2. Tesseract-OCR 執行檔 (https://github.com/tesseract-ocr/tesseract)")
        return
    
    print("\n" + "="*70)
    print("🚀 開始測試所有策略...")
    print("="*70 + "\n")
    
    # 測試策略列表
    strategies = [
        ("strategy9", "終極噪點殺手（多階段漸進式處理）"),
        ("strategy10", "頻域噪點殺手（傅立葉變換）"),
        ("strategy6", "極致降噪 + 連通組件分析"),
        ("strategy7", "頻域濾波 + 自適應閾值"),
        ("strategy8", "多尺度處理 + 投票機制"),
        ("strategy5", "形態學重建 + 距離變換"),
        ("strategy1", "超強放大 + 多次降噪"),
        ("strategy2", "雙邊濾波 + CLAHE"),
    ]
    
    all_results = []
    debug_images = {}
    
    for strategy_name, strategy_desc in strategies:
        print(f"📋 測試 {strategy_name}: {strategy_desc}")
        print("-" * 70)
        
        try:
            # 預處理圖片
            processed = recognizer.preprocess_image(gray.copy(), method=strategy_name)
            
            # 保存除錯圖片
            debug_filename = f"debug_{strategy_name}.png"
            cv2.imwrite(debug_filename, processed)
            debug_images[strategy_name] = debug_filename
            print(f"  💾 已保存除錯圖片: {debug_filename}")
            
            # 嘗試多個 PSM 模式進行 OCR
            psm_modes = [6, 7, 8, 10, 11, 13]
            strategy_results = []
            
            for psm in psm_modes:
                result = recognizer.recognize_with_tesseract_psm(
                    processed, 
                    char_type="alphanumeric", 
                    psm=psm
                )
                
                if result and len(result) >= 3:
                    strategy_results.append(result)
                    all_results.append((result, f"{strategy_name}-PSM{psm}"))
                    print(f"    PSM {psm:2d}: '{result}'")
            
            if not strategy_results:
                print(f"    ⚠️  未識別出結果")
            
        except Exception as e:
            print(f"    ❌ 執行失敗: {e}")
        
        print()
    
    # 統計分析
    print("="*70)
    print("📊 統計分析")
    print("="*70 + "\n")
    
    if all_results:
        from collections import Counter
        
        # 統計所有結果
        result_counts = Counter([r for r, _ in all_results])
        
        print(f"總共獲得 {len(all_results)} 個有效結果\n")
        
        print("📈 結果統計 (按出現次數排序):")
        print("-" * 70)
        for result, count in result_counts.most_common(10):
            percentage = (count / len(all_results)) * 100
            sources = [s for r, s in all_results if r == result]
            print(f"  '{result}' - 出現 {count} 次 ({percentage:.1f}%)")
            print(f"    來源: {', '.join(sources[:3])}" + 
                  (f" ... 等 {len(sources)} 個" if len(sources) > 3 else ""))
        
        print("\n" + "="*70)
        print("🎯 推薦結果")
        print("="*70 + "\n")
        
        # 選擇最佳結果
        most_common = result_counts.most_common(1)[0]
        
        if most_common[1] >= 3:
            # 如果某個結果出現 3 次以上，高度信任
            best_result = most_common[0]
            confidence = "極高" if most_common[1] >= 5 else "高"
            print(f"✅ 最可能結果: '{best_result}' (置信度: {confidence})")
            print(f"   出現次數: {most_common[1]}/{len(all_results)}")
        elif most_common[1] >= 2:
            # 出現 2 次，中等信任
            best_result = most_common[0]
            print(f"⚠️  可能結果: '{best_result}' (置信度: 中)")
            print(f"   出現次數: {most_common[1]}/{len(all_results)}")
        else:
            # 沒有重複，選最長的
            best_result = max(all_results, key=lambda x: len(x[0]))[0]
            print(f"❓ 不確定結果: '{best_result}' (置信度: 低)")
            print(f"   建議: 檢查除錯圖片後手動確認")
        
        # 如果正確答案是 76N8，進行驗證
        if '76N8' in [r for r, _ in all_results]:
            print(f"\n🎉 成功識別! 正確答案 '76N8' 已在結果中")
        elif best_result.upper() == '76N8':
            print(f"\n🎉 最佳結果匹配! 識別為 '{best_result}'")
        else:
            print(f"\n💡 提示: 正確答案應為 '76N8'")
            print(f"   實際識別: '{best_result}'")
            print(f"   建議: 查看除錯圖片 {list(debug_images.values())}")
        
    else:
        print("❌ 所有策略均未能識別出結果")
        print("\n建議:")
        print("  1. 檢查 Tesseract OCR 是否正確安裝")
        print("  2. 查看除錯圖片，確認預處理效果")
        print("  3. 如果圖片噪點特別強，可能需要進一步調整參數")
    
    print("\n" + "="*70)
    print("💾 除錯圖片位置:")
    print("="*70)
    for strategy, filename in debug_images.items():
        print(f"  {strategy}: {filename}")
    
    print("\n✅ 測試完成!\n")


def main():
    if len(sys.argv) < 2:
        print("\n使用方法:")
        print("  python test_76n8_ultimate.py <驗證碼圖片路徑>")
        print("\n範例:")
        print("  python test_76n8_ultimate.py 76n8_captcha.png")
        print("  python test_76n8_ultimate.py captcha.jpg")
        
        # 嘗試使用預設檔名
        default_files = ['76n8_captcha.png', 'captcha.png', 'test.png']
        for filename in default_files:
            if os.path.exists(filename):
                print(f"\n✓ 找到預設圖片: {filename}")
                test_captcha_image(filename)
                return
        
        print("\n❌ 找不到預設圖片，請指定圖片路徑")
        return
    
    image_path = sys.argv[1]
    test_captcha_image(image_path)


if __name__ == "__main__":
    main()
