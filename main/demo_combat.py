# -*- coding: utf-8 -*-
"""
ChroLens 自動戰鬥系統 - 快速演示
展示完整的自動打怪流程
"""

import time
import sys
import os

# 添加路徑
sys.path.insert(0, os.path.dirname(__file__))

from auto_combat_system import AutoCombatSystem
from image_recognition import ImageRecognition


def demo_move_to_image():
    """演示1: 滑鼠移動到圖片"""
    print("\n" + "=" * 60)
    print("演示1: 滑鼠移動到圖片中心")
    print("=" * 60)
    
    ir = ImageRecognition(confidence=0.75)
    
    # 選擇測試圖片
    templates_dir = os.path.join(os.path.dirname(__file__), "images", "templates")
    
    if not os.path.exists(templates_dir):
        print(f"✗ 圖片目錄不存在: {templates_dir}")
        print("請先創建目錄並放入測試圖片")
        return
    
    # 列出圖片
    images = [f for f in os.listdir(templates_dir) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not images:
        print("✗ 沒有找到圖片")
        return
    
    print(f"\n找到 {len(images)} 個圖片:")
    for i, img in enumerate(images[:5], 1):  # 只顯示前5個
        print(f"  {i}. {img}")
    
    if len(images) > 5:
        print(f"  ... 還有 {len(images) - 5} 個")
    
    choice = input(f"\n選擇要測試的圖片 (1-{min(5, len(images))}) 或按Enter跳過: ").strip()
    
    if not choice:
        print("跳過演示1")
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(images):
            test_image = os.path.join(templates_dir, images[idx])
            
            print(f"\n測試圖片: {images[idx]}")
            print("⏳ 搜尋圖片... (請確保圖片在螢幕上可見)")
            
            # 移動到圖片
            center = ir.move_to_image(test_image, duration=0.5)
            
            if center:
                print(f"✅ 成功! 滑鼠已移動到 {center}")
                print("(觀察滑鼠游標是否在圖片中心)")
            else:
                print("❌ 失敗: 未找到圖片")
        else:
            print("無效的選擇")
    except:
        print("輸入錯誤")


def demo_click_image():
    """演示2: 點擊圖片"""
    print("\n" + "=" * 60)
    print("演示2: 智能點擊圖片")
    print("=" * 60)
    
    ir = ImageRecognition(confidence=0.75)
    
    templates_dir = os.path.join(os.path.dirname(__file__), "images", "templates")
    
    if not os.path.exists(templates_dir):
        print("✗ 圖片目錄不存在")
        return
    
    images = [f for f in os.listdir(templates_dir) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not images:
        print("✗ 沒有找到圖片")
        return
    
    print(f"\n找到 {len(images)} 個圖片:")
    for i, img in enumerate(images[:5], 1):
        print(f"  {i}. {img}")
    
    choice = input(f"\n選擇要點擊的圖片 (1-{min(5, len(images))}) 或按Enter跳過: ").strip()
    
    if not choice:
        print("跳過演示2")
        return
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(images):
            test_image = os.path.join(templates_dir, images[idx])
            
            print(f"\n測試圖片: {images[idx]}")
            print("⏳ 搜尋並點擊... (請確保圖片在螢幕上可見)")
            print("⚠️ 注意: 3秒後將自動點擊!")
            
            time.sleep(3)
            
            # 點擊圖片
            success = ir.click_image(test_image, duration=0.5, move_first=True)
            
            if success:
                print("✅ 成功點擊!")
            else:
                print("❌ 失敗: 未找到圖片")
    except:
        print("輸入錯誤")


def demo_combat_system():
    """演示3: 自動戰鬥系統"""
    print("\n" + "=" * 60)
    print("演示3: 自動戰鬥系統 (模擬)")
    print("=" * 60)
    
    # 創建系統
    combat = AutoCombatSystem()
    
    # 配置
    combat.set_config(
        attack_key="1",
        skill_keys=["q", "w", "e"],
        move_duration=0.3,
        attack_delay=0.5,
        scan_interval=1.0
    )
    
    # 設定圖片 (示範用)
    templates_dir = os.path.join(os.path.dirname(__file__), "images", "templates")
    
    if os.path.exists(templates_dir):
        images = [f for f in os.listdir(templates_dir) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if images:
            print(f"\n使用測試圖片: {images[0]}")
            combat.set_templates(
                enemy=[images[0]]  # 使用第一張圖片作為敵人
            )
    
    # 設定回調
    def on_enemy_found(location):
        print(f"  🎯 發現敵人於: {location}")
    
    def on_attack(key):
        print(f"  ⚔️ 攻擊: 按下 {key}")
    
    combat.set_callback("on_enemy_found", on_enemy_found)
    combat.set_callback("on_attack", on_attack)
    
    print("\n配置完成!")
    print("系統將運行5秒鐘...")
    print("(如果找不到圖片,會持續搜尋)")
    
    choice = input("\n按 Enter 開始,或輸入 n 跳過: ").strip().lower()
    
    if choice == 'n':
        print("跳過演示3")
        return
    
    # 啟動
    combat.start()
    
    try:
        print("\n🎮 戰鬥系統運行中...")
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n中斷")
    finally:
        combat.stop()


def main():
    """主程式"""
    print("=" * 60)
    print("ChroLens 自動戰鬥系統 - 快速演示")
    print("=" * 60)
    print()
    print("這個演示將展示:")
    print("1. 滑鼠移動到圖片中心")
    print("2. 智能點擊圖片")
    print("3. 自動戰鬥系統運作")
    print()
    print("⚠️ 注意事項:")
    print("- 請先準備測試圖片放在 images/templates/ 目錄")
    print("- 測試時請將圖片顯示在螢幕上")
    print("- 點擊功能會真實點擊滑鼠,請注意!")
    print()
    
    ready = input("準備好了嗎? (y/N): ").strip().lower()
    
    if ready != 'y':
        print("已取消")
        return
    
    try:
        # 演示1: 移動滑鼠
        demo_move_to_image()
        
        input("\n按 Enter 繼續下一個演示...")
        
        # 演示2: 點擊圖片
        demo_click_image()
        
        input("\n按 Enter 繼續下一個演示...")
        
        # 演示3: 戰鬥系統
        demo_combat_system()
        
        print("\n" + "=" * 60)
        print("演示完成!")
        print("=" * 60)
        print()
        print("📚 更多資訊請參考:")
        print("- AUTO_COMBAT_GUIDE.md - 完整使用指南")
        print("- 範例_自動戰鬥腳本.txt - 腳本範例")
        print("- combat_command_parser.py - 指令解析器")
        print()
        
    except KeyboardInterrupt:
        print("\n\n演示已中斷")
    except Exception as e:
        print(f"\n\n演示過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except:
        pass
    
    input("\n按 Enter 鍵退出...")
