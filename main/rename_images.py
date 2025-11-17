# -*- coding: utf-8 -*-
"""
圖片重命名工具
將中文檔名轉為英文,避免OpenCV路徑問題
"""

import os
import shutil
from datetime import datetime

def rename_images():
    """批量重命名圖片"""
    
    print("=" * 60)
    print("ChroLens 圖片重命名工具")
    print("=" * 60)
    print()
    
    # 圖片目錄
    templates_dir = os.path.join(os.path.dirname(__file__), "images", "templates")
    
    if not os.path.exists(templates_dir):
        print(f"✗ 目錄不存在: {templates_dir}")
        return
    
    # 掃描圖片
    image_files = []
    for file in os.listdir(templates_dir):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            # 檢查是否包含中文或空格
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in file)
            has_space = ' ' in file
            
            if has_chinese or has_space:
                image_files.append(file)
    
    if not image_files:
        print("✓ 沒有需要重命名的圖片!")
        print("(所有圖片檔名都是純英文且不含空格)")
        return
    
    print(f"找到 {len(image_files)} 個需要重命名的圖片:")
    print()
    
    # 建議重命名
    rename_plan = []
    for i, old_name in enumerate(image_files, 1):
        # 取得副檔名
        name, ext = os.path.splitext(old_name)
        
        # 建議新名稱
        if "螢幕擷取畫面" in old_name or "截圖" in old_name:
            # 截圖類
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"screenshot_{date_str}_{i:02d}{ext}"
        else:
            # 一般圖片
            new_name = f"image_{i:02d}{ext}"
        
        rename_plan.append((old_name, new_name))
        print(f"  {i}. {old_name}")
        print(f"     → {new_name}")
        print()
    
    # 確認
    choice = input("是否執行重命名? (y/N): ").strip().lower()
    
    if choice != 'y':
        print("已取消")
        return
    
    print()
    print("=" * 60)
    print("開始重命名...")
    print("=" * 60)
    print()
    
    # 創建備份目錄
    backup_dir = os.path.join(templates_dir, "_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(backup_dir, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    for old_name, new_name in rename_plan:
        old_path = os.path.join(templates_dir, old_name)
        new_path = os.path.join(templates_dir, new_name)
        backup_path = os.path.join(backup_dir, old_name)
        
        try:
            # 備份
            shutil.copy2(old_path, backup_path)
            
            # 重命名
            os.rename(old_path, new_path)
            
            print(f"✓ {old_name} → {new_name}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ {old_name} 失敗: {e}")
            fail_count += 1
    
    print()
    print("=" * 60)
    print("重命名完成!")
    print("=" * 60)
    print(f"成功: {success_count} 個")
    print(f"失敗: {fail_count} 個")
    print(f"備份位置: {backup_dir}")
    print()
    print("💡 提示:")
    print("   - 原始檔案已備份")
    print("   - 如需還原,可從備份目錄複製回來")
    print("   - 建議之後手動給圖片取有意義的英文名稱")
    print("     例如: button_start.png, icon_settings.png")


def suggest_names():
    """建議有意義的英文檔名"""
    
    print()
    print("=" * 60)
    print("常用圖片命名建議")
    print("=" * 60)
    print()
    
    suggestions = {
        "按鈕類": [
            "button_start.png - 開始按鈕",
            "button_ok.png - 確定按鈕",
            "button_cancel.png - 取消按鈕",
            "button_close.png - 關閉按鈕",
            "button_menu.png - 選單按鈕",
        ],
        "圖示類": [
            "icon_app.png - 應用程式圖示",
            "icon_settings.png - 設定圖示",
            "icon_help.png - 說明圖示",
            "icon_home.png - 首頁圖示",
        ],
        "UI元素": [
            "input_username.png - 使用者名稱輸入框",
            "input_password.png - 密碼輸入框",
            "checkbox_accept.png - 同意勾選框",
            "dropdown_menu.png - 下拉選單",
        ],
        "狀態類": [
            "status_online.png - 線上狀態",
            "status_error.png - 錯誤訊息",
            "status_success.png - 成功提示",
            "loading_spinner.png - 載入中",
        ],
        "遊戲類": [
            "game_enemy.png - 敵人",
            "game_item.png - 道具",
            "game_hp_low.png - 血量低警告",
            "game_skill_ready.png - 技能準備完成",
        ]
    }
    
    for category, names in suggestions.items():
        print(f"【{category}】")
        for name in names:
            print(f"  {name}")
        print()


if __name__ == "__main__":
    try:
        rename_images()
        
        show_suggestions = input("\n是否顯示命名建議? (y/N): ").strip().lower()
        if show_suggestions == 'y':
            suggest_names()
            
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按Enter鍵退出...")
